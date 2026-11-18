import asyncio
import calendar
import html
import json
import logging
import os
import re
from aiohttp import web, ClientSession
from github_uploader import process_uploaded_file, get_uploader_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==================== КОНФИГУРАЦИЯ СЕРВЕРА ====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "AbhazBand_bot").strip().lstrip("@")
ADMIN_ID = int(os.getenv("ADMIN_ID", "303365656"))
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://jora71441-design.github.io/abhazband-app/").strip().rstrip("/")
DATA_JS_URL = "https://raw.githubusercontent.com/jora71441-design/abhazband-app/main/js/data.js"
PORT = int(os.getenv("PORT", "10000"))

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
THUMB_ICON_URL = f"{MINIAPP_URL}/Klubnie-compressed.jpeg"

MONTH_NAMES = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

# Глобальные переменные (обновляются парсером)
RIDES_DATA = {}
CAMPS_DATA = []

# ==================== ПАРСЕР ДАННЫХ ИЗ JS ====================
def parse_js_data(js_text: str):
    new_camps = []
    new_rides = {}
    
    # 1. Парсинг Кэмпов
    camps_match = re.search(r'const camps = \[(.*?)\];', js_text, re.DOTALL)
    if camps_match:
        blocks = re.findall(r'\{([^{}]*)\}', camps_match.group(1))
        for block in blocks:
            title = re.search(r'title:\s*["\']([^"\']+)["\']', block)
            dates = re.search(r'dates:\s*["\']([^"\']+)["\']', block)
            desc = re.search(r'description:\s*["\'](.*?)["\']', block, re.DOTALL)
            specs = re.search(r'specs:\s*["\'](.*?)["\']', block)
            
            if title and dates:
                s_str = f"{specs.group(1)} • " if specs and specs.group(1) else ""
                d_str = desc.group(1) if desc else ""
                new_camps.append({
                    "title": f"⛺ {title.group(1)}",
                    "dates": dates.group(1),
                    "desc": f"{s_str}{d_str}"
                })

    # 2. Парсинг Заездов
    rides_match = re.search(r'const rides = \[(.*?)\];', js_text, re.DOTALL)
    if rides_match:
        chunks = rides_match.group(1).split('id:')[1:]
        for chunk in chunks:
            type_match = re.search(r'type:\s*["\']([^"\']+)["\']', chunk)
            title = re.search(r'title:\s*["\']([^"\']+)["\']', chunk)
            subtitle = re.search(r'subtitle:\s*["\'](.*?)["\']', chunk)
            dates_match = re.search(r'dates:\s*\[(.*?)\]', chunk)
            
            dist = re.search(r'distance:\s*["\']([^"\']+)["\']', chunk)
            elev = re.search(r'elevation:\s*["\']([^"\']+)["\']', chunk)
            pace = re.search(r'pace:\s*["\']([^"\']+)["\']', chunk)
            
            if title and dates_match:
                emoji = "🔴" if type_match and type_match.group(1) == "weekend" else "🟢"
                date_str_match = re.search(r'["\']([^"\']+)["\']', dates_match.group(1))
                if date_str_match:
                    date_key = date_str_match.group(1)
                    desc_parts = []
                    if dist and elev:
                        desc_parts.append(f"{dist.group(1)}, {elev.group(1)}")
                    if pace:
                        desc_parts.append(f"Темп {pace.group(1)}")
                    
                    desc_header = " • ".join(desc_parts)
                    desc_full = f"{desc_header}\n{subtitle.group(1) if subtitle else ''}"
                    
                    new_rides[date_key] = {
                        "type": emoji,
                        "title": title.group(1),
                        "desc": desc_full
                    }
                    
    return new_camps, new_rides


async def load_remote_data():
    """Фоновая загрузка и обновление RIDES и CAMPS с GitHub"""
    global RIDES_DATA, CAMPS_DATA
    try:
        async with ClientSession() as session:
            async with session.get(DATA_JS_URL, timeout=10) as resp:
                if resp.status == 200:
                    js_text = await resp.text()
                    c, r = parse_js_data(js_text)
                    if c: CAMPS_DATA = c
                    if r: RIDES_DATA = r
                    logging.info("✅ Синхронизация: Данные календаря обновлены из GitHub")
    except Exception as e:
        logging.error(f"Ошибка загрузки data.js: {e}")

async def data_sync_loop():
    """Цикл автообновления данных каждые 5 минут"""
    await asyncio.sleep(5)  # Ждем старта сервера
    while True:
        await load_remote_data()
        await asyncio.sleep(300)


# ==================== TELEGRAM API HELPERS ====================
async def tg_request(session: ClientSession, method: str, payload: dict) -> dict:
    async with session.post(f"{API_URL}/{method}", json=payload) as resp:
        return await resp.json()

async def send_message(session: ClientSession, chat_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await tg_request(session, "sendMessage", payload)

async def edit_message(session: ClientSession, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await tg_request(session, "editMessageText", payload)


# ==================== ГЕНЕРАТОРЫ ИНТЕРФЕЙСОВ ====================
def get_overview_ui():
    text = (
        "🏠 <b>Интерактивный виджет событий AbhazBand</b>\n\n"
        "📅 <b>Календарь заездов</b> — узнать ближайшие даты;\n"
        "⛺ <b>Расписание кэмпов</b> — быстрый просмотр дат кэмпов;\n"
        "🚀 <b>Открыть Abhaz Band Hub</b> — полная экосистема со всей информацией и возможностями;\n"
        "💬 <b>Вопрос организатору (@Piti4)</b> — прямая связь для любых вопросов.\n\n"
        "<i>Выбери раздел ниже:</i>"
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": "📅 Календарь заездов", "callback_data": "nav_cal:2026:11"},
                {"text": "⛺ Расписание кэмпов", "callback_data": "nav_camps:0"}
            ],
            [{"text": "🚀 Открыть Abhaz Band Hub", "web_app": {"url": f"{MINIAPP_URL}/"}}],
            [{"text": "💬 Вопрос организатору (@Piti4)", "url": "https://t.me/Piti4"}],
        ]
    }
    return text, markup

def get_calendar_ui(year: int, month: int):
    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1

    markup = {"inline_keyboard": []}
    
    markup["inline_keyboard"].append([
        {"text": "◀️", "callback_data": f"nav_cal:{prev_y}:{prev_m}"},
        {"text": f"{MONTH_NAMES[month].upper()} {year}", "callback_data": "ignore"},
        {"text": "▶️", "callback_data": f"nav_cal:{next_y}:{next_m}"},
    ])
    
    markup["inline_keyboard"].append([{"text": d, "callback_data": "ignore"} for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]])
    
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append({"text": " ", "callback_data": "ignore"})
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                if date_str in RIDES_DATA:
                    emoji = RIDES_DATA[date_str]["type"]
                    row.append({"text": f"{emoji}{day}", "callback_data": f"view_ride:{date_str}"})
                else:
                    row.append({"text": str(day), "callback_data": "ignore"})
        markup["inline_keyboard"].append(row)
    
    markup["inline_keyboard"].append([
        {"text": "🏠 Обзор", "callback_data": "nav_overview"},
        {"text": "🗺 Весь Хаб и треки GPX →", "web_app": {"url": f"{MINIAPP_URL}/?tab=calendar"}}
    ])
    
    text = (
        f"📅 <b>КАЛЕНДАРЬ ЗАЕЗДОВ ({MONTH_NAMES[month]} {year})</b>\n\n"
        "🔴 — Weekend Camp (2 дня)\n"
        "🟢 — Social Ride (1 день)\n\n"
        "<i>Нажми на отмеченную дату, чтобы узнать маршрут и занять слот:</i>"
    )
    return text, markup

def get_ride_ui(date_str: str):
    ride = RIDES_DATA.get(date_str)
    if not ride:
        return get_calendar_ui(int(date_str[:4]), int(date_str[5:7]))
    
    text = (
        f"{ride['type']} <b>{ride['title']}</b>\n"
        f"📅 <b>Дата:</b> {date_str}\n\n"
        f"{ride['desc']}"
    )
    y, m, d = date_str.split("-")
    markup = {
        "inline_keyboard": [
            [{"text": "🚴 Занять слот на этот выезд", "callback_data": f"book_ride:{date_str}"}],
            [{"text": "🔙 Назад в календарь", "callback_data": f"nav_cal:{y}:{int(m)}"}],
        ]
    }
    return text, markup

def get_camps_ui(idx: int):
    if not CAMPS_DATA:
        return "Данные кэмпов загружаются...", {"inline_keyboard": [[{"text": "🏠 Обзор", "callback_data": "nav_overview"}]]}
        
    idx = idx % len(CAMPS_DATA)
    camp = CAMPS_DATA[idx]
    
    text = (
        f"⛺ <b>РАСПИСАНИЕ КЭМПОВ</b> ({idx + 1} из {len(CAMPS_DATA)})\n\n"
        f"<b>{camp['title']}</b>\n"
        f"📆 <b>Даты:</b> {camp['dates']}\n\n"
        f"{camp['desc']}"
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": "◀️", "callback_data": f"nav_camps:{(idx - 1) % len(CAMPS_DATA)}"},
                {"text": "🏠 Обзор", "callback_data": "nav_overview"},
                {"text": "▶️", "callback_data": f"nav_camps:{(idx + 1) % len(CAMPS_DATA)}"},
            ],
            [{"text": "⛺ Забронировать место", "callback_data": f"book_camp:{idx}"}],
            [{"text": "📖 Полная программа кэмпов →", "web_app": {"url": f"{MINIAPP_URL}/?tab=camps"}}],
        ]
    }
    return text, markup


# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================
async def handle_document(session: ClientSession, message: dict):
    chat_id = message["chat"]["id"]
    user_id = message.get("from", {}).get("id")

    if user_id != ADMIN_ID:
        return

    doc = message["document"]
    file_info = await tg_request(session, "getFile", {"file_id": doc["file_id"]})
    if not file_info.get("ok"):
        return
    
    async with session.get(f"{FILE_URL}/{file_info['result']['file_path']}") as f_resp:
        if f_resp.status != 200:
            return
        raw_bytes = await f_resp.read()

    report_text = await process_uploaded_file(session, doc.get("file_name", "unknown"), raw_bytes, message.get("caption", ""))
    await send_message(session, chat_id, report_text)


async def handle_text(session: ClientSession, message: dict):
    chat_id = message["chat"]["id"]
    chat_type = message.get("chat", {}).get("type", "private")
    text = (message.get("text") or "").strip()
    user = message.get("from", {})
    user_id = user.get("id")

    if text.startswith("/group_menu") and user_id == ADMIN_ID and chat_type in ("group", "supergroup"):
        await tg_request(session, "deleteMessage", {"chat_id": chat_id, "message_id": message["message_id"]})
        text_ui, markup = get_overview_ui()
        await send_message(session, chat_id, text_ui, reply_markup=markup)
        return

    if chat_type != "private":
        return

    if text.startswith("/start") or text.startswith("/widget") or text.startswith("/test"):
        text_ui, markup = get_overview_ui()
        await send_message(session, chat_id, text_ui, reply_markup=markup)


async def handle_callback_query(session: ClientSession, callback_query: dict):
    cb_id = callback_query["id"]
    data = callback_query.get("data", "")
    msg = callback_query.get("message", {})
    user = callback_query.get("from", {})
    
    if data == "ignore":
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
        
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    msg_id = msg["message_id"]

    if data == "nav_overview":
        t, m = get_overview_ui()
        await edit_message(session, chat_id, msg_id, t, m)
    elif data.startswith("nav_cal:"):
        _, y, m = data.split(":")
        t, markup = get_calendar_ui(int(y), int(m))
        await edit_message(session, chat_id, msg_id, t, markup)
    elif data.startswith("view_ride:"):
        date_str = data.split(":")[1]
        t, markup = get_ride_ui(date_str)
        await edit_message(session, chat_id, msg_id, t, markup)
    elif data.startswith("nav_camps:"):
        idx = int(data.split(":")[1])
        t, markup = get_camps_ui(idx)
        await edit_message(session, chat_id, msg_id, t, markup)
    elif data.startswith("book_ride:") or data.startswith("book_camp:"):
        cat = "Заезд" if "ride" in data else "Кэмп"
        param = data.split(":")[1]
        title = RIDES_DATA[param]["title"] if cat == "Заезд" else CAMPS_DATA[int(param)]["title"]
        uname = f"@{user['username']}" if user.get("username") else html.escape(user.get("first_name", "Райдер"))
        
        await send_message(
            session, ADMIN_ID,
            f"🚴 <b>Новая заявка из пульта ({cat})!</b>\n• Программа: <b>{title}</b>\n• Участник: {uname} (ID: <code>{user.get('id')}</code>)"
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "✅ Заявка отправлена! Организатор (@Piti4) свяжется с тобой.", "show_alert": True})
        return

    await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})


async def handle_inline_query(session: ClientSession, inline_query: dict):
    await tg_request(
        session, "answerInlineQuery",
        {
            "inline_query_id": inline_query["id"],
            "results": [],
            "cache_time": 10,
            "is_personal": True,
            "button": {"text": "🎛️ Открыть пульт управления", "start_parameter": "hub"},
        }
    )

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
                    params={"offset": offset, "timeout": 25, "allowed_updates": ["message", "inline_query", "callback_query"]},
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
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(3)

async def healthcheck(request: web.Request):
    return web.Response(text="OK", status=200)

async def on_startup(app: web.Application):
    app["data_task"] = asyncio.create_task(data_sync_loop())
    app["polling_task"] = asyncio.create_task(polling_loop(app))

async def on_cleanup(app: web.Application):
    for task_name in ["data_task", "polling_task"]:
        task = app.get(task_name)
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
