"""
Tag handler — tag/mention all members in a group.
Based on @all / all from bian.lua.
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

from src.constants.messages import MSG_TAG_WAIT, MSG_TAG_DISABLED, MSG_NO_PERMISSION
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()


@group_only
async def handle_tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members in the group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    # Check if tag is enabled
    settings = group_svc.get_settings(chat_id)
    if not settings.tag_enabled:
        await update.message.reply_text(MSG_TAG_DISABLED)
        return

    # Only admins can tag all
    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    await update.message.reply_text(MSG_TAG_WAIT)

    try:
        # Get member count
        member_count = await context.bot.get_chat_member_count(chat_id)

        # We can't truly enumerate all members via Bot API,
        # so we tag users we know about from Redis
        pattern = f"bot:group:{chat_id}:user:*"
        from src.services.redis_service import RedisService
        redis = RedisService()
        user_keys = redis.keys(pattern)

        if not user_keys:
            await update.message.reply_text("\u2756 لا توجد بيانات اعضاء مسجله")
            return

        # Build mentions in batches
        mentions = []
        for key in user_keys:
            uid = int(key.rsplit(":", 1)[-1])
            user = user_svc.get_user(uid)
            if user.first_name:
                mentions.append(f'<a href="tg://user?id={uid}">{user.first_name}</a>')

        # Send in batches of 5 mentions per message
        batch_size = 5
        for i in range(0, len(mentions), batch_size):
            batch = mentions[i:i + batch_size]
            text = " | ".join(batch)
            try:
                await context.bot.send_message(
                    chat_id, text, parse_mode="HTML"
                )
                await asyncio.sleep(0.5)  # Rate limiting
            except TelegramError as e:
                logger.warning(f"Tag batch failed: {e}")
                break

    except Exception as e:
        logger.error(f"Tag all failed: {e}")
        await update.message.reply_text("\u2756 حدث خطأ اثناء التاغ")


def register(app: Application) -> None:
    """Register tag handlers."""
    app.add_handler(MessageHandler(
        filters.Regex("^(all|@all|الكل|تاك للكل)$") & filters.ChatType.GROUPS,
        handle_tag_all,
    ), group=12)
