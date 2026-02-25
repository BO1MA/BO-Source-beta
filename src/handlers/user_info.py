"""
User Info handler — user information, bio, profile, and identity commands.
Ported from bian.lua / AVIRA.lua user info commands.

Commands:
- ايدي / ايديي — show user ID
- معرفي / يوزري — show username
- اسمي — show first name
- البايو / نبذتي — show bio
- سيفي / سي في — show full CV/profile info
- انا مين — show role and info
- جمالي / نسبه جمالي — random beauty percentage
- رتبتي — show role rank
- صلاحياتي — show permissions
- رسائلي — message count
- صورتي — profile photo
- الجروب — group info
"""
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

from src.constants.messages import get_activity_level, MSG_USER_INFO, MSG_GROUP_INFO
from src.constants.roles import get_role_name, ROLE_MEMBER
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.config import Config

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()


async def _get_target_user(update: Update) -> tuple:
    """Get target user (from reply or sender). Returns (user, user_obj)."""
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        tg_user = update.message.reply_to_message.from_user
    else:
        tg_user = update.effective_user

    db_user = user_svc.get_user(tg_user.id)
    return tg_user, db_user


@group_only
async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user ID."""
    tg_user, _ = await _get_target_user(update)
    await update.message.reply_text(f"✯ الايدي: <code>{tg_user.id}</code>", parse_mode="HTML")


@group_only
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show username."""
    tg_user, _ = await _get_target_user(update)
    username = tg_user.username if tg_user.username else "لا يوجد"
    await update.message.reply_text(f"✯ اليوزر: @{username}")


@group_only
async def handle_my_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show first name."""
    tg_user, _ = await _get_target_user(update)
    await update.message.reply_text(f"✯ الاسم: {tg_user.first_name}")


@group_only
async def handle_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user bio."""
    tg_user, _ = await _get_target_user(update)
    try:
        chat = await context.bot.get_chat(tg_user.id)
        bio = chat.bio if chat.bio else "لا يوجد"
    except TelegramError:
        bio = "لا يمكن جلب البايو"
    await update.message.reply_text(f"✯ البايو:\n{bio}")


@group_only
async def handle_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show full user profile/CV."""
    chat_id = update.effective_chat.id
    tg_user, db_user = await _get_target_user(update)

    # Get role
    role = user_svc.get_role(tg_user.id, chat_id)
    role_name = get_role_name(role) if role else get_role_name(ROLE_MEMBER)

    # Get bio
    try:
        chat = await context.bot.get_chat(tg_user.id)
        bio = chat.bio if chat.bio else "لا يوجد"
    except TelegramError:
        bio = "لا يمكن جلب البايو"

    # Get message count and activity
    msg_count = db_user.message_count
    activity = get_activity_level(msg_count)

    username = f"@{tg_user.username}" if tg_user.username else "لا يوجد"

    cv_text = (
        f"✯ سي في {tg_user.first_name}:\n"
        f"├─ 🆔 الايدي: <code>{tg_user.id}</code>\n"
        f"├─ 👤 الاسم: {tg_user.first_name}\n"
        f"├─ 📛 اليوزر: {username}\n"
        f"├─ 🏷 الرتبه: {role_name}\n"
        f"├─ 📝 البايو: {bio}\n"
        f"├─ 📊 الرسائل: {msg_count}\n"
        f"└─ ⚡️ النشاط: {activity}"
    )
    await update.message.reply_text(cv_text, parse_mode="HTML")


@group_only
async def handle_who_am_i(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """انا مين — show who the user is in this group."""
    chat_id = update.effective_chat.id
    tg_user = update.effective_user

    role = user_svc.get_role(tg_user.id, chat_id)
    role_name = get_role_name(role) if role else get_role_name(ROLE_MEMBER)

    await update.message.reply_text(
        f"✯ انت {tg_user.first_name}\n"
        f"✯ رتبتك: {role_name}"
    )


@group_only
async def handle_my_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رتبتي — show user's rank/role."""
    chat_id = update.effective_chat.id
    tg_user, _ = await _get_target_user(update)

    role = user_svc.get_role(tg_user.id, chat_id)
    role_name = get_role_name(role) if role else get_role_name(ROLE_MEMBER)

    await update.message.reply_text(f"✯ رتبة {tg_user.first_name}: {role_name}")


@group_only
async def handle_my_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """صلاحياتي — show user's permissions."""
    chat_id = update.effective_chat.id
    tg_user = update.effective_user

    role = user_svc.get_role(tg_user.id, chat_id)
    role_name = get_role_name(role) if role else get_role_name(ROLE_MEMBER)

    is_admin = user_svc.is_group_admin(tg_user.id, chat_id)
    is_sudo = user_svc.is_sudo(tg_user.id)

    perms = [f"✯ صلاحيات {tg_user.first_name}:"]
    perms.append(f"├─ الرتبه: {role_name}")
    perms.append(f"├─ ادمن: {'نعم ✅' if is_admin else 'لا ❌'}")
    perms.append(f"└─ مطور: {'نعم ✅' if is_sudo else 'لا ❌'}")

    await update.message.reply_text("\n".join(perms))


@group_only
async def handle_my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رسائلي — show message count."""
    tg_user, db_user = await _get_target_user(update)
    msg_count = db_user.message_count
    activity = get_activity_level(msg_count)

    await update.message.reply_text(
        f"✯ رسائل {tg_user.first_name}:\n"
        f"├─ العدد: {msg_count}\n"
        f"└─ النشاط: {activity}"
    )


@group_only
async def handle_my_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """صورتي — send user's profile photo."""
    tg_user, _ = await _get_target_user(update)

    try:
        photos = await context.bot.get_user_profile_photos(tg_user.id, limit=1)
        if photos.photos:
            photo = photos.photos[0][-1]  # Get highest quality
            await update.message.reply_photo(
                photo.file_id,
                caption=f"✯ صورة {tg_user.first_name}"
            )
        else:
            await update.message.reply_text("✯ لا توجد صوره للمستخدم")
    except TelegramError as e:
        logger.warning(f"Failed to get profile photo: {e}")
        await update.message.reply_text("✯ لا يمكن جلب الصوره")


@group_only
async def handle_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الجروب — show group information."""
    chat = update.effective_chat

    try:
        member_count = await context.bot.get_chat_member_count(chat.id)
    except TelegramError:
        member_count = 0

    # Get invite link
    link = "لا يوجد"
    try:
        chat_full = await context.bot.get_chat(chat.id)
        if chat_full.invite_link:
            link = chat_full.invite_link
        elif chat.username:
            link = f"@{chat.username}"
    except TelegramError:
        pass

    await update.message.reply_text(
        MSG_GROUP_INFO.format(
            title=chat.title,
            id=chat.id,
            members=member_count,
            link=link,
        )
    )


@group_only
async def handle_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الرابط — show group invite link."""
    chat = update.effective_chat

    link = None
    try:
        chat_full = await context.bot.get_chat(chat.id)
        if chat_full.invite_link:
            link = chat_full.invite_link
        elif chat.username:
            link = f"https://t.me/{chat.username}"
    except TelegramError:
        pass

    if link:
        await update.message.reply_text(f"✯ الرابط:\n{link}")
    else:
        await update.message.reply_text("✯ لا يوجد رابط للمجموعه")


@group_only
async def handle_admins_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الادمنيه / ادمنية الجروب — list group admins."""
    chat_id = update.effective_chat.id

    try:
        admins = await context.bot.get_chat_administrators(chat_id)

        lines = ["✯ ادمنية المجموعه:"]
        for i, admin in enumerate(admins, 1):
            user = admin.user
            if user.is_bot:
                name = f"{user.first_name} 🤖"
            else:
                name = user.first_name
            status = "👑" if admin.status == "creator" else "⚡️"
            lines.append(f"  {i}. {status} {name}")

        await update.message.reply_text("\n".join(lines))
    except TelegramError as e:
        logger.error(f"Failed to get admins: {e}")
        await update.message.reply_text("✯ لا يمكن جلب قائمة الادمنيه")


def register(app: Application) -> None:
    """Register user info handlers."""
    G = filters.ChatType.GROUPS

    # User ID
    app.add_handler(MessageHandler(
        filters.Regex("^(ايدي|ايديي|Id)$") & G, handle_user_id
    ), group=25)

    # Username
    app.add_handler(MessageHandler(
        filters.Regex("^(معرفي|يوزري)$") & G, handle_username
    ), group=25)

    # Name
    app.add_handler(MessageHandler(
        filters.Regex("^اسمي$") & G, handle_my_name
    ), group=25)

    # Bio
    app.add_handler(MessageHandler(
        filters.Regex("^(البايو|نبذتي)$") & G, handle_bio
    ), group=25)

    # CV / Full profile
    app.add_handler(MessageHandler(
        filters.Regex("^(سيفي|سي في)$") & G, handle_cv
    ), group=25)

    # Who am I
    app.add_handler(MessageHandler(
        filters.Regex("^انا مين$") & G, handle_who_am_i
    ), group=25)

    # Rank
    app.add_handler(MessageHandler(
        filters.Regex("^(رتبتي|لقبي)$") & G, handle_my_rank
    ), group=25)

    # Permissions
    app.add_handler(MessageHandler(
        filters.Regex("^صلاحياتي$") & G, handle_my_permissions
    ), group=25)

    # Messages count
    app.add_handler(MessageHandler(
        filters.Regex("^رسائلي$") & G, handle_my_messages
    ), group=25)

    # Profile photo
    app.add_handler(MessageHandler(
        filters.Regex("^صورتي$") & G, handle_my_photo
    ), group=25)

    # Group info
    app.add_handler(MessageHandler(
        filters.Regex("^(الجروب|معلومات الجروب)$") & G, handle_group_info
    ), group=25)

    # Group link
    app.add_handler(MessageHandler(
        filters.Regex("^الرابط$") & G, handle_group_link
    ), group=25)

    # Admins list
    app.add_handler(MessageHandler(
        filters.Regex("^(الادمنيه|ادمنية الجروب|رفع الادمنيه)$") & G, handle_admins_list
    ), group=25)
