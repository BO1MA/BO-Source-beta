"""
Start handler — /start, welcome new members, farewell, greetings,
user info, bot info, group info, custom commands/replies, and all
user-facing info commands from the Lua bot.
"""
import logging

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler,
    filters, ChatMemberHandler,
)

from src.config import Config
from src.constants.messages import (
    MSG_START, MSG_WELCOME, MSG_FAREWELL, MSG_GROUP_INFO, MSG_USER_INFO,
    MSG_DEVELOPER_INFO, MSG_STATS, MSG_NO_RULES,
    get_greeting_response, get_activity_level, CHAT_RESPONSES,
    HELP_ADD_COMMANDS, HELP_BROADCAST, HELP_TOGGLE,
)
from src.constants.roles import get_role_name, ROLE_NAMES
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.keyboard import build_main_menu_keyboard
from src.utils.text_utils import reverse_text, extract_command_arg

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    user_svc.register_user(user.id)
    user_svc.update_info(user.id, user.first_name, user.last_name or "", user.username or "")
    text = MSG_START.format(name=user.first_name, developer=Config.SUDO_USERNAME)
    await update.message.reply_text(text, reply_markup=build_main_menu_keyboard())


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome new members when they join."""
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    settings = group_svc.get_settings(chat.id)
    if not settings.welcome_enabled:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        user_svc.register_user(member.id)
        user_svc.update_info(member.id, member.first_name, member.last_name or "", member.username or "")
        welcome_text = settings.welcome_text or MSG_WELCOME
        await update.message.reply_text(
            welcome_text.format(name=member.first_name)
        )


async def farewell_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send farewell when a member leaves."""
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    settings = group_svc.get_settings(chat.id)
    if not settings.farewell_enabled:
        return

    left = update.message.left_chat_member
    if left and not left.is_bot:
        farewell_text = settings.farewell_text or MSG_FAREWELL
        await update.message.reply_text(farewell_text.format(name=left.first_name))


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process every group text message: register, count, check custom commands/replies, greetings."""
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    user = update.effective_user
    chat = update.effective_chat
    text = (update.message.text or "").strip()

    # Register group and user
    group_svc.register_group(chat.id, chat.title or "")
    user_svc.register_user(user.id)
    user_svc.update_info(user.id, user.first_name, user.last_name or "", user.username or "")
    user_svc.increment_messages(user.id, chat.id)
    group_svc.increment_total_messages()

    if not text:
        return

    # ── Check custom replies (substring match) ──
    replies = group_svc.get_all_custom_replies(chat.id)
    for trigger, response in replies.items():
        if trigger in text:
            await update.message.reply_text(response)
            return

    # Global replies
    global_replies = group_svc.get_all_global_replies()
    for trigger, response in global_replies.items():
        if trigger in text:
            await update.message.reply_text(response)
            return

    # ── Check custom commands (exact match) ──
    cmds = group_svc.get_all_custom_commands(chat.id)
    if text in cmds:
        await update.message.reply_text(cmds[text])
        return

    global_cmds = group_svc.get_all_global_commands()
    if text in global_cmds:
        await update.message.reply_text(global_cmds[text])
        return

    # ...existing code...

    # ── رتبتي — my rank ──
    if text == "رتبتي":
        role = user_svc.get_role(user.id, chat.id)
        await update.message.reply_text(f"✯ رتبتك: {get_role_name(role)}")
        return

    # ── رسائلي — my message count ──
    if text == "رسائلي":
        count = user_svc.get_message_count(user.id, chat.id)
        level = get_activity_level(count)
        await update.message.reply_text(
            f"✯ عدد رسائلك: {count}\n✯ مستوى نشاطك: {level}"
        )
        return

    # ── معرفي / يوزري — my username ──
    if text in ("معرفي", "يوزري"):
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        username = target.username or "لا يوجد"
        await update.message.reply_text(f"✯ اليوزر: @{username}")
        return

    # ── لقبي — my title/custom title ──
    if text == "لقبي":
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        try:
            member = await context.bot.get_chat_member(chat.id, target.id)
            title = getattr(member, 'custom_title', None) or "لا يوجد لقب"
        except Exception:
            title = "لا يوجد لقب"
        await update.message.reply_text(f"✯ اللقب: {title}")
        return

    # ── صورتي — my profile photo ──
    if text == "صورتي":
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        try:
            photos = await context.bot.get_user_profile_photos(target.id, limit=1)
            if photos.total_count > 0:
                await update.message.reply_photo(
                    photo=photos.photos[0][0].file_id,
                    caption=f"✯ صورة {target.first_name}"
                )
            else:
                await update.message.reply_text("✯ لا توجد صوره")
        except Exception:
            await update.message.reply_text("✯ لا يمكن جلب الصوره")
        return

    # ...existing code...

    # ── خاص / برايفت / بص خاص — private link ──
    if text in ("خاص", "برايفت", "بص خاص"):
        bot_me = await context.bot.get_me()
        await update.message.reply_text(f"✯ ارسلي خاص هنا: t.me/{bot_me.username}")
        return

    # ── تعديلاتي — edit count ──
    if text == "تعديلاتي":
        count = user_svc.get_stat(user.id, chat.id, "edits")
        await update.message.reply_text(f"✯ عدد تعديلاتك: {count}")
        return

    # ── مسح تعديلاتي ──
    if text == "مسح تعديلاتي":
        user_svc.reset_stat(user.id, chat.id, "edits")
        await update.message.reply_text("✯ تم مسح تعديلاتك ✅")
        return

    # ── جهاتي — contact count ──
    if text == "جهاتي":
        count = user_svc.get_stat(user.id, chat.id, "contacts")
        await update.message.reply_text(f"✯ عدد جهاتك: {count}")
        return

    # ── مسح جهاتي ──
    if text == "مسح جهاتي":
        user_svc.reset_stat(user.id, chat.id, "contacts")
        await update.message.reply_text("✯ تم مسح جهاتك ✅")
        return

    # ── سحكاتي — sticker count ──
    if text == "سحكاتي":
        count = user_svc.get_stat(user.id, chat.id, "stickers")
        await update.message.reply_text(f"✯ عدد ملصقاتك: {count}")
        return

    # ── مسح سحكاتي ──
    if text == "مسح سحكاتي":
        user_svc.reset_stat(user.id, chat.id, "stickers")
        await update.message.reply_text("✯ تم مسح عدد ملصقاتك ✅")
        return

    # ── مسح رسائلي ──
    if text == "مسح رسائلي":
        user_svc.reset_messages(user.id, chat.id)
        await update.message.reply_text("✯ تم مسح رسائلك ✅")
        return

    # ── عدد الميديا ──
    if text == "عدد الميديا":
        count = group_svc.get_stat(chat.id, "media_count")
        await update.message.reply_text(f"✯ عدد الميديا: {count}")
        return

    # ── مسح الميديا ──
    if text == "مسح الميديا":
        if not user_svc.is_group_admin(user.id, chat.id) and user.id != Config.SUDO_ID:
            return
        group_svc.reset_stat(chat.id, "media_count")
        await update.message.reply_text("✯ تم مسح عداد الميديا ✅")
        return

    # ── مجوهراتي — gems ──
    if text == "مجوهراتي":
        count = user_svc.get_stat(user.id, chat.id, "gems")
        await update.message.reply_text(f"✯ مجوهراتك: {count} 💎")
        return

    # ── اوامر اضف / اوامر الاذاعه / اوامر التفعيل — help pages ──
    if text == "اوامر اضف📝":
        await update.message.reply_text(HELP_ADD_COMMANDS)
        return
    if text == "اوامر الاذاعه📢":
        await update.message.reply_text(HELP_BROADCAST)
        return
    if text == "اوامر التفعيل♻️":
        await update.message.reply_text(HELP_TOGGLE)
        return

    # ── الغاء — cancel current operation ──
    if text == "الغاء":
        await update.message.reply_text("✯ تم الالغاء ✅")
        return

    if text in ("القائمه", "الاوامر", "الاوامر🧾", "القائمه الرئيسيه"):
        await update.message.reply_text(
            "\u2756 القائمه الرئيسيه \u2756",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    # ── Chat auto-responses (from bian.lua) ──
    if text in CHAT_RESPONSES:
        await update.message.reply_text(CHAT_RESPONSES[text])
        return


async def handle_edited_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Track edited messages — increment edit count for the user."""
    if not update.edited_message or not update.effective_user or not update.effective_chat:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    user = update.effective_user
    chat = update.effective_chat
    user_svc.increment_stat(user.id, chat.id, "edits")


async def handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Track media messages — increment sticker, contact, and media counts."""
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return

    user = update.effective_user
    chat = update.effective_chat
    msg = update.message

    if msg.sticker:
        user_svc.increment_stat(user.id, chat.id, "stickers")
    if msg.contact:
        user_svc.increment_stat(user.id, chat.id, "contacts")
    if msg.photo or msg.video or msg.animation or msg.document or msg.audio or msg.voice or msg.video_note:
        group_svc.increment_stat(chat.id, "media_count")


def register(app: Application) -> None:
    """Register start-related handlers."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, farewell_member))

    G = filters.ChatType.GROUPS

    # Edit tracking (group=3 — runs early for all edits)
    app.add_handler(MessageHandler(
        filters.UpdateType.EDITED_MESSAGE & G,
        handle_edited_message,
    ), group=3)

    # Media stats tracking (group=98 — runs for all non-text)
    app.add_handler(MessageHandler(
        (filters.PHOTO | filters.VIDEO | filters.Sticker.ALL | filters.ANIMATION |
         filters.Document.ALL | filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE |
         filters.CONTACT) & G,
        handle_media_message,
    ), group=98)

    # The group message handler is added with a low priority so other handlers run first
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        handle_group_message,
    ), group=99)
