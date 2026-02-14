"""
Decorators for permission checks on handler functions.
"""
import functools
import logging
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from src.config import Config
from src.constants.messages import MSG_NO_PERMISSION, MSG_GROUP_ONLY, MSG_PRIVATE_ONLY
from src.constants.roles import ROLE_HIERARCHY, SUDO_ROLES, GROUP_ADMIN_ROLES, is_higher_role
from src.services.user_service import UserService

logger = logging.getLogger(__name__)


def require_role(min_role: int):
    """Decorator: only allow users with a role >= min_role (lower number = higher)."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not update.effective_user:
                return
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id if update.effective_chat else None

            user_svc = UserService()

            # Sudo always passes
            if user_id == Config.SUDO_ID:
                return await func(update, context, *args, **kwargs)

            role = user_svc.get_role(user_id, chat_id)
            if is_higher_role(role, min_role) or role == min_role:
                return await func(update, context, *args, **kwargs)

            await update.effective_message.reply_text(MSG_NO_PERMISSION)
        return wrapper
    return decorator


def group_only(func: Callable):
    """Decorator: only allow the command in group chats."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat and update.effective_chat.type in ("group", "supergroup"):
            return await func(update, context, *args, **kwargs)
        if update.effective_message:
            await update.effective_message.reply_text(MSG_GROUP_ONLY)
    return wrapper


def private_only(func: Callable):
    """Decorator: only allow the command in private chats."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat and update.effective_chat.type == "private":
            return await func(update, context, *args, **kwargs)
        if update.effective_message:
            await update.effective_message.reply_text(MSG_PRIVATE_ONLY)
    return wrapper


def sudo_only(func: Callable):
    """Decorator: only allow the main developer / sudo users."""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        user_svc = UserService()
        if user_svc.is_sudo(user_id):
            return await func(update, context, *args, **kwargs)
        await update.effective_message.reply_text(MSG_NO_PERMISSION)
    return wrapper
