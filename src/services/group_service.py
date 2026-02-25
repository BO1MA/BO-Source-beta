 # ── Group Type (VIP/Free) ──
def set_group_type(self, chat_id: int, group_type: str) -> None:
    settings = self.get_settings(chat_id)
    settings.group_type = group_type
    self.save_settings(chat_id, settings)

def get_group_type(self, chat_id: int) -> str:
    return self.get_settings(chat_id).group_type
"""
Group service — CRUD for group settings, locks, custom commands stored in Redis.
Mirrors the group management features from bian.lua.
"""
from __future__ import annotations

import json
import logging

from src.models.group import Group, GroupSettings
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)

_PREFIX = "bot:group:"


class GroupService:
    def __init__(self) -> None:
        self.redis = RedisService()

    # ── Key builders ──

    def _group_key(self, chat_id: int) -> str:
        return f"{_PREFIX}{chat_id}"

    def _settings_key(self, chat_id: int) -> str:
        return f"{_PREFIX}{chat_id}:settings"

    def _locks_key(self, chat_id: int) -> str:
        return f"{_PREFIX}{chat_id}:locks"

    def _custom_cmd_key(self, chat_id: int) -> str:
        return f"{_PREFIX}{chat_id}:custom_commands"

    def _custom_reply_key(self, chat_id: int) -> str:
        return f"{_PREFIX}{chat_id}:custom_replies"

    def _global_cmd_key(self) -> str:
        return "bot:global:custom_commands"

    def _global_reply_key(self) -> str:
        return "bot:global:custom_replies"

    # ── Group CRUD ──

    def get_group(self, chat_id: int) -> Group:
        data = self.redis.hgetall(self._group_key(chat_id))
        if data:
            settings_raw = self.redis.get_json(self._settings_key(chat_id))
            group = Group(
                chat_id=chat_id,
                title=data.get("title", ""),
                username=data.get("username", ""),
                member_count=int(data.get("member_count", 0)),
            )
            if settings_raw:
                group.settings = GroupSettings.from_dict(settings_raw)
            return group
        return Group(chat_id=chat_id)

    def save_group(self, group: Group) -> None:
        key = self._group_key(group.chat_id)
        self.redis.hset(key, "chat_id", str(group.chat_id))
        self.redis.hset(key, "title", group.title)
        self.redis.hset(key, "username", group.username)
        self.redis.hset(key, "member_count", str(group.member_count))
        self.redis.set_json(self._settings_key(group.chat_id), group.settings.to_dict())

    def register_group(self, chat_id: int, title: str = "") -> Group:
        """Register or update a group."""
        group = self.get_group(chat_id)
        group.title = title or group.title
        self.save_group(group)
        self.redis.sadd("bot:groups", str(chat_id))
        return group

    def get_all_group_ids(self) -> list[int]:
        """Return all registered group IDs."""
        return [int(gid) for gid in self.redis.smembers("bot:groups")]

    def get_total_groups(self) -> int:
        return self.redis.scard("bot:groups")

    def remove_group(self, chat_id: int) -> None:
        self.redis.srem("bot:groups", str(chat_id))
        self.redis.delete(self._group_key(chat_id))
        self.redis.delete(self._settings_key(chat_id))
        self.redis.delete(self._locks_key(chat_id))

    # ── Settings ──

    def get_settings(self, chat_id: int) -> GroupSettings:
        return self.get_group(chat_id).settings

    def save_settings(self, chat_id: int, settings: GroupSettings) -> None:
        self.redis.set_json(self._settings_key(chat_id), settings.to_dict())

    def toggle_setting(self, chat_id: int, setting: str, value: bool) -> None:
        """Toggle a boolean setting by name."""
        settings = self.get_settings(chat_id)
        if hasattr(settings, setting):
            setattr(settings, setting, value)
            self.save_settings(chat_id, settings)

    # ── Locks ──

    def set_lock(self, chat_id: int, feature: str, punishment: str = "delete") -> None:
        """Lock a content type with a punishment."""
        self.redis.hset(self._locks_key(chat_id), feature, punishment)

    def remove_lock(self, chat_id: int, feature: str) -> None:
        """Unlock a content type."""
        self.redis.hdel(self._locks_key(chat_id), feature)

    def get_lock(self, chat_id: int, feature: str) -> str | None:
        """Get punishment type for a locked feature, or None if not locked."""
        return self.redis.hget(self._locks_key(chat_id), feature)

    def get_all_locks(self, chat_id: int) -> dict[str, str]:
        """Return all locks as {feature: punishment}."""
        return self.redis.hgetall(self._locks_key(chat_id))

    def is_locked(self, chat_id: int, feature: str) -> bool:
        return self.redis.hget(self._locks_key(chat_id), feature) is not None

    # ── Custom Commands ──

    def add_custom_command(self, chat_id: int, trigger: str, response: str) -> None:
        self.redis.hset(self._custom_cmd_key(chat_id), trigger, response)

    def delete_custom_command(self, chat_id: int, trigger: str) -> None:
        self.redis.hdel(self._custom_cmd_key(chat_id), trigger)

    def get_custom_command(self, chat_id: int, trigger: str) -> str | None:
        return self.redis.hget(self._custom_cmd_key(chat_id), trigger)

    def get_all_custom_commands(self, chat_id: int) -> dict[str, str]:
        return self.redis.hgetall(self._custom_cmd_key(chat_id))

    # ── Custom Replies ──

    def add_custom_reply(self, chat_id: int, trigger: str, response: str) -> None:
        self.redis.hset(self._custom_reply_key(chat_id), trigger, response)

    def delete_custom_reply(self, chat_id: int, trigger: str) -> None:
        self.redis.hdel(self._custom_reply_key(chat_id), trigger)

    def get_custom_reply(self, chat_id: int, trigger: str) -> str | None:
        return self.redis.hget(self._custom_reply_key(chat_id), trigger)

    def get_all_custom_replies(self, chat_id: int) -> dict[str, str]:
        return self.redis.hgetall(self._custom_reply_key(chat_id))

    # ── Global Custom Commands ──

    def add_global_command(self, trigger: str, response: str) -> None:
        self.redis.hset(self._global_cmd_key(), trigger, response)

    def get_global_command(self, trigger: str) -> str | None:
        return self.redis.hget(self._global_cmd_key(), trigger)

    def get_all_global_commands(self) -> dict[str, str]:
        return self.redis.hgetall(self._global_cmd_key())

    def add_global_reply(self, trigger: str, response: str) -> None:
        self.redis.hset(self._global_reply_key(), trigger, response)

    def get_global_reply(self, trigger: str) -> str | None:
        return self.redis.hget(self._global_reply_key(), trigger)

    def get_all_global_replies(self) -> dict[str, str]:
        return self.redis.hgetall(self._global_reply_key())

    # ── Flood tracking ──

    def track_flood(self, chat_id: int, user_id: int) -> int:
        """Increment flood counter. Auto-expires after interval. Returns count."""
        key = f"{_PREFIX}{chat_id}:flood:{user_id}"
        count = self.redis.incr(key)
        if count == 1:
            settings = self.get_settings(chat_id)
            self.redis.client.expire(key, settings.flood_interval)
        return count

    def get_flood_count(self, chat_id: int, user_id: int) -> int:
        val = self.redis.get(f"{_PREFIX}{chat_id}:flood:{user_id}")
        return int(val) if val else 0

    # ── Statistics ──

    def increment_total_messages(self) -> int:
        return self.redis.incr("bot:total_messages")

    def get_total_messages(self) -> int:
        val = self.redis.get("bot:total_messages")
        return int(val) if val else 0

    # ── Group Stats ──

    def get_stat(self, chat_id: int, stat_name: str) -> int:
        """Get a group stat."""
        val = self.redis.hget(self._group_key(chat_id), stat_name)
        return int(val) if val else 0

    def increment_stat(self, chat_id: int, stat_name: str) -> int:
        """Increment a group stat. Returns new count."""
        key = self._group_key(chat_id)
        current = self.redis.hget(key, stat_name)
        count = int(current) + 1 if current else 1
        self.redis.hset(key, stat_name, str(count))
        return count

    def reset_stat(self, chat_id: int, stat_name: str) -> None:
        """Reset a group stat to 0."""
        self.redis.hset(self._group_key(chat_id), stat_name, "0")

    # ── Delete operations for custom commands/replies ──

    def delete_global_command(self, trigger: str) -> None:
        """Delete a global custom command."""
        self.redis.hdel(self._global_cmd_key(), trigger)

    def delete_global_reply(self, trigger: str) -> None:
        """Delete a global custom reply."""
        self.redis.hdel(self._global_reply_key(), trigger)

    def delete_all_custom_commands(self, chat_id: int) -> None:
        """Delete all custom commands for a group."""
        self.redis.delete(self._custom_cmd_key(chat_id))

    def delete_all_global_commands(self) -> None:
        """Delete all global custom commands."""
        self.redis.delete(self._global_cmd_key())

    def delete_all_custom_replies(self, chat_id: int) -> None:
        """Delete all custom replies for a group."""
        self.redis.delete(self._custom_reply_key(chat_id))

    def delete_all_global_replies(self) -> None:
        """Delete all global custom replies."""
        self.redis.delete(self._global_reply_key())
