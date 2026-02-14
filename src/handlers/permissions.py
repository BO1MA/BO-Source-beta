"""
Permissions handler — group settings toggles, force subscribe,
pin/unpin, welcome/rules setup.
"""
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

from src.config import Config
from src.constants.messages import (
    MSG_ENABLED, MSG_DISABLED, MSG_PINNED, MSG_UNPINNED, MSG_ALL_UNPINNED,
    MSG_NO_PERMISSION, MSG_BOT_NOT_ADMIN,
)
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.utils.text_utils import extract_command_arg
from src.utils.keyboard import build_settings_keyboard
from src.utils.api_helpers import pin_message, unpin_message, is_bot_admin

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()

# Setting toggle commands
TOGGLE_COMMANDS = {
    "تفعيل الالعاب": ("games_enabled", True),
    "تعطيل الالعاب": ("games_enabled", False),
    "تفعيل التاغ": ("tag_enabled", True),
    "تعطيل التاغ": ("tag_enabled", False),
    "تفعيل الاذاعه": ("broadcast_enabled", True),
    "تعطيل الاذاعه": ("broadcast_enabled", False),
    "تفعيل الاشتراك الاجباري": ("force_subscribe_enabled", True),
    "تعطيل الاشتراك الاجباري": ("force_subscribe_enabled", False),
    "تفعيل المغادره": ("farewell_enabled", True),
    "تعطيل المغادره": ("farewell_enabled", False),
    "تفعيل الترحيب": ("welcome_enabled", True),
    "تعطيل الترحيب": ("welcome_enabled", False),
    "تفعيل الحمايه": ("protection_enabled", True),
    "تعطيل الحمايه": ("protection_enabled", False),
    "تفعيل @all": ("tag_enabled", True),
    "تعطيل @all": ("tag_enabled", False),
    "تفعيل all": ("tag_enabled", True),
    "تعطيل all": ("tag_enabled", False),
    "تفعيل المسح التلقائي": ("auto_clean_enabled", True),
    "تعطيل المسح التلقائي": ("auto_clean_enabled", False),
}


@group_only
async def handle_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle a group setting."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    for cmd, (setting, value) in TOGGLE_COMMANDS.items():
        if text == cmd:
            group_svc.toggle_setting(chat_id, setting, value)
            feature = cmd.replace("تفعيل ", "").replace("تعطيل ", "")
            msg = MSG_ENABLED if value else MSG_DISABLED
            await update.message.reply_text(msg.format(feature=feature))
            return


@group_only
async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show group settings panel."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    settings = group_svc.get_settings(chat_id)
    status = {
        "الترحيب": "\u2705" if settings.welcome_enabled else "\u274C",
        "المغادره": "\u2705" if settings.farewell_enabled else "\u274C",
        "الالعاب": "\u2705" if settings.games_enabled else "\u274C",
        "الاذاعه": "\u2705" if settings.broadcast_enabled else "\u274C",
        "التاغ": "\u2705" if settings.tag_enabled else "\u274C",
        "الاشتراك الاجباري": "\u2705" if settings.force_subscribe_enabled else "\u274C",
        "الحمايه": "\u2705" if settings.protection_enabled else "\u274C",
    }
    lines = ["\u2756 اعدادات المجموعه \u2699\uFE0F:"]
    for name, emoji in status.items():
        lines.append(f"{emoji} {name}")

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=build_settings_keyboard(chat_id),
    )


async def handle_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings toggle button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data  # toggle:{chat_id}:{setting}

    parts = data.split(":")
    if len(parts) != 3:
        return

    chat_id = int(parts[1])
    setting = parts[2]

    # Toggle the value
    settings = group_svc.get_settings(chat_id)
    current = getattr(settings, setting, None)
    if current is None:
        return

    new_value = not current
    group_svc.toggle_setting(chat_id, setting, new_value)

    feature = setting.replace("_enabled", "").replace("_", " ")
    msg = MSG_ENABLED if new_value else MSG_DISABLED
    await query.message.reply_text(msg.format(feature=feature))

    # Update the keyboard to reflect new state
    try:
        await query.message.edit_reply_markup(
            reply_markup=build_settings_keyboard(chat_id)
        )
    except Exception:
        pass


@group_only
async def handle_pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pin a message."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text(MSG_BOT_NOT_ADMIN)
        return

    if update.message.reply_to_message:
        if await pin_message(context.bot, chat_id, update.message.reply_to_message.message_id):
            await update.message.reply_text(MSG_PINNED)
    else:
        await update.message.reply_text("\u2756 قم بالرد على الرساله المراد تثبيتها")


@group_only
async def handle_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unpin a message or all messages."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text(MSG_BOT_NOT_ADMIN)
        return

    if text == "الغاء تثبيت الكل":
        if await unpin_message(context.bot, chat_id, None):
            await update.message.reply_text(MSG_ALL_UNPINNED)
    elif update.message.reply_to_message:
        if await unpin_message(context.bot, chat_id, update.message.reply_to_message.message_id):
            await update.message.reply_text(MSG_UNPINNED)
    else:
        if await unpin_message(context.bot, chat_id, None):
            await update.message.reply_text(MSG_UNPINNED)


@group_only
async def handle_set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set custom welcome text. Use {name} as placeholder."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Strip all possible trigger prefixes
    welcome_text = text
    for prefix in ("ضع ترحيب", "الترحيب"):
        if welcome_text.startswith(prefix):
            welcome_text = welcome_text[len(prefix):].strip()
            break
    if welcome_text:
        settings = group_svc.get_settings(chat_id)
        settings.welcome_text = welcome_text
        group_svc.save_settings(chat_id, settings)
        await update.message.reply_text(f"\u2756 تم تعيين رسالة الترحيب \u2705")
    else:
        settings = group_svc.get_settings(chat_id)
        current = settings.welcome_text or "الافتراضي"
        await update.message.reply_text(f"\u2756 رسالة الترحيب الحاليه:\n{current}")


@group_only
async def handle_set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set group rules."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Strip all possible trigger prefixes
    rules = text
    for prefix in ("ضع قوانين",):
        if rules.startswith(prefix):
            rules = rules[len(prefix):].strip()
            break
    if rules:
        settings = group_svc.get_settings(chat_id)
        settings.rules_text = rules
        group_svc.save_settings(chat_id, settings)
        await update.message.reply_text("\u2756 تم تعيين القوانين \u2705")


@group_only
async def handle_delete_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete custom welcome text, revert to default."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    settings = group_svc.get_settings(chat_id)
    settings.welcome_text = ""
    group_svc.save_settings(chat_id, settings)
    await update.message.reply_text("❖ تم حذف رسالة الترحيب ✅\nسيتم استخدام الترحيب الافتراضي.")


@group_only
async def handle_delete_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete group rules."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    settings = group_svc.get_settings(chat_id)
    settings.rules_text = ""
    group_svc.save_settings(chat_id, settings)
    await update.message.reply_text("❖ تم حذف القوانين ✅")


@group_only
async def handle_set_farewell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set custom farewell text."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    farewell_text = text
    for prefix in ("ضع مغادره", "المغادره"):
        if farewell_text.startswith(prefix):
            farewell_text = farewell_text[len(prefix):].strip()
            break
    if farewell_text:
        settings = group_svc.get_settings(chat_id)
        settings.farewell_text = farewell_text
        group_svc.save_settings(chat_id, settings)
        await update.message.reply_text("❖ تم تعيين رسالة المغادره ✅")
    else:
        settings = group_svc.get_settings(chat_id)
        current = settings.farewell_text or "الافتراضي"
        await update.message.reply_text(f"❖ رسالة المغادره الحاليه:\n{current}")


@group_only
async def handle_set_force_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the force-subscribe channel. Usage: تغيير الاشتراك الاجباري @channel"""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    arg = text.replace("تغيير الاشتراك الاجباري", "", 1).strip()
    if not arg:
        await update.message.reply_text("❖ الاستخدام: تغيير الاشتراك الاجباري @channel_username")
        return

    channel = arg if arg.startswith("@") else f"@{arg}"
    settings = group_svc.get_settings(chat_id)
    settings.force_subscribe_channel = channel
    group_svc.save_settings(chat_id, settings)
    await update.message.reply_text(f"❖ تم تعيين قناة الاشتراك الاجباري: {channel} ✅")


@group_only
async def handle_group_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current group permissions/locks status."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    from src.constants.commands import LOCK_FEATURES

    lines = ["❖ صلاحيات الجروب 🔒:"]
    for feature_key, feature_name in LOCK_FEATURES.items():
        locked = group_svc.is_locked(chat_id, feature_key)
        status = "🔒 مقفل" if locked else "🔓 مفتوح"
        lines.append(f"  {status} — {feature_name}")

    await update.message.reply_text("\n".join(lines))


@group_only
async def handle_my_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the requesting user's permissions based on their role."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    from src.constants.roles import (
        ROLE_MEMBER, ROLE_VIP, ROLE_ADMIN, ROLE_MANAGER,
        ROLE_CREATOR, ROLE_MAIN_CREATOR, ROLE_OWNER,
        ROLE_NAMES, ROLE_HIERARCHY, SUDO_ROLES, GROUP_ADMIN_ROLES,
    )

    role = user_svc.get_role(from_user.id, chat_id)
    role_name = ROLE_NAMES.get(role, "عضو")

    # Use hierarchy index for comparison (lower index = higher privilege)
    try:
        role_idx = ROLE_HIERARCHY.index(role)
    except ValueError:
        role_idx = len(ROLE_HIERARCHY)  # unknown role = lowest

    perms = ["❖ صلاحياتك:"]
    perms.append(f"📌 رتبتك: {role_name}")
    perms.append("")

    if role_idx <= ROLE_HIERARCHY.index(ROLE_VIP):
        perms.append("✅ محمي من الحظر والكتم")
    if role_idx <= ROLE_HIERARCHY.index(ROLE_ADMIN):
        perms.append("✅ حظر / كتم / طرد / تحذير")
        perms.append("✅ تثبيت / الغاء تثبيت")
        perms.append("✅ قفل / فتح")
    if role_idx <= ROLE_HIERARCHY.index(ROLE_MANAGER):
        perms.append("✅ ترقية وتنزيل الاعضاء")
        perms.append("✅ اعدادات الجروب")
    if role_idx <= ROLE_HIERARCHY.index(ROLE_CREATOR):
        perms.append("✅ الاذاعه")
        perms.append("✅ اضافة اوامر")
    if role_idx <= ROLE_HIERARCHY.index(ROLE_OWNER):
        perms.append("✅ تعيين مالكين ومنشئين")
    if role == ROLE_MEMBER:
        perms.append("📝 عضو عادي — لا صلاحيات ادارية")

    await update.message.reply_text("\n".join(perms))


@group_only
async def handle_force_subscribe_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show force subscribe info."""
    chat_id = update.effective_chat.id
    settings = group_svc.get_settings(chat_id)
    status = "\u2705 مفعل" if settings.force_subscribe_enabled else "\u274C معطل"
    channel = settings.force_subscribe_channel or Config.CHANNEL_USERNAME or "غير محدد"
    await update.message.reply_text(
        f"\u2756 الاشتراك الاجباري: {status}\n"
        f"\u2756 القناه: {channel}"
    )


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu:commands":
        await query.message.reply_text(
            "\u2756 اوامر الاداره:\n"
            "حظر | الغاء حظر | كتم | الغاء كتم\n"
            "طرد | تحذير | الغاء تحذير\n"
            "تثبيت | الغاء التثبيت\n"
            "ادمن | مدير | منشئ | مميز\n"
            "تنزيل | عزل\n"
            "قفل | فتح\n"
            "اضف امر | اضف رد | الغاء الامر"
        )
    elif data == "menu:games":
        from src.utils.keyboard import build_games_keyboard
        await query.message.reply_text(
            "❖ الالعاب:\n"
            "السمايلات | تخمين | الحروف | الاسرع\n"
            "حزوره | معاني | محيبس | المختلف\n"
            "رياضيات | انكليزي | امثله | كلمات",
            reply_markup=build_games_keyboard(),
        )
    elif data == "menu:broadcast":
        await query.message.reply_text(
            "\u2756 اوامر الاذاعه:\n"
            "اذاعه <نص>\n"
            "اذاعه بالتثبيت <نص>\n"
            "اذاعه بالتوجيه (رد على رساله)"
        )
    elif data == "menu:settings":
        chat = query.message.chat
        if chat.type in ("group", "supergroup"):
            await query.message.reply_text(
                "\u2756 الاعدادات:",
                reply_markup=build_settings_keyboard(chat.id),
            )
        else:
            await query.message.reply_text("\u2756 هذا الامر يعمل في المجموعات فقط")
    elif data == "menu:protection":
        chat = query.message.chat
        from src.utils.keyboard import build_protection_keyboard
        if chat.type in ("group", "supergroup"):
            await query.message.reply_text(
                "\u2756 الحمايه:",
                reply_markup=build_protection_keyboard(chat.id),
            )
        else:
            await query.message.reply_text("\u2756 هذا الامر يعمل في المجموعات فقط")
    elif data == "menu:developer":
        from src.config import Config
        from src.constants.messages import MSG_DEVELOPER_INFO
        await query.message.reply_text(MSG_DEVELOPER_INFO.format(developer=Config.SUDO_USERNAME))


def register(app: Application) -> None:
    """Register permission/settings handlers."""
    G = filters.ChatType.GROUPS

    # Toggle commands
    for cmd_text in TOGGLE_COMMANDS:
        app.add_handler(MessageHandler(filters.Regex(f"^{cmd_text}$") & G, handle_toggle), group=7)

    # Settings
    app.add_handler(MessageHandler(filters.Regex("^الاعدادات$") & G, handle_settings), group=7)

    # Pin
    app.add_handler(MessageHandler(filters.Regex("^تثبيت$") & G, handle_pin), group=7)
    app.add_handler(MessageHandler(
        filters.Regex("^(الغاء التثبيت|الغاء تثبيت الكل)$") & G,
        handle_unpin,
    ), group=7)

    # Welcome / Farewell / Rules
    app.add_handler(MessageHandler(filters.Regex("^(الترحيب|ضع ترحيب)") & G, handle_set_welcome), group=7)
    app.add_handler(MessageHandler(filters.Regex("^(حذف الترحيب|مسح الترحيب)$") & G, handle_delete_welcome), group=7)
    app.add_handler(MessageHandler(filters.Regex("^(المغادره|ضع مغادره)") & G, handle_set_farewell), group=7)
    app.add_handler(MessageHandler(filters.Regex("^ضع قوانين") & G, handle_set_rules), group=7)
    app.add_handler(MessageHandler(filters.Regex("^(حذف القوانين|مسح القوانين)$") & G, handle_delete_rules), group=7)

    # Force subscribe
    app.add_handler(MessageHandler(filters.Regex("^الاشتراك الاجباري$") & G, handle_force_subscribe_info), group=7)
    app.add_handler(MessageHandler(filters.Regex("^تغيير الاشتراك الاجباري") & G, handle_set_force_channel), group=7)

    # Group permissions
    app.add_handler(MessageHandler(filters.Regex("^(صلاحيات الجروب|الصلاحيات)$") & G, handle_group_permissions), group=7)
    app.add_handler(MessageHandler(filters.Regex("^صلاحياتي$") & G, handle_my_permissions), group=7)

    # Callback queries
    app.add_handler(CallbackQueryHandler(handle_toggle_callback, pattern="^toggle:"))
    app.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu:"))
