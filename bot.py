import asyncio
import html
import logging
import os
from aiohttp import web, ClientSession
from github_uploader import process_uploaded_file, get_uploader_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==================== КОНФИГУРАЦИЯ СЕРВЕРА ====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "303365656"))
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://jora71441-design.github.io/abhazband-app/").strip()
PORT = int(os.getenv("PORT", "10000"))

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

# Актуальные заезды для быстрого шеринга через инлайн-режим (@abhazband_ai)
INLINE_RIDES = [
    {
        "id": "weekend_nov_14_15",
        "title": "🔴 14–15 Ноября • Weekend Camp: Гагра — Сухум",
        "desc": "2 дня / 1 ночь • 195 км, +1 950 м • База с бассейном в Сухуме",
        "text": (
            "🔴 <b>WEEKEND CAMP • 14–15 Ноября (Сб–Вс)</b>\n"
            "<b>Маршрут:</b> Гагра — Ачандара — Эшера — Сухум\n"
            "📊 195 км | ⛰️ +1 950 м | ⚡ 27–30 км/ч\n\n"
            "⏰ <b>09:00</b> — Сбор на КПП Псоу, welcome-кофе, багаж в техничку\n"
            "🏨 Проживание в Сухуме на базе с бассейном + авто сопровождения\n\n"
            "👉 Запись и детали в календаре AbhazBand или у @Piti4"
        ),
    },
    {
        "id": "social_nov_21",
        "title": "🟢 21 Ноября • Social Ride: Псоу — Пицунда",
        "desc": "1 день • 85 км, +350 м • Плоский раскат, кофе-стоп, техничка",
        "text": (
            "🟢 <b>SOCIAL RIDE • 21 Ноября (Суббота)</b>\n"
            "<b>Маршрут:</b> Псоу — Пицунда — Ацгуара — Псоу\n"
            "📊 85 км | ⛰️ +350 м | ⚡ 25–28 км/ч\n\n"
            "⏰ <b>09:00</b> — Сбор на КПП Псоу + кофе | <b>10:00</b> — Старт\n"
            "🚗 Включено: машина сопровождения, питание/вода, фотосет\n\n"
            "👉 Запись и детали в календаре AbhazBand или у @Piti4"
        ),
    },
    {
        "id": "weekend_nov_28_29",
        "title": "🔴 28–29 Ноября • Восточный эпик: ИнгурГЭС",
        "desc": "2 дня • Сухум — Очамчыра — Гал — ИнгурГЭС • 220 км, +1 450 м",
        "text": (
            "🔴 <b>WEEKEND CAMP • 28–29 Ноября (Сб–Вс)</b>\n"
            "<b>Маршрут:</b> Сухум — Очамчыра — Гал — ИнгурГЭС\n"
            "📊 220 км | ⛰️ +1 450 м | ⚡ 27–30 км/ч\n\n"
            "🚆 Встреча с вечерней Ласточки в Сухуме, пустые трассы Востока и дамба ИнгурГЭС\n\n"
            "👉 Запись и детали в календаре AbhazBand или у @Piti4"
        ),
    },
    {
        "id": "social_dec_5",
        "title": "🟢 5 Декабря • Social Ride: Мюссера и Форель",
        "desc": "1 день • Псоу — Мюссера — Форелевое хозяйство • 95 км, +850 м",
        "text": (
            "🟢 <b>SOCIAL RIDE • 5 Декабря (Суббота)</b>\n"
            "<b>Маршрут:</b> Псоу — Мюссера — Форелевое хозяйство\n"
            "📊 95 км | ⛰️ +850 м | ⚡ 25–28 км/ч\n\n"
            "⏰ <b>09:00</b> — КПП Псоу | Обед со свежей форелью на углях у горной реки\n\n"
            "👉 Запись и детали в календаре AbhazBand или у @Piti4"
        ),
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
    user_id = message.get("from", {}).get("id")
    text = (message.get("text") or "").strip()

    open_app_markup = {
        "inline_keyboard": [
            [{"text": "🚴 Открыть Abhaz Band Hub", "web_app": {"url": MINIAPP_URL}}],
            [{"text": "💬 Задать вопрос организатору (@Piti4)", "url": "https://t.me/Piti4"}],
        ]
    }

    if text.startswith("/start"):
        if user_id == ADMIN_ID:
            await send_message(
                session,
                chat_id,
                "👋 <b>AbhazBand Dev & Widget Server в сети!</b>\n\n"
                "Отправляй любые файлы кода документами в этот чат — я проверю синтаксис и обновлю репозиторий.\n"
                "• Подсказка: можно указать кастомный путь в подписи (например <code>images/velouyut/v11.png</code>).\n"
                "• Команда /status — проверить токены и статус Render.",
                reply_markup=open_app_markup,
            )
        else:
            await send_message(
                session,
                chat_id,
                "🚴 <b>Добро пожаловать в экосистему AbhazBand!</b>\n\n"
                "В нашем приложении собраны:\n"
                "• 📅 Интерактивный календарь уикендов и кофе-райдов\n"
                "• ⛺ Расписание тренировочных кэмпов в Абхазии\n"
                "• 🛠️ Калькулятор давления в шинах и клубный мерч\n\n"
                "Жми кнопку ниже, чтобы открыть хаб:",
                reply_markup=open_app_markup,
            )

    elif text.startswith("/status") and user_id == ADMIN_ID:
        status_block = get_uploader_status()
        await send_message(
            session,
            chat_id,
            f"⚙️ <b>Статус сервера AbhazBand:</b>\n"
            f"• Bot Token: {'✅ задан' if BOT_TOKEN else '❌ отсутствует'}\n"
            f"{status_block}",
        )

    elif text.startswith("/rides"):
        rides_preview = "\n\n".join(f"• <b>{r['title']}</b>\n  {r['desc']}" for r in INLINE_RIDES)
        await send_message(
            session,
            chat_id,
            f"📅 <b>Ближайшие заезды AbhazBand:</b>\n\n{rides_preview}",
            reply_markup=open_app_markup,
        )


async def handle_inline_query(session: ClientSession, inline_query: dict):
    """Инлайн-режим (@AbhazBand_bot / @abhazband_ai) для быстрой отправки карточек в чаты."""
    query_id = inline_query["id"]
    query_text = (inline_query.get("query") or "").strip().lower()

    results = [
        {
            "type": "article",
            "id": "abhazband_hub_main",
            "title": "🚴 Abhaz Band Hub — Календарь, Кэмпы, Калькулятор",
            "description": "Открыть мини-приложение велоклуба AbhazBand в Telegram",
            "input_message_content": {
                "message_text": (
                    "🚴 <b>Abhaz Band Hub</b> — велоклуб в Абхазии\n"
                    "Интерактивный календарь заездов со стартом от КПП Псоу, расписание кэмпов, "
                    "треки маршрутов и калькулятор давления в шинах."
                ),
                "parse_mode": "HTML",
            },
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": "🚀 Открыть Abhaz Band Hub", "url": "https://t.me/AbhazBand_bot/app"}]
                ]
            },
        }
    ]

    for ride in INLINE_RIDES:
        if query_text and query_text not in ride["title"].lower() and query_text not in ride["desc"].lower():
            continue
        results.append(
            {
                "type": "article",
                "id": ride["id"],
                "title": ride["title"],
                "description": ride["desc"],
                "input_message_content": {
                    "message_text": ride["text"],
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                "reply_markup": {
                    "inline_keyboard": [
                        [{"text": "🚴 Записаться (@Piti4)", "url": "https://t.me/Piti4"}],
                        [{"text": "📅 Весь календарь", "url": "https://t.me/AbhazBand_bot"}],
                    ]
                },
            }
        )

    await tg_request(
        session,
        "answerInlineQuery",
        {"inline_query_id": query_id, "results": results[:10], "cache_time": 60},
    )


async def handle_widget_query(session: ClientSession, widget_query: dict):
    """Заготовка обработчика реактивных событий Bot API 10.4 (answerWidgetQuery)."""
    query_id = widget_query.get("id")
    if query_id:
        await tg_request(session, "answerWidgetQuery", {"widget_query_id": query_id})


# ==================== LONG POLLING & RENDER HTTP SERVER ====================
async def polling_loop(app: web.Application):
    if not BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN не задан! Polling остановлен.")
        return

    offset = 0
    async with ClientSession() as session:
        # Сбрасываем старый webhook при запуске, чтобы избежать 409 Conflict
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
