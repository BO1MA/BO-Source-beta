"""
Group model — represents a Telegram group with its settings and lock state.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GroupSettings:
    """All toggle-able settings for a group (mirrors GetSetieng in Lua)."""
    welcome_enabled: bool = True
    farewell_enabled: bool = False
    games_enabled: bool = True
    tag_enabled: bool = True
    broadcast_enabled: bool = True
    force_subscribe_enabled: bool = False
    force_subscribe_channel: str = ""
    protection_enabled: bool = False
    # Lock states — key = lock feature name, value = punishment type
    locks: dict[str, str] = field(default_factory=dict)
    # Custom welcome text
    welcome_text: str = ""
    # Group rules
    rules_text: str = ""
    # Flood settings
    flood_limit: int = 10
    flood_interval: int = 5  # seconds
    # Warn settings
    max_warnings: int = 3

    def to_dict(self) -> dict:
        return {
            "welcome_enabled": self.welcome_enabled,
            "farewell_enabled": self.farewell_enabled,
            "games_enabled": self.games_enabled,
            "tag_enabled": self.tag_enabled,
            "broadcast_enabled": self.broadcast_enabled,
            "force_subscribe_enabled": self.force_subscribe_enabled,
            "force_subscribe_channel": self.force_subscribe_channel,
            "protection_enabled": self.protection_enabled,
            "locks": self.locks,
            "welcome_text": self.welcome_text,
            "rules_text": self.rules_text,
            "flood_limit": self.flood_limit,
            "flood_interval": self.flood_interval,
            "max_warnings": self.max_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GroupSettings":
        return cls(
            welcome_enabled=_bool(data.get("welcome_enabled", True)),
            farewell_enabled=_bool(data.get("farewell_enabled", False)),
            games_enabled=_bool(data.get("games_enabled", True)),
            tag_enabled=_bool(data.get("tag_enabled", True)),
            broadcast_enabled=_bool(data.get("broadcast_enabled", True)),
            force_subscribe_enabled=_bool(data.get("force_subscribe_enabled", False)),
            force_subscribe_channel=data.get("force_subscribe_channel", ""),
            protection_enabled=_bool(data.get("protection_enabled", False)),
            locks=data.get("locks", {}),
            welcome_text=data.get("welcome_text", ""),
            rules_text=data.get("rules_text", ""),
            flood_limit=int(data.get("flood_limit", 10)),
            flood_interval=int(data.get("flood_interval", 5)),
            max_warnings=int(data.get("max_warnings", 3)),
        )


@dataclass
class Group:
    chat_id: int
    title: str = ""
    username: str = ""
    member_count: int = 0
    settings: GroupSettings = field(default_factory=GroupSettings)

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "title": self.title,
            "username": self.username,
            "member_count": self.member_count,
            "settings": self.settings.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        settings_data = data.get("settings", {})
        return cls(
            chat_id=int(data.get("chat_id", 0)),
            title=data.get("title", ""),
            username=data.get("username", ""),
            member_count=int(data.get("member_count", 0)),
            settings=GroupSettings.from_dict(settings_data) if isinstance(settings_data, dict) else GroupSettings(),
        )


def _bool(value: Any) -> bool:
    """Convert various truthy representations to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)
