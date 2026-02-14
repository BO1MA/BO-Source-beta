"""
Broadcast handler — send messages to all groups or all users (private).
Based on the broadcast system from bian.lua.
Supports: اذاعه, اذاعه بالتثبيت, اذاعه بالتوجيه, اذاعه خاص.
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

from src.config import Config
from src.constants.messages import MSG_BROADCAST_DONE, MSG_BROADCAST_STARTED, MSG_NO_PERMISSION
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.services.redis_service import RedisService
from src.utils.decorators import group_only
from src.utils.text_utils import extract_command_arg
from src.utils.api_helpers import pin_message

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()
redis_svc = RedisService()


async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all registered groups."""
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Determine broadcast mode
    pin = False
    forward = False
    private = False
    groups_only = False

    if text.startswith("اذاعه بالتثبيت"):
        pin = True
    elif text.startswith("اذاعه بالتوجيه خاص"):
        forward = True
        private = True
    elif text.startswith("اذاعه بالتوجيه"):
        forward = True
    elif text.startswith("اذاعه خاص"):
        private = True
    elif text.startswith("اذاعه للمجموعات"):
        groups_only = True

    # Determine content to broadcast
    broadcast_msg = None
    if update.message.reply_to_message:
        broadcast_msg = update.message.reply_to_message
    else:
        for prefix in ("اذاعه بالتثبيت", "اذاعه بالتوجيه خاص", "اذاعه بالتوجيه", "اذاعه للمجموعات", "اذاعه خاص", "اذاعه"):
            if text.startswith(prefix):
                content = text[len(prefix):].strip()
                if content:
                    broadcast_msg = content
                break

    if not broadcast_msg:
        await update.message.reply_text("✯ قم بالرد على رساله او اكتب نص بعد الامر")
        return

    await update.message.reply_text(MSG_BROADCAST_STARTED)

    if private:
        # Broadcast to all registered users via private message
        user_ids = [int(uid) for uid in redis_svc.smembers("bot:users")]
        success = 0
        failed = 0
        for uid in user_ids:
            try:
                if forward and hasattr(broadcast_msg, 'message_id'):
                    await context.bot.forward_message(
                        chat_id=uid,
                        from_chat_id=update.effective_chat.id,
                        message_id=broadcast_msg.message_id,
                    )
                elif hasattr(broadcast_msg, 'message_id'):
                    await context.bot.copy_message(
                        chat_id=uid,
                        from_chat_id=update.effective_chat.id,
                        message_id=broadcast_msg.message_id,
                    )
                else:
                    await context.bot.send_message(chat_id=uid, text=broadcast_msg)
                success += 1
                await asyncio.sleep(0.05)
            except TelegramError as e:
                logger.warning(f"Private broadcast failed for {uid}: {e}")
                failed += 1

        await update.message.reply_text(
            f"✯ تم ارسال الاذاعه الخاصه الى {success} مستخدم ✅"
            + (f"\n✯ فشل: {failed}" if failed else "")
        )
    else:
        # Broadcast to all groups
        group_ids = group_svc.get_all_group_ids()
        success = 0
        failed = 0

        for gid in group_ids:
            try:
                # groups_only mode ignores broadcast_enabled setting
                if not groups_only:
                    settings = group_svc.get_settings(gid)
                    if not settings.broadcast_enabled:
                        continue

                if forward and hasattr(broadcast_msg, 'message_id'):
                    await context.bot.forward_message(
                        chat_id=gid,
                        from_chat_id=update.effective_chat.id,
                        message_id=broadcast_msg.message_id,
                    )
                elif hasattr(broadcast_msg, 'message_id'):
                    sent = await context.bot.copy_message(
                        chat_id=gid,
                        from_chat_id=update.effective_chat.id,
                        message_id=broadcast_msg.message_id,
                    )
                    if pin:
                        await pin_message(context.bot, gid, sent.message_id)
                else:
                    sent = await context.bot.send_message(chat_id=gid, text=broadcast_msg)
                    if pin:
                        await pin_message(context.bot, gid, sent.message_id)

                success += 1
                await asyncio.sleep(0.1)
            except TelegramError as e:
                logger.warning(f"Broadcast failed for {gid}: {e}")
                failed += 1
                if "chat not found" in str(e).lower() or "kicked" in str(e).lower():
                    group_svc.remove_group(gid)

        await update.message.reply_text(
            MSG_BROADCAST_DONE.format(count=success)
            + (f"\n✯ فشل: {failed}" if failed else "")
        )


def register(app: Application) -> None:
    """Register broadcast handlers."""
    app.add_handler(MessageHandler(
        filters.Regex("^اذاعه") & (filters.ChatType.GROUPS | filters.ChatType.PRIVATE),
        handle_broadcast,
    ), group=8)
