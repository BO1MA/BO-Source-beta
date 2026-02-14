"""
Inline keyboard builders for various bot menus.
"""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.constants.commands import LOCK_FEATURES


def build_inline_keyboard(
    buttons: list[tuple[str, str]],
    columns: int = 2,
) -> InlineKeyboardMarkup:
    """Build an inline keyboard from a list of (text, callback_data) tuples."""
    keyboard = []
    row = []
    for text, data in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=data))
        if len(row) >= columns:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def build_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Build the group settings toggle keyboard with current state indicators."""
    from src.services.group_service import GroupService
    group_svc = GroupService()
    settings = group_svc.get_settings(chat_id)

    def icon(enabled: bool) -> str:
        return "\u2705" if enabled else "\u274C"

    buttons = [
        (f"{icon(settings.welcome_enabled)} الترحيب", f"toggle:{chat_id}:welcome_enabled"),
        (f"{icon(settings.farewell_enabled)} المغادره", f"toggle:{chat_id}:farewell_enabled"),
        (f"{icon(settings.games_enabled)} الالعاب", f"toggle:{chat_id}:games_enabled"),
        (f"{icon(settings.broadcast_enabled)} الاذاعه", f"toggle:{chat_id}:broadcast_enabled"),
        (f"{icon(settings.tag_enabled)} التاغ", f"toggle:{chat_id}:tag_enabled"),
        (f"{icon(settings.force_subscribe_enabled)} الاشتراك الاجباري", f"toggle:{chat_id}:force_subscribe_enabled"),
        (f"{icon(settings.protection_enabled)} الحمايه", f"toggle:{chat_id}:protection_enabled"),
    ]
    return build_inline_keyboard(buttons, columns=2)


def build_lock_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Build the lock/unlock feature selection keyboard."""
    buttons = []
    for feature_key, arabic_name in LOCK_FEATURES.items():
        buttons.append((arabic_name, f"lock:{chat_id}:{feature_key}"))
    return build_inline_keyboard(buttons, columns=3)


def build_games_keyboard() -> InlineKeyboardMarkup:
    """Build the games menu keyboard."""
    buttons = [
        ("🎯 السمايلات", "game:emoji"),
        ("🔢 تخمين", "game:guess"),
        ("⚡ الاسرع", "game:fastest"),
        ("🔤 الحروف", "game:letters"),
        ("❓ حزوره", "game:riddle"),
        ("😃 معاني", "game:meaning"),
        ("💍 محيبس", "game:ring"),
        ("🔍 المختلف", "game:different"),
        ("➕ رياضيات", "game:math"),
        ("🇬🇧 انكليزي", "game:english"),
        ("📜 امثله", "game:proverb"),
        ("🔀 كلمات", "game:scramble"),
    ]
    return build_inline_keyboard(buttons, columns=3)


def build_yt_keyboard(query: str) -> InlineKeyboardMarkup:
    """Build YouTube download options keyboard."""
    buttons = [
        ("\U0001F3B5 MP3", f"yt:mp3:{query}"),
        ("\U0001F3AC MP4", f"yt:mp4:{query}"),
    ]
    return build_inline_keyboard(buttons, columns=2)


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main commands menu."""
    buttons = [
        ("\U0001F4CB الاوامر", "menu:commands"),
        ("\U0001F3AE الالعاب", "menu:games"),
        ("\U0001F4E2 الاذاعه", "menu:broadcast"),
        ("\u2699\uFE0F الاعدادات", "menu:settings"),
        ("\U0001F512 الحمايه", "menu:protection"),
        ("\U0001F464 المطور", "menu:developer"),
    ]
    return build_inline_keyboard(buttons, columns=2)


def build_protection_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Build the protection settings keyboard (lock overview)."""
    buttons = [
        ("\U0001F512 قفل", f"protection:lock:{chat_id}"),
        ("\U0001F513 فتح", f"protection:unlock:{chat_id}"),
        ("\U0001F4CB القفل الحالي", f"protection:list:{chat_id}"),
    ]
    return build_inline_keyboard(buttons, columns=2)
