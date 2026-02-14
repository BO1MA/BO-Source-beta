"""
Telegram API helper functions.
"""
from __future__ import annotations

import logging
from telegram import Bot, ChatMember, ChatPermissions
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


async def get_chat_member_safe(bot: Bot, chat_id: int, user_id: int) -> ChatMember | None:
    """Safely get a chat member, returning None on error."""
    try:
        return await bot.get_chat_member(chat_id, user_id)
    except TelegramError as e:
        logger.warning(f"Failed to get chat member {user_id} in {chat_id}: {e}")
        return None


async def is_bot_admin(bot: Bot, chat_id: int) -> bool:
    """Check if the bot is an admin in the given chat."""
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
        return member.status in ("administrator", "creator")
    except TelegramError:
        return False


async def check_channel_membership(bot: Bot, channel_id: int, user_id: int) -> bool:
    """Check if a user is a member of the required channel."""
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramError:
        return False


async def ban_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Ban a user from a chat."""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        return True
    except TelegramError as e:
        logger.error(f"Failed to ban {user_id} in {chat_id}: {e}")
        return False


async def unban_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Unban a user from a chat."""
    try:
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        return True
    except TelegramError as e:
        logger.error(f"Failed to unban {user_id} in {chat_id}: {e}")
        return False


async def kick_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Kick a user (ban then unban so they can rejoin)."""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        return True
    except TelegramError as e:
        logger.error(f"Failed to kick {user_id} in {chat_id}: {e}")
        return False


async def mute_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Restrict a user from sending messages."""
    try:
        perms = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(chat_id, user_id, permissions=perms)
        return True
    except TelegramError as e:
        logger.error(f"Failed to mute {user_id} in {chat_id}: {e}")
        return False


async def unmute_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Unrestrict a user."""
    try:
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_send_polls=True,
            can_invite_users=True,
        )
        await bot.restrict_chat_member(chat_id, user_id, permissions=perms)
        return True
    except TelegramError as e:
        logger.error(f"Failed to unmute {user_id} in {chat_id}: {e}")
        return False


async def promote_member(
    bot: Bot, chat_id: int, user_id: int,
    can_manage_chat: bool = True,
    can_delete_messages: bool = True,
    can_restrict_members: bool = True,
    can_promote_members: bool = False,
    can_change_info: bool = True,
    can_invite_users: bool = True,
    can_pin_messages: bool = True,
) -> bool:
    """Promote a user to admin in Telegram."""
    try:
        await bot.promote_chat_member(
            chat_id, user_id,
            can_manage_chat=can_manage_chat,
            can_delete_messages=can_delete_messages,
            can_restrict_members=can_restrict_members,
            can_promote_members=can_promote_members,
            can_change_info=can_change_info,
            can_invite_users=can_invite_users,
            can_pin_messages=can_pin_messages,
        )
        return True
    except TelegramError as e:
        logger.error(f"Failed to promote {user_id} in {chat_id}: {e}")
        return False


async def demote_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Remove admin privileges from a user."""
    try:
        await bot.promote_chat_member(
            chat_id, user_id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        return True
    except TelegramError as e:
        logger.error(f"Failed to demote {user_id} in {chat_id}: {e}")
        return False


async def pin_message(bot: Bot, chat_id: int, message_id: int, disable_notification: bool = False) -> bool:
    try:
        await bot.pin_chat_message(chat_id, message_id, disable_notification=disable_notification)
        return True
    except TelegramError as e:
        logger.error(f"Failed to pin message {message_id} in {chat_id}: {e}")
        return False


async def unpin_message(bot: Bot, chat_id: int, message_id: int | None = None) -> bool:
    try:
        if message_id:
            await bot.unpin_chat_message(chat_id, message_id)
        else:
            await bot.unpin_all_chat_messages(chat_id)
        return True
    except TelegramError as e:
        logger.error(f"Failed to unpin in {chat_id}: {e}")
        return False


async def delete_message_safe(bot: Bot, chat_id: int, message_id: int) -> bool:
    try:
        await bot.delete_message(chat_id, message_id)
        return True
    except TelegramError:
        return False
