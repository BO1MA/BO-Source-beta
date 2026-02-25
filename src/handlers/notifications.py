"""
Notifications handler — sends notifications to developer about bot events.

Features:
- Notify when bot is added to a new group
- Notify when new users contact the bot in private chat
- Notify when bot is removed from a group
- Notify when bot is promoted/demoted
"""
import logging
from datetime import datetime

from telegram import Update, Chat, User, ChatMemberUpdated
from telegram.ext import (
    Application, ContextTypes, MessageHandler, ChatMemberHandler, filters
)
from telegram.error import TelegramError

from src.config import Config
from src.services.group_service import GroupService
from src.services.redis_service import RedisService
from src.services.user_service import UserService

logger = logging.getLogger(__name__)
group_svc = GroupService()
redis_svc = RedisService()
user_svc = UserService()

# Key to track users who have already been notified
_NOTIFIED_USERS_KEY = "bot:notified_private_users"


def _is_user_notified(user_id: int) -> bool:
    """Check if we already notified about this user."""
    return redis_svc.sismember(_NOTIFIED_USERS_KEY, str(user_id))


def _mark_user_notified(user_id: int) -> None:
    """Mark user as notified."""
    redis_svc.sadd(_NOTIFIED_USERS_KEY, str(user_id))


def _private_notifications_enabled() -> bool:
    """Check if private user notifications are enabled (default: True)."""
    val = redis_svc.get("bot:notify_private_users")
    # Default to enabled if not set
    return val != "0"


def _format_user_link(user: User) -> str:
    """Format user mention with link."""
    name = user.first_name
    if user.last_name:
        name += f" {user.last_name}"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def _format_chat_info(chat: Chat) -> str:
    """Format chat info for notification."""
    chat_type = {
        "group": "مجموعه",
        "supergroup": "سوبر جروب",
        "channel": "قناه",
    }.get(chat.type, chat.type)
    
    link = ""
    if chat.username:
        link = f"\n├─ الرابط: @{chat.username}"
    elif hasattr(chat, 'invite_link') and chat.invite_link:
        link = f"\n├─ الرابط: {chat.invite_link}"
    
    return (
        f"├─ الاسم: {chat.title}\n"
        f"├─ النوع: {chat_type}\n"
        f"├─ الايدي: <code>{chat.id}</code>"
        f"{link}"
    )


async def notify_developer(context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    """Send notification to developer."""
    if not Config.SUDO_ID:
        return
    
    try:
        await context.bot.send_message(
            chat_id=Config.SUDO_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except TelegramError as e:
        logger.error(f"Failed to send notification to developer: {e}")


# ══════════════════════════════════════════════════
# Bot Added/Removed from Group
# ══════════════════════════════════════════════════

async def handle_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when bot is added to a new group."""
    my_chat_member = update.my_chat_member
    if not my_chat_member:
        return
    
    chat = my_chat_member.chat
    new_status = my_chat_member.new_chat_member.status
    old_status = my_chat_member.old_chat_member.status
    added_by = my_chat_member.from_user
    
    # Bot was added (status changed to member or administrator)
    if old_status in ("left", "kicked") and new_status in ("member", "administrator"):
        # Register the group
        group_svc.register_group(chat.id, chat.title)
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = (
            f"🆕 <b>تمت اضافة البوت لمجموعه جديده</b>\n\n"
            f"📋 معلومات المجموعه:\n"
            f"{_format_chat_info(chat)}\n\n"
            f"👤 اضافه بواسطة:\n"
            f"├─ الاسم: {_format_user_link(added_by)}\n"
            f"├─ الايدي: <code>{added_by.id}</code>\n"
            f"└─ اليوزر: @{added_by.username or 'لايوجد'}\n\n"
            f"🕐 الوقت: {now}"
        )
        
        await notify_developer(context, notification)
        logger.info(f"Bot added to group: {chat.title} ({chat.id}) by {added_by.id}")
    
    # Bot was removed
    elif old_status in ("member", "administrator") and new_status in ("left", "kicked"):
        # Remove group from database
        group_svc.remove_group(chat.id)
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = (
            f"❌ <b>تم ازالة البوت من مجموعه</b>\n\n"
            f"📋 معلومات المجموعه:\n"
            f"{_format_chat_info(chat)}\n\n"
            f"👤 ازاله بواسطة:\n"
            f"├─ الاسم: {_format_user_link(added_by)}\n"
            f"├─ الايدي: <code>{added_by.id}</code>\n"
            f"└─ اليوزر: @{added_by.username or 'لايوجد'}\n\n"
            f"🕐 الوقت: {now}"
        )
        
        await notify_developer(context, notification)
        logger.info(f"Bot removed from group: {chat.title} ({chat.id}) by {added_by.id}")
    
    # Bot was promoted to admin
    elif old_status == "member" and new_status == "administrator":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = (
            f"⬆️ <b>تمت ترقية البوت الى مشرف</b>\n\n"
            f"📋 معلومات المجموعه:\n"
            f"{_format_chat_info(chat)}\n\n"
            f"👤 ترقيه بواسطة:\n"
            f"├─ الاسم: {_format_user_link(added_by)}\n"
            f"└─ الايدي: <code>{added_by.id}</code>\n\n"
            f"🕐 الوقت: {now}"
        )
        
        await notify_developer(context, notification)
    
    # Bot was demoted from admin
    elif old_status == "administrator" and new_status == "member":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        notification = (
            f"⬇️ <b>تم تنزيل البوت من المشرفين</b>\n\n"
            f"📋 معلومات المجموعه:\n"
            f"{_format_chat_info(chat)}\n\n"
            f"👤 تنزيل بواسطة:\n"
            f"├─ الاسم: {_format_user_link(added_by)}\n"
            f"└─ الايدي: <code>{added_by.id}</code>\n\n"
            f"🕐 الوقت: {now}"
        )
        
        await notify_developer(context, notification)


# ══════════════════════════════════════════════════
# New User Contacts Bot in Private Chat
# ══════════════════════════════════════════════════

async def handle_new_private_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Notify developer when a new user contacts the bot in private chat."""
    if not update.message or not update.effective_user:
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    # Only handle private chats
    if chat.type != "private":
        return
    
    # Skip if it's the developer himself
    if user.id == Config.SUDO_ID:
        return
    
    # Skip if notifications are disabled
    if not _private_notifications_enabled():
        return
    
    # Skip if already notified about this user
    if _is_user_notified(user.id):
        return
    
    # Mark as notified
    _mark_user_notified(user.id)
    
    # Get user bio if possible
    bio = ""
    try:
        chat_info = await context.bot.get_chat(user.id)
        if chat_info.bio:
            bio = f"\n├─ البايو: {chat_info.bio}"
    except TelegramError:
        pass
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_preview = (update.message.text or "")[:50]
    if len(update.message.text or "") > 50:
        message_preview += "..."
    
    notification = (
        f"💬 <b>مستخدم جديد تواصل مع البوت</b>\n\n"
        f"👤 معلومات المستخدم:\n"
        f"├─ الاسم: {_format_user_link(user)}\n"
        f"├─ الايدي: <code>{user.id}</code>\n"
        f"├─ اليوزر: @{user.username or 'لايوجد'}"
        f"{bio}\n\n"
        f"💭 الرساله: {message_preview}\n\n"
        f"🕐 الوقت: {now}"
    )
    
    await notify_developer(context, notification)
    logger.info(f"New private user: {user.first_name} ({user.id})")


# ══════════════════════════════════════════════════
# Toggle Notifications Commands
# ══════════════════════════════════════════════════

async def handle_enable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable private user notifications (sudo only)."""
    from_user = update.effective_user
    
    # Only sudo can enable
    if from_user.id != Config.SUDO_ID:
        return
    
    redis_svc.set("bot:notify_private_users", "1")
    await update.message.reply_text("✯ تم تفعيل اشعارات المستخدمين الجدد ✅")


async def handle_disable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disable private user notifications (sudo only)."""
    from_user = update.effective_user
    
    # Only sudo can disable
    if from_user.id != Config.SUDO_ID:
        return
    
    redis_svc.set("bot:notify_private_users", "0")
    await update.message.reply_text("✯ تم تعطيل اشعارات المستخدمين الجدد ❌")


# ══════════════════════════════════════════════════
# New Chat Members via Message (fallback)
# ══════════════════════════════════════════════════

async def handle_new_chat_members_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new_chat_members message event (fallback for older style)."""
    if not update.message or not update.message.new_chat_members:
        return
    
    chat = update.effective_chat
    
    for new_member in update.message.new_chat_members:
        # Check if the bot itself was added
        if new_member.id == context.bot.id:
            # Register the group
            group_svc.register_group(chat.id, chat.title)
            
            added_by = update.effective_user
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            notification = (
                f"🆕 <b>تمت اضافة البوت لمجموعه جديده</b>\n\n"
                f"📋 معلومات المجموعه:\n"
                f"├─ الاسم: {chat.title}\n"
                f"├─ الايدي: <code>{chat.id}</code>\n\n"
                f"👤 اضافه بواسطة:\n"
                f"├─ الاسم: {_format_user_link(added_by)}\n"
                f"├─ الايدي: <code>{added_by.id}</code>\n"
                f"└─ اليوزر: @{added_by.username or 'لايوجد'}\n\n"
                f"🕐 الوقت: {now}"
            )
            
            await notify_developer(context, notification)


# ══════════════════════════════════════════════════
# Left Chat Member (bot removed fallback)
# ══════════════════════════════════════════════════

async def handle_left_chat_member_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle left_chat_member message event (fallback)."""
    if not update.message or not update.message.left_chat_member:
        return
    
    chat = update.effective_chat
    left_member = update.message.left_chat_member
    
    # Check if the bot was removed
    if left_member.id == context.bot.id:
        group_svc.remove_group(chat.id)
        
        removed_by = update.effective_user
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        notification = (
            f"❌ <b>تم ازالة البوت من مجموعه</b>\n\n"
            f"📋 معلومات المجموعه:\n"
            f"├─ الاسم: {chat.title}\n"
            f"├─ الايدي: <code>{chat.id}</code>\n\n"
            f"👤 ازاله بواسطة:\n"
            f"├─ الاسم: {_format_user_link(removed_by)}\n"
            f"├─ الايدي: <code>{removed_by.id}</code>\n\n"
            f"🕐 الوقت: {now}"
        )
        
        await notify_developer(context, notification)


def register(app: Application) -> None:
    """Register notification handlers."""
    G = filters.ChatType.GROUPS
    P = filters.ChatType.PRIVATE
    
    # Bot status changes (ChatMemberHandler for my_chat_member updates)
    app.add_handler(ChatMemberHandler(
        handle_bot_added_to_group,
        ChatMemberHandler.MY_CHAT_MEMBER
    ), group=1)
    
    # New user in private chat (first message from new users)
    app.add_handler(MessageHandler(
        P & filters.TEXT & ~filters.COMMAND,
        handle_new_private_user
    ), group=1)
    
    # Fallback: new_chat_members message (some clients still send this)
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS & G,
        handle_new_chat_members_message
    ), group=2)
    
    # Fallback: left_chat_member message
    app.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER & G,
        handle_left_chat_member_message
    ), group=2)
    
    # Toggle notification commands (sudo only)
    app.add_handler(MessageHandler(
        filters.Regex("^تفعيل الاشعارات$") & G,
        handle_enable_notifications
    ), group=37)
    
    app.add_handler(MessageHandler(
        filters.Regex("^تعطيل الاشعارات$") & G,
        handle_disable_notifications
    ), group=37)
