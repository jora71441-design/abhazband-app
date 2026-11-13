import ast
import base64
import html
import os
from aiohttp import ClientSession

# ==================== КОНФИГУРАЦИЯ GITHUB И RENDER ====================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "jora71441-design").strip()
GITHUB_APP_REPO = os.getenv("GITHUB_APP_REPO", "abhazband-app").strip()
GITHUB_BOT_REPO = os.getenv("GITHUB_BOT_REPO", GITHUB_APP_REPO).strip()
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main").strip()
RENDER_DEPLOY_HOOK = os.getenv("RENDER_DEPLOY_HOOK", "").strip()

# Автоматическая карта путей для фронтенда AbhazBand Mini App
FRONTEND_PATH_MAP = {
    "index.html": "index.html",
    "style.css": "css/style.css",
    "config.js": "js/config.js",
    "data.js": "js/data.js",
    "supabase.js": "js/supabase.js",
    "utils.js": "js/utils.js",
    "render.js": "js/render.js",
    "app.js": "js/app.js",
}


def resolve_target(filename: str, caption: str) -> tuple[str, str, bool]:
    """
    Определяет целевой репозиторий, путь внутри него и необходимость редеплоя Render.
    Поддерживает явные пути в подписи к файлу (например: js/data.js, images/velouyut/v11.png, bot:widgets/rides.py).
    """
    clean_caption = (caption or "").strip()

    if clean_caption.startswith("app:"):
        return GITHUB_APP_REPO, clean_caption[4:].strip().lstrip("/"), False
    if clean_caption.startswith("bot:"):
        return GITHUB_BOT_REPO, clean_caption[4:].strip().lstrip("/"), True

    if clean_caption and " " not in clean_caption:
        target_path = clean_caption.lstrip("/")
        is_backend = target_path.endswith(".py") or target_path in ("requirements.txt", "Procfile")
        return (GITHUB_BOT_REPO if is_backend else GITHUB_APP_REPO), target_path, is_backend

    if filename in FRONTEND_PATH_MAP:
        return GITHUB_APP_REPO, FRONTEND_PATH_MAP[filename], False

    if filename.lower().endswith(".gpx"):
        return GITHUB_APP_REPO, f"Gpx/{filename}", False

    if filename.lower().endswith((".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg")):
        return GITHUB_APP_REPO, filename, False

    is_backend = filename.endswith(".py") or filename in ("requirements.txt", "Procfile")
    return GITHUB_BOT_REPO, filename, is_backend


def validate_python_syntax(filename: str, raw_bytes: bytes) -> tuple[bool, str]:
    """Проверяет синтаксис Python-файла в памяти перед отправкой на GitHub."""
    try:
        source_code = raw_bytes.decode("utf-8")
        ast.parse(source_code, filename=filename)
        return True, ""
    except UnicodeDecodeError:
        return False, "Файл не в кодировке UTF-8."
    except SyntaxError as err:
        return False, f"Строка {err.lineno}, позиция {err.offset}: {err.msg}"


async def upload_to_github(
    session: ClientSession, repo: str, path: str, content_bytes: bytes, commit_message: str
) -> tuple[bool, str]:
    """Получает текущий SHA файла (если существует) и создаёт коммит через GitHub Contents API."""
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    sha = None
    async with session.get(url, headers=headers, params={"ref": GITHUB_BRANCH}) as resp:
        if resp.status == 200:
            data = await resp.json()
            sha = data.get("sha")
        elif resp.status != 404:
            err_text = await resp.text()
            return False, f"Ошибка чтения SHA ({resp.status}): {err_text[:200]}"

    payload = {
        "message": commit_message,
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    async with session.put(url, headers=headers, json=payload) as put_resp:
        if put_resp.status in (200, 201):
            res_data = await put_resp.json()
            html_url = res_data.get("content", {}).get("html_url", "")
            return True, html_url
        err_text = await put_resp.text()
        return False, f"Ошибка коммита ({put_resp.status}): {err_text[:250]}"


async def trigger_render_deploy(session: ClientSession) -> bool:
    """Запускает пересборку веб-сервиса на Render через Deploy Hook."""
    if not RENDER_DEPLOY_HOOK:
        return False
    async with session.post(RENDER_DEPLOY_HOOK) as resp:
        return resp.status in (200, 201, 202)


async def process_uploaded_file(
    session: ClientSession, filename: str, raw_bytes: bytes, caption: str = ""
) -> str:
    """Полный пайплайн обработки документа от администратора. Возвращает HTML-отчёт для Telegram."""
    if not GITHUB_TOKEN:
        return "⚠️ Переменная <code>GITHUB_TOKEN</code> не задана в настройках Render."

    if filename.endswith(".py"):
        is_valid, err_msg = validate_python_syntax(filename, raw_bytes)
        if not is_valid:
            safe_err = html.escape(err_msg)
            return (
                f"🚫 <b>Коммит отменён!</b>\n"
                f"В файле <code>{html.escape(filename)}</code> найдена ошибка синтаксиса:\n"
                f"<code>{safe_err}</code>"
            )

    target_repo, target_path, need_redeploy = resolve_target(filename, caption)
    commit_msg = f"Update {target_path} via @AbhazBand_bot"

    ok, info = await upload_to_github(session, target_repo, target_path, raw_bytes, commit_msg)
    if not ok:
        return f"❌ <b>Сбой GitHub API:</b>\n<code>{html.escape(info)}</code>"

    lines = [
        "✅ <b>Файл успешно залит в репозиторий!</b>",
        f"📦 Репо: <code>{GITHUB_OWNER}/{target_repo}</code>",
        f"📄 Путь: <code>{target_path}</code>",
    ]

    if need_redeploy:
        if RENDER_DEPLOY_HOOK:
            redeployed = await trigger_render_deploy(session)
            if redeployed:
                lines.append("🚀 <b>Render Deploy Hook:</b> запущена пересборка сервера бота.")
            else:
                lines.append("⚠️ Не удалось вызвать Render Deploy Hook.")
        else:
            lines.append("ℹ️ <code>RENDER_DEPLOY_HOOK</code> не задан — пересборку на Render нужно запустить вручную.")
    else:
        lines.append("🌐 <b>GitHub Pages:</b> фронтенд обновится автоматически (~30 сек).")

    return "\n".join(lines)


def get_uploader_status() -> str:
    gh_status = "✅ подключён" if GITHUB_TOKEN else "❌ не задан"
    hook_status = "✅ подключён" if RENDER_DEPLOY_HOOK else "⚠️ не задан"
    return (
        f"• GitHub Token: {gh_status}\n"
        f"• Репозиторий: <code>{GITHUB_OWNER}/{GITHUB_APP_REPO}</code> (ветка <code>{GITHUB_BRANCH}</code>)\n"
        f"• Render Deploy Hook: {hook_status}"
    )
