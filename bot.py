import asyncio
import base64
import calendar
import datetime
import html
import json
import logging
import os
import re
import urllib.parse
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
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

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

# ==================== НАСТРОЙКИ ДАЙДЖЕСТА ====================
ENABLE_CHANNEL_POST = False  # Включить публикацию дайджеста в ветку/канал при необходимости
DIGEST_HOURS = [8, 10, 12, 18, 21]
DIGEST_RETENTION_DAYS = 4
MSK_TZ = datetime.timezone(datetime.timedelta(hours=3))
PENDING_DIGEST: Dict[int, str] = {}
PENDING_BROADCAST: Dict[int, str] = {}

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
PENDING_INPUT: Dict[Any, Dict[str, Any]] = {}
PENDING_ROLLBACK: Dict[int, str] = {}


# ==================== ОКНО КАЛЕНДАРЯ (4 МЕСЯЦА ВПЕРЁД) ====================
def get_allowed_months() -> List[Tuple[int, int]]:
    """Возвращает 4 ближайших месяца: текущий и 3 следующих."""
    today = datetime.date.today()
    months: List[Tuple[int, int]] = []
    y, m = today.year, today.month
    for _ in range(4):
        months.append((y, m))
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1
    return months


def clamp_calendar_month(year: int, month: int) -> Tuple[int, int]:
    """Ограничивает выбор месяца окном из 4 ближайших месяцев."""
    allowed = get_allowed_months()
    if (year, month) in allowed:
        return year, month
    first_y, first_m = allowed[0]
    last_y, last_m = allowed[-1]
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
            title = re.search(r"[\"\x27]?title[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", block)
            dates = re.search(r"[\"\x27]?dates[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", block)
            desc = re.search(r"[\"\x27]?description[\"\x27]?\s*:\s*[\"\x27](.*?)[\"\x27]", block, re.DOTALL)
            specs = re.search(r"[\"\x27]?specs[\"\x27]?\s*:\s*[\"\x27](.*?)[\"\x27]", block)

            cid = re.search(r'[\"\x27]?id[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]', block)
            if title and dates:
                s_str = f"{specs.group(1)} • " if specs and specs.group(1) else ""
                d_str = desc.group(1) if desc else ""
                new_camps.append({
                    "id": cid.group(1) if cid else f"camp_{len(new_camps)}",
                    "title": f"⛺ {title.group(1)}",
                    "dates": dates.group(1),
                    "desc": f"{s_str}{d_str}",
                })

    # 2. Парсинг Заездов:
    # weekend / social -> красная кнопка ("danger"), маркер 🔴
    # festival -> зелёная кнопка ("success"), маркер 🟢
    # camp -> синяя кнопка ("primary"), маркер 🔵
    rides_match = re.search(r"const rides\s*=\s*\[(.*?)\];", js_text, re.DOTALL)
    if rides_match:
        chunks = re.split(r"(?:^|\n)\s*\{", rides_match.group(1))[1:]
        for chunk in chunks:
            type_match = re.search(r"[\"\x27]?type[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", chunk)
            title = re.search(r"[\"\x27]?title[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", chunk)
            subtitle = re.search(r"[\"\x27]?subtitle[\"\x27]?\s*:\s*[\"\x27](.*?)[\"\x27]", chunk)
            date_disp = re.search(r"[\"\x27]?dateDisplay[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", chunk)
            dates_match = re.search(r"[\"\x27]?dates[\"\x27]?\s*:\s*\[(.*?)\]", chunk, re.DOTALL)

            dist = re.search(r"[\"\x27]?distance[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", chunk)
            elev = re.search(r"[\"\x27]?elevation[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", chunk)
            pace = re.search(r"[\"\x27]?pace[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]", chunk)

            if title and dates_match:
                rtype = type_match.group(1) if type_match else "social"
                if rtype == "camp":
                    marker = "🔵"
                    btn_style = "primary"
                elif rtype == "festival":
                    marker = "🟢"
                    btn_style = "success"
                else:
                    marker = "🔴"
                    btn_style = "danger"

                date_keys = re.findall(r"[\"\x27](\d{4}-\d{2}-\d{2})[\"\x27]", dates_match.group(1))
                desc_parts = []
                if dist and elev:
                    desc_parts.append(f"{dist.group(1)}, {elev.group(1)}")
                if pace:
                    desc_parts.append(f"Темп {pace.group(1)}")
                if date_disp:
                    desc_parts.append(date_disp.group(1))

                desc_header = " • ".join(desc_parts)
                desc_full = f"{desc_header}\n{subtitle.group(1) if subtitle else ''}".strip()

                rid_match = re.search(r'[\"\x27]?id[\"\x27]?\s*:\s*[\"\x27]([^\"\x27]+)[\"\x27]', chunk)
                ride_id = rid_match.group(1) if rid_match else f"ride_{date_keys[0] if date_keys else 'x'}"
                for date_key in date_keys:
                    new_rides[date_key] = {
                        "id": ride_id,
                        "type": marker,
                        "style": btn_style,
                        "rtype": rtype,
                        "title": title.group(1),
                        "date_display": date_disp.group(1) if date_disp else date_key,
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
            [{"text": "🔍 Открыть Preview", "web_app": {"url": preview_url_for(branch)}}],
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
            [{"text": "📰 Загрузить дайджест", "callback_data": "dg_adm_start"}],
            [
                {"text": "📣 Общая рассылка", "callback_data": "bc_start"},
                {"text": "📣 Анонс дайджеста", "callback_data": "dg_ann_preview"},
            ],
            [
                {"text": "📖 Команды админа", "callback_data": "sys_cmds"},
                {"text": "🏠 Виджет событий", "callback_data": "nav_overview"},
            ],
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


def build_admin_commands_text() -> str:
    return (
        "📖 <b>Команды управления Abhaz Band</b>\n\n"
        "<b>Панель и деплой:</b>\n"
        "• <code>/panel</code> — главная панель управления\n"
        "• <code>/status</code> — статус веток и загрузчика\n"
        "• <code>/preview имя</code> — создать preview-ветку\n\n"
        "<b>Ветки и заявки:</b>\n"
        "• <code>/new_topic Название</code> — создать ветку в чате с ботом\n"
        "• <code>/set_leads</code> — назначить текущую ветку для заявок\n"
        "• <code>/test_105</code> — диагностика Bot API 10.5 и веток\n\n"
        "<b>Слоты («Мой кэмп»):</b>\n"
        "• <code>/grant ID slot_id [тип]</code> — выдать доступ к слоту\n"
        "• <code>/revoke ID slot_id</code> — отозвать доступ к слоту\n\n"
        "<b>Контент и чаты:</b>\n"
        "• <code>/digest</code> — загрузить новый выпуск дайджеста\n"
        "• <code>/group_menu</code> — отправить виджет в групповой чат\n"
        "• <code>/start</code> — открыть пользовательский виджет"
    )


# ==================== SUPABASE: ПОДТВЕРЖДЁННЫЕ СЛОТЫ ====================
def _sb_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


async def supabase_upsert_slot(
    session: ClientSession,
    telegram_id: int,
    username: str,
    slot_id: str,
    slot_type: str,
    slot_title: str,
    status: str = "confirmed",
) -> Tuple[bool, str]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False, "Не заданы SUPABASE_URL или SUPABASE_SERVICE_KEY на Render."
    url = f"{SUPABASE_URL}/rest/v1/user_slots?on_conflict=telegram_id,slot_id"
    payload = {
        "telegram_id": int(telegram_id),
        "username": username or "",
        "slot_id": slot_id,
        "slot_type": slot_type if slot_type in ("camp", "weekend", "social", "festival") else "social",
        "slot_title": slot_title,
        "status": status,
    }
    try:
        async with session.post(url, headers=_sb_headers(), json=payload, timeout=15) as resp:
            if resp.status in (200, 201):
                return True, "OK"
            txt = await resp.text()
            return False, f"Supabase {resp.status}: {txt[:200]}"
    except Exception as exc:
        return False, str(exc)


async def supabase_revoke_slot(session: ClientSession, telegram_id: int, slot_id: str) -> Tuple[bool, str]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False, "Не заданы SUPABASE_URL или SUPABASE_SERVICE_KEY на Render."
    url = f"{SUPABASE_URL}/rest/v1/user_slots?telegram_id=eq.{int(telegram_id)}&slot_id=eq.{urllib.parse.quote(slot_id)}"
    try:
        async with session.patch(url, headers=_sb_headers(), json={"status": "rejected"}, timeout=15) as resp:
            if resp.status in (200, 204):
                return True, "OK"
            txt = await resp.text()
            return False, f"Supabase {resp.status}: {txt[:200]}"
    except Exception as exc:
        return False, str(exc)


# ==================== SUPABASE: ДАЙДЖЕСТЫ И ПОДПИСЧИКИ ====================
def _parse_topics(raw_topics: Any) -> List[str]:
    if isinstance(raw_topics, list):
        return [t for t in raw_topics if t in ("road", "gravel")]
    if isinstance(raw_topics, str):
        try:
            parsed = json.loads(raw_topics)
            if isinstance(parsed, list):
                return [t for t in parsed if t in ("road", "gravel")]
        except Exception:
            pass
    return ["road", "gravel"]


async def sb_ensure_subscriber(session: ClientSession, user: dict) -> Optional[dict]:
    """Регистрирует пользователя в subscribers (если его ещё нет) без перезаписи настроек."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not user or not user.get("id"):
        return None
    uid = int(user["id"])
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/subscribers?on_conflict=user_id"
    payload = {
        "user_id": uid,
        "username": user.get("username") or "",
        "first_name": user.get("first_name") or "",
        "is_blocked": False,
        "updated_at": now_iso,
    }
    try:
        async with session.post(url, headers=_sb_headers(), json=payload, timeout=15) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                return data[0] if isinstance(data, list) and data else None
    except Exception as exc:
        logging.warning(f"sb_ensure_subscriber error: {exc}")
    return None


async def sb_get_subscriber(session: ClientSession, user_id: int) -> Optional[dict]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/subscribers?user_id=eq.{int(user_id)}&select=*"
    try:
        async with session.get(url, headers=_sb_headers(), timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data[0] if isinstance(data, list) and data else None
    except Exception as exc:
        logging.warning(f"sb_get_subscriber error: {exc}")
    return None


async def sb_update_subscriber(session: ClientSession, user_id: int, fields: Dict[str, Any]) -> bool:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False
    fields = dict(fields)
    fields["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    url = f"{SUPABASE_URL}/rest/v1/subscribers?user_id=eq.{int(user_id)}"
    try:
        async with session.patch(url, headers=_sb_headers(), json=fields, timeout=15) as resp:
            return resp.status in (200, 204)
    except Exception as exc:
        logging.warning(f"sb_update_subscriber error: {exc}")
        return False


async def sb_save_digest(session: ClientSession, topic: str, content: str) -> Tuple[Optional[dict], str]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None, "Не заданы SUPABASE_URL или SUPABASE_SERVICE_KEY."
    url = f"{SUPABASE_URL}/rest/v1/digests"
    payload = {"topic": topic, "content": content}
    try:
        async with session.post(url, headers=_sb_headers(), json=payload, timeout=15) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                row = data[0] if isinstance(data, list) and data else None
                return row, "OK"
            txt = await resp.text()
            return None, f"Supabase {resp.status}: {txt[:200]}"
    except Exception as exc:
        return None, str(exc)


async def sb_get_latest_digest(session: ClientSession, topic: str) -> Optional[dict]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/digests?topic=eq.{topic}&order=id.desc&limit=1"
    try:
        async with session.get(url, headers=_sb_headers(), timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data[0] if isinstance(data, list) and data else None
    except Exception as exc:
        logging.warning(f"sb_get_latest_digest({topic}) error: {exc}")
    return None


async def sb_get_digest_by_id(session: ClientSession, digest_id: int) -> Optional[dict]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    url = f"{SUPABASE_URL}/rest/v1/digests?id=eq.{int(digest_id)}&limit=1"
    try:
        async with session.get(url, headers=_sb_headers(), timeout=15) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data[0] if isinstance(data, list) and data else None
    except Exception as exc:
        logging.warning(f"sb_get_digest_by_id error: {exc}")
    return None


async def sb_cleanup_old_digests(session: ClientSession):
    """Удаляет дайджесты старше DIGEST_RETENTION_DAYS дней, сохраняя самый свежий по каждой теме."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DIGEST_RETENTION_DAYS)).isoformat()
    for topic in ("road", "gravel"):
        latest = await sb_get_latest_digest(session, topic)
        if not latest:
            continue
        latest_id = int(latest["id"])
        url = (
            f"{SUPABASE_URL}/rest/v1/digests"
            f"?topic=eq.{topic}&id=neq.{latest_id}&created_at=lt.{urllib.parse.quote(cutoff)}"
        )
        try:
            async with session.delete(url, headers=_sb_headers(), timeout=15) as resp:
                if resp.status in (200, 204):
                    logging.info(f"🧹 Автоочистка дайджестов ({topic}): старые выпуски проверены/удалены")
        except Exception as exc:
            logging.warning(f"sb_cleanup_old_digests({topic}) error: {exc}")


async def sb_get_pending_subscribers(
    session: ClientSession,
    topic: str,
    digest_id: int,
    max_hour: Optional[int] = None,
) -> List[dict]:
    """Возвращает подписчиков, которым пора доставить выпуск digest_id по теме topic."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return []
    sent_col = "last_sent_road_id" if topic == "road" else "last_sent_gravel_id"
    url = (
        f"{SUPABASE_URL}/rest/v1/subscribers"
        f"?digest_enabled=eq.true&is_blocked=eq.false&{sent_col}=lt.{int(digest_id)}"
        f"&select=user_id,digest_topics,digest_hour,{sent_col}"
    )
    if max_hour is not None:
        url += f"&digest_hour=lte.{int(max_hour)}"
    try:
        async with session.get(url, headers=_sb_headers(), timeout=20) as resp:
            if resp.status == 200:
                rows = await resp.json()
                if not isinstance(rows, list):
                    return []
                return [r for r in rows if topic in _parse_topics(r.get("digest_topics"))]
    except Exception as exc:
        logging.warning(f"sb_get_pending_subscribers error: {exc}")
    return []


async def sb_get_all_active_subscribers(session: ClientSession) -> List[dict]:
    """Возвращает всех активных (не заблокировавших бота) подписчиков из subscribers."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return []
    url = f"{SUPABASE_URL}/rest/v1/subscribers?is_blocked=eq.false&select=user_id"
    try:
        async with session.get(url, headers=_sb_headers(), timeout=20) as resp:
            if resp.status == 200:
                rows = await resp.json()
                return rows if isinstance(rows, list) else []
    except Exception as exc:
        logging.warning(f"sb_get_all_active_subscribers error: {exc}")
    return []


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


_USER_TOPIC_CONFIG = {
    "digest": ("digest_topic_id", "📰 Велодайджест"),
    "slots": ("slots_topic_id", "🏕 Мои слоты и кэмпы"),
}


async def create_chat_topic(session: ClientSession, chat_id: int, name: str) -> Optional[int]:
    """Создаёт форум-ветку в чате и возвращает её message_thread_id (или None)."""
    try:
        res = await tg_request(session, "createForumTopic", {"chat_id": int(chat_id), "name": name[:128]})
        if res.get("ok") and isinstance(res.get("result"), dict):
            tid = res["result"].get("message_thread_id")
            if tid:
                return int(tid)
        logging.debug(f"createForumTopic({chat_id}, {name}) -> {res}")
    except Exception as exc:
        logging.warning(f"create_chat_topic error: {exc}")
    return None


async def ensure_user_topic(
    session: ClientSession,
    user_id: int,
    kind: str,
    force_recreate: bool = False,
) -> Optional[int]:
    """Возвращает ID принудительной ветки пользователя (создаёт лениво при первом обращении)."""
    cfg = _USER_TOPIC_CONFIG.get(kind)
    if not cfg:
        return None
    col_name, topic_title = cfg

    if not force_recreate:
        sub = await sb_get_subscriber(session, user_id)
        if sub and sub.get(col_name):
            try:
                return int(sub[col_name])
            except (TypeError, ValueError):
                pass

    new_tid = await create_chat_topic(session, user_id, topic_title)
    if new_tid:
        await sb_update_subscriber(session, user_id, {col_name: new_tid})
    return new_tid


def _is_thread_missing_error(res: dict) -> bool:
    if not isinstance(res, dict) or res.get("ok"):
        return False
    desc = str(res.get("description") or "").lower()
    return (
        "thread not found" in desc
        or "topic_deleted" in desc
        or "topic_closed" in desc
        or "message_thread_id" in desc
    )


async def send_message_to_user_topic(
    session: ClientSession,
    user_id: int,
    kind: str,
    text: str,
    reply_markup: dict | None = None,
) -> dict:
    """Отправляет сообщение в принудительную ветку пользователя с автопересозданием и фоллбэком в общий чат."""
    tid = await ensure_user_topic(session, user_id, kind, force_recreate=False)
    res = await send_message(session, user_id, text, reply_markup=reply_markup, message_thread_id=tid)
    if res.get("ok") or res.get("error_code") == 403:
        return res
    if tid and _is_thread_missing_error(res):
        new_tid = await ensure_user_topic(session, user_id, kind, force_recreate=True)
        if new_tid:
            res2 = await send_message(session, user_id, text, reply_markup=reply_markup, message_thread_id=new_tid)
            if res2.get("ok") or res2.get("error_code") == 403:
                return res2
        return await send_message(session, user_id, text, reply_markup=reply_markup, message_thread_id=None)
    return res


_DIGEST_EMOJI_RULES = [
    (("контракт", "продлен", "подписан", "трансфер", "переход", "ростер", "состав"), "✍️"),
    (("отмен", "перенос", "отложен", "сворачива", "приостанов", "закрыт"), "❌"),
    (("санкц", "допинг", "дисквал", "решени", "суд", "штраф", "нарушен"), "⚖️"),
    (("график", "календар", "расписан", "сезон", "старт", "даты", "маршрут"), "📅"),
    (("форм", "джерси", "экип", "дизайн", "цвет", "шлем"), "👕"),
    (("велосипед", "рам", "дебют", "новинк", "презентац", "колес", "покрыш", "трансмисс", "групсет", "компьютер", "навигац"), "🚲"),
    (("побед", "чемпион", "рекорд", "титул", "подиум", "триумф", "выиграл"), "🏆"),
    (("травм", "паден", "перелом", "болезн", "восстановлен"), "🩹"),
    (("финанс", "долг", "спонсор", "бюджет", "инвестиц", "банкрот"), "💼"),
]


def _starts_with_emoji(text: str) -> bool:
    if not text:
        return False
    ch = text[0]
    code = ord(ch)
    return (
        0x2600 <= code <= 0x27BF
        or 0x1F300 <= code <= 0x1FAFF
        or ch in ("•", "▪", "▫", "▸", "—", "-")
    )


def _pick_digest_emoji(line_text: str, topic: str) -> str:
    low = line_text.lower()
    for keywords, emoji in _DIGEST_EMOJI_RULES:
        if any(kw in low for kw in keywords):
            return emoji
    return "🚴" if topic == "road" else "🧭"


def _beautify_digest_body(raw_content: str, topic: str) -> str:
    rubric_emoji = "🏁" if topic == "road" else "⛰"
    lines = [ln.strip() for ln in raw_content.strip().splitlines() if ln.strip()]
    formatted_blocks: List[str] = []

    for ln in lines:
        # Убираем ведущие маркеры списка, чтобы не дублировать со смайлом
        clean_ln = re.sub(r"^[\-\*•▪▫]+\s+", "", ln).strip()
        if not clean_ln:
            continue

        already_has_emoji = _starts_with_emoji(clean_ln)

        # Короткая строка без двоеточия и без точки в конце — считаем заголовком рубрики
        if ":" not in clean_ln and len(clean_ln) <= 90 and not clean_ln.endswith((".", "!", "?")):
            safe_rubric = html.escape(clean_ln)
            prefix = "" if already_has_emoji else f"{rubric_emoji} "
            formatted_blocks.append(f"{prefix}<b>{safe_rubric}</b>")
            continue

        # Новость в формате «Заголовок: текст»
        colon_idx = clean_ln.find(":")
        if 0 < colon_idx <= 140:
            title_part = clean_ln[: colon_idx + 1].strip()
            body_part = clean_ln[colon_idx + 1 :].strip()
            emoji = "" if already_has_emoji else f"{_pick_digest_emoji(title_part, topic)} "
            if body_part:
                formatted_blocks.append(
                    f"{emoji}<b>{html.escape(title_part)}</b> {html.escape(body_part)}"
                )
            else:
                formatted_blocks.append(f"{emoji}<b>{html.escape(title_part)}</b>")
        else:
            emoji = "" if already_has_emoji else f"{_pick_digest_emoji(clean_ln, topic)} "
            formatted_blocks.append(f"{emoji}{html.escape(clean_ln)}")

    return "\n\n".join(formatted_blocks)


_RU_MONTHS_GEN = [
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]


def _format_msk_date_label(dt: Optional[datetime.datetime] = None) -> str:
    now = dt.astimezone(MSK_TZ) if dt else datetime.datetime.now(MSK_TZ)
    return f"{now.day} {_RU_MONTHS_GEN[now.month]} {now.year}"


def format_digest_text(
    topic: str,
    raw_content: str,
    published_at: Optional[datetime.datetime] = None,
) -> str:
    header = (
        "🛣️ <b>Велодайджест Abhaz Band • Шоссе</b>"
        if topic == "road"
        else "🪨 <b>Велодайджест Abhaz Band • Гравел</b>"
    )
    date_label = _format_msk_date_label(published_at)
    pretty_body = _beautify_digest_body(raw_content, topic)
    return (
        f"{header}\n"
        f"📅 <i>{html.escape(date_label)} • МСК</i>\n\n"
        f"{pretty_body}\n\n"
        "<i>⚙️ Темы (Шоссе / Гравел) и удобное время доставки можно переключить кнопкой ниже.</i>"
    )


def digest_footer_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "⚙️ Настроить темы и время", "callback_data": "dg_menu"},
                {"text": "🚀 Abhaz Band Hub", "web_app": {"url": f"{MINIAPP_URL}/"}},
            ]
        ]
    }


def _split_text_chunks(text: str, max_len: int = 3900) -> List[str]:
    if len(text) <= max_len:
        return [text]
    chunks: List[str] = []
    rest = text
    while len(rest) > max_len:
        cut = rest.rfind("\n\n", 0, max_len)
        if cut < max_len // 2:
            cut = rest.rfind("\n", 0, max_len)
        if cut < max_len // 2:
            cut = max_len
        chunks.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        chunks.append(rest)
    return chunks


def _parse_iso_dt(raw_ts: Any) -> Optional[datetime.datetime]:
    if not raw_ts or not isinstance(raw_ts, str):
        return None
    try:
        cleaned = raw_ts.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(MSK_TZ)
    except Exception:
        return None


async def send_digest_to_user(
    session: ClientSession,
    chat_id: int,
    topic: str,
    raw_content: str,
    published_at: Optional[datetime.datetime] = None,
) -> Tuple[bool, bool]:
    """Отправляет дайджест в ветку «📰 Велодайджест» с разбивкой на части. Возвращает (ok, is_blocked)."""
    full_text = format_digest_text(topic, raw_content, published_at=published_at)
    chunks = _split_text_chunks(full_text)
    kb = digest_footer_keyboard()
    for idx, chunk in enumerate(chunks):
        markup = kb if idx == len(chunks) - 1 else None
        res = await send_message_to_user_topic(session, chat_id, "digest", chunk, reply_markup=markup)
        if not res.get("ok"):
            err_code = res.get("error_code")
            if err_code == 403:
                return False, True
            logging.warning(f"Ошибка отправки дайджеста {chat_id}: {res}")
            return False, False
    return True, False


async def deliver_digest_batch(
    session: ClientSession,
    topic: str,
    digest_row: dict,
    max_hour: Optional[int] = None,
) -> Tuple[int, int]:
    """Рассылает выпуск подходящим подписчикам. Возвращает (sent_count, blocked_count)."""
    digest_id = int(digest_row["id"])
    content = digest_row["content"]
    sent_col = "last_sent_road_id" if topic == "road" else "last_sent_gravel_id"
    users = await sb_get_pending_subscribers(session, topic, digest_id, max_hour=max_hour)
    sent = 0
    blocked = 0
    for u in users:
        uid = int(u["user_id"])
        pub_dt = _parse_iso_dt(digest_row.get("created_at"))
        ok, is_blk = await send_digest_to_user(session, uid, topic, content, published_at=pub_dt)
        if ok:
            await sb_update_subscriber(session, uid, {sent_col: digest_id})
            sent += 1
        elif is_blk:
            await sb_update_subscriber(session, uid, {"is_blocked": True})
            blocked += 1
        await asyncio.sleep(0.05)
    return sent, blocked


def get_digest_announce_ui() -> Tuple[str, Dict[str, Any]]:
    text = (
        "📰 <b>Запускаем еженедельный велодайджест Abhaz Band</b>\n\n"
        "Раз в неделю будем присылать короткую выжимку главных новостей веломира — без воды и только по твоим интересам:\n"
        "• <b>Шоссе</b> — гонки, трансферы, календарь и железо;\n"
        "• <b>Гравел</b> — новинки, маршруты, приключения и экипировка.\n\n"
        "<i>Выбери прямо сейчас, что хочешь получать (настройки и удобное время доставки можно изменить в любой момент):</i>"
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": "🛣️ Только Шоссе", "callback_data": "dg_quick:road"},
                {"text": "🪨 Только Гравел", "callback_data": "dg_quick:gravel"},
            ],
            [{"text": "🔥 Шоссе + Гравел", "callback_data": "dg_quick:both"}],
            [{"text": "⏰ Выбрать время доставки", "callback_data": "dg_hours"}],
            [{"text": "🔕 Не присылать дайджест", "callback_data": "dg_quick:off"}],
        ]
    }
    return text, markup


def general_broadcast_keyboard() -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "🚀 Abhaz Band Hub", "web_app": {"url": f"{MINIAPP_URL}/"}},
                {"text": "📰 Велодайджест", "callback_data": "dg_menu"},
            ]
        ]
    }


async def send_general_broadcast_to_user(
    session: ClientSession,
    chat_id: int,
    raw_text: str,
) -> Tuple[bool, bool]:
    """Отправляет общее сообщение пользователю с разбивкой на части. Возвращает (ok, is_blocked)."""
    safe_text = html.escape(raw_text.strip())
    chunks = _split_text_chunks(safe_text)
    kb = general_broadcast_keyboard()
    for idx, chunk in enumerate(chunks):
        markup = kb if idx == len(chunks) - 1 else None
        res = await send_message(session, chat_id, chunk, reply_markup=markup)
        if not res.get("ok"):
            if res.get("error_code") == 403:
                return False, True
            logging.warning(f"Ошибка общей рассылки {chat_id}: {res}")
            return False, False
    return True, False


async def broadcast_general_all(session: ClientSession, raw_text: str) -> Tuple[int, int]:
    users = await sb_get_all_active_subscribers(session)
    sent = 0
    blocked = 0
    for u in users:
        uid = int(u["user_id"])
        ok, is_blk = await send_general_broadcast_to_user(session, uid, raw_text)
        if ok:
            sent += 1
        elif is_blk:
            await sb_update_subscriber(session, uid, {"is_blocked": True})
            blocked += 1
        await asyncio.sleep(0.05)
    return sent, blocked


async def broadcast_digest_announce_all(session: ClientSession) -> Tuple[int, int]:
    users = await sb_get_all_active_subscribers(session)
    ann_text, ann_kb = get_digest_announce_ui()
    sent = 0
    blocked = 0
    for u in users:
        uid = int(u["user_id"])
        res = await send_message(session, uid, ann_text, reply_markup=ann_kb)
        if res.get("ok"):
            sent += 1
        elif res.get("error_code") == 403:
            await sb_update_subscriber(session, uid, {"is_blocked": True})
            blocked += 1
        await asyncio.sleep(0.05)
    return sent, blocked


async def digest_scheduler_loop():
    """Фоновый цикл доставки дайджестов по выбранному часу МСК + автоочистка архива."""
    await asyncio.sleep(15)
    last_cleanup_day = None
    while True:
        try:
            now_msk = datetime.datetime.now(MSK_TZ)
            async with ClientSession() as session:
                for topic in ("road", "gravel"):
                    latest = await sb_get_latest_digest(session, topic)
                    if not latest:
                        continue
                    sent, blocked = await deliver_digest_batch(session, topic, latest, max_hour=now_msk.hour)
                    if sent or blocked:
                        logging.info(f"📰 Дайджест ({topic} #{latest['id']}): доставлено={sent}, заблокировали={blocked}")
                if last_cleanup_day != now_msk.date():
                    await sb_cleanup_old_digests(session)
                    last_cleanup_day = now_msk.date()
        except Exception as exc:
            logging.error(f"Ошибка digest_scheduler_loop: {exc}")
        await asyncio.sleep(300)


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
def get_invite_friend_ui():
    """Экран «Позвать друга» с готовым шаблоном пересылки, ссылкой на бота и нативным botinvite."""
    bot_link = f"https://t.me/{BOT_USERNAME}"
    botinvite_link = f"https://t.me/botinvite/{BOT_USERNAME}"
    share_text = (
        "Привет! Залетай в экосистему велоклуба Abhaz Band — кэмпы, выезды по Абхазии, "
        "календарь заездов и полезные фичи для райдеров: "
    )
    share_url = (
        "https://t.me/share/url?"
        + urllib.parse.urlencode({"url": bot_link, "text": share_text})
    )
    text = (
        "🤝 <b>Позвать друга в Abhaz Band</b>\n\n"
        "<b>Как быстро пригласить:</b>\n"
        "1. Нажми <b>«📤 Переслать приглашение другу»</b> — откроется выбор чатов с готовым текстом.\n"
        "2. Или нажми <b>«⚡ Пригласить контакты (botinvite)»</b> — Telegram откроет твой список контактов (до 10 человек за раз) и отправит прямое приглашение в чат с ботом.\n\n"
        "<b>Текст для пересылки:</b>\n"
        f"<i>«{html.escape(share_text.strip())} {html.escape(bot_link)}»</i>"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "📤 Переслать приглашение другу", "url": share_url}],
            [{"text": "⚡ Пригласить контакты (botinvite)", "url": botinvite_link}],
            [{"text": "🏠 Назад в меню", "callback_data": "nav_overview"}],
        ]
    }
    return text, markup


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
            [
                {"text": "📰 Велодайджест", "callback_data": "dg_menu"},
                {"text": "🤝 Позвать друга", "callback_data": "nav_invite"},
            ],
            [
                {"text": "💬 Вопрос организатору (@Piti4)", "url": "https://t.me/Piti4"},
            ],
        ]
    }
    return text, markup


def get_digest_settings_ui(sub: Optional[dict]) -> Tuple[str, Dict[str, Any]]:
    enabled = True if not sub else bool(sub.get("digest_enabled", True))
    topics = _parse_topics(sub.get("digest_topics") if sub else None)
    hour = int(sub.get("digest_hour", 10)) if sub else 10

    has_road = "road" in topics
    has_gravel = "gravel" in topics
    status_str = "🔔 Включён" if enabled else "🔕 Отключён"
    topics_list = []
    if has_road:
        topics_list.append("Шоссе")
    if has_gravel:
        topics_list.append("Гравел")
    topics_str = ", ".join(topics_list) if topics_list else "не выбраны"

    text = (
        "📰 <b>Велодайджест Abhaz Band</b>\n\n"
        f"• Статус: <b>{status_str}</b>\n"
        f"• Темы: <b>{topics_str}</b>\n"
        f"• Время доставки: <b>{hour:02d}:00 МСК</b>\n\n"
        "<i>Переключай дисциплины и время в один тап или запроси последний выпуск прямо сейчас:</i>"
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": f"{'✅' if has_road else '⬜'} 🛣️ Шоссе", "callback_data": "dg_toggle:road"},
                {"text": f"{'✅' if has_gravel else '⬜'} 🪨 Гравел", "callback_data": "dg_toggle:gravel"},
            ],
            [{"text": f"⏰ Время доставки: {hour:02d}:00 МСК", "callback_data": "dg_hours"}],
            [{"text": "📰 Получить последний дайджест", "callback_data": "dg_latest"}],
            [
                {
                    "text": "🔕 Отключить дайджест" if enabled else "🔔 Включить дайджест",
                    "callback_data": "dg_toggle_en",
                }
            ],
            [{"text": "🏠 В главное меню", "callback_data": "nav_overview"}],
        ]
    }
    return text, markup


def get_digest_hours_ui(current_hour: int) -> Tuple[str, Dict[str, Any]]:
    text = (
        "⏰ <b>Выбор времени доставки (МСК)</b>\n\n"
        "Выбери удобный час, когда бот будет присылать новые выпуски велодайджеста <b>Abhaz Band</b>:"
    )
    row = [
        {
            "text": f"{'✅ ' if h == current_hour else ''}{h:02d}:00",
            "callback_data": f"dg_set_h:{h}",
        }
        for h in DIGEST_HOURS
    ]
    markup = {
        "inline_keyboard": [
            row[:3],
            row[3:],
            [{"text": "⬅️ Назад к настройкам", "callback_data": "dg_menu"}],
        ]
    }
    return text, markup


def _build_month_events_summary(year: int, month: int) -> List[str]:
    """Собирает список уникальных событий за выбранный месяц с согласованными цветными метками."""
    prefix = f"{year}-{month:02d}-"
    seen_titles = set()
    lines: List[str] = []
    for date_key in sorted(RIDES_DATA.keys()):
        if not date_key.startswith(prefix):
            continue
        item = RIDES_DATA[date_key]
        sig = (item["type"], item["title"], item.get("date_display", ""))
        if sig in seen_titles:
            continue
        seen_titles.add(sig)
        disp = html.escape(item.get("date_display", date_key))
        lines.append(f"{item['type']} <b>{disp}</b> — {html.escape(item['title'])}")
    return lines


def get_calendar_ui(year: int, month: int):
    year, month = clamp_calendar_month(year, month)
    allowed = get_allowed_months()
    idx = allowed.index((year, month))

    if idx > 0:
        py, pm = allowed[idx - 1]
        prev_btn = {"text": "◀️", "callback_data": f"nav_cal:{py}:{pm}"}
    else:
        prev_btn = {"text": "·", "callback_data": "cal_limit"}

    if idx < len(allowed) - 1:
        ny, nm = allowed[idx + 1]
        next_btn = {"text": "▶️", "callback_data": f"nav_cal:{ny}:{nm}"}
    else:
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
                    ride_item = RIDES_DATA[date_str]
                    btn: Dict[str, Any] = {
                        "text": f"[{day}]",
                        "callback_data": f"view_ride:{date_str}",
                    }
                    if ride_item.get("style"):
                        btn["style"] = ride_item["style"]
                    row.append(btn)
                else:
                    row.append({"text": str(day), "callback_data": "ignore"})
        markup["inline_keyboard"].append(row)

    markup["inline_keyboard"].append([
        {"text": "🏠 Обзор", "callback_data": "nav_overview"},
        {"text": "🗺 Полный календарь →", "web_app": {"url": f"{MINIAPP_URL}/?tab=calendar"}},
    ])

    events_lines = _build_month_events_summary(year, month)
    events_block = "\n".join(events_lines) if events_lines else "<i>В этом месяце запланированных выездов в списке пока нет.</i>"

    text = (
        f"📅 <b>КАЛЕНДАРЬ ЗАЕЗДОВ ({MONTH_NAMES[month]} {year})</b>\n\n"
        f"{events_block}\n\n"
        "🔴 Выезды (Weekend / Social) • 🟢 Фестивали • 🔵 Кэмпы\n"
        "<i>В сетке выделены даты [число]. Нажми на дату, чтобы открыть детали:</i>"
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
def _find_slot_by_id(slot_id: str) -> Tuple[str, str, str, str]:
    """Ищет слот по id среди CAMPS_DATA и RIDES_DATA. Возвращает (cat_label, slot_id, slot_type, title)."""
    sid = (slot_id or "").strip()
    for c in CAMPS_DATA:
        if c.get("id") == sid:
            return "Кэмп", sid, "camp", c.get("title", sid)
    for r in RIDES_DATA.values():
        if r.get("id") == sid:
            rtype = r.get("rtype", "social")
            cat = "Кэмп" if rtype == "camp" else "Заезд"
            return cat, sid, rtype, r.get("title", sid)
    # Фоллбэк, если id не найден в кэше
    inferred_type = (
        "camp" if "camp" in sid else
        ("festival" if "festival" in sid else
         ("weekend" if "weekend" in sid or "dourtour" in sid else "social"))
    )
    cat = "Кэмп" if inferred_type == "camp" else "Заезд"
    return cat, sid, inferred_type, sid


async def _dispatch_booking_lead(
    session: ClientSession,
    user: dict,
    slot_id: str,
    slot_type: str,
    title: str,
    cat_label: str,
    source_label: str = "пульта",
):
    req_uid = user.get("id")
    uname = f"@{user['username']}" if user.get("username") else html.escape(user.get("first_name", "Райдер"))
    if req_uid:
        PENDING_INPUT[f"slot_meta:{req_uid}:{slot_id[:28]}"] = {
            "slot_id": slot_id,
            "slot_type": slot_type,
            "slot_title": title,
            "username": user.get("username") or "",
        }
    approve_markup = {
        "inline_keyboard": [
            [{"text": "✅ Подтвердить оплату (открыть доступ)", "callback_data": f"slot_ok:{req_uid}:{slot_type}:{slot_id[:28]}"}],
            [{"text": "❌ Отклонить заявку", "callback_data": f"slot_no:{req_uid}:{slot_id[:28]}"}],
        ]
    }
    await send_message(
        session,
        ADMIN_ID,
        f"🚴 <b>Новая заявка из {html.escape(source_label)} ({html.escape(cat_label)})!</b>\n"
        f"• Программа: <b>{html.escape(title)}</b>\n"
        f"• Слот ID: <code>{html.escape(slot_id)}</code>\n"
        f"• Участник: {uname} (ID: <code>{req_uid}</code>)",
        reply_markup=approve_markup,
        message_thread_id=LEADS_TOPIC_ID,
    )


async def handle_write_access(session: ClientSession, message: dict):
    """Обработка приглашения (Bot API 10.5: botinvite / write_access_allowed) в связке с реферальным учётом."""
    chat_id = message["chat"]["id"]
    user = message.get("from", {})
    uname = f"@{user['username']}" if user.get("username") else html.escape(user.get("first_name", "Райдер"))

    waa = message.get("write_access_allowed", {})
    inviter = waa.get("inviter") or {}
    inviter_id = inviter.get("id")

    await sb_ensure_subscriber(session, user)
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
            (
                f"🤝 <b>Клубное приглашение от участника (botinvite)!</b>\n"
                f"• Новый райдер: {uname} (ID: <code>{user.get('id')}</code>)\n"
                f"• Пригласил: {inv_name} (ID: <code>{inviter_id}</code>)"
            ),
            message_thread_id=LEADS_TOPIC_ID,
        )
        try:
            await send_message(
                session,
                int(inviter_id),
                f"🚴‍♂️ Спасибо, что позвал в <b>Abhaz Band</b>! Райдер {uname} принял приглашение и открыл виджет клуба.",
            )
        except Exception as exc:
            logging.debug(f"Не удалось отправить отметку пригласившему {inviter_id}: {exc}")
    else:
        await send_message(
            session,
            ADMIN_ID,
            f"📥 <b>Принят доступ через botinvite (без указания inviter)</b>\n• Райдер: {uname} (ID: <code>{user.get('id')}</code>)",
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
            if mode == "upload_digest":
                PENDING_DIGEST[user_id] = text
                preview_snip = html.escape(text[:600]) + ("…" if len(text) > 600 else "")
                kb = {
                    "inline_keyboard": [
                        [
                            {"text": "🛣️ Сохранить как Шоссе", "callback_data": "dg_save:road"},
                            {"text": "🪨 Сохранить как Гравел", "callback_data": "dg_save:gravel"},
                        ],
                        [{"text": "📣 Разослать всем (общее)", "callback_data": "dg_as_bc"}],
                        [{"text": "❌ Отмена", "callback_data": "dg_cancel"}],
                    ]
                }
                await send_message(
                    session,
                    chat_id,
                    f"📰 <b>Предпросмотр дайджеста</b> ({len(text)} симв.)\n\n{preview_snip}\n\n<i>Выбери дисциплину для сохранения:</i>",
                    reply_markup=kb,
                    message_thread_id=thread_id,
                )
                return
            if mode == "broadcast_general":
                PENDING_BROADCAST[user_id] = text
                users = await sb_get_all_active_subscribers(session)
                preview_snip = html.escape(text[:600]) + ("…" if len(text) > 600 else "")
                kb = {
                    "inline_keyboard": [
                        [{"text": "🧪 Тест себе (Админу)", "callback_data": "bc_test"}],
                        [{"text": f"🚀 Отправить всем ({len(users)} чел.)", "callback_data": "bc_send_ask"}],
                        [{"text": "❌ Отмена", "callback_data": "bc_cancel"}],
                    ]
                }
                await send_message(
                    session,
                    chat_id,
                    f"📣 <b>Предпросмотр общей рассылки</b> ({len(text)} симв.)\n\n{preview_snip}\n\n<i>Выбери действие:</i>",
                    reply_markup=kb,
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

        if text.startswith("/new_topic"):
            parts = text.split(maxsplit=1)
            t_name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "🚴 Заявки"
            new_tid = await create_chat_topic(session, chat_id, t_name)
            if new_tid:
                await send_message(
                    session,
                    chat_id,
                    f"✅ <b>Ветка «{html.escape(t_name)}» создана!</b>\n"
                    f"• ID темы: <code>{new_tid}</code>\n\n"
                    f"Если это ветка для заявок, зайди в неё и отправь <code>/set_leads</code> (или добавь <code>LEADS_TOPIC_ID={new_tid}</code> в Render).",
                    message_thread_id=new_tid,
                )
            else:
                await send_message(
                    session,
                    chat_id,
                    "⚠️ Не удалось создать ветку через <code>createForumTopic</code>. Проверь <code>/test_105</code>.",
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

        if text.startswith("/grant"):
            parts = text.split(maxsplit=3)
            if len(parts) < 3:
                await send_message(
                    session,
                    chat_id,
                    "Формат: <code>/grant &lt;telegram_id&gt; &lt;slot_id&gt; [camp|weekend|social]</code>\n"
                    "Пример: <code>/grant 123456789 camp_ny_2027 camp</code>",
                    message_thread_id=thread_id,
                )
                return
            try:
                target_uid = int(parts[1])
            except ValueError:
                await send_message(session, chat_id, "⚠️ telegram_id должен быть числом.", message_thread_id=thread_id)
                return
            slot_id = parts[2].strip()
            slot_type = parts[3].strip().lower() if len(parts) >= 4 else (
                "camp" if "camp" in slot_id else ("weekend" if "weekend" in slot_id or "dourtour" in slot_id else "social")
            )
            ok, err = await supabase_upsert_slot(session, target_uid, "", slot_id, slot_type, slot_id, "confirmed")
            if ok:
                await send_message(
                    session,
                    chat_id,
                    f"✅ Доступ к слоту <code>{html.escape(slot_id)}</code> ({slot_type}) выдан пользователю <code>{target_uid}</code>.",
                    message_thread_id=thread_id,
                )
                try:
                    await send_message_to_user_topic(
                        session,
                        target_uid,
                        "slots",
                        "✅ <b>Доступ в личный кабинет «Мой кэмп» открыт!</b>\nНажми кнопку ниже, чтобы открыть треки, тайминг и чек-лист:",
                        reply_markup={"inline_keyboard": [[{"text": "🏕 Открыть Мой кэмп", "web_app": {"url": f"{MINIAPP_URL}/?tab=my-camp"}}]]},
                    )
                except Exception:
                    pass
            else:
                await send_message(session, chat_id, f"⚠️ Ошибка Supabase: <code>{html.escape(err)}</code>", message_thread_id=thread_id)
            return

        if text.startswith("/revoke"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                await send_message(session, chat_id, "Формат: <code>/revoke &lt;telegram_id&gt; &lt;slot_id&gt;</code>", message_thread_id=thread_id)
                return
            try:
                target_uid = int(parts[1])
            except ValueError:
                await send_message(session, chat_id, "⚠️ telegram_id должен быть числом.", message_thread_id=thread_id)
                return
            slot_id = parts[2].strip()
            ok, err = await supabase_revoke_slot(session, target_uid, slot_id)
            msg_out = f"🚫 Доступ к <code>{html.escape(slot_id)}</code> отозван у <code>{target_uid}</code>." if ok else f"⚠️ Ошибка: <code>{html.escape(err)}</code>"
            await send_message(session, chat_id, msg_out, message_thread_id=thread_id)
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

    if text.startswith("/digest"):
        await sb_ensure_subscriber(session, user)
        if user_id == ADMIN_ID:
            PENDING_INPUT[user_id] = {"mode": "upload_digest"}
            await send_message(
                session,
                chat_id,
                "📰 <b>Режим загрузки дайджеста</b>\n\nОтправь или перешли готовый текст дайджеста следующим сообщением (Шоссе или Гравел).",
                message_thread_id=thread_id,
            )
            return
        sub = await sb_get_subscriber(session, user_id)
        t_ui, m_ui = get_digest_settings_ui(sub)
        await send_message(session, chat_id, t_ui, reply_markup=m_ui, message_thread_id=thread_id)
        return

    if text.startswith("/start") or text.startswith("/widget") or text.startswith("/test"):
        await sb_ensure_subscriber(session, user)
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        if text.startswith("/start") and payload.startswith("book_"):
            raw_slot_id = urllib.parse.unquote(payload[len("book_"):]).strip()
            if not RIDES_DATA and not CAMPS_DATA:
                await load_remote_data()
            cat_label, slot_id, slot_type, title = _find_slot_by_id(raw_slot_id)
            await _dispatch_booking_lead(
                session,
                user,
                slot_id,
                slot_type,
                title,
                cat_label,
                source_label="Abhaz Band Hub",
            )
            user_kb = {
                "inline_keyboard": [
                    [{"text": "💬 Написать организатору (@Piti4)", "url": "https://t.me/Piti4"}],
                    [{"text": "🏠 Главное меню", "callback_data": "nav_overview"}],
                ]
            }
            await send_message_to_user_topic(
                session,
                chat_id,
                "slots",
                f"✅ <b>Заявка отправлена!</b>\n\n"
                f"• Программа: <b>{html.escape(title)}</b>\n"
                f"• Слот: <code>{html.escape(slot_id)}</code>\n\n"
                f"После подтверждения оплаты у @Piti4 откроется доступ во вкладку <b>«Мой кэмп»</b> с треками, таймингом и чек-листом.",
                reply_markup=user_kb,
            )
            return
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
                "text": "В виджете показаны 4 ближайших месяца. Остальные даты — в кнопке «Полный календарь».",
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
    elif data == "nav_invite":
        t, m = get_invite_friend_ui()
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
        param = data.split(":", 1)[1]
        if cat == "Заезд":
            r_obj = RIDES_DATA.get(param, {})
            title = r_obj.get("title", param)
            slot_id = r_obj.get("id", f"ride_{param}")
            slot_type = r_obj.get("rtype", "social")
        else:
            c_idx = int(param) if param.isdigit() else 0
            c_obj = CAMPS_DATA[c_idx] if c_idx < len(CAMPS_DATA) else {}
            title = c_obj.get("title", "Кэмп Abhaz Band")
            slot_id = c_obj.get("id", f"camp_{param}")
            slot_type = "camp"

        req_uid = user.get("id")
        uname = f"@{user['username']}" if user.get("username") else html.escape(user.get("first_name", "Райдер"))
        # Храним title в PENDING_INPUT для админа, чтобы при подтверждении записать в user_slots реальное slot_title
        if req_uid:
            PENDING_INPUT[f"slot_meta:{req_uid}:{slot_id[:28]}"] = {
                "slot_id": slot_id,
                "slot_type": slot_type,
                "slot_title": title,
                "username": user.get("username") or "",
            }
        approve_markup = {
            "inline_keyboard": [
                [{"text": "✅ Подтвердить оплату (открыть доступ)", "callback_data": f"slot_ok:{req_uid}:{slot_type}:{slot_id[:28]}"}],
                [{"text": "❌ Отклонить заявку", "callback_data": f"slot_no:{req_uid}:{slot_id[:28]}"}],
            ]
        }

        await send_message(
            session,
            ADMIN_ID,
            f"🚴 <b>Новая заявка из пульта ({cat})!</b>\n"
            f"• Программа: <b>{html.escape(title)}</b>\n"
            f"• Слот ID: <code>{html.escape(slot_id)}</code>\n"
            f"• Участник: {uname} (ID: <code>{req_uid}</code>)",
            reply_markup=approve_markup,
            message_thread_id=LEADS_TOPIC_ID,
        )
        await tg_request(
            session,
            "answerCallbackQuery",
            {"callback_query_id": cb_id, "text": "✅ Заявка отправлена! После подтверждения оплаты у @Piti4 откроется доступ в «Мой кэмп».", "show_alert": True},
        )
        return
    elif user_id == ADMIN_ID and data.startswith("slot_ok:"):
        parts = data.split(":", 3)
        if len(parts) == 4:
            _, req_uid_s, s_type, s_id = parts
            req_uid = int(req_uid_s)
            orig_text = msg.get("text", "")
            meta = PENDING_INPUT.pop(f"slot_meta:{req_uid}:{s_id}", None) or {}
            full_slot_id = meta.get("slot_id") or s_id
            full_slot_title = meta.get("slot_title") or full_slot_id
            full_uname = meta.get("username") or ""
            ok, err = await supabase_upsert_slot(session, req_uid, full_uname, full_slot_id, s_type, full_slot_title, "confirmed")
            if ok:
                await edit_message(session, chat_id, msg_id, f"{html.escape(orig_text)}\n\n✅ <b>Оплата подтверждена — доступ в «Мой кэмп» открыт!</b>")
                await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "✅ Доступ открыт!"})
                try:
                    await send_message_to_user_topic(
                        session,
                        req_uid,
                        "slots",
                        "✅ <b>Оплата подтверждена!</b>\nДоступ в личный кабинет <b>«Мой кэмп»</b> открыт — внутри тебя ждут треки, тайминг, чек-лист и памятка.",
                        reply_markup={"inline_keyboard": [[{"text": "🏕 Открыть Мой кэмп", "web_app": {"url": f"{MINIAPP_URL}/?tab=my-camp"}}]]},
                    )
                except Exception as exc:
                    logging.warning(f"Не удалось уведомить участника {req_uid}: {exc}")
            else:
                await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Ошибка Supabase: {err[:100]}", "show_alert": True})
        return
    elif user_id == ADMIN_ID and data.startswith("slot_no:"):
        parts = data.split(":", 2)
        if len(parts) == 3:
            _, req_uid_s, s_id = parts
            await supabase_revoke_slot(session, int(req_uid_s), s_id)
            orig_text = msg.get("text", "")
            await edit_message(session, chat_id, msg_id, f"{html.escape(orig_text)}\n\n❌ <b>Заявка отклонена.</b>")
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Отклонено"})
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
                    {"text": f"🔍 {short}", "web_app": {"url": preview_url_for(b)}},
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
    elif user_id == ADMIN_ID and data == "sys_cmds":
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        await edit_message(
            session,
            chat_id,
            msg_id,
            build_admin_commands_text(),
            {"inline_keyboard": [[{"text": "⬅️ Назад в панель", "callback_data": "sys_status"}]]},
        )
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
    elif data == "dg_menu":
        await sb_ensure_subscriber(session, user)
        sub = await sb_get_subscriber(session, user_id)
        t_ui, m_ui = get_digest_settings_ui(sub)
        await edit_message(session, chat_id, msg_id, t_ui, m_ui)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif data.startswith("dg_toggle:"):
        topic = data.split(":", 1)[1]
        await sb_ensure_subscriber(session, user)
        sub = await sb_get_subscriber(session, user_id)
        topics = _parse_topics(sub.get("digest_topics") if sub else None)
        if topic in topics:
            topics = [t for t in topics if t != topic]
        else:
            topics.append(topic)
        await sb_update_subscriber(session, user_id, {"digest_topics": topics})
        sub = await sb_get_subscriber(session, user_id)
        t_ui, m_ui = get_digest_settings_ui(sub)
        await edit_message(session, chat_id, msg_id, t_ui, m_ui)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Темы обновлены"})
        return
    elif data == "dg_toggle_en":
        await sb_ensure_subscriber(session, user)
        sub = await sb_get_subscriber(session, user_id)
        cur_en = True if not sub else bool(sub.get("digest_enabled", True))
        await sb_update_subscriber(session, user_id, {"digest_enabled": not cur_en})
        sub = await sb_get_subscriber(session, user_id)
        t_ui, m_ui = get_digest_settings_ui(sub)
        await edit_message(session, chat_id, msg_id, t_ui, m_ui)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Статус обновлён"})
        return
    elif data == "dg_hours":
        sub = await sb_get_subscriber(session, user_id)
        cur_h = int(sub.get("digest_hour", 10)) if sub else 10
        t_ui, m_ui = get_digest_hours_ui(cur_h)
        await edit_message(session, chat_id, msg_id, t_ui, m_ui)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif data.startswith("dg_set_h:"):
        new_h = int(data.split(":", 1)[1])
        if new_h in DIGEST_HOURS:
            await sb_ensure_subscriber(session, user)
            await sb_update_subscriber(session, user_id, {"digest_hour": new_h})
        sub = await sb_get_subscriber(session, user_id)
        t_ui, m_ui = get_digest_settings_ui(sub)
        await edit_message(session, chat_id, msg_id, t_ui, m_ui)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Время: {new_h:02d}:00 МСК"})
        return
    elif data == "dg_latest":
        await sb_ensure_subscriber(session, user)
        sub = await sb_get_subscriber(session, user_id)
        topics = _parse_topics(sub.get("digest_topics") if sub else None)
        if not topics:
            await tg_request(
                session,
                "answerCallbackQuery",
                {"callback_query_id": cb_id, "text": "Сначала выбери хотя бы одну тему (Шоссе или Гравел).", "show_alert": True},
            )
            return
        sent_any = False
        for topic in topics:
            latest = await sb_get_latest_digest(session, topic)
            if latest:
                pub_dt = _parse_iso_dt(latest.get("created_at"))
                ok, _ = await send_digest_to_user(session, chat_id, topic, latest["content"], published_at=pub_dt)
                if ok:
                    sent_any = True
        await tg_request(
            session,
            "answerCallbackQuery",
            {
                "callback_query_id": cb_id,
                "text": "Свежий дайджест отправлен!" if sent_any else "Свежих выпусков по выбранным темам пока нет.",
                "show_alert": not sent_any,
            },
        )
        return
    elif user_id == ADMIN_ID and data == "dg_adm_start":
        PENDING_INPUT[user_id] = {"mode": "upload_digest"}
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Жду текст дайджеста"})
        await send_message(
            session,
            chat_id,
            "📰 <b>Загрузка велодайджеста</b>\n\nОтправь или перешли готовый текст дайджеста следующим сообщением:",
            message_thread_id=thread_id,
        )
        return
    elif user_id == ADMIN_ID and data == "dg_cancel":
        PENDING_DIGEST.pop(user_id, None)
        await edit_message(session, chat_id, msg_id, "❌ Загрузка дайджеста отменена.")
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data.startswith("dg_save:"):
        topic = data.split(":", 1)[1]
        raw_text = PENDING_DIGEST.pop(user_id, None)
        if not raw_text:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Текст не найден, отправь заново.", "show_alert": True})
            return
        row, err = await sb_save_digest(session, topic, raw_text)
        if not row:
            await edit_message(session, chat_id, msg_id, f"⚠️ Ошибка сохранения в Supabase:\n<code>{html.escape(err)}</code>")
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Ошибка"})
            return
        await sb_cleanup_old_digests(session)
        d_id = int(row["id"])
        t_label = "Шоссе" if topic == "road" else "Гравел"
        kb = {
            "inline_keyboard": [
                [{"text": "⏰ Доставить по расписанию пользователей", "callback_data": "dg_mode_sched"}],
                [{"text": "🧪 Тест себе (Админу)", "callback_data": f"dg_send_test:{topic}:{d_id}"}],
                [{"text": "🚀 Отправить сейчас всем", "callback_data": f"dg_send_now_ask:{topic}:{d_id}"}],
            ]
        }
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"✅ Дайджест <b>{t_label}</b> (#<code>{d_id}</code>) сохранён в Supabase.\n\nВыбери способ доставки:",
            kb,
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Сохранено!"})
        return
    elif user_id == ADMIN_ID and data == "dg_mode_sched":
        await edit_message(
            session,
            chat_id,
            msg_id,
            "⏰ <b>Поставлено в очередь!</b>\nБот доставит выпуск каждому подписчику в выбранный им час по МСК.",
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data.startswith("dg_send_test:"):
        _, topic, d_id_s = data.split(":", 2)
        row = await sb_get_digest_by_id(session, int(d_id_s))
        if not row:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Выпуск не найден", "show_alert": True})
            return
        pub_dt = _parse_iso_dt(row.get("created_at"))
        ok, _ = await send_digest_to_user(session, ADMIN_ID, topic, row["content"], published_at=pub_dt)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Тест отправлен!" if ok else "Ошибка отправки"})
        return
    elif user_id == ADMIN_ID and data.startswith("dg_send_now_ask:"):
        _, topic, d_id_s = data.split(":", 2)
        d_id = int(d_id_s)
        users = await sb_get_pending_subscribers(session, topic, d_id, max_hour=None)
        t_label = "Шоссе" if topic == "road" else "Гравел"
        kb = {
            "inline_keyboard": [
                [
                    {"text": f"✅ Да, отправить ({len(users)})", "callback_data": f"dg_send_now_go:{topic}:{d_id}"},
                    {"text": "⏰ Оставить по расписанию", "callback_data": "dg_mode_sched"},
                ]
            ]
        }
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"🚀 Подтверди мгновенную рассылку <b>{t_label}</b> (#<code>{d_id}</code>).\nПолучателей: <b>{len(users)}</b>",
            kb,
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data.startswith("dg_send_now_go:"):
        _, topic, d_id_s = data.split(":", 2)
        row = await sb_get_digest_by_id(session, int(d_id_s))
        if not row:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Выпуск не найден", "show_alert": True})
            return
        await edit_message(session, chat_id, msg_id, "⏳ Запускаю рассылку дайджеста…")
        sent, blocked = await deliver_digest_batch(session, topic, row, max_hour=None)
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"✅ <b>Рассылка завершена!</b>\n• Доставлено: <b>{sent}</b>\n• Заблокировали бота: <b>{blocked}</b>",
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Готово!"})
        return
    elif data.startswith("dg_quick:"):
        choice = data.split(":", 1)[1]
        await sb_ensure_subscriber(session, user)
        if choice == "road":
            await sb_update_subscriber(session, user_id, {"digest_enabled": True, "digest_topics": ["road"]})
            toast = "Выбрано: только Шоссе!"
        elif choice == "gravel":
            await sb_update_subscriber(session, user_id, {"digest_enabled": True, "digest_topics": ["gravel"]})
            toast = "Выбрано: только Гравел!"
        elif choice == "both":
            await sb_update_subscriber(session, user_id, {"digest_enabled": True, "digest_topics": ["road", "gravel"]})
            toast = "Выбрано: Шоссе + Гравел!"
        else:
            await sb_update_subscriber(session, user_id, {"digest_enabled": False})
            toast = "Дайджест отключён."
        sub = await sb_get_subscriber(session, user_id)
        t_ui, m_ui = get_digest_settings_ui(sub)
        await edit_message(session, chat_id, msg_id, t_ui, m_ui)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": toast})
        return
    elif user_id == ADMIN_ID and data == "dg_as_bc":
        raw_text = PENDING_DIGEST.pop(user_id, None)
        if not raw_text:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Текст не найден, отправь заново.", "show_alert": True})
            return
        PENDING_BROADCAST[user_id] = raw_text
        users = await sb_get_all_active_subscribers(session)
        preview_snip = html.escape(raw_text[:600]) + ("…" if len(raw_text) > 600 else "")
        kb = {
            "inline_keyboard": [
                [{"text": "🧪 Тест себе (Админу)", "callback_data": "bc_test"}],
                [{"text": f"🚀 Отправить всем ({len(users)} чел.)", "callback_data": "bc_send_ask"}],
                [{"text": "❌ Отмена", "callback_data": "bc_cancel"}],
            ]
        }
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"📣 <b>Общая рассылка всем</b> ({len(raw_text)} симв.)\n\n{preview_snip}\n\n<i>Выбери действие:</i>",
            kb,
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data == "bc_start":
        PENDING_INPUT[user_id] = {"mode": "broadcast_general"}
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Жду текст рассылки"})
        await send_message(
            session,
            chat_id,
            "📣 <b>Общая рассылка пользователям бота</b>\n\nОтправь текст сообщения следующим сообщением:",
            message_thread_id=thread_id,
        )
        return
    elif user_id == ADMIN_ID and data == "bc_cancel":
        PENDING_BROADCAST.pop(user_id, None)
        await edit_message(session, chat_id, msg_id, "❌ Общая рассылка отменена.")
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data == "bc_test":
        raw_text = PENDING_BROADCAST.get(user_id)
        if not raw_text:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Текст не найден.", "show_alert": True})
            return
        ok, _ = await send_general_broadcast_to_user(session, ADMIN_ID, raw_text)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Тест отправлен!" if ok else "Ошибка отправки"})
        return
    elif user_id == ADMIN_ID and data == "bc_send_ask":
        raw_text = PENDING_BROADCAST.get(user_id)
        if not raw_text:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Текст не найден.", "show_alert": True})
            return
        users = await sb_get_all_active_subscribers(session)
        kb = {
            "inline_keyboard": [
                [
                    {"text": f"✅ Да, отправить ({len(users)})", "callback_data": "bc_send_go"},
                    {"text": "❌ Отмена", "callback_data": "bc_cancel"},
                ]
            ]
        }
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"🚀 Подтверди общую рассылку.\nПолучателей в базе: <b>{len(users)}</b>",
            kb,
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data == "bc_send_go":
        raw_text = PENDING_BROADCAST.pop(user_id, None)
        if not raw_text:
            await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Текст не найден.", "show_alert": True})
            return
        await edit_message(session, chat_id, msg_id, "⏳ Запускаю общую рассылку…")
        sent, blocked = await broadcast_general_all(session, raw_text)
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"✅ <b>Общая рассылка завершена!</b>\n• Доставлено: <b>{sent}</b>\n• Недоступны / заблокировали: <b>{blocked}</b>",
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Готово!"})
        return
    elif user_id == ADMIN_ID and data == "dg_ann_preview":
        users = await sb_get_all_active_subscribers(session)
        ann_text, _ = get_digest_announce_ui()
        kb = {
            "inline_keyboard": [
                [{"text": "🧪 Тест себе (Админу)", "callback_data": "dg_ann_test"}],
                [{"text": f"🚀 Отправить всем ({len(users)} чел.)", "callback_data": "dg_ann_ask"}],
                [{"text": "⬅️ Назад в панель", "callback_data": "sys_status"}],
            ]
        }
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"📣 <b>Предпросмотр анонса дайджеста</b>\n\n{ann_text}",
            kb,
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data == "dg_ann_test":
        ann_text, ann_kb = get_digest_announce_ui()
        res = await send_message(session, ADMIN_ID, ann_text, reply_markup=ann_kb)
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Тест отправлен!" if res.get("ok") else "Ошибка отправки"})
        return
    elif user_id == ADMIN_ID and data == "dg_ann_ask":
        users = await sb_get_all_active_subscribers(session)
        kb = {
            "inline_keyboard": [
                [
                    {"text": f"✅ Да, разослать ({len(users)})", "callback_data": "dg_ann_go"},
                    {"text": "❌ Отмена", "callback_data": "sys_status"},
                ]
            ]
        }
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"🚀 Подтверди рассылку анонса велодайджеста с кнопками выбора тем.\nПолучателей: <b>{len(users)}</b>",
            kb,
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id})
        return
    elif user_id == ADMIN_ID and data == "dg_ann_go":
        await edit_message(session, chat_id, msg_id, "⏳ Рассылаю анонс дайджеста…")
        sent, blocked = await broadcast_digest_announce_all(session)
        await edit_message(
            session,
            chat_id,
            msg_id,
            f"✅ <b>Анонс дайджеста разослан!</b>\n• Доставлено: <b>{sent}</b>\n• Недоступны / заблокировали: <b>{blocked}</b>",
        )
        await tg_request(session, "answerCallbackQuery", {"callback_query_id": cb_id, "text": "Готово!"})
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
    app["digest_task"] = asyncio.create_task(digest_scheduler_loop())
    app["polling_task"] = asyncio.create_task(polling_loop(app))


async def on_cleanup(app: web.Application):
    for task_name in ["data_task", "digest_task", "polling_task"]:
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