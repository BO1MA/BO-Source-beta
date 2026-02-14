"""
Admin handler — role management (promote, demote), role listing, admin info,
group management (activate, leave, set title/description/photo),
developer commands, and custom commands.
Based on the role hierarchy from bian.lua / AVIRA.lua.
"""
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.config import Config
from src.constants.messages import (
    MSG_PROMOTED, MSG_DEMOTED, MSG_NO_PERMISSION, MSG_USER_NOT_FOUND,
    MSG_ALREADY_ROLE, MSG_CANT_ACTION_HIGHER, MSG_STATS,
)
from src.constants.roles import (
    ROLE_SECONDARY_DEVELOPER, ROLE_ASSISTANT, ROLE_DEVELOPER, ROLE_OWNER,
    ROLE_MAIN_CREATOR, ROLE_CREATOR, ROLE_MANAGER, ROLE_ADMIN, ROLE_VIP,
    ROLE_MEMBER, ROLE_HIERARCHY, get_role_name, is_higher_role,
    ROLE_NAMES,
)
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.services.redis_service import RedisService
from src.utils.decorators import group_only
from src.utils.text_utils import extract_user_id, format_user_list
from src.utils.api_helpers import promote_member, demote_member, is_bot_admin

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()
redis_svc = RedisService()

# Mapping Arabic role commands to role levels
ROLE_COMMANDS = {
    "مطور ثانوي": ROLE_SECONDARY_DEVELOPER,
    "مساعد": ROLE_ASSISTANT,
    "مطور": ROLE_DEVELOPER,
    "مالك": ROLE_OWNER,
    "منشئ اساسي": ROLE_MAIN_CREATOR,
    "منشئ": ROLE_CREATOR,
    "مدير": ROLE_MANAGER,
    "ادمن": ROLE_ADMIN,
    "مميز": ROLE_VIP,
}

ROLE_LIST_COMMANDS = {
    "المطورين": ROLE_DEVELOPER,
    "المطورين الثانويين": ROLE_SECONDARY_DEVELOPER,
    "المالكين": ROLE_OWNER,
    "المالك": ROLE_OWNER,
    "المنشئين": ROLE_CREATOR,
    "المنشئ": ROLE_CREATOR,
    "المدراء": ROLE_MANAGER,
    "الادمنية": ROLE_ADMIN,
    "المميزين": ROLE_VIP,
}


@group_only
async def handle_promote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Promote a user to a specific role."""
    text = (update.message.text or "").strip()
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    # Determine which role is being assigned
    target_role = None
    for cmd, role in ROLE_COMMANDS.items():
        if text == cmd or text.startswith(cmd + " "):
            target_role = role
            break
    if target_role is None:
        return

    # Check promoter's role
    promoter_role = user_svc.get_role(from_user.id, chat_id)
    if not is_higher_role(promoter_role, target_role) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Find target user
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    # Check if target already has this role
    current_role = user_svc.get_role(target_id, chat_id)
    if current_role == target_role:
        target_user = user_svc.get_user(target_id)
        await update.message.reply_text(MSG_ALREADY_ROLE.format(name=target_user.full_name))
        return

    # Set role
    user_svc.set_role(target_id, target_role, chat_id)
    target_user = user_svc.get_user(target_id)

    # Also promote in Telegram if it's an admin-level role
    if target_role in (ROLE_ADMIN, ROLE_MANAGER, ROLE_CREATOR, ROLE_MAIN_CREATOR, ROLE_OWNER):
        can_promote = target_role in (ROLE_OWNER, ROLE_MAIN_CREATOR)
        await promote_member(
            context.bot, chat_id, target_id,
            can_promote_members=can_promote,
        )

    await update.message.reply_text(
        MSG_PROMOTED.format(name=target_user.full_name, role=get_role_name(target_role))
    )


@group_only
async def handle_demote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Demote a user back to member."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    promoter_role = user_svc.get_role(from_user.id, chat_id)
    target_role = user_svc.get_role(target_id, chat_id)

    if not is_higher_role(promoter_role, target_role) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_CANT_ACTION_HIGHER)
        return

    target_user = user_svc.get_user(target_id)
    old_role_name = get_role_name(target_role)
    user_svc.remove_role(target_id, chat_id)

    # Also demote in Telegram
    await demote_member(context.bot, chat_id, target_id)

    await update.message.reply_text(MSG_DEMOTED.format(name=target_user.full_name, role=old_role_name))


@group_only
async def handle_role_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List users with a specific role."""
    text = (update.message.text or "").strip()
    chat_id = update.effective_chat.id

    target_role = None
    for cmd, role in ROLE_LIST_COMMANDS.items():
        if text == cmd:
            target_role = role
            break
    if target_role is None:
        return

    users = user_svc.list_users_by_role(target_role, chat_id)
    title = get_role_name(target_role)
    await update.message.reply_text(format_user_list(users, title))


@group_only
async def handle_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List Telegram admins of the group."""
    chat_id = update.effective_chat.id
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        lines = ["\u2756 ادمنيه الجروب:"]
        for i, admin in enumerate(admins, 1):
            name = admin.user.first_name
            title = admin.custom_title or ""
            status = "منشئ" if admin.status == "creator" else "مشرف"
            line = f"{i}. {name}"
            if title:
                line += f" | {title}"
            line += f" [{status}]"
            lines.append(line)
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Failed to get admins: {e}")
        await update.message.reply_text("\u2756 فشل في جلب قائمة الادمنيه")


@group_only
async def handle_custom_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle adding/deleting custom commands and replies."""
    text = (update.message.text or "").strip()
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if text.startswith("اضف امر عام"):
        if from_user.id != Config.SUDO_ID:
            await update.message.reply_text(MSG_NO_PERMISSION)
            return
        parts = text.split("\n", 1)
        if len(parts) >= 2:
            trigger = parts[0].replace("اضف امر عام", "").strip()
            response = parts[1].strip()
            if trigger and response:
                group_svc.add_global_command(trigger, response)
                await update.message.reply_text(f"\u2756 تم اضافة الامر العام: {trigger} \u2705")
        return

    if text.startswith("اضف امر"):
        parts = text.split("\n", 1)
        if len(parts) >= 2:
            trigger = parts[0].replace("اضف امر", "").strip()
            response = parts[1].strip()
            if trigger and response:
                group_svc.add_custom_command(chat_id, trigger, response)
                await update.message.reply_text(f"\u2756 تم اضافة الامر: {trigger} \u2705")
        return

    if text.startswith("اضف رد عام"):
        if from_user.id != Config.SUDO_ID:
            await update.message.reply_text(MSG_NO_PERMISSION)
            return
        parts = text.split("\n", 1)
        if len(parts) >= 2:
            trigger = parts[0].replace("اضف رد عام", "").strip()
            response = parts[1].strip()
            if trigger and response:
                group_svc.add_global_reply(trigger, response)
                await update.message.reply_text(f"\u2756 تم اضافة الرد العام: {trigger} \u2705")
        return

    if text.startswith("اضف رد"):
        parts = text.split("\n", 1)
        if len(parts) >= 2:
            trigger = parts[0].replace("اضف رد", "").strip()
            response = parts[1].strip()
            if trigger and response:
                group_svc.add_custom_reply(chat_id, trigger, response)
                await update.message.reply_text(f"\u2756 تم اضافة الرد: {trigger} \u2705")
        return

    if text.startswith("الغاء الامر"):
        trigger = text.replace("الغاء الامر", "").strip()
        if trigger:
            group_svc.delete_custom_command(chat_id, trigger)
            await update.message.reply_text(f"\u2756 تم حذف الامر: {trigger} \u2705")
        return

    if text == "الاوامر المضافه":
        cmds = group_svc.get_all_custom_commands(chat_id)
        if cmds:
            lines = ["\u2756 الاوامر المضافه:"]
            for i, cmd in enumerate(cmds, 1):
                lines.append(f"{i}. {cmd}")
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("\u2756 لا توجد اوامر مضافه")
        return

    if text == "الاوامر المضافه العامه":
        cmds = group_svc.get_all_global_commands()
        if cmds:
            lines = ["\u2756 الاوامر العامه:"]
            for i, cmd in enumerate(cmds, 1):
                lines.append(f"{i}. {cmd}")
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("\u2756 لا توجد اوامر عامه")
        return


# ══════════════════════════════════════════════════
# Group Management Commands
# ══════════════════════════════════════════════════

@group_only
async def handle_activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تفعيل — activate the bot in this group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    group_svc.register_group(chat_id, update.effective_chat.title or "")
    await update.message.reply_text("✯ تم تفعيل البوت في هذا الجروب ✅")


@group_only
async def handle_bot_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بوت غادر — make the bot leave the group (sudo only)."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text("✯ وداعاً 👋")
    group_svc.remove_group(chat_id)
    await context.bot.leave_chat(chat_id)


@group_only
async def handle_set_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ضع اسم <text> — set group title."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text("✯ يجب ان اكون مشرف لتنفيذ هذا الامر")
        return

    new_title = text.replace("ضع اسم", "", 1).strip()
    if new_title:
        try:
            await context.bot.set_chat_title(chat_id, new_title)
            await update.message.reply_text(f"✯ تم تغيير اسم الجروب الى: {new_title} ✅")
        except Exception as e:
            await update.message.reply_text(f"✯ فشل تغيير الاسم: {e}")
    else:
        await update.message.reply_text("✯ اكتب الاسم الجديد بعد الامر")


@group_only
async def handle_set_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ضع وصف <text> — set group description."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text("✯ يجب ان اكون مشرف لتنفيذ هذا الامر")
        return

    desc = text.replace("ضع وصف", "", 1).strip()
    if desc:
        try:
            await context.bot.set_chat_description(chat_id, desc)
            await update.message.reply_text("✯ تم تغيير وصف الجروب ✅")
        except Exception as e:
            await update.message.reply_text(f"✯ فشل تغيير الوصف: {e}")
    else:
        await update.message.reply_text("✯ اكتب الوصف الجديد بعد الامر")


@group_only
async def handle_set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تغيير صورة الجروب — set group photo (reply to a photo)."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text("✯ يجب ان اكون مشرف لتنفيذ هذا الامر")
        return

    if update.message.reply_to_message and update.message.reply_to_message.photo:
        photo = update.message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        try:
            from io import BytesIO
            await context.bot.set_chat_photo(chat_id, BytesIO(photo_bytes))
            await update.message.reply_text("✯ تم تغيير صورة الجروب ✅")
        except Exception as e:
            await update.message.reply_text(f"✯ فشل تغيير الصوره: {e}")
    else:
        await update.message.reply_text("✯ قم بالرد على صوره لتعيينها كصورة الجروب")


@group_only
async def handle_detect_bots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """كشف البوتات — list bots in the group."""
    chat_id = update.effective_chat.id
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        bots = [a for a in admins if a.user.is_bot]
        if bots:
            lines = ["✯ البوتات في الجروب 🤖:"]
            for i, bot in enumerate(bots, 1):
                lines.append(f"{i}. {bot.user.first_name} (@{bot.user.username or 'N/A'})")
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("✯ لا توجد بوتات مشرفه")
    except Exception:
        await update.message.reply_text("✯ فشل في جلب قائمة البوتات")


@group_only
async def handle_demote_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تنزيل الكل — demote all users in this group to member."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Remove all group roles
    pattern = f"bot:group:{chat_id}:user:*"
    count = 0
    for key in redis_svc.keys(pattern):
        data = redis_svc.hgetall(key)
        if data.get("role") and int(data.get("role", ROLE_MEMBER)) != ROLE_MEMBER:
            redis_svc.hset(key, "role", str(ROLE_MEMBER))
            count += 1

    await update.message.reply_text(f"✯ تم تنزيل {count} عضو الى عضو عادي ✅")


# ══════════════════════════════════════════════════
# Developer/Sudo Commands
# ══════════════════════════════════════════════════

async def handle_sudo_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """احصائيات البوت — full bot stats (sudo only)."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        return

    total_groups = group_svc.get_total_groups()
    total_users = user_svc.get_total_users()
    total_msgs = group_svc.get_total_messages()

    await update.message.reply_text(MSG_STATS.format(
        groups=total_groups, users=total_users, messages=total_msgs,
    ))


async def handle_group_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عدد الجروبات — show how many groups the bot is in."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    count = group_svc.get_total_groups()
    await update.message.reply_text(f"✯ عدد المجموعات: {count}")


async def handle_user_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عدد المستخدمين — show total registered users."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    count = user_svc.get_total_users()
    await update.message.reply_text(f"✯ عدد المستخدمين: {count}")


async def handle_group_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """قائمة الجروبات — list all registered groups."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    group_ids = group_svc.get_all_group_ids()
    if not group_ids:
        await update.message.reply_text("✯ لا توجد مجموعات مسجله")
        return

    lines = [f"✯ المجموعات المسجله ({len(group_ids)}):"]
    for i, gid in enumerate(group_ids[:50], 1):
        group = group_svc.get_group(gid)
        lines.append(f"{i}. {group.title or 'بدون اسم'} [{gid}]")

    if len(group_ids) > 50:
        lines.append(f"... و {len(group_ids) - 50} مجموعه اخرى")

    await update.message.reply_text("\n".join(lines))


def register(app: Application) -> None:
    """Register admin-related handlers."""
    G = filters.ChatType.GROUPS

    # Promote commands
    for cmd_text in ROLE_COMMANDS:
        app.add_handler(MessageHandler(
            filters.Regex(f"^{cmd_text}( |$)") & filters.ChatType.GROUPS,
            handle_promote,
        ), group=10)

    # Demote commands
    app.add_handler(MessageHandler(
        filters.Regex("^(تنزيل|عزل)( |$)") & G,
        handle_demote,
    ), group=10)

    # Demote all
    app.add_handler(MessageHandler(
        filters.Regex("^تنزيل الكل$") & G,
        handle_demote_all,
    ), group=10)

    # Role listing
    for cmd_text in ROLE_LIST_COMMANDS:
        app.add_handler(MessageHandler(
            filters.Regex(f"^{cmd_text}$") & G,
            handle_role_list,
        ), group=10)

    # Admin list
    app.add_handler(MessageHandler(
        filters.Regex("^(الادمنيه|ادمنيه الجروب)$") & G,
        handle_admin_list,
    ), group=10)

    # Custom commands
    app.add_handler(MessageHandler(
        filters.Regex("^(اضف امر|اضف رد|الغاء الامر|الاوامر المضافه)") & G,
        handle_custom_commands,
    ), group=10)

    # Group management
    app.add_handler(MessageHandler(filters.Regex("^تفعيل$") & G, handle_activate), group=10)
    app.add_handler(MessageHandler(filters.Regex("^بوت غادر$") & G, handle_bot_leave), group=10)
    app.add_handler(MessageHandler(filters.Regex("^ضع اسم") & G, handle_set_title), group=10)
    app.add_handler(MessageHandler(filters.Regex("^ضع وصف") & G, handle_set_description), group=10)
    app.add_handler(MessageHandler(filters.Regex("^(تغيير صورة الجروب|صورة الجروب)$") & G, handle_set_photo), group=10)
    app.add_handler(MessageHandler(filters.Regex("^كشف البوتات$") & G, handle_detect_bots), group=10)

    # Developer/sudo commands (work in groups and private)
    app.add_handler(MessageHandler(
        filters.Regex("^عدد الجروبات$"), handle_group_count,
    ), group=10)
    app.add_handler(MessageHandler(
        filters.Regex("^عدد المستخدمين$"), handle_user_count,
    ), group=10)
    app.add_handler(MessageHandler(
        filters.Regex("^قائمة الجروبات$"), handle_group_list,
    ), group=10)
