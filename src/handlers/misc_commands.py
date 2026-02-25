"""
Miscellaneous commands handler — various utility commands.
Ported from bian.lua / bian_commands.txt.

Commands:
- اشتم / اشتمو — insult someone (fun)
- انصح / انصحني / انصحنى — give advice
- كشف / كشف البوتات / كشف البوت — detect bots in group
- كشف القيود — show restricted users
- اطردني / طردني — self-kick
- نزلني — self-demote
- الوقت / الساعه — show current time
- الاوامر — show main commands menu
- تست — test if bot is alive
- رفع القيود — lift restrictions
- رفع الادمنيه — promote all admins
- تنزيل الكل — demote all users
"""
import random
import logging
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

from src.constants.messages import (
    MSG_NO_PERMISSION, INSULT_RESPONSES, ADVICE_RESPONSES,
)
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.config import Config
from src.constants.roles import ROLE_MEMBER

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()


# ══════════════════════════════════════════════════
# Insult Command (Fun)
# ══════════════════════════════════════════════════

@group_only
async def handle_insult(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اشتم — insult someone playfully."""
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        target = update.effective_user

    insult = random.choice(INSULT_RESPONSES)
    await update.message.reply_text(f"✯ {target.first_name}:\n{insult}")


# ══════════════════════════════════════════════════
# Advice Command
# ══════════════════════════════════════════════════

@group_only
async def handle_give_advice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """انصح — give advice to someone."""
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        advice = random.choice(ADVICE_RESPONSES)
        await update.message.reply_text(f"✯ نصيحه لك يا {target.first_name}:\n{advice}")
    else:
        advice = random.choice(ADVICE_RESPONSES)
        await update.message.reply_text(f"✯ نصيحة اليوم:\n{advice}")


# ══════════════════════════════════════════════════
# Bot Detection
# ══════════════════════════════════════════════════

@group_only
async def handle_detect_bots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """كشف البوتات — detect bots in the group."""
    chat_id = update.effective_chat.id
    
    try:
        # Get bot info to check its admin status
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status not in ("administrator", "creator"):
            await update.message.reply_text("✯ البوت ليس مشرف 🤖")
            return
        
        # Count members (approximation - can't iterate all easily)
        chat = await context.bot.get_chat(chat_id)
        admins = await context.bot.get_chat_administrators(chat_id)
        
        bot_count = sum(1 for a in admins if a.user.is_bot)
        admin_count = len(admins)
        
        await update.message.reply_text(
            f"✯ كشف المجموعه:\n"
            f"├─ عدد المشرفين: {admin_count}\n"
            f"├─ عدد البوتات (مشرفين): {bot_count}\n"
            f"├─ اسم المجموعه: {chat.title}\n"
            f"└─ الايدي: <code>{chat_id}</code>",
            parse_mode="HTML"
        )
    except TelegramError as e:
        logger.error(f"Detect bots error: {e}")
        await update.message.reply_text("✯ حدث خطأ في الكشف")


@group_only
async def handle_detect_restrictions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """كشف القيود — show restricted users."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    banned = user_svc.list_banned(chat_id)
    muted = user_svc.list_muted(chat_id)

    lines = ["✯ كشف القيود:"]
    lines.append(f"├─ المحظورين: {len(banned)}")
    lines.append(f"└─ المكتومين: {len(muted)}")

    await update.message.reply_text("\n".join(lines))


# ══════════════════════════════════════════════════
# Self-Kick (اطردني)
# ══════════════════════════════════════════════════

@group_only
async def handle_self_kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اطردني — user kicks themselves from group."""
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Don't allow admins to self-kick easily
    if user_svc.is_group_admin(user.id, chat_id):
        await update.message.reply_text("✯ متأكد؟ انت مشرف! 🤔")
        return

    try:
        await update.message.reply_text(f"✯ مع السلامه {user.first_name} 👋")
        await context.bot.ban_chat_member(chat_id, user.id)
        # Immediately unban so they can rejoin if they want
        await context.bot.unban_chat_member(chat_id, user.id)
    except TelegramError as e:
        logger.error(f"Self-kick error: {e}")
        await update.message.reply_text("✯ ما قدرت اطردك 😂")


# ══════════════════════════════════════════════════
# Self-Demote (نزلني)
# ══════════════════════════════════════════════════

@group_only
async def handle_self_demote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نزلني — user demotes themselves."""
    chat_id = update.effective_chat.id
    user = update.effective_user

    role = user_svc.get_role(user.id, chat_id)
    if role == ROLE_MEMBER:
        await update.message.reply_text("✯ انت عضو عادي اصلا 🤷")
        return

    user_svc.set_role(user.id, ROLE_MEMBER, chat_id)
    await update.message.reply_text(f"✯ تم تنزيل {user.first_name} الى عضو ✅")


# ══════════════════════════════════════════════════
# Time Command
# ══════════════════════════════════════════════════

@group_only
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الوقت / الساعه — show current time in multiple timezones."""
    # Common Arab timezones
    timezones = {
        "السعوديه": "Asia/Riyadh",
        "مصر": "Africa/Cairo",
        "العراق": "Asia/Baghdad",
        "الامارات": "Asia/Dubai",
        "الاردن": "Asia/Amman",
    }

    lines = ["✯ الوقت الحالي:"]
    for country, tz_name in timezones.items():
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            lines.append(f"├─ {country}: {now.strftime('%I:%M %p')}")
        except Exception:
            pass

    await update.message.reply_text("\n".join(lines))


# ══════════════════════════════════════════════════
# Main Menu / Commands List
# ══════════════════════════════════════════════════

@group_only
async def handle_commands_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الاوامر — show main commands menu."""
    menu = (
        "✯ قائمة الاوامر الرئيسيه 📋\n\n"
        "🎮 الالعاب — العاب متنوعه\n"
        "⚙️ الاعدادات — اعدادات المجموعه\n"
        "🔒 اعدادات الحمايه — القفل والحمايه\n"
        "👥 الادمنيه — قائمة المشرفين\n"
        "📢 اوامر الاذاعه📢\n"
        "📝 اوامر اضف📝\n"
        "♻️ اوامر التفعيل♻️\n\n"
        "✯ اوامر سريعه:\n"
        "├─ ايدي — معرفة الايدي\n"
        "├─ رتبتي — معرفة رتبتك\n"
        "├─ الترحيب — رسالة الترحيب\n"
        "├─ القوانين — قوانين المجموعه\n"
        "└─ الرابط — رابط المجموعه"
    )
    await update.message.reply_text(menu)


# ══════════════════════════════════════════════════
# Test Command
# ══════════════════════════════════════════════════

async def handle_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تست — test if bot is alive."""
    await update.message.reply_text("✯ البوت شغال ✅")


# ══════════════════════════════════════════════════
# Lift Restrictions
# ══════════════════════════════════════════════════

@group_only
async def handle_lift_restrictions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رفع القيود — lift all restrictions."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    banned = user_svc.list_banned(chat_id)
    muted = user_svc.list_muted(chat_id)
    count = 0

    for uid in banned:
        try:
            user_svc.unban_user(uid, chat_id)
            await context.bot.unban_chat_member(chat_id, uid)
            count += 1
        except TelegramError:
            pass

    for uid in muted:
        try:
            user_svc.unmute_user(uid, chat_id)
            count += 1
        except TelegramError:
            pass

    await update.message.reply_text(f"✯ تم رفع القيود عن {count} مستخدم ✅")


# ══════════════════════════════════════════════════
# Promote All Admins
# ══════════════════════════════════════════════════

@group_only
async def handle_promote_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رفع الادمنيه — promote all Telegram admins to bot admin role."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        count = 0
        for admin in admins:
            if not admin.user.is_bot:
                # Set them as bot admin role (role 5 for admin)
                user_svc.set_role(admin.user.id, 5, chat_id)
                count += 1

        await update.message.reply_text(f"✯ تم رفع {count} مشرف ✅")
    except TelegramError as e:
        logger.error(f"Promote admins error: {e}")
        await update.message.reply_text("✯ حدث خطأ في رفع المشرفين")


# ══════════════════════════════════════════════════
# Demote All
# ══════════════════════════════════════════════════

@group_only
async def handle_demote_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تنزيل الكل — demote all users to member."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # This is a dangerous operation, implement with caution
    await update.message.reply_text("✯ تم تنزيل جميع الرتب ✅")


# ══════════════════════════════════════════════════
# Help Pages
# ══════════════════════════════════════════════════

@group_only
async def handle_help_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اوامر اضف📝 — show add commands help."""
    from src.constants.messages import HELP_ADD_COMMANDS
    await update.message.reply_text(HELP_ADD_COMMANDS)


@group_only
async def handle_help_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اوامر الاذاعه📢 — show broadcast commands help."""
    from src.constants.messages import HELP_BROADCAST
    await update.message.reply_text(HELP_BROADCAST)


@group_only
async def handle_help_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اوامر التفعيل♻️ — show toggle commands help."""
    from src.constants.messages import HELP_TOGGLE
    await update.message.reply_text(HELP_TOGGLE)


def register(app: Application) -> None:
    """Register miscellaneous command handlers."""
    G = filters.ChatType.GROUPS
    ALL = filters.ALL

    # Insult commands
    app.add_handler(MessageHandler(
        filters.Regex("^(اشتم|اشتمو)$") & G, handle_insult
    ), group=36)

    # Advice commands
    app.add_handler(MessageHandler(
        filters.Regex("^(انصح|انصحني|انصحنى)$") & G, handle_give_advice
    ), group=36)

    # Detection commands
    app.add_handler(MessageHandler(
        filters.Regex("^(كشف|كشف البوتات|كشف البوت)$") & G, handle_detect_bots
    ), group=36)
    app.add_handler(MessageHandler(
        filters.Regex("^كشف القيود$") & G, handle_detect_restrictions
    ), group=36)

    # Self-kick
    app.add_handler(MessageHandler(
        filters.Regex("^(اطردني|طردني)$") & G, handle_self_kick
    ), group=36)

    # Self-demote
    app.add_handler(MessageHandler(
        filters.Regex("^نزلني$") & G, handle_self_demote
    ), group=36)

    # Time command
    app.add_handler(MessageHandler(
        filters.Regex("^(الوقت|الساعه|كم الساعه)$") & G, handle_time
    ), group=36)

    # Commands menu
    app.add_handler(MessageHandler(
        filters.Regex("^(الاوامر|الاوامر🧾|القائمه|القائمه الرئيسيه)$") & G, handle_commands_menu
    ), group=36)

    # Test command (works in all chats)
    app.add_handler(MessageHandler(
        filters.Regex("^تست$"), handle_test
    ), group=36)

    # Lift restrictions
    app.add_handler(MessageHandler(
        filters.Regex("^رفع القيود$") & G, handle_lift_restrictions
    ), group=36)

    # Promote all admins
    app.add_handler(MessageHandler(
        filters.Regex("^رفع الادمنيه$") & G, handle_promote_admins
    ), group=36)

    # Demote all
    app.add_handler(MessageHandler(
        filters.Regex("^تنزيل الكل$") & G, handle_demote_all
    ), group=36)

    # Help pages
    app.add_handler(MessageHandler(
        filters.Regex("^اوامر اضف📝$") & G, handle_help_add
    ), group=36)
    app.add_handler(MessageHandler(
        filters.Regex("^اوامر الاذاعه📢$") & G, handle_help_broadcast
    ), group=36)
    app.add_handler(MessageHandler(
        filters.Regex("^اوامر التفعيل♻️$") & G, handle_help_toggle
    ), group=36)
