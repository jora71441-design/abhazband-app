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
    widget_html = build_hub_widget_html(initial_tab=initial_tab, user_name=user_name)
    res = await tg_request(
        session,
        "sendWidget",
        {
            "chat_id": chat_id,
            "widget": {
                "type": "html",
                "html": widget_html,
            },
        }
    )
    if res.get("ok"):
        return True

    # Если API отклонил рабочий виджет, выводим админу точную причину прямо в чат!
    if chat_id == ADMIN_ID:
        await send_message(session, chat_id, f"⚠️ <b>Отказ API (Главный виджет):</b>\n<code>{html.escape(str(res))}</code>")

    # Мягкий откат на текст (чтобы бот не молчал)
    await send_message(
        session, 
        chat_id, 
        "🏠 <b>AbhazBand</b>\nОткрой Хаб по кнопке ниже:",
        reply_markup={"inline_keyboard": [[{"text": "🚀 Открыть Хаб", "web_app": {"url": f"{MINIAPP_URL}/"}}]]}
    )
    return False


# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================
async def handle_document(session: ClientSession, message: dict):
    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id")

    if user_id != ADMIN_ID:
        await send_message(session, chat_id, "⛔ Только для админа.")
        return

    doc = message["document"]
    filename = doc.get("file_name", "unknown_file")
    file_id = doc["file_id"]
    caption = message.get("caption", "")

    file_info = await tg_request(session, "getFile", {"file_id": file_id})
    if not file_info.get("ok"):
        return
    tg_file_path = file_info["result"]["file_path"]
    
    async with session.get(f"{FILE_URL}/{tg_file_path}") as f_resp:
        if f_resp.status != 200:
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

    if chat_type != "private":
        return

    if text.startswith("/start") or text.startswith("/widget"):
        await send_hub_widget(session, chat_id, initial_tab="overview", user_name=user_name)

    # 🟢 СТЕРИЛЬНЫЙ ТЕСТ ВИДЖЕТА
    elif text.startswith("/test"):
        if user_id != ADMIN_ID:
            return
        
        test_html = (
            "<!DOCTYPE html><html><body style='background:#0f172a;color:#10b981;padding:30px;text-align:center;font-family:sans-serif;'>"
            "<h2>✅ Виджет доступен!</h2><p>Telegram разрешает HTML.</p>"
            "</body></html>"
        )
        
        res = await tg_request(session, "sendWidget", {
            "chat_id": chat_id,
            "widget": {"type": "html", "html": test_html}
        })
        
        if not res.get("ok"):
            await send_message(session, chat_id, f"❌ <b>API отклонил даже пустой виджет:</b>\n<code>{html.escape(str(res))}</code>")


async def handle_callback_query(session: ClientSession, callback_query: dict):
    await tg_request(session, "answerCallbackQuery", {"callback_query_id": callback_query["id"]})

async def handle_inline_query(session: ClientSession, inline_query: dict):
    await tg_request(session, "answerInlineQuery", {"inline_query_id": inline_query["id"], "results": []})

async def handle_widget_query(session: ClientSession, widget_query: dict):
    await tg_request(session, "answerWidgetQuery", {"widget_query_id": widget_query.get("id")})

# ==================== LONG POLLING & RENDER HTTP SERVER ====================
async def polling_loop(app: web.Application):
    if not BOT_TOKEN:
        return
    offset = 0
    async with ClientSession() as session:
        await tg_request(session, "deleteWebhook", {"drop_pending_updates": False})
        while True:
            try:
                async with session.get(
                    f"{API_URL}/getUpdates",
                    params={"offset": offset, "timeout": 25, "allowed_updates": ["message", "inline_query", "callback_query", "widget_query"]},
                    timeout=35,
                ) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
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
            except Exception:
                await asyncio.sleep(3)

async def healthcheck(request: web.Request):
    return web.Response(text="OK", status=200)

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
