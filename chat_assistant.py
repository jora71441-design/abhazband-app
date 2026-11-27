import datetime
import html
import logging
import re
import time
from typing import Any, Callable, Dict, List, Optional
from aiohttp import ClientSession

# Защита от навязчивости
CHAT_COOLDOWN_SEC = 1800    # Не чаще 1 ответа в 30 минут на весь чат
USER_COOLDOWN_SEC = 86400   # Не чаще 1 ответа в сутки одному пользователю
MIN_TEXT_LENGTH = 20        # Игнорируем короткие реплики

_LAST_CHAT_REPLY: Dict[int, float] = {}
_LAST_USER_REPLY: Dict[int, float] = {}

# Маркеры вопроса / запроса помощи
QUESTION_MARKERS = (
    "?",
    "подскаж",
    "посовету",
    "кто-то",
    "кто то",
    "кто-нибудь",
    "кто нибудь",
    "есть кто",
    "где ",
    "когда ",
    "сколько ",
    "куда ",
    "какой ",
    "какую ",
    "какие ",
    "ищу ",
    "собираюсь",
    "планирую",
    "еду в ",
    "лечу в ",
    "можно ли",
    "есть ли",
)

# Корни по 4 интентам (порядок важен: от более узких к более общим)
INTENT_RULES = [
    (
        "camps",
        (
            "кэмп", "кемп", "новогодн", "майск", "сборы", "велосбор", "велолагер",
        ),
    ),
    (
        "bike",
        (
            "гравийник", "гравел", "шоссейник", "шоссер", "фреймсет", "групсет",
            "di2", "axs", "wheeltop", "l-twoo", "winspace", "размер рам",
            "купить вел", "подобрать вел", "выбрать вел", "покрышк", "колёс", "колес",
        ),
    ),
    (
        "tools",
        (
            "давлен", "качать", " psi", " bar", "байкфит", "bikefit", "bike-fit",
            "посадк", "где поесть", "покушать", "столов", "кафе в гагр",
        ),
    ),
    (
        "rides",
        (
            "гагр", "сухум", "пицунд", "мюссер", "абхаз", "покатат", "катать",
            "катнуть", "выезд", "заезд", "компани", "выходн", "маршрут",
        ),
    ),
]


def _has_question_marker(low_text: str) -> bool:
    return any(marker in low_text for marker in QUESTION_MARKERS)


def _detect_intent(low_text: str) -> Optional[str]:
    for intent, roots in INTENT_RULES:
        if any(root in low_text for root in roots):
            return intent
    return None


def _get_upcoming_rides_preview(rides_data: Dict[str, Any], limit: int = 2) -> List[str]:
    today_str = datetime.date.today().isoformat()
    seen = set()
    lines: List[str] = []
    for date_key in sorted(rides_data.keys()):
        if date_key < today_str:
            continue
        item = rides_data[date_key]
        sig = (item.get("title"), item.get("date_display"))
        if sig in seen:
            continue
        seen.add(sig)
        disp = html.escape(item.get("date_display") or date_key)
        title = html.escape(item.get("title") or "Выезд Abhaz Band")
        lines.append(f"• {item.get('type', '🚴')} <b>{disp}</b> — {title}")
        if len(lines) >= limit:
            break
    return lines


def _build_reply_payload(
    intent: str,
    rides_data: Dict[str, Any],
    camps_data: List[Dict[str, Any]],
    bot_username: str,
) -> Optional[Dict[str, Any]]:
    bot_link = f"https://t.me/{bot_username}"

    if intent == "rides":
        upcoming = _get_upcoming_rides_preview(rides_data, limit=2)
        if upcoming:
            rides_block = "\n".join(upcoming)
            text = (
                "Ребята в чате сейчас откликнутся, а ближайшие организованные выезды "
                "с техничкой и кофе уже есть в календаре:\n\n"
                f"{rides_block}"
            )
        else:
            text = (
                "Ребята в чате сейчас подскажут по компании, а актуальное расписание "
                "наших выездов и маршрутов по Абхазии всегда под рукой в календаре:"
            )
        markup = {
            "inline_keyboard": [
                [{"text": "📅 Открыть календарь заездов", "url": f"{bot_link}?startapp=calendar"}]
            ]
        }
        return {"text": text, "reply_markup": markup}

    if intent == "camps":
        if camps_data:
            c = camps_data[0]
            c_title = html.escape(c.get("title") or "Кэмп Abhaz Band")
            c_dates = html.escape(c.get("dates") or "")
            text = (
                f"Ближайший клубный кэмп — <b>{c_title}</b> ({c_dates}).\n"
                "Подробная программа, маршруты и бронирование слота — в нашем хабе:"
            )
        else:
            text = "Актуальное расписание кэмпов Abhaz Band, программы и свободные слоты — в нашем хабе:"
        markup = {
            "inline_keyboard": [
                [{"text": "🏕 Программа кэмпов", "url": f"{bot_link}?startapp=camps"}]
            ]
        }
        return {"text": text, "reply_markup": markup}

    if intent == "bike":
        text = (
            "Ребята сейчас поделятся опытом, а если нужен точный подбор велосипеда, "
            "рамы или комплектующих с доставкой — загляни к нашему помощнику @liferidelife_ai:"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "🚲 Подбор в LifeRideLife", "url": "https://t.me/liferidelife_ai"}]
            ]
        }
        return {"text": text, "reply_markup": markup}

    if intent == "tools":
        text = (
            "Кстати, в <b>Abhaz Band Hub</b> есть встроенный калькулятор давления в шинах, "
            "онлайн bike-fit и полезные инструменты для райдеров:"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "🛠 Открыть полезные фичи", "url": f"{bot_link}?startapp=features"}]
            ]
        }
        return {"text": text, "reply_markup": markup}

    return None


async def handle_group_message(
    tg_request: Callable,
    session: ClientSession,
    message: dict,
    admin_id: int,
    rides_data: Dict[str, Any],
    camps_data: List[Dict[str, Any]],
    bot_username: str,
) -> bool:
    """Уровень 1 (Python-фильтр): нативный ответ на типовые вопросы в групповом чате."""
    chat = message.get("chat", {})
    if chat.get("type") not in ("group", "supergroup"):
        return False

    user = message.get("from", {})
    user_id = user.get("id")
    if not user_id or user.get("is_bot") or user_id == admin_id:
        return False

    # Не влезаем в чужие ответы/диалоги
    if message.get("reply_to_message"):
        return False

    text = (message.get("text") or "").strip()
    if len(text) < MIN_TEXT_LENGTH or text.startswith("/"):
        return False

    chat_id = chat["id"]
    now = time.monotonic()

    if now - _LAST_CHAT_REPLY.get(chat_id, 0.0) < CHAT_COOLDOWN_SEC:
        return False
    if now - _LAST_USER_REPLY.get(user_id, 0.0) < USER_COOLDOWN_SEC:
        return False

    low_text = re.sub(r"\s+", " ", text.lower())
    if not _has_question_marker(low_text):
        return False

    intent = _detect_intent(low_text)
    if not intent:
        return False

    payload_data = _build_reply_payload(intent, rides_data, camps_data, bot_username)
    if not payload_data:
        return False

    res = await tg_request(
        session,
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": payload_data["text"],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_to_message_id": message.get("message_id"),
            "reply_markup": payload_data["reply_markup"],
        },
    )
    if res.get("ok"):
        _LAST_CHAT_REPLY[chat_id] = now
        _LAST_USER_REPLY[user_id] = now
        logging.info(f"💬 Чат-помощник: ответил в чате {chat_id} на интент '{intent}' (user={user_id})")
        return True
    return False
