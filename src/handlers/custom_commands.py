"""
Custom Commands handler — add, delete, and trigger custom commands/replies.
Ported from bian.lua / AVIRA.lua custom command system.

Commands:
- اضف امر <trigger>\n<response>
- اضف رد <trigger>\n<response>
- حذف امر <trigger>
- حذف رد <trigger>
- اضف امر عام <trigger>\n<response>
- اضف رد عام <trigger>\n<response>
- حذف امر عام <trigger>
- حذف رد عام <trigger>
- الاوامر المضافه
- الاوامر المضافه العامه
- مسح الاوامر المضافه
- مسح الاوامر المضافه العامه
"""
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.constants.messages import (
    MSG_COMMAND_ADDED, MSG_COMMAND_DELETED, MSG_REPLY_ADDED,
    MSG_REPLY_DELETED, MSG_NO_CUSTOM_COMMANDS, MSG_NO_PERMISSION,
)
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.config import Config

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()


# ── Add Custom Command ──

@group_only
async def handle_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a custom command for this group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    # Need admin role
    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    # Parse: اضف امر <trigger>\n<response>
    if text.startswith("اضف امر "):
        content = text[len("اضف امر "):].strip()
    else:
        return

    if "\n" not in content:
        await update.message.reply_text("✯ استخدم: اضف امر <الامر>\\n<الرد>")
        return

    trigger, response = content.split("\n", 1)
    trigger = trigger.strip()
    response = response.strip()

    if not trigger or not response:
        await update.message.reply_text("✯ يجب كتابة الامر والرد")
        return

    group_svc.add_custom_command(chat_id, trigger, response)
    await update.message.reply_text(MSG_COMMAND_ADDED.format(command=trigger))


@group_only
async def handle_add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a custom reply for this group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if text.startswith("اضف رد "):
        content = text[len("اضف رد "):].strip()
    else:
        return

    if "\n" not in content:
        await update.message.reply_text("✯ استخدم: اضف رد <الكلمه>\\n<الرد>")
        return

    trigger, response = content.split("\n", 1)
    trigger = trigger.strip()
    response = response.strip()

    if not trigger or not response:
        await update.message.reply_text("✯ يجب كتابة الكلمه والرد")
        return

    group_svc.add_custom_reply(chat_id, trigger, response)
    await update.message.reply_text(MSG_REPLY_ADDED.format(reply=trigger))


# ── Delete Custom Command/Reply ──

@group_only
async def handle_delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a custom command."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    trigger = ""
    for prefix in ("حذف امر ", "مسح امر "):
        if text.startswith(prefix):
            trigger = text[len(prefix):].strip()
            break

    if not trigger:
        return

    group_svc.delete_custom_command(chat_id, trigger)
    await update.message.reply_text(MSG_COMMAND_DELETED.format(command=trigger))


@group_only
async def handle_delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a custom reply."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    trigger = ""
    for prefix in ("حذف رد ", "مسح رد "):
        if text.startswith(prefix):
            trigger = text[len(prefix):].strip()
            break

    if not trigger:
        return

    group_svc.delete_custom_reply(chat_id, trigger)
    await update.message.reply_text(MSG_REPLY_DELETED.format(reply=trigger))


# ── Global Commands (sudo only) ──

async def handle_add_global_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a global custom command (sudo only)."""
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if text.startswith("اضف امر عام "):
        content = text[len("اضف امر عام "):].strip()
    else:
        return

    if "\n" not in content:
        await update.message.reply_text("✯ استخدم: اضف امر عام <الامر>\\n<الرد>")
        return

    trigger, response = content.split("\n", 1)
    trigger = trigger.strip()
    response = response.strip()

    if not trigger or not response:
        await update.message.reply_text("✯ يجب كتابة الامر والرد")
        return

    group_svc.add_global_command(trigger, response)
    await update.message.reply_text(MSG_COMMAND_ADDED.format(command=trigger) + " (عام)")


async def handle_add_global_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a global custom reply (sudo only)."""
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    if text.startswith("اضف رد عام "):
        content = text[len("اضف رد عام "):].strip()
    else:
        return

    if "\n" not in content:
        await update.message.reply_text("✯ استخدم: اضف رد عام <الكلمه>\\n<الرد>")
        return

    trigger, response = content.split("\n", 1)
    trigger = trigger.strip()
    response = response.strip()

    if not trigger or not response:
        await update.message.reply_text("✯ يجب كتابة الكلمه والرد")
        return

    group_svc.add_global_reply(trigger, response)
    await update.message.reply_text(MSG_REPLY_ADDED.format(reply=trigger) + " (عام)")


async def handle_delete_global_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a global command (sudo only)."""
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    trigger = ""
    for prefix in ("حذف امر عام ", "مسح امر عام "):
        if text.startswith(prefix):
            trigger = text[len(prefix):].strip()
            break

    if not trigger:
        return

    group_svc.delete_global_command(trigger)
    await update.message.reply_text(MSG_COMMAND_DELETED.format(command=trigger) + " (عام)")


async def handle_delete_global_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a global reply (sudo only)."""
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    trigger = ""
    for prefix in ("حذف رد عام ", "مسح رد عام "):
        if text.startswith(prefix):
            trigger = text[len(prefix):].strip()
            break

    if not trigger:
        return

    group_svc.delete_global_reply(trigger)
    await update.message.reply_text(MSG_REPLY_DELETED.format(reply=trigger) + " (عام)")


# ── List Commands ──

@group_only
async def handle_list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all custom commands for this group."""
    chat_id = update.effective_chat.id
    commands = group_svc.get_all_custom_commands(chat_id)
    replies = group_svc.get_all_custom_replies(chat_id)

    if not commands and not replies:
        await update.message.reply_text(MSG_NO_CUSTOM_COMMANDS)
        return

    lines = ["✯ الاوامر المضافه:"]
    if commands:
        lines.append("\n📝 الاوامر:")
        for i, trigger in enumerate(commands.keys(), 1):
            lines.append(f"  {i}. {trigger}")

    if replies:
        lines.append("\n💬 الردود:")
        for i, trigger in enumerate(replies.keys(), 1):
            lines.append(f"  {i}. {trigger}")

    await update.message.reply_text("\n".join(lines))


async def handle_list_global_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all global custom commands."""
    from_user = update.effective_user

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    commands = group_svc.get_all_global_commands()
    replies = group_svc.get_all_global_replies()

    if not commands and not replies:
        await update.message.reply_text("✯ لا توجد اوامر عامه مضافه")
        return

    lines = ["✯ الاوامر العامه المضافه:"]
    if commands:
        lines.append("\n📝 الاوامر:")
        for i, trigger in enumerate(commands.keys(), 1):
            lines.append(f"  {i}. {trigger}")

    if replies:
        lines.append("\n💬 الردود:")
        for i, trigger in enumerate(replies.keys(), 1):
            lines.append(f"  {i}. {trigger}")

    await update.message.reply_text("\n".join(lines))


# ── Delete All Commands ──

@group_only
async def handle_clear_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear all custom commands for this group."""
    chat_id = update.effective_chat.id
    from_user = update.effective_user

    if not user_svc.is_group_admin(from_user.id, chat_id) and not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    group_svc.delete_all_custom_commands(chat_id)
    group_svc.delete_all_custom_replies(chat_id)
    await update.message.reply_text("✯ تم مسح جميع الاوامر والردود المضافه ✅")


async def handle_clear_global_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear all global commands (sudo only)."""
    from_user = update.effective_user

    if not user_svc.is_sudo(from_user.id):
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    group_svc.delete_all_global_commands()
    group_svc.delete_all_global_replies()
    await update.message.reply_text("✯ تم مسح جميع الاوامر والردود العامه ✅")


# ── Trigger Custom Commands/Replies ──

@group_only
async def handle_custom_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if message matches a custom command or reply."""
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if not text:
        return

    # Check group-specific command first
    response = group_svc.get_custom_command(chat_id, text)
    if response:
        await update.message.reply_text(response)
        return

    # Check global command
    response = group_svc.get_global_command(text)
    if response:
        await update.message.reply_text(response)
        return

    # Check group-specific reply (substring match)
    replies = group_svc.get_all_custom_replies(chat_id)
    for trigger, response in replies.items():
        if trigger in text:
            await update.message.reply_text(response)
            return

    # Check global reply (substring match)
    global_replies = group_svc.get_all_global_replies()
    for trigger, response in global_replies.items():
        if trigger in text:
            await update.message.reply_text(response)
            return


def register(app: Application) -> None:
    """Register custom command handlers."""
    G = filters.ChatType.GROUPS

    # Add commands
    app.add_handler(MessageHandler(
        filters.Regex("^اضف امر ") & G, handle_add_command
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^اضف رد ") & G, handle_add_reply
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^اضف امر عام "), handle_add_global_command
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^اضف رد عام "), handle_add_global_reply
    ), group=30)

    # Delete commands
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف|مسح) امر ") & G, handle_delete_command
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف|مسح) رد ") & G, handle_delete_reply
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف|مسح) امر عام "), handle_delete_global_command
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^(حذف|مسح) رد عام "), handle_delete_global_reply
    ), group=30)

    # List commands
    app.add_handler(MessageHandler(
        filters.Regex("^الاوامر المضافه$") & G, handle_list_commands
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^الاوامر المضافه العامه$"), handle_list_global_commands
    ), group=30)

    # Clear commands
    app.add_handler(MessageHandler(
        filters.Regex("^مسح الاوامر المضافه$") & G, handle_clear_commands
    ), group=30)
    app.add_handler(MessageHandler(
        filters.Regex("^مسح الاوامر المضافه العامه$"), handle_clear_global_commands
    ), group=30)

    # Custom trigger (low priority - should run after all other handlers)
    app.add_handler(MessageHandler(
        filters.TEXT & G, handle_custom_trigger
    ), group=200)
