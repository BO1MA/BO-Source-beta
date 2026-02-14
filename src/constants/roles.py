"""
Role hierarchy for the bot (from highest to lowest privilege).
Mirrors the Lua bot's Arabic role system.
"""

# Role levels — lower number = higher privilege
ROLE_MAIN_DEVELOPER = 1       # المطور الاساسي
ROLE_SECONDARY_DEVELOPER = 2  # المطور الثانوي
ROLE_ASSISTANT = 22           # المساعد
ROLE_DEVELOPER = 3            # المطور
ROLE_OWNER = 44               # المالك
ROLE_MAIN_CREATOR = 4         # المنشئ الاساسي
ROLE_CREATOR = 5              # المنشئ
ROLE_MANAGER = 6              # المدير
ROLE_ADMIN = 7                # الادمن
ROLE_VIP = 8                  # المميز
ROLE_MEMBER = 99              # العضو

ROLE_NAMES = {
    ROLE_MAIN_DEVELOPER: "المطور الاساسي",
    ROLE_SECONDARY_DEVELOPER: "المطور الثانوي",
    ROLE_ASSISTANT: "المساعد",
    ROLE_DEVELOPER: "المطور",
    ROLE_OWNER: "المالك",
    ROLE_MAIN_CREATOR: "المنشئ الاساسي",
    ROLE_CREATOR: "المنشئ",
    ROLE_MANAGER: "المدير",
    ROLE_ADMIN: "الادمن",
    ROLE_VIP: "المميز",
    ROLE_MEMBER: "العضو",
}

ROLE_NAMES_EN = {
    ROLE_MAIN_DEVELOPER: "Main Developer",
    ROLE_SECONDARY_DEVELOPER: "Secondary Developer",
    ROLE_ASSISTANT: "Assistant",
    ROLE_DEVELOPER: "Developer",
    ROLE_OWNER: "Owner",
    ROLE_MAIN_CREATOR: "Main Creator",
    ROLE_CREATOR: "Creator",
    ROLE_MANAGER: "Manager",
    ROLE_ADMIN: "Admin",
    ROLE_VIP: "VIP",
    ROLE_MEMBER: "Member",
}

# Ordered hierarchy for comparison (index order = rank order)
ROLE_HIERARCHY = [
    ROLE_MAIN_DEVELOPER,
    ROLE_SECONDARY_DEVELOPER,
    ROLE_ASSISTANT,
    ROLE_DEVELOPER,
    ROLE_OWNER,
    ROLE_MAIN_CREATOR,
    ROLE_CREATOR,
    ROLE_MANAGER,
    ROLE_ADMIN,
    ROLE_VIP,
    ROLE_MEMBER,
]

# Roles that are considered "sudo" (bot-wide, not per-group)
SUDO_ROLES = {ROLE_MAIN_DEVELOPER, ROLE_SECONDARY_DEVELOPER, ROLE_ASSISTANT, ROLE_DEVELOPER}

# Roles that can manage a group
GROUP_ADMIN_ROLES = {
    ROLE_OWNER, ROLE_MAIN_CREATOR, ROLE_CREATOR, ROLE_MANAGER, ROLE_ADMIN
}


def get_role_name(role_level: int, lang: str = "ar") -> str:
    """Return the display name for a role level."""
    names = ROLE_NAMES_EN if lang == "en" else ROLE_NAMES
    return names.get(role_level, "عضو" if lang == "ar" else "Member")


def get_role_level_by_name(name: str) -> int:
    """Lookup role level by its Arabic name."""
    for level, role_name in ROLE_NAMES.items():
        if role_name == name:
            return level
    return ROLE_MEMBER


def is_higher_role(role_a: int, role_b: int) -> bool:
    """Return True if role_a is higher (more privileged) than role_b."""
    try:
        return ROLE_HIERARCHY.index(role_a) < ROLE_HIERARCHY.index(role_b)
    except ValueError:
        return False
