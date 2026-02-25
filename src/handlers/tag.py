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
from src.services.redis_service import RedisService
from src.utils.decorators import group_only

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()
redis = RedisService()


def _tag_cooldown_key(chat_id: int, user_id: int) -> str:
    return f"bot:tagall:cooldown:{chat_id}:{user_id}"


def _build_tag_header(text: str) -> str:
    msg = text.strip()
    lowered = msg.lower()

    if lowered.startswith("@all "):
        extra = msg[5:].strip()
        return f"#all {extra}" if extra else "#all"

    if lowered.startswith("all "):
        extra = msg[4:].strip()
        return f"#all {extra}" if extra else "#all"

    return "#all"


@group_only
async def handle_tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tag all members in the group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    # Check if tag is enabled
    settings = group_svc.get_settings(chat_id)
    if not settings.tag_enabled:
        await update.message.reply_text(MSG_TAG_DISABLED)
        return

    # Only admins can tag all
    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Cooldown (matches Lua behavior: 60s)
    cooldown_key = _tag_cooldown_key(chat_id, from_user.id)
    if redis.exists(cooldown_key):
        await update.message.reply_text(MSG_TAG_WAIT)
        return
    redis.set(cooldown_key, "1", ex=60)

    await update.message.reply_text(MSG_TAG_WAIT)

    try:
        tag_header = _build_tag_header(text)

        # We can't truly enumerate all members via Bot API,
        # so we tag users we know about from Redis
        pattern = f"bot:group:{chat_id}:user:*"
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

        # Send in batches of 5 mentions per message (like Lua)
        batch_size = 5
        for i in range(0, len(mentions), batch_size):
            batch = mentions[i:i + batch_size]
            payload = f"{tag_header}\n" + "، ".join(batch)
            try:
                await context.bot.send_message(
                    chat_id, payload, parse_mode="HTML"
                )
                await asyncio.sleep(0.5)  # Rate limiting
            except TelegramError as e:
                logger.warning(f"Tag batch failed: {e}")
                break

    except Exception as e:
        logger.error(f"Tag all failed: {e}")
        await update.message.reply_text("\u2756 حدث خطأ اثناء التاغ")


@group_only
async def handle_enable_tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تفعيل all / تفعيل @all."""
    chat_id = update.effective_chat.id
    user = update.effective_user

    if not user_svc.is_group_admin(user.id, chat_id) and not user_svc.is_sudo(user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    group_svc.toggle_setting(chat_id, "tag_enabled", True)
    await update.message.reply_text("☭ تم تفعيل امر @all")


@group_only
async def handle_disable_tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تعطيل all / تعطيل @all."""
    chat_id = update.effective_chat.id
    user = update.effective_user

    if not user_svc.is_group_admin(user.id, chat_id) and not user_svc.is_sudo(user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    group_svc.toggle_setting(chat_id, "tag_enabled", False)
    await update.message.reply_text("☭ تم تعطيل امر @all")


def register(app: Application) -> None:
    """Register tag handlers."""
    G = filters.ChatType.GROUPS

    # Enable / disable all tagging
    app.add_handler(MessageHandler(
        filters.Regex("^(تفعيل all|تفعيل @all)$") & G,
        handle_enable_tag_all,
    ), group=12)

    app.add_handler(MessageHandler(
        filters.Regex("^(تعطيل all|تعطيل @all)$") & G,
        handle_disable_tag_all,
    ), group=12)

    # all with optional text (all hello / @all hello)
    app.add_handler(MessageHandler(
        filters.Regex(r"^(@all|all)\s+.+$") & G,
        handle_tag_all,
    ), group=12)

    # plain all / @all
    app.add_handler(MessageHandler(
        filters.Regex("^(all|@all|الكل|تاك للكل)$") & G,
        handle_tag_all,
    ), group=12)
