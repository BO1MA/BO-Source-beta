"""
Moderation handler — ban, unban, mute, unmute, kick, warn.
Based on moderation features from bian.lua.
"""
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.config import Config
from src.constants.messages import (
    MSG_BANNED, MSG_UNBANNED, MSG_GLOBAL_BANNED, MSG_GLOBAL_UNBANNED,
    MSG_MUTED, MSG_UNMUTED, MSG_GLOBAL_MUTED, MSG_GLOBAL_UNMUTED,
    MSG_KICKED, MSG_WARNED, MSG_WARN_LIMIT,
    MSG_NO_PERMISSION, MSG_USER_NOT_FOUND, MSG_CANT_ACTION_SELF,
    MSG_CANT_ACTION_HIGHER, MSG_BOT_NOT_ADMIN,
)
from src.constants.roles import is_higher_role
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.utils.text_utils import extract_user_id, format_user_list
from src.utils.api_helpers import (
    ban_member, unban_member, kick_member, mute_member, unmute_member,
    is_bot_admin,
)

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()


async def _check_permissions(update: Update, target_id: int) -> bool:
    """Common permission checks for moderation actions. Returns True if allowed."""
    from_user = update.effective_user
    chat_id = update.effective_chat.id

    if from_user.id == target_id:
        await update.message.reply_text(MSG_CANT_ACTION_SELF)
        return False

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return False

    # Can't act on higher roles
    from_role = user_svc.get_role(from_user.id, chat_id)
    target_role = user_svc.get_role(target_id, chat_id)
    if is_higher_role(target_role, from_role) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_CANT_ACTION_HIGHER)
        return False

    return True


@group_only
async def handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from the group."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    if not await _check_permissions(update, target_id):
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text(MSG_BOT_NOT_ADMIN)
        return

    user_svc.ban_user(target_id, chat_id)
    await ban_member(context.bot, chat_id, target_id)
    target = user_svc.get_user(target_id)
    await update.message.reply_text(MSG_BANNED.format(name=target.full_name))


@group_only
async def handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    from_user = update.effective_user
    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    user_svc.unban_user(target_id, chat_id)
    await unban_member(context.bot, chat_id, target_id)
    target = user_svc.get_user(target_id)
    await update.message.reply_text(MSG_UNBANNED.format(name=target.full_name))


@group_only
async def handle_global_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from all groups."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    user_svc.global_ban(target_id)
    target = user_svc.get_user(target_id)

    # Ban from all registered groups
    count = 0
    for gid in group_svc.get_all_group_ids():
        if await ban_member(context.bot, gid, target_id):
            count += 1

    await update.message.reply_text(
        MSG_GLOBAL_BANNED.format(name=target.full_name) + f"\n\u2756 ({count} مجموعه)"
    )


@group_only
async def handle_global_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user from all groups."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    user_svc.global_unban(target_id)
    target = user_svc.get_user(target_id)

    for gid in group_svc.get_all_group_ids():
        await unban_member(context.bot, gid, target_id)

    await update.message.reply_text(MSG_GLOBAL_UNBANNED.format(name=target.full_name))


@group_only
async def handle_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mute a user in the group."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    if not await _check_permissions(update, target_id):
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text(MSG_BOT_NOT_ADMIN)
        return

    user_svc.mute_user(target_id, chat_id)
    await mute_member(context.bot, chat_id, target_id)
    target = user_svc.get_user(target_id)
    await update.message.reply_text(MSG_MUTED.format(name=target.full_name))


@group_only
async def handle_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unmute a user."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    from_user = update.effective_user
    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    user_svc.unmute_user(target_id, chat_id)
    await unmute_member(context.bot, chat_id, target_id)
    target = user_svc.get_user(target_id)
    await update.message.reply_text(MSG_UNMUTED.format(name=target.full_name))


@group_only
async def handle_global_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mute a user in all groups."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    user_svc.global_mute(target_id)
    target = user_svc.get_user(target_id)

    count = 0
    for gid in group_svc.get_all_group_ids():
        if await mute_member(context.bot, gid, target_id):
            count += 1

    await update.message.reply_text(
        MSG_GLOBAL_MUTED.format(name=target.full_name) + f"\n\u2756 ({count} مجموعه)"
    )


@group_only
async def handle_kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kick a user from the group."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    if not await _check_permissions(update, target_id):
        return

    if not await is_bot_admin(context.bot, chat_id):
        await update.message.reply_text(MSG_BOT_NOT_ADMIN)
        return

    await kick_member(context.bot, chat_id, target_id)
    target = user_svc.get_user(target_id)
    await update.message.reply_text(MSG_KICKED.format(name=target.full_name))


@group_only
async def handle_kick_self(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User kicks themselves from the group (اطردني)."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if await is_bot_admin(context.bot, chat_id):
        await kick_member(context.bot, chat_id, user_id)


@group_only
async def handle_warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Warn a user. Kick on max warnings."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    if not await _check_permissions(update, target_id):
        return

    settings = group_svc.get_settings(chat_id)
    count = user_svc.add_warning(target_id, chat_id)
    target = user_svc.get_user(target_id)

    if count >= settings.max_warnings:
        # Kick on max warns
        user_svc.reset_warnings(target_id, chat_id)
        await kick_member(context.bot, chat_id, target_id)
        await update.message.reply_text(MSG_WARN_LIMIT.format(name=target.full_name))
    else:
        await update.message.reply_text(
            MSG_WARNED.format(name=target.full_name, count=count, max=settings.max_warnings)
        )


@group_only
async def handle_unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a warning from a user."""
    chat_id = update.effective_chat.id
    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    from_user = update.effective_user
    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    user_svc.reset_warnings(target_id, chat_id)
    target = user_svc.get_user(target_id)
    await update.message.reply_text(f"\u2756 تم الغاء تحذيرات {target.full_name} \u2705")


@group_only
async def handle_list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List banned users."""
    chat_id = update.effective_chat.id
    banned_ids = user_svc.list_banned(chat_id)
    users = [user_svc.get_user(uid) for uid in banned_ids]
    await update.message.reply_text(format_user_list(users, "المحظورين"))


@group_only
async def handle_list_muted(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List muted users."""
    chat_id = update.effective_chat.id
    muted_ids = user_svc.list_muted(chat_id)
    users = [user_svc.get_user(uid) for uid in muted_ids]
    await update.message.reply_text(format_user_list(users, "المكتومين"))


@group_only
async def handle_global_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unmute a user from all groups."""
    from_user = update.effective_user
    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    target_id = extract_user_id(update.message)
    if not target_id:
        await update.message.reply_text(MSG_USER_NOT_FOUND)
        return

    user_svc.global_unmute(target_id)
    target = user_svc.get_user(target_id)

    count = 0
    for gid in group_svc.get_all_group_ids():
        if await unmute_member(context.bot, gid, target_id):
            count += 1

    await update.message.reply_text(
        MSG_GLOBAL_UNMUTED.format(name=target.full_name) + f"\n✯ ({count} مجموعه)"
    )


@group_only
async def handle_delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a replied-to message: حذف (reply)."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if update.message.reply_to_message:
        from src.utils.api_helpers import delete_message_safe
        await delete_message_safe(context.bot, chat_id, update.message.reply_to_message.message_id)
        await delete_message_safe(context.bot, chat_id, update.message.message_id)
    else:
        await update.message.reply_text("✯ قم بالرد على الرساله المراد حذفها")


def register(app: Application) -> None:
    """Register moderation handlers."""
    G = filters.ChatType.GROUPS

    app.add_handler(MessageHandler(filters.Regex("^حظر( |$)") & G, handle_ban), group=5)
    app.add_handler(MessageHandler(filters.Regex("^(الغاء الحظر|الغاء حظر)( |$)") & G, handle_unban), group=5)
    app.add_handler(MessageHandler(filters.Regex("^حظر عام( |$)") & G, handle_global_ban), group=5)
    app.add_handler(MessageHandler(filters.Regex("^الغاء حظر عام( |$)") & G, handle_global_unban), group=5)
    app.add_handler(MessageHandler(filters.Regex("^(كتم|منع)( |$)") & G, handle_mute), group=5)
    app.add_handler(MessageHandler(filters.Regex("^(الغاء كتم|الغاء منع)( |$)") & G, handle_unmute), group=5)
    app.add_handler(MessageHandler(filters.Regex("^كتم عام( |$)") & G, handle_global_mute), group=5)
    app.add_handler(MessageHandler(filters.Regex("^الغاء كتم عام( |$)") & G, handle_global_unmute), group=5)
    app.add_handler(MessageHandler(filters.Regex("^طرد( |$)") & G, handle_kick), group=5)
    app.add_handler(MessageHandler(filters.Regex("^اطردني$") & G, handle_kick_self), group=5)
    app.add_handler(MessageHandler(filters.Regex("^تحذير( |$)") & G, handle_warn), group=5)
    app.add_handler(MessageHandler(filters.Regex("^الغاء تحذير( |$)") & G, handle_unwarn), group=5)
    app.add_handler(MessageHandler(filters.Regex("^المحظورين$") & G, handle_list_banned), group=5)
    app.add_handler(MessageHandler(filters.Regex("^المكتومين$") & G, handle_list_muted), group=5)
    app.add_handler(MessageHandler(filters.Regex("^حذف$") & G, handle_delete_message), group=5)
