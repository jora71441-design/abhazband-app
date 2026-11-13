import asyncio
import html
import logging
import os
from aiohttp import web, ClientSession
from github_uploader import process_uploaded_file, get_uploader_status
from widgets import build_hub_widget_html, parse_widget_action

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==================== КОНФИГУРАЦИЯ СЕРВЕРА ====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "AbhazBand_bot").strip().lstrip("@")
ADMIN_ID = int(os.getenv("ADMIN_ID", "303365656"))
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://jora71441-design.github.io/abhazband-app/").strip().rstrip("/")
PORT = int(os.getenv("PORT", "10000"))

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
THUMB_ICON_URL = f"{MINIAPP_URL}/Klubnie-compressed.jpeg"

# Карточки для инлайн-шеринга ТОЛЬКО в личных диалогах (в группах список пуст, чтобы не спамить)
PRIVATE_SHARE_CARDS = [
    {
        "id": "share_rides_nov",
        "title": "📅 Календарь заездов AbhazBand (Ноябрь–Декабрь)",
        "desc": "Weekend Camp Гагра—Сухум, Псоу—Пицунда, ИнгурГЭС, Мюссера",
        "text": (
            "📅 <b>Ближайшие выезды велоклуба AbhazBand:</b>\n"
            "• <b>14–15 Ноя:</b> Weekend Camp Гагра — Сухум (195 км, +1 950 м)\n"
            "• <b>21 Ноя:</b> Social Ride Псоу — Пицунда (85 км, +350 м)\n"
            "• <b>28–29 Ноя:</b> Восточный эпик ИнгурГЭС (220 км, +1 450 м)\n\n"
            "👉 Подробности, GPX и запись — в пульте @abhazband_ai"
        ),
        "btn_text": "🎛️ Открыть пульт управления",
        "btn_url": f"https://t.me/{BOT_USERNAME}?start=w_rides",
    },
    {
        "id": "share_camps_season",
        "title": "⛺ Велокэмпы AbhazBand в Гагре (Ноябрь — Январь)",
        "desc": "Клубные сборы, зимняя вкатка и Новогодний кэмп в Абхазии",
        "text": (
            "⛺ <b>Велокэмпы AbhazBand в Гагре:</b>\n"
            "• <b>Ноябрь:</b> Клубные заезды 4–10 дней (Шоссе / Гравел)\n"
            "• <b>Декабрь:</b> Зимняя вкатка по побережью и горам\n"
            "• <b>1–10 Января:</b> Новогодний кэмп в Абхазии\n\n"
            "👉 Программа и бронь слотов — в пульте @abhazband_ai"
        ),
        "btn_text": "⛺ Смотреть кэмпы в боте",
        "btn_url": f"https://t.me/{BOT_USERNAME}?start=w_camps",
    },
]


# ==================== TELEGRAM API HELPERS ====================
async def tg_request(session: ClientSession, method: str, payload: dict) -> dict:
    async with session.post(f"{API_URL}/{method}", json=payload) as resp:
        return await resp.json()


async def send_message(
    session: ClientSession, chat_id: int, text: str, reply_markup: dict | None = None
) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await tg_request(session, "sendMessage", payload)


async def send_hub_widget(
    session: ClientSession, chat_id: int, initial_tab: str = "overview", user_name: str = "Райдер"
) -> bool:
    """
    Отправляет HTML-виджет Bot API 10.4 (Обзор / Заезды / Кэмпы) в ЛС пользователю.
    Если версия клиента Telegram ещё не поддерживает sendWidget, отдаёт компактную карточку с кнопками.
    """
    widget_html = build_hub_widget_html(
        initial_tab=initial_tab,
        user_name=user_name,
        miniapp_url=MINIAPP_URL,
    )
    res = await tg_request(
        session,
        "sendWidget",
        {
            "chat_id": chat_id,
            "widget": {
                "type": "html",
                "html": widget_html,
                "height": 365,
            },
        },
    )
    if res.get("ok"):
        return True

    # Мягкий откат для необновлённых клиентов Telegram
    if initial_tab == "camps":
        text = (
            "⛺ <b>Велокэмпы AbhazBand в Гагре</b>\n\n"
            "• <b>5–30 Ноября:</b> Клубные заезды (Шоссе / Гравел, 4–10 дней)\n"
            "• <b>1–30 Декабря:</b> Зимняя вкатка без снега + Social Rides\n"
            "• <b>1–10 Января:</b> Новогодний кэмп в Абхазии\n\n"
            "Открой полную программу кэмпов или забронируй место:"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "📖 Полная программа кэмпов →", "web_app": {"url": f"{MINIAPP_URL}/?tab=camps"}}],
                [{"text": "🚴 Записаться (@Piti4)", "url": "https://t.me/Piti4"}],
            ]
        }
    elif initial_tab == "rides":
        text = (
            "📅 <b>Ближайшие заезды AbhazBand</b>\n\n"
            "• <b>14–15 Ноя:</b> Weekend Camp Гагра — Сухум (195 км, +1 950 м)\n"
            "• <b>21 Ноя:</b> Social Ride Псоу — Пицунда (85 км, +350 м)\n"
            "• <b>28–29 Ноя:</b> Восточный эпик ИнгурГЭС (220 км, +1 450 м)\n\n"
            "Открой весь календарь с треками GPX или займи слот:"
        )
        markup = {
            "inline_keyboard": [
                [{"text": "📅 Весь календарь и GPX →", "web_app": {"url": f"{MINIAPP_URL}/?tab=rides"}}],
                [{"text": "🚴 Записаться (@Piti4)", "url": "https://t.me/Piti4"}],
            ]
        }
    else:
        text = (
            "🏠 <b>Пульт велоклуба AbhazBand (Гагра, Абхазия)</b>\n\n"
            "Выбери интересующее направление:\n"
            "• <b>📅 Заезды:</b> уикенды и Social Rides на 1–2 дня от КПП Псоу\n"
            "• <b>⛺ Кэмпы:</b> многодневные шоссейные и гравел-сборы"
        )
        markup = {
            "inline_keyboard": [
                [
                    {"text": "📅 Заезды", "web_app": {"url": f"{MINIAPP_URL}/?tab=rides"}},
                    {"text": "⛺ Кэмпы", "web_app": {"url": f"{MINIAPP_URL}/?tab=camps"}},
                ],
                [{"text": "🚀 Открыть весь Abhaz Band Hub", "web_app": {"url": f"{MINIAPP_URL}/"}}],
            ]
        }

    fallback_res = await send_message(session, chat_id, text, reply_markup=markup)
    return bool(fallback_res.get("ok"))


# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================
async def handle_document(session: ClientSession, message: dict):
    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id")

    if user_id != ADMIN_ID:
        await send_message(session, chat_id, "⛔ Загрузка файлов в репозиторий доступна только администратору.")
        return

    doc = message["document"]
    filename = doc.get("file_name", "unknown_file")
    file_id = doc["file_id"]
    caption = message.get("caption", "")

    file_info = await tg_request(session, "getFile", {"file_id": file_id})
    if not file_info.get("ok"):
        await send_message(session, chat_id, "❌ Не удалось получить метаданные файла от Telegram.")
        return

    tg_file_path = file_info["result"]["file_path"]
    async with session.get(f"{FILE_URL}/{tg_file_path}") as f_resp:
        if f_resp.status != 200:
            await send_message(session, chat_id, "❌ Ошибка при скачивании файла с серверов Telegram.")
            return
        raw_bytes = await f_resp.read()

    report_text = await process_uploaded_file(session, filename, raw_bytes, caption)
    await send_message(session, chat_id, report_text)


async def handle_text(session: ClientSession, message: dict):
    chat_id = message["chat"]["id"]
    chat_type = message.get("chat", {}).get("type", "private")
    user = message.get("from", {})
    user_id = user.get("id")
    user_name = user.get("username") or user.get("first_name") or "Райдер"
    text = (message.get("text") or "").strip()

    # Закреп-навигатор в общем чате без спама при нажатии кнопок
    if text.startswith("/group_menu") and user_id == ADMIN_ID and chat_type in ("group", "supergroup"):
        await tg_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message["message_id"]})
        await send_message(
            session,
            chat_id,
            "🚴 <b>Пульт велоклуба AbhazBand</b>\n"
            "Выбери раздел ниже — я открою интерактивный виджет <b>тебе в личку</b>, "
            "не засоряя общий чат:",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "🏠 Обзор клуба", "callback_data": "pm_widget:overview"}],
                    [
                        {"text": "📅 Заезды", "callback_data": "pm_widget:rides"},
                        {"text": "⛺ Кэмпы", "callback_data": "pm_widget:camps"},
                    ],
                    [{"text": "🚀 Открыть Abhaz Band Hub", "url": f"https://t.me/{BOT_USERNAME}/app"}],
                ]
            },
        )
        return

    if chat_type != "private":
        return

    open_app_markup = {
        "inline_keyboard": [
            [{"text": "🚴 Открыть Abhaz Band Hub", "web_app": {"url": f"{MINIAPP_URL}/"}}],
            [{"text": "💬 Задать вопрос организатору (@Piti4)", "url": "https://t.me/Piti4"}],
        ]
    }

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        deep_param = parts[1].strip() if len(parts) > 1 else ""

        # Диплинки из инлайн-кнопки и группового закрепа -> сразу нужная вкладка виджета в ЛС
        if deep_param in ("hub", "w_overview"):
            await send_hub_widget(session, chat_id, initial_tab="overview", user_name=user_name)
            return
        if deep_param == "w_rides":
            await send_hub_widget(session, chat_id, initial_tab="rides", user_name=user_name)
            return
        if deep_param == "w_camps":
            await send_hub_widget(session, chat_id, initial_tab="camps", user_name=user_name)
            return

        if user_id == ADMIN_ID:
            await send_message(
                session,
                chat_id,
                "👋 <b>AbhazBand Dev & Widget Server в сети!</b>\n\n"
                "• Отправляй файлы кода документами в этот чат для автозаливки в GitHub.\n"
                "• Команда /widget — открыть стартовый пульт (Обзор / Заезды / Кэмпы).\n"
                "• Команда <code>/group_menu</code> в группе — опубликовать закреп-пульт без спама.\n"
                "• Команда /status — проверить токены.",
                reply_markup=open_app_markup,
            )
        else:
            await send_message(
                session,
                chat_id,
                "🚴 <b>Добро пожаловать в экосистему AbhazBand!</b>\n\n"
                "Жми /widget, чтобы открыть пульт с ближайшими заездами и кэмпами прямо в чате, "
                "или открой полный хаб по кнопке ниже:",
                reply_markup=open_app_markup,
            )

    elif text.startswith("/widget"):
        await send_hub_widget(session, chat_id, initial_tab="overview", user_name=user_name)

    elif text.startswith("/rides"):
        await send_hub_widget(session, chat_id, initial_tab="rides", user_name=user_name)

    elif text.startswith("/camps"):
        await send_hub_widget(session, chat_id, initial_tab="camps", user_name=user_name)

    elif text.startswith("/status") and user_id == ADMIN_ID:
        status_block = get_uploader_status()
        await send_message(
            session,
            chat_id,
            f"⚙️ <b>Статус сервера AbhazBand:</b>\n"
            f"• Bot Token: {'✅ задан' if BOT_TOKEN else '❌ отсутствует'}\n"
            f"{status_block}",
        )


async def handle_callback_query(session: ClientSession, callback_query: dict):
    """Тихая отправка виджета в ЛС по нажатию кнопок в общем чате."""
    cb_id = callback_query["id"]
    user = callback_query.get("from", {})
    user_id = user.get("id")
    user_name = user.get("username") or user.get("first_name") or "Райдер"
    data = callback_query.get("data", "")

    if data.startswith("pm_widget:"):
        tab = data.split(":", 1)[1]
        sent = await send_hub_widget(session, user_id, initial_tab=tab, user_name=user_name)
        if sent:
            await tg_request(
                session,
                "answerCallbackQuery",
                {
                    "callback_query_id": cb_id,
                    "text": "✅ Отправил виджет тебе в личку @AbhazBand_bot!",
                    "show_alert": False,
                },
            )
        else:
            await tg_request(
                session,
                "answerCallbackQuery",
                {
                    "callback_query_id": cb_id,
                    "url": f"https://t.me/{BOT_USERNAME}?start=w_{tab}",
                },
            )


async def handle_inline_query(session: ClientSession, inline_query: dict):
    """
    Инлайн-меню:
    - В общих группах список карточек ПУСТОЙ (ничего не падает в чат), работает только верхняя кнопка перехода в ЛС.
    - Пустой ввод открывает стартовый экран «🏠 Обзор», ввод слов 'кэмп' или 'заезд' — сразу нужную вкладку.
    """
    query_id = inline_query["id"]
    chat_type = inline_query.get("chat_type", "")
    q = (inline_query.get("query") or "").strip().lower()

    if any(word in q for word in ("кэмп", "camp")):
        btn_text = "⛺ Открыть расписание кэмпов в ЛС →"
        start_param = "w_camps"
    elif any(word in q for word in ("заезд", "уикенд", "райд", "календар", "ride", "weekend")):
        btn_text = "📅 Открыть календарь заездов в ЛС →"
        start_param = "w_rides"
    else:
        btn_text = "🎛️ Открыть пульт управления"
        start_param = "hub"

    results = []
    if chat_type == "private":
        for card in PRIVATE_SHARE_CARDS:
            if q and q not in card["title"].lower() and q not in card["desc"].lower():
                continue
            results.append(
                {
                    "type": "article",
                    "id": card["id"],
                    "title": card["title"],
                    "description": card["desc"],
                    "thumbnail_url": THUMB_ICON_URL,
                    "input_message_content": {
                        "message_text": card["text"],
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                    "reply_markup": {
                        "inline_keyboard": [[{"text": card["btn_text"], "url": card["btn_url"]}]]
                    },
                }
            )

    await tg_request(
        session,
        "answerInlineQuery",
        {
            "inline_query_id": query_id,
            "results": results,
            "cache_time": 10,
            "is_personal": True,
            "button": {
                "text": btn_text,
                "start_parameter": start_param,
            },
        },
    )


async def handle_widget_query(session: ClientSession, widget_query: dict):
    """Обработчик действий из HTML-виджета Bot API 10.4 (заявка на слот или переход в раздел Mini App)."""
    query_id = widget_query.get("id")
    user = widget_query.get("from", {})
    user_id = user.get("id")
    payload = parse_widget_action(widget_query.get("data", ""))
    action = payload.get("action")

    if action == "book_item":
        category_label = "Кэмп" if payload.get("category") == "camp" else "Заезд"
        item_title = html.escape(str(payload.get("title", "")))
        item_dates = html.escape(str(payload.get("dates", "")))
        uname = f"@{user['username']}" if user.get("username") else html.escape(user.get("first_name", "Райдер"))

        await send_message(
            session,
            ADMIN_ID,
            f"🚴 <b>Новая заявка из чат-виджета ({category_label})!</b>\n"
            f"• Программа: <b>{item_title}</b> ({item_dates})\n"
            f"• Участник: {uname} (ID: <code>{user_id}</code>)",
        )
        if query_id:
            await tg_request(
                session,
                "answerWidgetQuery",
                {"widget_query_id": query_id, "text": "✅ Заявка передана организатору!"},
            )
        return

    if action == "open_tab" and user_id:
        tab = payload.get("tab")
        if tab == "camps":
            msg_text = "📖 <b>Полное расписание и программы кэмпов AbhazBand:</b>"
            btn_text = "⛺ Открыть раздел «Кэмпы»"
            target_url = f"{MINIAPP_URL}/?tab=camps"
        elif tab == "rides":
            msg_text = "📅 <b>Полный интерактивный календарь заездов и треки GPX:</b>"
            btn_text = "📅 Открыть раздел «Календарь»"
            target_url = f"{MINIAPP_URL}/?tab=rides"
        else:
            msg_text = "🚴 <b>Abhaz Band Hub — все разделы клуба:</b>"
            btn_text = "🚀 Открыть Abhaz Band Hub"
            target_url = f"{MINIAPP_URL}/"

        await send_message(
            session,
            user_id,
            msg_text,
            reply_markup={
                "inline_keyboard": [[{"text": btn_text, "web_app": {"url": target_url}}]]
            },
        )
        if query_id:
            await tg_request(session, "answerWidgetQuery", {"widget_query_id": query_id})
        return

    if query_id:
        await tg_request(session, "answerWidgetQuery", {"widget_query_id": query_id})


# ==================== LONG POLLING & RENDER HTTP SERVER ====================
async def polling_loop(app: web.Application):
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN не задан! Polling остановлен.")
        return

    offset = 0
    async with ClientSession() as session:
        await tg_request(session, "deleteWebhook", {"drop_pending_updates": False})
        logging.info("Long polling для @AbhazBand_bot запущен.")

        while True:
            try:
                async with session.get(
                    f"{API_URL}/getUpdates",
                    params={
                        "offset": offset,
                        "timeout": 25,
                        "allowed_updates": ["message", "inline_query", "callback_query", "widget_query"],
                    },
                    timeout=35,
                ) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
                        logging.warning(f"Ответ Telegram API: {data}")
                        await asyncio.sleep(3)
                        continue

                    for update in data.get("result", []):
                        offset = update["update_id"] + 1

                        if "message" in update:
                            msg = update["message"]
                            if "document" in msg:
                                asyncio.create_task(handle_document(session, msg))
                            elif "text" in msg:
                                asyncio.create_task(handle_text(session, msg))
                        elif "inline_query" in update:
                            asyncio.create_task(handle_inline_query(session, update["inline_query"]))
                        elif "callback_query" in update:
                            asyncio.create_task(handle_callback_query(session, update["callback_query"]))
                        elif "widget_query" in update:
                            asyncio.create_task(handle_widget_query(session, update["widget_query"]))

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logging.error(f"Сбой в цикле polling: {html.escape(str(exc))}")
                await asyncio.sleep(3)


async def healthcheck(request: web.Request):
    return web.Response(text="AbhazBand Bot Server OK", status=200)


async def on_startup(app: web.Application):
    app["polling_task"] = asyncio.create_task(polling_loop(app))


async def on_cleanup(app: web.Application):
    task = app.get("polling_task")
    if task:
        task.cancel()
        await task


def main():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
