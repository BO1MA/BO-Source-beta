"""
User model — represents a bot user with role, stats, and status.
"""
from dataclasses import dataclass, field
from src.constants.roles import ROLE_MEMBER


@dataclass
class User:
    user_id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    role: int = ROLE_MEMBER
    message_count: int = 0
    warnings: int = 0
    is_banned: bool = False
    is_global_banned: bool = False
    is_muted: bool = False
    is_global_muted: bool = False

    @property
    def full_name(self) -> str:
        """Return the user's full display name."""
        parts = [self.first_name]
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts) or str(self.user_id)

    @property
    def mention(self) -> str:
        """Return a Telegram HTML mention for the user."""
        return f'<a href="tg://user?id={self.user_id}">{self.full_name}</a>'

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "role": self.role,
            "message_count": self.message_count,
            "warnings": self.warnings,
            "is_banned": self.is_banned,
            "is_global_banned": self.is_global_banned,
            "is_muted": self.is_muted,
            "is_global_muted": self.is_global_muted,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            user_id=int(data.get("user_id", 0)),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            username=data.get("username", ""),
            role=int(data.get("role", ROLE_MEMBER)),
            message_count=int(data.get("message_count", 0)),
            warnings=int(data.get("warnings", 0)),
            is_banned=data.get("is_banned", False) in (True, "True", "1", 1),
            is_global_banned=data.get("is_global_banned", False) in (True, "True", "1", 1),
            is_muted=data.get("is_muted", False) in (True, "True", "1", 1),
            is_global_muted=data.get("is_global_muted", False) in (True, "True", "1", 1),
        )
