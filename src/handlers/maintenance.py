"""
Maintenance handler — sudo-only operational commands.
Implements missing Lua-style maintenance commands such as:
- تحديث السورس / تحديث الملفات
- جلب نسخه احتياطيه
- رفع نسخه احتياطيه
- رفع نسخه كلير
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.constants.messages import MSG_NO_PERMISSION
from src.services.user_service import UserService
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
user_svc = UserService()
redis_svc = RedisService()


def _is_sudo(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user_svc.is_sudo(user.id))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_command(command: list[str], cwd: Path, timeout: int = 120) -> tuple[bool, str]:
    try:
        res = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        output = output.strip()[:3500] or "(no output)"
        return res.returncode == 0, output
    except Exception as exc:
        return False, str(exc)


def _dump_bot_data() -> dict:
    payload: dict = {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "keys": [],
    }

    keys = redis_svc.keys("bot:*")
    for key in keys:
        key_type = redis_svc.client.type(key)

        if key_type == "string":
            payload["keys"].append({"key": key, "type": "string", "value": redis_svc.get(key)})
        elif key_type == "hash":
            payload["keys"].append({"key": key, "type": "hash", "value": redis_svc.hgetall(key)})
        elif key_type == "set":
            payload["keys"].append({"key": key, "type": "set", "value": sorted(list(redis_svc.smembers(key)))})
        elif key_type == "list":
            payload["keys"].append({"key": key, "type": "list", "value": redis_svc.client.lrange(key, 0, -1)})

    return payload


def _restore_bot_data(data: dict, clear_first: bool = False) -> tuple[int, int]:
    if clear_first:
        existing = redis_svc.keys("bot:*")
        if existing:
            redis_svc.client.delete(*existing)

    restored = 0
    skipped = 0

    for item in data.get("keys", []):
        key = item.get("key")
        key_type = item.get("type")
        value = item.get("value")
        if not key or not key_type:
            skipped += 1
            continue

        try:
            if key_type == "string":
                redis_svc.set(key, value or "")
            elif key_type == "hash":
                redis_svc.client.delete(key)
                if isinstance(value, dict) and value:
                    redis_svc.client.hset(key, mapping=value)
            elif key_type == "set":
                redis_svc.client.delete(key)
                if isinstance(value, list) and value:
                    redis_svc.client.sadd(key, *value)
            elif key_type == "list":
                redis_svc.client.delete(key)
                if isinstance(value, list) and value:
                    redis_svc.client.rpush(key, *value)
            else:
                skipped += 1
                continue
            restored += 1
        except Exception:
            skipped += 1

    return restored, skipped


async def handle_update_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تحديث السورس — sudo-only git pull."""
    if not _is_sudo(update):
        await update.effective_message.reply_text(MSG_NO_PERMISSION)
        return

    root = _repo_root()
    if not (root / ".git").exists():
        await update.effective_message.reply_text("✯ لا يوجد مستودع git في هذا السيرفر")
        return

    await update.effective_message.reply_text("✯ جاري تحديث السورس...")
    ok, out = _run_command(["git", "pull", "--ff-only"], root)
    status = "✅ تم تحديث السورس" if ok else "❌ فشل تحديث السورس"
    await update.effective_message.reply_text(f"{status}\n\n{out}")


async def handle_update_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تحديث الملفات — sudo-only git pull + pip install -r requirements.txt."""
    if not _is_sudo(update):
        await update.effective_message.reply_text(MSG_NO_PERMISSION)
        return

    root = _repo_root()
    if not (root / ".git").exists():
        await update.effective_message.reply_text("✯ لا يوجد مستودع git في هذا السيرفر")
        return

    await update.effective_message.reply_text("✯ جاري تحديث الملفات...")

    ok_pull, out_pull = _run_command(["git", "pull", "--ff-only"], root)

    req = root / "requirements.txt"
    if req.exists():
        ok_pip, out_pip = _run_command([sys.executable, "-m", "pip", "install", "-r", str(req)], root, timeout=240)
    else:
        ok_pip, out_pip = True, "requirements.txt not found"

    ok = ok_pull and ok_pip
    status = "✅ تم تحديث الملفات" if ok else "❌ فشل تحديث الملفات"
    await update.effective_message.reply_text(
        f"{status}\n\n[git]\n{out_pull}\n\n[pip]\n{out_pip}"
    )


async def handle_backup_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """جلب نسخه احتياطيه — export bot Redis data."""
    if not _is_sudo(update):
        await update.effective_message.reply_text(MSG_NO_PERMISSION)
        return

    payload = _dump_bot_data()
    content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    bio = BytesIO(content)
    bio.name = f"bo_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    bio.seek(0)

    await update.effective_message.reply_document(
        document=bio,
        filename=bio.name,
        caption=f"✯ تم إنشاء النسخة الاحتياطية\n✯ عدد المفاتيح: {len(payload.get('keys', []))}",
    )


async def _restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE, clear_first: bool) -> None:
    if not _is_sudo(update):
        await update.effective_message.reply_text(MSG_NO_PERMISSION)
        return

    source_msg = update.effective_message
    doc = None
    if source_msg and source_msg.reply_to_message and source_msg.reply_to_message.document:
        doc = source_msg.reply_to_message.document
    elif source_msg and source_msg.document:
        doc = source_msg.document

    if not doc:
        await update.effective_message.reply_text(
            "✯ ارسل الامر مع الرد على ملف النسخة الاحتياطية (.json)"
        )
        return

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        file_bytes = await tg_file.download_as_bytearray()
        data = json.loads(bytes(file_bytes).decode("utf-8"))
    except Exception as exc:
        await update.effective_message.reply_text(f"✯ فشل قراءة ملف النسخة: {exc}")
        return

    restored, skipped = _restore_bot_data(data, clear_first=clear_first)
    mode = "(كلير)" if clear_first else ""
    await update.effective_message.reply_text(
        f"✯ تم استرجاع النسخة {mode} ✅\n✯ تم: {restored}\n✯ تخطي: {skipped}"
    )


async def handle_backup_restore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رفع نسخه احتياطيه — restore without clearing all existing keys first."""
    await _restore_backup(update, context, clear_first=False)


async def handle_backup_restore_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رفع نسخه كلير — clear bot keys then restore backup."""
    await _restore_backup(update, context, clear_first=True)


def register(app: Application) -> None:
    """Register maintenance handlers."""
    ANY = filters.ALL

    app.add_handler(MessageHandler(
        filters.Regex(r"^(تحديث السورس|تحديث السورس 𖥔)$") & ANY,
        handle_update_source,
    ), group=3)

    app.add_handler(MessageHandler(
        filters.Regex(r"^(تحديث الملفات|تحديث الملفات 𖥔)$") & ANY,
        handle_update_files,
    ), group=3)

    app.add_handler(MessageHandler(
        filters.Regex(r"^(جلب نسخه احتياطيه|جلب النسخه الاحتياطيه 𖥔)$") & ANY,
        handle_backup_export,
    ), group=3)

    app.add_handler(MessageHandler(
        filters.Regex(r"^(رفع نسخه احتياطيه|رفع النسخه الاحتياطيه)$") & ANY,
        handle_backup_restore,
    ), group=3)

    app.add_handler(MessageHandler(
        filters.Regex(r"^رفع نسخه كلير$") & ANY,
        handle_backup_restore_clear,
    ), group=3)
