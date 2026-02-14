"""
Private DM relay — forwards private messages from users to the developer,
and lets the developer reply back to the user through the bot.

Flow:
  1. User sends DM to bot → bot forwards it to SUDO_ID with user info header.
  2. Developer replies to the forwarded message → bot sends it back to the user.
"""
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.config import Config

# Redis key pattern: dm_relay:{developer_msg_id} → user_chat_id
_KEY_PREFIX = "dm_relay"


async def _relay_to_developer(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward a user's private message to the developer."""
    msg = update.effective_message
    if not msg or not update.effective_user:
        return

    sudo_id = Config.SUDO_ID
    if not sudo_id:
        return

    user = update.effective_user
    # Don't relay messages from the developer themselves
    if user.id == sudo_id:
        return

    # Build info header
    header = (
        f"📩 رسالة خاصة\n"
        f"👤 الاسم: {user.full_name}\n"
        f"🆔 الايدي: {user.id}\n"
    )
    if user.username:
        header += f"📎 اليوزر: @{user.username}\n"

    # Send header then forward the actual message
    sent_header = await ctx.bot.send_message(chat_id=sudo_id, text=header)
    forwarded = await msg.forward(chat_id=sudo_id)

    # Store the mapping: forwarded_msg_id → user_chat_id in Redis (TTL = 7 days)
    if forwarded:
        from src.services.redis_service import RedisService
        redis = RedisService()
        key = f"{_KEY_PREFIX}:{forwarded.message_id}"
        redis.set(key, str(user.id), ex=7 * 86400)

    await msg.reply_text("✅ تم إرسال رسالتك للمطور، سيتم الرد عليك قريباً.")


async def _relay_to_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """When developer replies to a forwarded message, send it back to the user."""
    msg = update.effective_message
    if not msg or not update.effective_user:
        return

    sudo_id = Config.SUDO_ID
    if not sudo_id:
        return

    # Only process developer's replies
    if update.effective_user.id != sudo_id:
        return

    # Must be a reply to a forwarded message
    if not msg.reply_to_message:
        return

    replied_id = msg.reply_to_message.message_id

    from src.services.redis_service import RedisService
    redis = RedisService()
    key = f"{_KEY_PREFIX}:{replied_id}"
    user_id_str = redis.get(key)

    if not user_id_str:
        return

    user_id = int(user_id_str)

    try:
        # Send text or copy the whole message
        if msg.text:
            await ctx.bot.send_message(
                chat_id=user_id,
                text=f"💬 رد المطور:\n\n{msg.text}",
            )
        else:
            await msg.copy(chat_id=user_id)

        await msg.reply_text("✅ تم إرسال الرد.")
    except Exception as e:
        await msg.reply_text(f"❌ فشل الإرسال: {e}")


def register(app: Application) -> None:
    """Register DM relay handlers (private chat only)."""
    # Developer reply (must come first — higher priority)
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.REPLY & filters.User(Config.SUDO_ID),
            _relay_to_user,
        ),
        group=110,
    )

    # User → Developer relay (catch-all private messages, lowest priority)
    # Allow all messages including commands (except /start which is handled separately)
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.User(Config.SUDO_ID) & ~filters.Regex("^/start"),
            _relay_to_developer,
        ),
        group=111,
    )
