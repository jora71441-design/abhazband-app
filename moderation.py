import asyncio
import html
import logging
import random
from typing import Any, Callable, Dict, Tuple
from aiohttp import ClientSession

CAPTCHA_TIMEOUT_SEC = 50  # 50 секунд на прохождение капчи

CORRECT_EMOJI = "🚲"
DECOY_EMOJIS = ["🍕", "🚗", "🎸", "🚀", "🌵", "⚽", "🍔", "🛸", "🕶️", "🎲"]

# Активные капчи: (chat_id, user_id) -> {"msg_id": int, "task": asyncio.Task, "mention": str}
PENDING_CAPTCHAS: Dict[Tuple[int, int], Dict[str, Any]] = {}

WELCOME_TEXT_TEMPLATE = (
    "Добро пожаловать в чат ❤️Abhaz🤍Band💚, {mention}!\n"
    "Теперь ты часть большой велобанды 🤗\n\n"
    "Вся информация про события, заезды, кэмпы и велодайджест живёт в нашем боте: @AbhazBand_ai.\n"
    "Любые вопросы о подборе, покупке и умном поиске: @liferidelife_ai\n"
    "Задавай любые вопросы — мы всегда поможем!"
)


def _user_mention(user: dict) -> str:
    if user.get("username"):
        return f"@{html.escape(user['username'])}"
    uid = user.get("id", 0)
    name = html.escape(user.get("first_name") or "Райдер")
    return f'<a href="tg://user?id={uid}">{name}</a>'


async def _restrict_user(
    tg_request: Callable,
    session: ClientSession,
    chat_id: int,
    user_id: int,
    can_send: bool,
) -> dict:
    permissions = {
        "can_send_messages": can_send,
        "can_send_audios": can_send,
        "can_send_documents": can_send,
        "can_send_photos": can_send,
        "can_send_videos": can_send,
        "can_send_video_notes": can_send,
        "can_send_voice_notes": can_send,
        "can_send_polls": can_send,
        "can_send_other_messages": can_send,
        "can_add_web_page_previews": can_send,
    }
    return await tg_request(
        session,
        "restrictChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "permissions": permissions,
        },
    )


async def _kick_user_soft(
    tg_request: Callable,
    session: ClientSession,
    chat_id: int,
    user_id: int,
    msg_id: int,
    reason: str,
):
    """Удаляет сообщение капчи и мягко кикает пользователя (ban + unban)."""
    try:
        await tg_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": msg_id})
        await tg_request(session, "banChatMember", {"chat_id": chat_id, "user_id": user_id})
        await tg_request(session, "unbanChatMember", {"chat_id": chat_id, "user_id": user_id, "only_if_banned": True})
        logging.info(f"🛡 Антиспам: пользователь {user_id} кикнут ({reason}) из чата {chat_id}")
    except Exception as exc:
        logging.warning(f"Ошибка кика ({chat_id}, {user_id}): {exc}")


async def _captcha_timeout_worker(
    tg_request: Callable,
    session: ClientSession,
    chat_id: int,
    user_id: int,
    msg_id: int,
):
    try:
        await asyncio.sleep(CAPTCHA_TIMEOUT_SEC)
        key = (chat_id, user_id)
        if key not in PENDING_CAPTCHAS:
            return
        PENDING_CAPTCHAS.pop(key, None)
        await _kick_user_soft(tg_request, session, chat_id, user_id, msg_id, "таймаут капчи")
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logging.warning(f"Ошибка таймаута капчи ({chat_id}, {user_id}): {exc}")


def _build_emoji_captcha_keyboard(uid: int) -> dict:
    decoys = random.sample(DECOY_EMOJIS, 3)
    options = [(CORRECT_EMOJI, f"cap_ok:{uid}:1")] + [
        (em, f"cap_ok:{uid}:0:{idx}") for idx, em in enumerate(decoys)
    ]
    random.shuffle(options)
    return {
        "inline_keyboard": [
            [{"text": em, "callback_data": cb} for em, cb in options]
        ]
    }


async def handle_new_chat_members(
    tg_request: Callable,
    send_message: Callable,
    session: ClientSession,
    message: dict,
):
    """Обработка входа новых участников в группу: чистка сервисного сообщения + эмодзи-капча."""
    chat = message.get("chat", {})
    if chat.get("type") not in ("group", "supergroup"):
        return

    chat_id = chat["id"]
    msg_id = message.get("message_id")
    members = message.get("new_chat_members") or []

    # Удаляем системное сообщение «вступил в группу»
    if msg_id:
        try:
            await tg_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": msg_id})
        except Exception:
            pass

    for member in members:
        if member.get("is_bot"):
            continue
        uid = member.get("id")
        if not uid:
            continue

        mention = _user_mention(member)
        await _restrict_user(tg_request, session, chat_id, uid, can_send=False)

        kb = _build_emoji_captcha_keyboard(uid)
        res = await send_message(
            session,
            chat_id,
            f"👋 Привет, {mention}!\n"
            f"<b>Нажми на велосипед, чтобы войти</b> в чат ❤️Abhaz🤍Band💚 "
            f"(у тебя есть <b>{CAPTCHA_TIMEOUT_SEC} секунд</b>).",
            reply_markup=kb,
        )
        cap_msg_id = res.get("result", {}).get("message_id") if res.get("ok") else None
        if cap_msg_id:
            key = (chat_id, uid)
            old = PENDING_CAPTCHAS.pop(key, None)
            if old and old.get("task"):
                old["task"].cancel()
            task = asyncio.create_task(
                _captcha_timeout_worker(tg_request, session, chat_id, uid, cap_msg_id)
            )
            PENDING_CAPTCHAS[key] = {
                "msg_id": cap_msg_id,
                "task": task,
                "mention": mention,
            }


async def handle_left_chat_member(
    tg_request: Callable,
    session: ClientSession,
    message: dict,
):
    """Удаляет системное сообщение «покинул группу»."""
    chat = message.get("chat", {})
    if chat.get("type") not in ("group", "supergroup"):
        return
    msg_id = message.get("message_id")
    if msg_id:
        try:
            await tg_request(session, "deleteMessage", {"chat_id": chat["id"], "message_id": msg_id})
        except Exception:
            pass


async def handle_captcha_callback(
    tg_request: Callable,
    edit_message: Callable,
    session: ClientSession,
    callback_query: dict,
    miniapp_url: str,
) -> bool:
    """Обработка нажатия кнопки эмодзи-капчи. Возвращает True, если callback обработан."""
    data = callback_query.get("data", "")
    if not data.startswith("cap_ok:"):
        return False

    cb_id = callback_query["id"]
    clicker = callback_query.get("from", {})
    clicker_id = clicker.get("id")
    msg = callback_query.get("message", {})
    if not msg:
        return True

    chat_id = msg["chat"]["id"]
    msg_id = msg["message_id"]

    parts = data.split(":")
    try:
        target_uid = int(parts[1])
    except (IndexError, ValueError):
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return True

    if clicker_id != target_uid:
        await tg_request(
            session,
            "answerCallbackQuery",
            {
                "callback_query_id": cb_id,
                "text": "Эта кнопка только для нового участника чата 😉",
                "show_alert": True,
            },
        )
        return True

    is_correct = len(parts) < 3 or parts[2] == "1"

    key = (chat_id, target_uid)
    entry = PENDING_CAPTCHAS.pop(key, None)
    if entry and entry.get("task"):
        entry["task"].cancel()

    if not is_correct:
        await tg_request(
            session,
            "answerCallbackQuery",
            {
                "callback_query_id": cb_id,
                "text": "❌ Неверный выбор! Попробуй зайти в чат ещё раз.",
                "show_alert": True,
            },
        )
        await _kick_user_soft(tg_request, session, chat_id, target_uid, msg_id, "неверная кнопка капчи")
        return True

    # Снимаем ограничения
    await _restrict_user(tg_request, session, chat_id, target_uid, can_send=True)

    mention = entry["mention"] if entry and entry.get("mention") else _user_mention(clicker)
    welcome_text = WELCOME_TEXT_TEMPLATE.format(mention=mention)
    welcome_kb = {
        "inline_keyboard": [
            [{"text": "🚀 Открыть Abhaz Band Hub", "url": "https://t.me/AbhazBand_ai"}]
        ]
    }
    await edit_message(session, chat_id, msg_id, welcome_text, reply_markup=welcome_kb)
    await tg_request(
        session,
        "answerCallbackQuery",
        {"callback_query_id": cb_id, "text": "✅ Добро пожаловать в Abhaz Band!"},
    )
    return True
