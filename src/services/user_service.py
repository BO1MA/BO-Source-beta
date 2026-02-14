"""
User service — CRUD for user data stored in Redis.
Mirrors the role/ban/mute system from bian.lua.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from src.config import Config
from src.constants.roles import (
    ROLE_MEMBER, ROLE_HIERARCHY, SUDO_ROLES, GROUP_ADMIN_ROLES,
    get_role_name, is_higher_role,
)
from src.models.user import User
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)

_PREFIX = "bot:user:"


class UserService:
    def __init__(self) -> None:
        self.redis = RedisService()

    # ── Key builders ──

    def _user_key(self, user_id: int) -> str:
        return f"{_PREFIX}{user_id}"

    def _group_user_key(self, chat_id: int, user_id: int) -> str:
        return f"bot:group:{chat_id}:user:{user_id}"

    # ── Get / Save ──

    def get_user(self, user_id: int) -> User:
        """Get or create a user record."""
        data = self.redis.hgetall(self._user_key(user_id))
        if data:
            return User.from_dict(data)
        return User(user_id=user_id)

    def save_user(self, user: User) -> None:
        """Persist a user record."""
        for k, v in user.to_dict().items():
            self.redis.hset(self._user_key(user.user_id), k, str(v))

    def update_info(self, user_id: int, first_name: str, last_name: str = "", username: str = "") -> User:
        """Update basic identity info and return the user."""
        user = self.get_user(user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        self.save_user(user)
        return user

    # ── Roles ──

    def get_role(self, user_id: int, chat_id: int | None = None) -> int:
        """Get user's role. Global role takes precedence if higher."""
        user = self.get_user(user_id)
        global_role = user.role

        if chat_id:
            group_role_str = self.redis.hget(self._group_user_key(chat_id, user_id), "role")
            group_role = int(group_role_str) if group_role_str else ROLE_MEMBER
            # Return the higher (lower number) of the two
            if is_higher_role(global_role, group_role):
                return global_role
            return group_role
        return global_role

    def set_role(self, user_id: int, role: int, chat_id: int | None = None) -> None:
        """Set a user's role globally or per-group."""
        if role in SUDO_ROLES and chat_id:
            # Sudo roles are always global
            user = self.get_user(user_id)
            user.role = role
            self.save_user(user)
        elif chat_id:
            self.redis.hset(self._group_user_key(chat_id, user_id), "role", str(role))
        else:
            user = self.get_user(user_id)
            user.role = role
            self.save_user(user)

    def remove_role(self, user_id: int, chat_id: int | None = None) -> None:
        """Reset user to member role."""
        self.set_role(user_id, ROLE_MEMBER, chat_id)

    def is_sudo(self, user_id: int) -> bool:
        """Check if user is the main developer."""
        return user_id == Config.SUDO_ID or self.get_user(user_id).role in SUDO_ROLES

    def is_group_admin(self, user_id: int, chat_id: int) -> bool:
        """Check if user has a group admin role."""
        role = self.get_role(user_id, chat_id)
        return role in GROUP_ADMIN_ROLES or role in SUDO_ROLES

    # ── List by role ──

    def list_users_by_role(self, role: int, chat_id: int | None = None) -> list[User]:
        """Return all users with a specific role."""
        results = []
        if chat_id:
            pattern = f"bot:group:{chat_id}:user:*"
            for key in self.redis.keys(pattern):
                data = self.redis.hgetall(key)
                if data and int(data.get("role", ROLE_MEMBER)) == role:
                    uid = int(key.rsplit(":", 1)[-1])
                    user = self.get_user(uid)
                    results.append(user)
        else:
            pattern = f"{_PREFIX}*"
            for key in self.redis.keys(pattern):
                data = self.redis.hgetall(key)
                if data and int(data.get("role", ROLE_MEMBER)) == role:
                    results.append(User.from_dict(data))
        return results

    # ── Ban ──

    def ban_user(self, user_id: int, chat_id: int) -> None:
        self.redis.hset(self._group_user_key(chat_id, user_id), "is_banned", "True")

    def unban_user(self, user_id: int, chat_id: int) -> None:
        self.redis.hset(self._group_user_key(chat_id, user_id), "is_banned", "False")

    def is_banned(self, user_id: int, chat_id: int) -> bool:
        val = self.redis.hget(self._group_user_key(chat_id, user_id), "is_banned")
        return val in ("True", "1")

    def global_ban(self, user_id: int) -> None:
        user = self.get_user(user_id)
        user.is_global_banned = True
        self.save_user(user)

    def global_unban(self, user_id: int) -> None:
        user = self.get_user(user_id)
        user.is_global_banned = False
        self.save_user(user)

    def is_global_banned(self, user_id: int) -> bool:
        return self.get_user(user_id).is_global_banned

    def list_banned(self, chat_id: int) -> list[int]:
        pattern = f"bot:group:{chat_id}:user:*"
        banned = []
        for key in self.redis.keys(pattern):
            data = self.redis.hgetall(key)
            if data.get("is_banned") in ("True", "1"):
                banned.append(int(key.rsplit(":", 1)[-1]))
        return banned

    def list_muted(self, chat_id: int) -> list[int]:
        """List muted users in a group."""
        pattern = f"bot:group:{chat_id}:user:*"
        muted = []
        for key in self.redis.keys(pattern):
            data = self.redis.hgetall(key)
            if data.get("is_muted") in ("True", "1"):
                muted.append(int(key.rsplit(":", 1)[-1]))
        return muted

    def list_global_banned(self) -> list[int]:
        """List all globally banned users."""
        banned = []
        for uid_str in self.redis.smembers("bot:users"):
            uid = int(uid_str)
            user = self.get_user(uid)
            if user.is_global_banned:
                banned.append(uid)
        return banned

    def list_global_muted(self) -> list[int]:
        """List all globally muted users."""
        muted = []
        for uid_str in self.redis.smembers("bot:users"):
            uid = int(uid_str)
            user = self.get_user(uid)
            if user.is_global_muted:
                muted.append(uid)
        return muted

    # ── Mute ──

    def mute_user(self, user_id: int, chat_id: int) -> None:
        self.redis.hset(self._group_user_key(chat_id, user_id), "is_muted", "True")

    def unmute_user(self, user_id: int, chat_id: int) -> None:
        self.redis.hset(self._group_user_key(chat_id, user_id), "is_muted", "False")

    def is_muted(self, user_id: int, chat_id: int) -> bool:
        val = self.redis.hget(self._group_user_key(chat_id, user_id), "is_muted")
        return val in ("True", "1")

    def global_mute(self, user_id: int) -> None:
        user = self.get_user(user_id)
        user.is_global_muted = True
        self.save_user(user)

    def global_unmute(self, user_id: int) -> None:
        user = self.get_user(user_id)
        user.is_global_muted = False
        self.save_user(user)

    # ── Warnings ──

    def add_warning(self, user_id: int, chat_id: int) -> int:
        """Add a warning. Returns the new count."""
        key = self._group_user_key(chat_id, user_id)
        current = self.redis.hget(key, "warnings")
        count = int(current) + 1 if current else 1
        self.redis.hset(key, "warnings", str(count))
        return count

    def get_warnings(self, user_id: int, chat_id: int) -> int:
        val = self.redis.hget(self._group_user_key(chat_id, user_id), "warnings")
        return int(val) if val else 0

    def reset_warnings(self, user_id: int, chat_id: int) -> None:
        self.redis.hset(self._group_user_key(chat_id, user_id), "warnings", "0")

    # ── Message count ──

    def increment_messages(self, user_id: int, chat_id: int) -> int:
        """Increment message count for user in group. Returns new count."""
        key = self._group_user_key(chat_id, user_id)
        current = self.redis.hget(key, "message_count")
        count = int(current) + 1 if current else 1
        self.redis.hset(key, "message_count", str(count))
        return count

    def get_message_count(self, user_id: int, chat_id: int) -> int:
        val = self.redis.hget(self._group_user_key(chat_id, user_id), "message_count")
        return int(val) if val else 0

    # ── Registered users set ──

    def register_user(self, user_id: int) -> None:
        self.redis.sadd("bot:users", str(user_id))

    def get_total_users(self) -> int:
        return self.redis.scard("bot:users")

    # ── User Stats ──

    def get_stat(self, user_id: int, chat_id: int, stat_name: str) -> int:
        """Get a user stat (edits, contacts, stickers, media, gems, etc.)."""
        val = self.redis.hget(self._group_user_key(chat_id, user_id), stat_name)
        return int(val) if val else 0

    def increment_stat(self, user_id: int, chat_id: int, stat_name: str) -> int:
        """Increment a user stat. Returns new count."""
        key = self._group_user_key(chat_id, user_id)
        current = self.redis.hget(key, stat_name)
        count = int(current) + 1 if current else 1
        self.redis.hset(key, stat_name, str(count))
        return count

    def reset_stat(self, user_id: int, chat_id: int, stat_name: str) -> None:
        """Reset a user stat to 0."""
        self.redis.hset(self._group_user_key(chat_id, user_id), stat_name, "0")

    def reset_messages(self, user_id: int, chat_id: int) -> None:
        """Reset message count for user in group."""
        self.redis.hset(self._group_user_key(chat_id, user_id), "message_count", "0")
