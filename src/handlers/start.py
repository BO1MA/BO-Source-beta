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

    # ── Greetings ──
    greeting = get_greeting_response(text)
    if greeting:
        await update.message.reply_text(greeting)
        return

    # ── Info commands ──
    if text in ("Id", "ايدي", "ايديي"):
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        await update.message.reply_text(f"\u2756 الايدي: {target.id}")
        return

    if text == "اسمي":
        await update.message.reply_text(f"\u2756 اسمك: {user.first_name}")
        return

    if text == "البايو":
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        try:
            chat_obj = await context.bot.get_chat(target.id)
            bio = chat_obj.bio or "لا يوجد بايو"
        except Exception:
            bio = "لا يوجد بايو"
        await update.message.reply_text(f"\u2756 البايو: {bio}")
        return

    if text in ("البوت", "بوت"):
        bot_me = await context.bot.get_me()
        await update.message.reply_text(
            f"\u2756 اسم البوت: {bot_me.first_name}\n"
            f"\u2756 اليوزر: @{bot_me.username}\n"
            f"\u2756 الايدي: {bot_me.id}"
        )
        return

    if text == "الجروب":
        try:
            count = await context.bot.get_chat_member_count(chat.id)
            link = (await context.bot.get_chat(chat.id)).invite_link or "غير متوفر"
        except Exception:
            count = 0
            link = "غير متوفر"
        await update.message.reply_text(
            MSG_GROUP_INFO.format(title=chat.title, id=chat.id, members=count, link=link)
        )
        return

    if text == "الرابط":
        try:
            link = (await context.bot.get_chat(chat.id)).invite_link
            if not link:
                link = await context.bot.export_chat_invite_link(chat.id)
        except Exception:
            link = "غير متوفر"
        await update.message.reply_text(f"\u2756 رابط المجموعه: {link}")
        return

    if text in ("المبرمج", "السورس", "سورس", "مطور", "مطور البوت",
                 "المبرمج أشموديل", "المبرمج إيمو", "المبرمج احمد"):
        await update.message.reply_text(MSG_DEVELOPER_INFO.format(developer=Config.SUDO_USERNAME))
        return

    if text == "الاحصائيات":
        await update.message.reply_text(MSG_STATS.format(
            groups=group_svc.get_total_groups(),
            users=user_svc.get_total_users(),
            messages=group_svc.get_total_messages(),
        ))
        return

    if text == "القوانين":
        settings = group_svc.get_settings(chat.id)
        if settings.rules_text:
            await update.message.reply_text(f"\u2756 قوانين المجموعه:\n{settings.rules_text}")
        else:
            await update.message.reply_text(MSG_NO_RULES)
        return

    if text.startswith("العكس"):
        arg = extract_command_arg(text)
        if arg:
            await update.message.reply_text(reverse_text(arg))
        elif update.message.reply_to_message and update.message.reply_to_message.text:
            await update.message.reply_text(reverse_text(update.message.reply_to_message.text))
        return

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

    # ── انا مين — full user info card ──
    if text == "انا مين":
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        role = user_svc.get_role(target.id, chat.id)
        count = user_svc.get_message_count(target.id, chat.id)
        level = get_activity_level(count)
        warns = user_svc.get_warnings(target.id, chat.id)
        username = target.username or "لا يوجد"
        try:
            chat_obj = await context.bot.get_chat(target.id)
            bio = chat_obj.bio or "لا يوجد"
        except Exception:
            bio = "لا يوجد"
        await update.message.reply_text(
            f"✯ بطاقة المعلومات ✯\n"
            f"✯ الاسم: {target.first_name}\n"
            f"✯ الايدي: {target.id}\n"
            f"✯ اليوزر: @{username}\n"
            f"✯ البايو: {bio}\n"
            f"✯ الرتبه: {get_role_name(role)}\n"
            f"✯ الرسائل: {count}\n"
            f"✯ النشاط: {level}\n"
            f"✯ التحذيرات: {warns}"
        )
        return

    # ── نبذتي / سيفي / سي في — my bio ──
    if text in ("نبذتي", "سيفي", "سي في"):
        target = update.message.reply_to_message.from_user if update.message.reply_to_message else user
        try:
            chat_obj = await context.bot.get_chat(target.id)
            bio = chat_obj.bio or "لا يوجد بايو"
        except Exception:
            bio = "لا يوجد بايو"
        await update.message.reply_text(f"✯ النبذه: {bio}")
        return

    # ── تحذيراتي — my warnings ──
    if text == "تحذيراتي":
        warns = user_svc.get_warnings(user.id, chat.id)
        settings = group_svc.get_settings(chat.id)
        await update.message.reply_text(
            f"✯ تحذيراتك: {warns}/{settings.max_warnings}"
        )
        return

    # ── الرتب — show all role names ──
    if text == "الرتب":
        lines = ["✯ الرتب المتاحه:"]
        for level, name in ROLE_NAMES.items():
            lines.append(f"  • {name}")
        await update.message.reply_text("\n".join(lines))
        return

    # ── عدد الاعضاء — member count ──
    if text == "عدد الاعضاء":
        try:
            count = await context.bot.get_chat_member_count(chat.id)
        except Exception:
            count = 0
        await update.message.reply_text(f"✯ عدد الاعضاء: {count}")
        return

    # ── اسم الجروب — group name ──
    if text == "اسم الجروب":
        await update.message.reply_text(f"✯ اسم الجروب: {chat.title}")
        return

    # ── وصف الجروب — group description ──
    if text == "وصف الجروب":
        try:
            chat_obj = await context.bot.get_chat(chat.id)
            desc = chat_obj.description or "لا يوجد وصف"
        except Exception:
            desc = "لا يوجد وصف"
        await update.message.reply_text(f"✯ وصف الجروب:\n{desc}")
        return

    # ── ستارت — Arabic start alias ──
    if text == "ستارت":
        user_svc.register_user(user.id)
        start_text = MSG_START.format(name=user.first_name, developer=Config.SUDO_USERNAME)
        await update.message.reply_text(start_text, reply_markup=build_main_menu_keyboard())
        return

    # ── السيرفر — server info ──
    if text == "السيرفر":
        import platform
        import sys as _sys
        await update.message.reply_text(
            f"✯ معلومات السيرفر:\n"
            f"✯ النظام: {platform.system()} {platform.release()}\n"
            f"✯ بايثون: {_sys.version.split()[0]}\n"
            f"✯ المعالج: {platform.machine()}\n"
            f"✯ الاستضافه: Vercel Serverless"
        )
        return

    # ── تست — test if bot alive ──
    if text == "تست":
        await update.message.reply_text("✯ البوت يعمل بنجاح ✅")
        return

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


def register(app: Application) -> None:
    """Register start-related handlers."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, farewell_member))
    # The group message handler is added with a low priority so other handlers run first
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        handle_group_message,
    ), group=99)
