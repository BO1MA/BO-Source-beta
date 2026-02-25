import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.utils.decorators import group_only
from src.constants.messages import MSG_NO_PERMISSION
# ...other necessary imports...

@group_only
async def handle_toggle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حماية من السبام — toggle spam protection."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return
    settings = group_svc.get_settings(chat_id)
    settings.protection_enabled = not settings.protection_enabled
    group_svc.save_settings(chat_id, settings)
    state = "مفعلة ✅" if settings.protection_enabled else "معطلة ❌"
    await update.message.reply_text(f"✯ حماية السبام: {state}")

@group_only
async def handle_set_flood_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تعيين التكرار <عدد> — set flood limit."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()
    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return
    try:
        num = int(text.split()[-1])
        settings = group_svc.get_settings(chat_id)
        settings.flood_limit = num
        group_svc.save_settings(chat_id, settings)
        await update.message.reply_text(f"✯ تم تعيين حد التكرار: {num}")
    except Exception:
        await update.message.reply_text("✯ استخدم: تعيين التكرار <عدد>")

@group_only
async def handle_toggle_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """استقبال الطلبات — toggle requests from users."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return
    settings = group_svc.get_settings(chat_id)
    settings.force_subscribe_enabled = not settings.force_subscribe_enabled
    group_svc.save_settings(chat_id, settings)
    state = "مفعلة ✅" if settings.force_subscribe_enabled else "معطلة ❌"
    await update.message.reply_text(f"✯ استقبال الطلبات: {state}")

@group_only
async def handle_show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض الاعدادات — show current group settings."""
    chat_id = update.effective_chat.id
    settings = group_svc.get_settings(chat_id)
    msg = (
        f"✯ اعدادات المجموعة:\n"
        f"- نوع المجموعة: {settings.group_type.upper()}\n"
        f"- حماية السبام: {'مفعلة ✅' if settings.protection_enabled else 'معطلة ❌'}\n"
        f"- حد التكرار: {settings.flood_limit}\n"
        f"- استقبال الطلبات: {'مفعلة ✅' if settings.force_subscribe_enabled else 'معطلة ❌'}\n"
        f"- رسالة الترحيب: {'مفعلة ✅' if settings.welcome_enabled else 'معطلة ❌'}\n"
        f"- الالعاب: {'مفعلة ✅' if settings.games_enabled else 'معطلة ❌'}\n"
        f"- الوسوم: {'مفعلة ✅' if settings.tag_enabled else 'معطلة ❌'}\n"
        f"- البث: {'مفعلة ✅' if settings.broadcast_enabled else 'معطلة ❌'}\n"
    )
    await update.message.reply_text(msg)
@group_only
async def handle_upgrade_vip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ترقية — upgrade group to VIP."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return
    group_svc.set_group_type(chat_id, "vip")
    await update.message.reply_text("✯ تم ترقية المجموعة إلى VIP ✅")

@group_only
async def handle_downgrade_free(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عادية — downgrade group to free."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return
    group_svc.set_group_type(chat_id, "free")
    await update.message.reply_text("✯ تم تحويل المجموعة إلى مجانية ✅")

@group_only
async def handle_show_group_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض نوع المجموعة — show group type (VIP/free)."""
    chat_id = update.effective_chat.id
    group_type = group_svc.get_group_type(chat_id)
    await update.message.reply_text(f"✯ نوع المجموعة: {group_type.upper()}")
"""
Group Settings handler — pin, welcome, rules, description, and other group management.
Ported from bian.lua / AVIRA.lua group settings commands.

Commands:
- تثبيت — pin a message
- الغاء التثبيت — unpin a message
- الغاء تثبيت الكل — unpin all messages
- ضع ترحيب / وضع ترحيب — set welcome message
- حذف الترحيب / مسح الترحيب — delete welcome message
- الترحيب — show welcome message
- ضع قوانين / وضع قوانين — set rules
- حذف القوانين / مسح القوانين — delete rules
- القوانين — show rules
- ضع وصف / وضع وصف — set description
- حذف الوصف / مسح الوصف — delete description
- ضع رابط / وضع رابط — set group link
- حذف الرابط / مسح الرابط — delete saved link
- بوت غادر / غادر — bot leaves group
- المحظورين — list banned users
- المكتومين — list muted users
- المقيدين — list restricted users
"""
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

from src.constants.messages import (
    MSG_PINNED, MSG_UNPINNED, MSG_ALL_UNPINNED,
    MSG_NO_PERMISSION, MSG_NO_RULES,
)
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.services.redis_service import RedisService
from src.config import Config

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()
redis_svc = RedisService()


def _welcome_key(chat_id: int) -> str:
    return f"bot:group:{chat_id}:welcome"


def _rules_key(chat_id: int) -> str:
    return f"bot:group:{chat_id}:rules"


def _description_key(chat_id: int) -> str:
    return f"bot:group:{chat_id}:description"


def _link_key(chat_id: int) -> str:
    return f"bot:group:{chat_id}:link"


# ══════════════════════════════════════════════════
# Pin Commands
# ══════════════════════════════════════════════════

@group_only
async def handle_pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pin a replied message."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("✯ رد على رساله لتثبيتها")
        return

    try:
        await context.bot.pin_chat_message(
            chat_id,
            update.message.reply_to_message.message_id,
            disable_notification=False
        )
        await update.message.reply_text(MSG_PINNED)
    except TelegramError as e:
        logger.error(f"Pin failed: {e}")
        await update.message.reply_text("✯ فشل تثبيت الرساله")


@group_only
async def handle_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unpin a replied message or latest pinned."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    try:
        if update.message.reply_to_message:
            await context.bot.unpin_chat_message(
                chat_id,
                update.message.reply_to_message.message_id
            )
        else:
            await context.bot.unpin_chat_message(chat_id)
        await update.message.reply_text(MSG_UNPINNED)
    except TelegramError as e:
        logger.error(f"Unpin failed: {e}")
        await update.message.reply_text("✯ فشل الغاء تثبيت الرساله")


@group_only
async def handle_unpin_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unpin all messages."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    try:
        await context.bot.unpin_all_chat_messages(chat_id)
        await update.message.reply_text(MSG_ALL_UNPINNED)
    except TelegramError as e:
        logger.error(f"Unpin all failed: {e}")
        await update.message.reply_text("✯ فشل الغاء تثبيت الرسائل")


# ══════════════════════════════════════════════════
# Welcome Commands
# ══════════════════════════════════════════════════

@group_only
async def handle_set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set welcome message."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Extract welcome text
    welcome_text = ""
    for prefix in ("ضع ترحيب ", "وضع ترحيب "):
        if text.startswith(prefix):
            welcome_text = text[len(prefix):].strip()
            break

    # Or from reply
    if not welcome_text and update.message.reply_to_message:
        welcome_text = update.message.reply_to_message.text or ""

    if not welcome_text:
        await update.message.reply_text("✯ اكتب رسالة الترحيب بعد الامر او رد على رساله")
        return

    redis_svc.set(_welcome_key(chat_id), welcome_text)
    await update.message.reply_text("✯ تم حفظ رسالة الترحيب ✅")


@group_only
async def handle_delete_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete welcome message."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    redis_svc.delete(_welcome_key(chat_id))
    await update.message.reply_text("✯ تم حذف رسالة الترحيب ✅")


@group_only
async def handle_show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current welcome message."""
    chat_id = update.effective_chat.id
    welcome = redis_svc.get(_welcome_key(chat_id))

    if welcome:
        await update.message.reply_text(f"✯ رسالة الترحيب:\n{welcome}")
    else:
        await update.message.reply_text("✯ لا توجد رسالة ترحيب محدده")


# ══════════════════════════════════════════════════
# Rules Commands
# ══════════════════════════════════════════════════

@group_only
async def handle_set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set group rules."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    rules_text = ""
    for prefix in ("ضع قوانين ", "وضع قوانين "):
        if text.startswith(prefix):
            rules_text = text[len(prefix):].strip()
            break

    if not rules_text and update.message.reply_to_message:
        rules_text = update.message.reply_to_message.text or ""

    if not rules_text:
        await update.message.reply_text("✯ اكتب القوانين بعد الامر او رد على رساله")
        return

    redis_svc.set(_rules_key(chat_id), rules_text)
    await update.message.reply_text("✯ تم حفظ القوانين ✅")


@group_only
async def handle_delete_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete rules."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    redis_svc.delete(_rules_key(chat_id))
    await update.message.reply_text("✯ تم حذف القوانين ✅")


@group_only
async def handle_show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show group rules."""
    chat_id = update.effective_chat.id
    rules = redis_svc.get(_rules_key(chat_id))

    if rules:
        await update.message.reply_text(f"✯ قوانين المجموعه:\n{rules}")
    else:
        await update.message.reply_text(MSG_NO_RULES)


# ══════════════════════════════════════════════════
# Description Commands
# ══════════════════════════════════════════════════

@group_only
async def handle_set_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set group description."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    desc_text = ""
    for prefix in ("ضع وصف ", "وضع وصف "):
        if text.startswith(prefix):
            desc_text = text[len(prefix):].strip()
            break

    if not desc_text and update.message.reply_to_message:
        desc_text = update.message.reply_to_message.text or ""

    if not desc_text:
        await update.message.reply_text("✯ اكتب الوصف بعد الامر او رد على رساله")
        return

    try:
        await context.bot.set_chat_description(chat_id, desc_text)
        await update.message.reply_text("✯ تم تعيين وصف المجموعه ✅")
    except TelegramError as e:
        logger.error(f"Set description failed: {e}")
        await update.message.reply_text("✯ فشل تعيين الوصف")


@group_only
async def handle_delete_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete group description."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    try:
        await context.bot.set_chat_description(chat_id, "")
        await update.message.reply_text("✯ تم حذف وصف المجموعه ✅")
    except TelegramError as e:
        logger.error(f"Delete description failed: {e}")
        await update.message.reply_text("✯ فشل حذف الوصف")


# ══════════════════════════════════════════════════
# Link Commands
# ══════════════════════════════════════════════════

@group_only
async def handle_set_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set/save group link."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    link = ""
    for prefix in ("ضع رابط ", "وضع رابط "):
        if text.startswith(prefix):
            link = text[len(prefix):].strip()
            break

    if not link:
        # Try to export invite link
        try:
            link = await context.bot.export_chat_invite_link(chat_id)
        except TelegramError:
            pass

    if link:
        redis_svc.set(_link_key(chat_id), link)
        await update.message.reply_text(f"✯ تم حفظ الرابط:\n{link}")
    else:
        await update.message.reply_text("✯ اكتب الرابط بعد الامر")


@group_only
async def handle_delete_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete saved group link."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    redis_svc.delete(_link_key(chat_id))
    await update.message.reply_text("✯ تم حذف الرابط ✅")


# ══════════════════════════════════════════════════
# Bot Leave
# ══════════════════════════════════════════════════

@group_only
async def handle_bot_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Make bot leave the group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    # Only sudo or group owner can make bot leave
    if not user_svc.is_sudo(from_user.id):
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            is_owner = any(a.user.id == from_user.id and a.status == "creator" for a in admins)
            if not is_owner:
                await update.message.reply_text(MSG_NO_PERMISSION)
                return
        except TelegramError:
            await update.message.reply_text(MSG_NO_PERMISSION)
            return

    await update.message.reply_text("✯ مع السلامه 👋")
    try:
        await context.bot.leave_chat(chat_id)
        group_svc.remove_group(chat_id)
    except TelegramError as e:
        logger.error(f"Leave chat failed: {e}")


# ══════════════════════════════════════════════════
# User Lists (Banned, Muted, Restricted)
# ══════════════════════════════════════════════════

@group_only
async def handle_list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List banned users."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    banned_users = user_svc.list_banned(chat_id)
    if not banned_users:
        await update.message.reply_text("✯ لا يوجد محظورين في المجموعه")
        return

    lines = ["✯ قائمة المحظورين:"]
    for i, uid in enumerate(banned_users[:20], 1):
        user = user_svc.get_user(int(uid))
        lines.append(f"  {i}. {user.full_name} (<code>{uid}</code>)")

    if len(banned_users) > 20:
        lines.append(f"\n... و {len(banned_users) - 20} اخرين")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@group_only
async def handle_list_muted(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List muted users."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    muted_users = user_svc.list_muted(chat_id)
    if not muted_users:
        await update.message.reply_text("✯ لا يوجد مكتومين في المجموعه")
        return

    lines = ["✯ قائمة المكتومين:"]
    for i, uid in enumerate(muted_users[:20], 1):
        user = user_svc.get_user(int(uid))
        lines.append(f"  {i}. {user.full_name} (<code>{uid}</code>)")

    if len(muted_users) > 20:
        lines.append(f"\n... و {len(muted_users) - 20} اخرين")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


@group_only
async def handle_list_restricted(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List restricted users."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Get both banned and muted as restricted
    banned = user_svc.list_banned(chat_id)
    muted = user_svc.list_muted(chat_id)
    restricted = set(banned) | set(muted)

    if not restricted:
        await update.message.reply_text("✯ لا يوجد مقيدين في المجموعه")
        return

    lines = ["✯ قائمة المقيدين:"]
    for i, uid in enumerate(list(restricted)[:20], 1):
        user = user_svc.get_user(int(uid))
        lines.append(f"  {i}. {user.full_name} (<code>{uid}</code>)")

    if len(restricted) > 20:
        lines.append(f"\n... و {len(restricted) - 20} اخرين")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


def register(app: Application) -> None:
    # Advanced settings commands
    app.add_handler(MessageHandler(filters.Regex("^(حماية من السبام|حماية السبام)$") & G, handle_toggle_spam), group=35)
    app.add_handler(MessageHandler(filters.Regex("^تعيين التكرار \\d+$") & G, handle_set_flood_limit), group=35)
    app.add_handler(MessageHandler(filters.Regex("^(استقبال الطلبات|استقبال الطلب)$") & G, handle_toggle_requests), group=35)
    app.add_handler(MessageHandler(filters.Regex("^(عرض الاعدادات|الاعدادات|settings)$") & G, handle_show_settings), group=35)

    G = filters.ChatType.GROUPS
    # VIP/Free group type commands
    app.add_handler(MessageHandler(filters.Regex("^ترقية$") & G, handle_upgrade_vip), group=35)
    app.add_handler(MessageHandler(filters.Regex("^عادية$") & G, handle_downgrade_free), group=35)
    app.add_handler(MessageHandler(filters.Regex("^(نوع المجموعة|نوع الجروب)$") & G, handle_show_group_type), group=35)

    # Pin commands
    app.add_handler(MessageHandler(
        filters.Regex("^تثبيت$") & G, handle_pin
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^(الغاء التثبيت|الغاء تثبيت)$") & G, handle_unpin
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^الغاء تثبيت الكل$") & G, handle_unpin_all
    ), group=35)

    # Welcome commands
    app.add_handler(MessageHandler(
        filters.Regex("^(ضع ترحيب|وضع ترحيب)") & G, handle_set_welcome
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف الترحيب|مسح الترحيب)$") & G, handle_delete_welcome
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^الترحيب$") & G, handle_show_welcome
    ), group=35)

    # Rules commands
    app.add_handler(MessageHandler(
        filters.Regex("^(ضع قوانين|وضع قوانين)") & G, handle_set_rules
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف القوانين|مسح القوانين)$") & G, handle_delete_rules
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^القوانين$") & G, handle_show_rules
    ), group=35)

    # Description commands
    app.add_handler(MessageHandler(
        filters.Regex("^(ضع وصف|وضع وصف)") & G, handle_set_description
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف الوصف|مسح الوصف)$") & G, handle_delete_description
    ), group=35)

    # Link commands
    app.add_handler(MessageHandler(
        filters.Regex("^(ضع رابط|وضع رابط)") & G, handle_set_link
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف الرابط|مسح الرابط)$") & G, handle_delete_link
    ), group=35)

    # Bot leave
    app.add_handler(MessageHandler(
        filters.Regex("^(بوت غادر|غادر)$") & G, handle_bot_leave
    ), group=35)

    # User lists
    app.add_handler(MessageHandler(
        filters.Regex("^(المحظورين|المحظورين عام)$") & G, handle_list_banned
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^(المكتومين|المكتومين عام)$") & G, handle_list_muted
    ), group=35)
    app.add_handler(MessageHandler(
        filters.Regex("^المقيدين$") & G, handle_list_restricted
    ), group=35)
