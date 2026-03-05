"""Force subscribe middleware - verify channel membership before allowing commands."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
redis_svc = RedisService()


async def check_channel_subscription(
    bot, user_id: int, channel_username: str
) -> bool:
    """Check if user is subscribed to a channel."""
    try:
        member = await bot.get_chat_member(
            chat_id=f"@{channel_username.strip('@')}",
            user_id=user_id
        )
        
        # Check if user is a member (not restricted or kicked)
        return member.status in ["member", "administrator", "creator"]
        
    except BadRequest:
        # Channel doesn't exist or other error
        return False
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        return False


async def force_subscribe_middleware(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    required_channels: list[str]
) -> bool:
    """
    Middleware to force subscription before allowing command.
    
    Args:
        update: Telegram update
        context: Bot context
        required_channels: List of channel usernames to verify
        
    Returns:
        True if user is subscribed to all channels, False otherwise.
    """
    
    if not update.message or not required_channels:
        return True
    
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    # Skip force subscribe in group chats
    if chat_type == "group" or chat_type == "supergroup":
        return True
    
    # Get cache key
    cache_key = f"subscribed:{user_id}"
    
    # Check if recently verified
    if redis_svc.get(cache_key):
        return True
    
    unsubscribed = []
    
    # Check each required channel
    for channel in required_channels:
        if not await check_channel_subscription(context.bot, user_id, channel):
            unsubscribed.append(channel)
    
    # If user is subscribed to all channels
    if not unsubscribed:
        # Cache for 24 hours
        redis_svc.set(cache_key, "1", ex=86400)
        return True
    
    # User is not subscribed - show message
    keyboard = []
    for channel in unsubscribed:
        clean_name = channel.strip("@")
        keyboard.append([
            InlineKeyboardButton(
                f"اشترك في {clean_name} 🔗",
                url=f"https://t.me/{clean_name}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            "تحقق من الاشتراك ✓",
            callback_data="check_subscription"
        )
    ])
    
    await update.message.reply_text(
        "✯ يجب عليك الاشتراك في القنوات التالية أولاً:\n\n" +
        "\n".join([f"• {ch.strip('@')}" for ch in unsubscribed]) +
        "\n\nبعد الاشتراك اضغط على 'تحقق من الاشتراك'",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return False


async def handle_subscription_check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    required_channels: list[str]
) -> None:
    """Handle subscription check button click."""
    query = update.callback_query
    user_id = query.from_user.id
    
    unsubscribed = []
    
    for channel in required_channels:
        if not await check_channel_subscription(context.bot, user_id, channel):
            unsubscribed.append(channel)
    
    if not unsubscribed:
        # User is now subscribed
        cache_key = f"subscribed:{user_id}"
        redis_svc.set(cache_key, "1", ex=86400)
        
        await query.answer("✓ تم التحقق من الاشتراك بنجاح!", show_alert=False)
        await query.edit_message_text(
            "✯ شكراً للاشتراك! 🎉\n\n"
            "يمكنك الآن استخدام الأوامر بحرية."
        )
    else:
        # Still not subscribed
        await query.answer(
            f"❌ لم تشترك في جميع القنوات المطلوبة بعد",
            show_alert=False
        )


def get_force_subscribe_decorator(required_channels: list[str]):
    """
    Create a decorator for force subscribe middleware.
    
    Usage:
        @get_force_subscribe_decorator(["@channel1", "@channel2"])
        async def my_handler(update, context):
            ...
    """
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if await force_subscribe_middleware(update, context, required_channels):
                return await func(update, context)
        return wrapper
    return decorator


async def register_force_subscribe(app, required_channels: list[str]) -> None:
    """Register force subscribe handlers."""
    from telegram.ext import CallbackQueryHandler
    
    # Create callback handler for subscription check
    async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await handle_subscription_check(update, context, required_channels)
    
    app.add_handler(
        CallbackQueryHandler(
            check_handler,
            pattern="^check_subscription$"
        )
    )


# Example usage in messages.py or config-like file:
"""
FORCE_SUBSCRIBE_CHANNELS = [
    "@channel1",
    "@channel2",
    "@updates_channel"
]

# Then in bot registration:
from src.handlers.force_subscribe import get_force_subscribe_decorator
force_subs = get_force_subscribe_decorator(FORCE_SUBSCRIBE_CHANNELS)

@force_subs
@group_only
async def some_command(update, context):
    ...
"""
