import asyncio
import base64
import calendar
import datetime
import html
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from aiohttp import web, ClientSession
from github_uploader import process_uploaded_file, get_uploader_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==================== КОНФИГУРАЦИЯ СЕРВЕРА ====================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "AbhazBand_bot").strip().lstrip("@")
ADMIN_ID = int(os.getenv("ADMIN_ID", "303365656"))
LEADS_TOPIC_ID: Optional[int] = int(os.getenv("LEADS_TOPIC_ID", "0")) or None
MINIAPP_URL = os.getenv("MINIAPP_URL", "https://jora71441-design.github.io/abhazband-app/").strip().rstrip("/")
DATA_JS_URL = "https://raw.githubusercontent.com/jora71441-design/abhazband-app/main/js/data.js"
PORT = int(os.getenv("PORT", "10000"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "jora71441-design/abhazband-app").strip()
MAIN_BRANCH = os.getenv("GITHUB_MAIN_BRANCH", "main").strip()
PAGES_BASE_URL = os.getenv(
    "PAGES_BASE_URL",
    f"https://{GITHUB_REPO.split('/')[0]}.github.io/{GITHUB_REPO.split('/')[1]}"
    if "/" in GITHUB_REPO
    else MINIAPP_URL,
).rstrip("/")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_URL = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
GH_API = f"https://api.github.com/repos/{GITHUB_REPO}"
THUMB_ICON_URL = f"{MINIAPP_URL}/Klubnie-compressed.jpeg"

MONTH_NAMES = [
    "",
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]

# Глобальные переменные (обновляются парсером)
RIDES_DATA = {}
CAMPS_DATA = []

# Состояние ожидающих действий владельца
PENDING_INPUT: Dict[int, Dict[str, Any]] = {}
PENDING_ROLLBACK: Dict[int, str] = {}


# ==================== ОКНО КАЛЕНДАРЯ (2 БЛИЖАЙШИХ МЕСЯЦА) ====================
def get_allowed_months() -> List[Tuple[int, int]]:
    """Возвращает 2 ближайших месяца: текущий и следующий."""
    today = datetime.date.today()
    y1, m1 = today.year, today.month
    y2, m2 = (y1, m1 + 1) if m1 < 12 else (y1 + 1, 1)
    return [(y1, m1), (y2, m2)]


def clamp_calendar_month(year: int, month: int) -> Tuple[int, int]:
    """Ограничивает выбор месяца окном из 2 ближайших месяцев."""
    allowed = get_allowed_months()
    if (year, month) in allowed:
        return year, month
    first_y, first_m = allowed[0]
    last_y, last_m = allowed[1]
    if (year, month) < (first_y, first_m):
        return first_y, first_m
    return last_y, last_m


# ==================== ПАРСЕР ДАННЫХ ИЗ JS ====================
def parse_js_data(js_text: str):
    new_camps = []
    new_rides = {}

    # 1. Парсинг Кэмпов
    camps_match = re.search(r"const camps\s*=\s*\[(.*?)\];", js_text, re.DOTALL)
    if camps_match:
        blocks = re.findall(r"\{([^{}]*)\}", camps_match.group(1))
        for block in blocks:
            title = re.search(r'["\']?title["\']?\s*:\s*["\']([^"\']+)["\']', block)
            dates = re.search(r'["\']?dates["\']?\s*:\s*["\']([^"\']+)["\']', block)
            desc = re.search(r'["\']?description["\']?\s*:\s*["\'](.*?)["\']', block, re.DOTALL)
            specs = re.search(r'["\']?specs["\']?\s*:\s*["\'](.*?)["\']', block)

            if title and dates:
                s_str = f"{specs.group(1)} • " if specs and specs.group(1) else ""
                d_str = desc.group(1) if desc else ""
                new_camps.append({
                    "title": f"⛺ {title.group(1)}",
                    "dates": dates.group(1),
                    "desc": f"{s_str}{d_str}",
                })

    # 2. Парсинг Заездов (поддерживаем многодневные dates и оба стиля ключей в JS)
    rides_match = re.search(r"const rides\s*=\s*\[(.*?)\];", js_text, re.DOTALL)
    if rides_match:
        chunks = re.split(r"(?:^|\n)\s*\{", rides_match.group(1))[1:]
        for chunk in chunks:
            type_match = re.search(r'["\']?type["\']?\s*:\s*["\']([^"\']+)["\']', chunk)
            title = re.search(r'["\']?title["\']?\s*:\s*["\']([^"\']+)["\']', chunk)
            subtitle = re.search(r'["\']?subtitle["\']?\s*:\s*["\'](.*?)["\']', chunk)
            date_disp = re.search(r'["\']?dateDisplay["\']?\s*:\s*["\']([^"\']+)["\']', chunk)
            dates_match = re.search(r'["\']?dates["\']?\s*:\s*\[(.*?)\]', chunk, re.DOTALL)

            dist = re.search(r'["\']?distance["\']?\s*:\s*["\']([^"\']+)["\']', chunk)
            elev = re.search(r'["\']?elevation["\']?\s*:\s*["\']([^"\']+)["\']', chunk)
            pace = re.search(r'["\']?pace["\']?\s*:\s*["\']([^"\']+)["\']', chunk)

            if title and dates_match:
                emoji = "🔴" if type_match and type_match.group(1) == "weekend" else "🟢"
                date_keys = re.findall(r'["\'](\d{4}-\d{2}-\d{2})["\']', dates_match.group(1))
                desc_parts = []
                if dist and elev:
                    desc_parts.append(f"{dist.group(1)}, {elev.group(1)}")
                if pace:
                    desc_parts.append(f"Темп {pace.group(1)}")
                if date_disp:
                    desc_parts.append(date_disp.group(1))

                desc_header = " • ".join(desc_parts)
                desc_full = f"{desc_header}\n{subtitle.group(1) if subtitle else ''}".strip()

                for date_key in date_keys:
                    new_rides[date_key] = {
                        "type": emoji,
                        "title": title.group(1),
                        "desc": desc_full,
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
                    if c:
                        CAMPS_DATA = c
                    if r:
                        RIDES_DATA = r
                    logging.info("✅ Синхронизация: Данные календаря обновлены из GitHub")
    except Exception as e:
        logging.error(f"Ошибка загрузки data.js: {e}")


async def data_sync_loop():
    """Цикл автообновления данных каждые 5 минут"""
    await asyncio.sleep(5)
    while True:
        await load_remote_data()
        await asyncio.sleep(300)


# ==================== GITHUB PREVIEW & ROLLBACK ====================
def slugify_branch(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw.strip().lower()).strip("-")
    return cleaned[:40] or "task"


def preview_url_for(branch: str) -> str:
    slug = branch[len("preview/") :] if branch.startswith("preview/") else branch
    safe_slug = re.sub(r"[^A-Za-z0-9_-]+", "-", slug).strip("-")
    return f"{PAGES_BASE_URL}/preview/{safe_slug}/"


def gh_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


async def gh_request(
    session: ClientSession,
    method: str,
    path: str,
    json_body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any]:
    url = f"{GH_API}{path}"
    async with session.request(method, url, headers=gh_headers(), json=json_body, timeout=15) as resp:
        status = resp.status
        try:
            body = await resp.json(content_type=None)
        except Exception:
            body = await resp.text()
        return status, body


async def get_branch_sha(session: ClientSession, branch: str) -> Optional[str]:
    status, data = await gh_request(session, "GET", f"/git/ref/heads/{branch}")
    if status == 200 and isinstance(data, dict):
        return data.get("object", {}).get("sha")
    return None


async def list_preview_branches(session: ClientSession) -> List[str]:
    status, data = await gh_request(session, "GET", "/git/matching-refs/heads/preview/")
    if status != 200 or not isinstance(data, list):
        return []
    branches: List[str] = []
    for item in data:
        ref = item.get("ref", "")
        if ref.startswith("refs/heads/"):
            branches.append(ref[len("refs/heads/") :])
    return branches


async def create_preview_branch(session: ClientSession, slug: str) -> Tuple[bool, str]:
    if not GITHUB_TOKEN:
        return False, "Не задан GITHUB_TOKEN на Render."
    branch = f"preview/{slugify_branch(slug)}"
    existing = await get_branch_sha(session, branch)
    if existing:
        return True, f"Ветка <code>{html.escape(branch)}</code> уже существует ({existing[:7]}).\nPreview: {html.escape(preview_url_for(branch))}"

    main_sha = await get_branch_sha(session, MAIN_BRANCH)
    if not main_sha:
        return False, f"Не удалось получить SHA ветки <code>{html.escape(MAIN_BRANCH)}</code>."

    status, data = await gh_request(
        session,
        "POST",
        "/git/refs",
        {"ref": f"refs/heads/{branch}", "sha": main_sha},
    )
    if status in (200, 201):
        return (
            True,
            f"Создана ветка <code>{html.escape(branch)}</code> от <code>{html.escape(MAIN_BRANCH)}</code> ({main_sha[:7]}).\n"
            f"Запущена сборка Preview.\n"
            f"Ссылка Preview: {html.escape(preview_url_for(branch))}",
        )
    return False, f"Ошибка создания ветки ({status}): <code>{html.escape(str(data)[:300])}</code>"


async def merge_preview_to_main(session: ClientSession, branch: str) -> Tuple[bool, str]:
    if not GITHUB_TOKEN:
        return False, "Не задан GITHUB_TOKEN на Render."
    status, data = await gh_request(
        session,
        "POST",
        "/merges",
        {
            "base": MAIN_BRANCH,
            "head": branch,
            "commit_message": f"Promote {branch} to {MAIN_BRANCH}",
        },
    )
    if status in (200, 201):
        sha = data.get("sha", "")[:7] if isinstance(data, dict) else ""
        return True, f"Ветка <code>{html.escape(branch)}</code> выложена в <code>{html.escape(MAIN_BRANCH)}</code> ({sha})."
    return False, f"Ошибка выкладки в {MAIN_BRANCH} ({status}): <code>{html.escape(str(data)[:300])}</code>"


async def close_preview_branch(session: ClientSession, branch: str) -> Tuple[bool, str]:
    if not GITHUB_TOKEN:
        return False, "Не задан GITHUB_TOKEN на Render."
    status, data = await gh_request(session, "DELETE", f"/git/refs/heads/{branch}")
    if status in (200, 204):
        return True, f"Ветка <code>{html.escape(branch)}</code> удалена. <code>{html.escape(MAIN_BRANCH)}</code> не затронут."
    return False, f"Ошибка удаления ветки ({status}): <code>{html.escape(str(data)[:300])}</code>"


async def get_previous_main_sha(session: ClientSession) -> Optional[str]:
    status, data = await gh_request(session, "GET", f"/commits?sha={MAIN_BRANCH}&per_page=2")
    if status == 200 and isinstance(data, list) and len(data) >= 2:
        return data[1].get("sha")
    return None


async def rollback_main(session: ClientSession) -> Tuple[bool, str]:
    if not GITHUB_TOKEN:
        return False, "Не задан GITHUB_TOKEN на Render."
    prev_sha = await get_previous_main_sha(session)
    if not prev_sha:
        return False, "Не найден предыдущий коммит для отката."

    status, data = await gh_request(
        session,
        "PATCH",
        f"/git/refs/heads/{MAIN_BRANCH}",
        {"sha": prev_sha, "force": True},
    )
    if status == 200:
        return True, f"Ветка <code>{html.escape(MAIN_BRANCH)}</code> откатана к коммиту <code>{prev_sha[:7]}</code>."
    return False, f"Ошибка отката ({status}): <code>{html.escape(str(data)[:300])}</code>"


async def upsert_file_in_branch(
    session: ClientSession,
    branch: str,
    file_path: str,
    raw_bytes: bytes,
    commit_message: str,
) -> Tuple[bool, str]:
    if not GITHUB_TOKEN:
        return False, "Не задан GITHUB_TOKEN на Render."
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    payload: Dict[str, Any] = {
        "message": commit_message,
        "content": encoded,
        "branch": branch,
    }
    get_status, get_data = await gh_request(session, "GET", f"/contents/{file_path}?ref={branch}")
    if get_status == 200 and isinstance(get_data, dict) and get_data.get("sha"):
        payload["sha"] = get_data["sha"]

    put_status, put_data = await gh_request(session, "PUT", f"/contents/{file_path}", payload)
    if put_status in (200, 201):
        return True, f"Файл <code>{html.escape(file_path)}</code> сохранён в ветку <code>{html.escape(branch)}</code>."
    return False, f"Ошибка записи файла ({put_status}): <code>{html.escape(str(put_data)[:300])}</code>"


def preview_controls_keyboard(branch: str) -> Dict[str, Any]:
    short_slug = branch[len("preview/") :] if branch.startswith("preview/") else branch
    return {
        "inline_keyboard": [
            [{"text": "🔍 Открыть Preview", "url": preview_url_for(branch)}],
            [
                {"text": "✏️ Заметка к ветке", "callback_data": f"pv_note:{short_slug}"},
                {"text": "🚀 Выкатить в main", "callback_data": f"pv_push:{short_slug}"},
            ],
            [{"text": "🗑 Закрыть ветку", "callback_data": f"pv_close:{short_slug}"}],
        ]
    }


def admin_panel_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "🌿 Новая preview-ветка", "callback_data": "sys_new_pv"},
                {"text": "📋 Список preview", "callback_data": "sys_list_pv"},
            ],
            [
                {"text": "📊 Статус", "callback_data": "sys_status"},
                {"text": "⏪ Откатить main", "callback_data": "sys_rb_ask"},
            ],
            [{"text": "🏠 Виджет событий", "callback_data": "nav_overview"}],
        ]
    }


async def build_status_text(session: ClientSession) -> str:
    main_sha = await get_branch_sha(session, MAIN_BRANCH) or "неизвестно"
    prev_sha = await get_previous_main_sha(session)
    previews = await list_preview_branches(session)
    uploader_info = get_uploader_status() if callable(get_uploader_status) else ""
    lines = [
        "🛠 <b>Панель управления Abhaz Band</b>",
        f"• Прод (<code>{html.escape(MAIN_BRANCH)}</code>): <code>{main_sha[:7]}</code>",
        f"• Точка отката: <code>{prev_sha[:7]}</code>" if prev_sha else "• Точка отката: нет данных",
        f"• Активных preview-веток: <b>{len(previews)}</b>",
        f"• Тема заявок: <code>{LEADS_TOPIC_ID}</code>" if LEADS_TOPIC_ID else "• Тема заявок: общий чат",
    ]
    for b in previews:
        lines.append(f"  — <code>{html.escape(b)}</code>")
    if uploader_info:
        lines.append(f"• Загрузчик: <code>{html.escape(str(uploader_info)[:120])}</code>")
    return "\n".join(lines)


# ==================== TELEGRAM API HELPERS ====================
async def tg_request(session: ClientSession, method: str, payload: dict) -> dict:
    async with session.post(f"{API_URL}/{method}", json=payload) as resp:
        return await resp.json()


async def send_message(
    session: ClientSession,
    chat_id: int,
    text: str,
    reply_markup: dict | None = None,
    message_thread_id: int | None = None,
) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if message_thread_id:
        payload["message_thread_id"] = message_thread_id
    return await tg_request(session, "sendMessage", payload)


async def edit_message(session: ClientSession, chat_id: int, message_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await tg_request(session, "editMessageText", payload)


async def setup_bot_settings(session: ClientSession) -> dict:
    """Автонастройка бота через Bot API 10.5 (включаем боковую панель, отключаем создание тем для обычных пользователей)"""
    try:
        res = await tg_request(
            session,
            "setMySettings",
            {
                "has_topics_enabled": True,
                "has_topic_sidebar": True,
                "allows_users_to_create_topics": False,
            },
        )
        logging.info(f"⚙️ Bot API 10.5 setMySettings: {res}")
        return res
    except Exception as e:
        logging.warning(f"⚠️ Не удалось применить setMySettings: {e}")
        return {"ok": False, "error": str(e)}


# ==================== ГЕНЕРАТОРЫ ИНТЕРФЕЙСОВ ====================
def get_overview_ui():
    cur_y, cur_m = get_allowed_months()[0]
    text = (
        "🏠 <b>Интерактивный виджет событий Abhaz Band</b>\n\n"
        "📅 <b>Календарь заездов</b> — узнать ближайшие даты;\n"
        "⛺ <b>Расписание кэмпов</b> — быстрый просмотр дат кэмпов;\n"
        "🛠 <b>Полезные фичи</b> — онлайн bike-fit и другие полезности;\n"
        "🚀 <b>Открыть Abhaz Band Hub</b> — полная экосистема со всей информацией и возможностями;\n"
        "💬 <b>Вопрос организатору (@Piti4)</b> — прямая связь для любых вопросов.\n\n"
        "<i>Выбери раздел ниже:</i>"
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": "📅 Календарь заездов", "callback_data": f"nav_cal:{cur_y}:{cur_m}"},
                {"text": "🏕 Ближайшие кэмпы", "callback_data": "nav_camps:0"},
            ],
            [
                {"text": "🛠 Полезные фичи", "web_app": {"url": f"{MINIAPP_URL}/?tab=features"}},
                {"text": "🚀 Abhaz Band Hub", "web_app": {"url": f"{MINIAPP_URL}/"}},
            ],
            [{"text": "💬 Вопрос организатору (@Piti4)", "url": "https://t.me/Piti4"}],
        ]
    }
    return text, markup


def get_calendar_ui(year: int, month: int):
    year, month = clamp_calendar_month(year, month)
    allowed = get_allowed_months()
    first_y, first_m = allowed[0]
    last_y, last_m = allowed[1]

    if (year, month) == (first_y, first_m):
        prev_btn = {"text": "·", "callback_data": "cal_limit"}
        next_btn = {"text": "▶️", "callback_data": f"nav_cal:{last_y}:{last_m}"}
    else:
        prev_btn = {"text": "◀️", "callback_data": f"nav_cal:{first_y}:{first_m}"}
        next_btn = {"text": "·", "callback_data": "cal_limit"}

    markup = {"inline_keyboard": []}

    markup["inline_keyboard"].append([
        prev_btn,
        {"text": f"{MONTH_NAMES[month].upper()} {year}", "callback_data": "ignore"},
        next_btn,
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
        {"text": "🗺 Полный календарь →", "web_app": {"url": f"{MINIAPP_URL}/?tab=calendar"}},
    ])

    text = (
        f"📅 <b>КАЛЕНДАРЬ ЗАЕЗДОВ ({MONTH_NAMES[month]} {year})</b>\n\n"
        "🔴 — Weekend Camp (2 дня)\n"
        "🟢 — Social Ride (1 день)\n\n"
        "<i>Показаны 2 ближайших месяца. Остальные даты — в полном календаре:</i>"
    )
    return text, markup


def get_ride_ui(date_str: str):
    ride = RIDES_DATA.get(date_str)
    if not ride:
        cur_y, cur_m = get_allowed_months()[0]
        return get_calendar_ui(cur_y, cur_m)

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
    badge = "🔥 Ближайший кэмп" if idx == 0 else f"Кэмп {idx + 1} из {len(CAMPS_DATA)}"

    text = (
        f"🏕 <b>{badge}</b>\n\n"
        f"<b>{camp['title']}</b>\n"
        f"📆 <b>Даты:</b> {camp['dates']}\n\n"
        f"{camp['desc']}"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "⛺ Забронировать место", "callback_data": f"book_camp:{idx}"}],
            [{"text": "📖 Полный список кэмпов →", "web_app": {"url": f"{MINIAPP_URL}/?tab=camps"}}],
            [
                {"text": "◀️", "callback_data": f"nav_camps:{(idx - 1) % len(CAMPS_DATA)}"},
                {"text": "🏠 В меню", "callback_data": "nav_overview"},
                {"text": "▶️", "callback_data": f"nav_camps:{(idx + 1) % len(CAMPS_DATA)}"},
            ],
        ]
    }
    return text, markup


# ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================
async def handle_write_access(session: ClientSession, message: dict):
    """Обработка массового приглашения (Bot API 10.5: botinvite / write_access_allowed)"""
    chat_id = message["chat"]["id"]
    user = message.get("from", {})
    uname = f"@{user['username']}" if user.get("username") else html.escape(user.get("first_name", "Райдер"))

    waa = message.get("write_access_allowed", {})
    inviter = waa.get("inviter") or {}
    inviter_id = inviter.get("id")

    t, m = get_overview_ui()
    await send_message(session, chat_id, t, reply_markup=m)

    if inviter_id == ADMIN_ID:
        await send_message(
            session,
            ADMIN_ID,
            f"✅ <b>Новый участник по твоему botinvite!</b>\n• Райдер: {uname} (ID: <code>{user.get('id')}</code>)\n• Приветственный виджет Abhaz Band отправлен.",
            message_thread_id=LEADS_TOPIC_ID,
        )
    elif inviter_id:
        inv_name = f"@{inviter['username']}" if inviter.get("username") else html.escape(inviter.get("first_name", str(inviter_id)))
        await send_message(
            session,
            ADMIN_ID,
            f"🤝 <b>Приглашение от участника клуба (botinvite)!</b>\n• Новый райдер: {uname}\n• Пригласил: {inv_name} (ID: <code>{inviter_id}</code>)",
            message_thread_id=LEADS_TOPIC_ID,
        )


async def handle_document(session: ClientSession, message: dict):
    chat_id = message["chat"]["id"]
    thread_id = message.get("message_thread_id")
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

    pending = PENDING_INPUT.get(user_id, {})
    target_branch = pending.get("branch")
    file_name = doc.get("file_name", "unknown")

    if target_branch and target_branch.startswith("preview/"):
        if file_name.endswith(".py"):
            try:
                compile(raw_bytes.decode("utf-8"), file_name, "exec")
            except Exception as exc:
                await send_message(
                    session,
                    chat_id,
                    f"⚠️ Ошибка синтаксиса в <code>{html.escape(file_name)}</code>:\n<code>{html.escape(str(exc))}</code>",
                    message_thread_id=thread_id,
                )
                return
        ok, msg = await upsert_file_in_branch(
            session,
            target_branch,
            file_name.lstrip("/"),
            raw_bytes,
            f"Update {file_name} in {target_branch}",
        )
        await send_message(session, chat_id, msg, reply_markup=preview_controls_keyboard(target_branch), message_thread_id=thread_id)
        return

    report_text = await process_uploaded_file(session, file_name, raw_bytes, message.get("caption", ""))
    await send_message(session, chat_id, report_text, message_thread_id=thread_id)


async def handle_text(session: ClientSession, message: dict):
    global LEADS_TOPIC_ID
    chat_id = message["chat"]["id"]
    thread_id = message.get("message_thread_id")
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

    if user_id == ADMIN_ID:
        pending = PENDING_INPUT.get(user_id)
        if pending and not text.startswith("/"):
            mode = pending.get("mode")
            PENDING_INPUT.pop(user_id, None)
            if mode == "create_preview":
                ok, msg = await create_preview_branch(session, text)
                branch = f"preview/{slugify_branch(text)}"
                markup = preview_controls_keyboard(branch) if ok else admin_panel_keyboard()
                await send_message(session, chat_id, msg, reply_markup=markup, message_thread_id=thread_id)
                return
            if mode == "note_preview":
                branch = pending.get("branch", "")
                ok, msg = await upsert_file_in_branch(
                    session,
                    branch,
                    "PREVIEW_NOTES.md",
                    f"# Заметка к ветке `{branch}`\n\n{text}\n".encode("utf-8"),
                    f"Update notes in {branch}",
                )
                await send_message(
                    session,
                    chat_id,
                    f"📝 Заметка для <code>{html.escape(branch)}</code>:\n<i>{html.escape(text)}</i>\n{msg}",
                    reply_markup=preview_controls_keyboard(branch),
                    message_thread_id=thread_id,
                )
                return

        if text.startswith("/test_105"):
            set_res = await setup_bot_settings(session)
            me_res = await tg_request(session, "getMe", {})
            set_json = html.escape(json.dumps(set_res, ensure_ascii=False, indent=2)[:1500])
            me_json = html.escape(json.dumps(me_res, ensure_ascii=False, indent=2)[:1500])
            await send_message(
                session,
                chat_id,
                f"🧪 <b>Диагностика Bot API 10.5</b>\n\n"
                f"<b>1. setMySettings:</b>\n<pre>{set_json}</pre>\n\n"
                f"<b>2. getMe (BotFullInfo):</b>\n<pre>{me_json}</pre>",
                message_thread_id=thread_id,
            )
            return

        if text.startswith("/set_leads"):
            LEADS_TOPIC_ID = thread_id
            if thread_id:
                await send_message(
                    session,
                    chat_id,
                    f"✅ <b>Эта тема назначена для заявок райдеров и логов botinvite!</b>\n"
                    f"ID темы: <code>{thread_id}</code>\n\n"
                    f"<i>Чтобы не сбрасывалось при рестарте Render, добавь в Environment Variables:</i>\n"
                    f"<code>LEADS_TOPIC_ID={thread_id}</code>",
                    message_thread_id=thread_id,
                )
            else:
                await send_message(
                    session,
                    chat_id,
                    "ℹ️ Заявки переключены в основной чат (без привязки к конкретной теме).",
                )
            return

        if text.startswith("/panel"):
            async with ClientSession() as gh_session:
                st_text = await build_status_text(gh_session)
            await send_message(session, chat_id, st_text, reply_markup=admin_panel_keyboard(), message_thread_id=thread_id)
            return

        if text.startswith("/preview"):
            parts = text.split(maxsplit=1)
            slug = parts[1] if len(parts) > 1 else "task"
            async with ClientSession() as gh_session:
                ok, msg = await create_preview_branch(gh_session, slug)
            branch = f"preview/{slugify_branch(slug)}"
            markup = preview_controls_keyboard(branch) if ok else admin_panel_keyboard()
            await send_message(session, chat_id, msg, reply_markup=markup, message_thread_id=thread_id)
            return

        if text.startswith("/status"):
            async with ClientSession() as gh_session:
                st_text = await build_status_text(gh_session)
            await send_message(session, chat_id, st_text, reply_markup=admin_panel_keyboard(), message_thread_id=thread_id)
            return

    if text.startswith("/start") or text.startswith("/widget") or text.startswith("/test"):
        text_ui, markup = get_overview_ui()
        await send_message(session, chat_id, text_ui, reply_markup=markup, message_thread_id=thread_id)


async def handle_callback_query(session: ClientSession, callback_query: dict):
    cb_id = callback_query["id"]
    data = callback_query.get("data", "")
    msg = callback_query.get("message", {})
    user = callback_query.get("from", {})
    user_id = user.get("id")

    if data == "ignore":
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return

    if data == "cal_limit":
        await tg_request(
            session,
            "answerCallbackQuery",
            {
                "callback_query_id": cb_id,
                "text": "В виджете показаны 2 ближайших месяца. Остальные даты — в кнопке «Полный календарь».",
                "show_alert": False,
            },
        )
        return

    if not msg:
        return

    chat_id = msg["chat"]["id"]
    msg_id = msg["message_id"]
    thread_id = msg.get("message_thread_id")

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
            session,
            ADMIN_ID,
            f"🚴 <b>Новая заявка из пульта ({cat})!</b>\n• Программа: <b>{title}</b>\n• Участник: {uname} (ID: <code>{user.get('id')}</code>)",
            message_thread_id=LEADS_TOPIC_ID,
        )
        await tg_request(
            session,
            "answerCallbackQuery",
            {"callback_query_id": cb_id, "text": "✅ Заявка отправлена! Организатор (@Piti4) свяжется с тобой.", "show_alert": True},
        )
        return
    elif user_id == ADMIN_ID and data == "sys_new_pv":
        PENDING_INPUT[user_id] = {"mode": "create_preview"}
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Введите название ветки"})
        await send_message(
            session,
            chat_id,
            "Напишите короткое название задачи для preview-ветки (например: <code>calendar-2027</code>):",
            message_thread_id=thread_id,
        )
        return
    elif user_id == ADMIN_ID and data == "sys_list_pv":
        async with ClientSession() as gh_session:
            branches = await list_preview_branches(gh_session)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        if not branches:
            await edit_message(session, chat_id, msg_id, "Активных preview-веток нет.", admin_panel_keyboard())
        else:
            lines = ["<b>Активные preview-ветки:</b>"]
            buttons = []
            for b in branches:
                short = b[len("preview/") :]
                lines.append(f"• <code>{html.escape(b)}</code>")
                buttons.append([
                    {"text": f"🔍 {short}", "url": preview_url_for(b)},
                    {"text": "🚀 В main", "callback_data": f"pv_push:{short}"},
                    {"text": "🗑", "callback_data": f"pv_close:{short}"},
                ])
            buttons.append([{"text": "⬅️ Назад", "callback_data": "sys_status"}])
            await edit_message(session, chat_id, msg_id, "\n".join(lines), {"inline_keyboard": buttons})
        return
    elif user_id == ADMIN_ID and data == "sys_status":
        async with ClientSession() as gh_session:
            st_text = await build_status_text(gh_session)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        await edit_message(session, chat_id, msg_id, st_text, admin_panel_keyboard())
        return
    elif user_id == ADMIN_ID and data == "sys_rb_ask":
        async with ClientSession() as gh_session:
            prev_sha = await get_previous_main_sha(gh_session)
        if not prev_sha:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Нет коммита для отката", "show_alert": True})
            return
        PENDING_ROLLBACK[user_id] = prev_sha
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"⚠️ Откатить <code>{html.escape(MAIN_BRANCH)}</code> к коммиту <code>{prev_sha[:7]}</code>?",
            {
                "inline_keyboard": [
                    [
                        {"text": "✅ Да, откатить", "callback_data": "sys_rb_yes"},
                        {"text": "❌ Отмена", "callback_data": "sys_status"},
                    ]
                ]
            },
        )
        return
    elif user_id == ADMIN_ID and data == "sys_rb_yes":
        PENDING_ROLLBACK.pop(user_id, None)
        async with ClientSession() as gh_session:
            ok, msg_txt = await rollback_main(gh_session)
            st_text = await build_status_text(gh_session)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Готово" if ok else "Ошибка"})
        await edit_message(session, chat_id, msg_id, f"{msg_txt}\n\n{st_text}", admin_panel_keyboard())
        return
    elif user_id == ADMIN_ID and data.startswith("pv_note:"):
        short = data.split(":", 1)[1]
        branch = f"preview/{short}"
        PENDING_INPUT[user_id] = {"mode": "note_preview", "branch": branch}
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Жду текст заметки"})
        await send_message(
            session,
            chat_id,
            f"Напишите правку/заметку для <code>{html.escape(branch)}</code> следующим сообщением:",
            message_thread_id=thread_id,
        )
        return
    elif user_id == ADMIN_ID and data.startswith("pv_push:"):
        short = data.split(":", 1)[1]
        branch = f"preview/{short}"
        async with ClientSession() as gh_session:
            ok, msg_txt = await merge_preview_to_main(gh_session, branch)
            st_text = await build_status_text(gh_session)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Выложено" if ok else "Ошибка"})
        await edit_message(session, chat_id, msg_id, f"{msg_txt}\n\n{st_text}", admin_panel_keyboard())
        return
    elif user_id == ADMIN_ID and data.startswith("pv_close:"):
        short = data.split(":", 1)[1]
        branch = f"preview/{short}"
        async with ClientSession() as gh_session:
            ok, msg_txt = await close_preview_branch(gh_session, branch)
            st_text = await build_status_text(gh_session)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Закрыта" if ok else "Ошибка"})
        await edit_message(session, chat_id, msg_id, f"{msg_txt}\n\n{st_text}", admin_panel_keyboard())
        return

    await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})


async def handle_inline_query(session: ClientSession, inline_query: dict):
    await tg_request(
        session,
        "answerInlineQuery",
        {
            "inline_query_id": inline_query["id"],
            "results": [],
            "cache_time": 10,
            "is_personal": True,
            "button": {"text": "🎛️ Открыть пульт управления", "start_parameter": "hub"},
        },
    )


# ==================== LONG POLLING & RENDER HTTP SERVER ====================
async def polling_loop(app: web.Application):
    if not BOT_TOKEN:
        return
    offset = 0
    async with ClientSession() as session:
        await tg_request(session, "deleteWebhook", {"drop_pending_updates": False})
        await setup_bot_settings(session)
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
                            if "write_access_allowed" in msg:
                                asyncio.create_task(handle_write_access(session, msg))
                            elif "document" in msg:
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