"""
Text utility functions used across the bot.
"""
from __future__ import annotations

import re
from telegram import Message, Update


def extract_user_id(message: Message) -> int | None:
    """Extract target user ID from a reply or from message text."""
    # If replying to someone
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id

    # Try to extract numeric ID from text
    if message.text:
        parts = message.text.strip().split()
        for part in parts:
            if part.isdigit():
                return int(part)
            # Handle @username mentioned in text (can't resolve to ID directly)
    return None


def extract_command_arg(text: str) -> str:
    """Extract the argument after the command trigger.
    e.g. 'حظر 12345' -> '12345'
    e.g. 'اضف امر hello' -> 'hello'
    """
    parts = text.strip().split(maxsplit=1)
    return parts[1] if len(parts) > 1 else ""


def reverse_text(text: str) -> str:
    """Reverse a string (for the العكس command)."""
    return text[::-1]


def contains_link(text: str) -> bool:
    """Check if text contains a URL."""
    url_pattern = re.compile(
        r'https?://[^\s<>"]+|www\.[^\s<>"]+|t\.me/[^\s<>"]+'
    )
    return bool(url_pattern.search(text))


def contains_hashtag(text: str) -> bool:
    return bool(re.search(r'#\w+', text))


def is_arabic_only(text: str) -> bool:
    """Check if text contains only Arabic characters and common punctuation."""
    cleaned = re.sub(r'[\s\d.,!?؟،؛:()\[\]{}\-_]', '', text)
    if not cleaned:
        return True
    return bool(re.match(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+$', cleaned))


def is_english_only(text: str) -> bool:
    """Check if text contains only Latin characters and common punctuation."""
    cleaned = re.sub(r'[\s\d.,!?:;()\[\]{}\-_]', '', text)
    if not cleaned:
        return True
    return bool(re.match(r'^[a-zA-Z]+$', cleaned))


def is_long_message(text: str, limit: int = 4096) -> bool:
    return len(text) > limit


def get_message_content_type(message: Message) -> str | None:
    """Identify what kind of media/content a message contains."""
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.sticker:
        return "sticker"
    if message.animation:
        return "animation"
    if message.document:
        return "document"
    if message.voice:
        return "voice"
    if message.video_note:
        return "video_note"
    if message.audio:
        return "audio"
    if message.contact:
        return "contact"
    if message.location:
        return "location"
    if message.poll:
        return "poll"
    if message.dice:
        return "dice"
    if message.game:
        return "game"
    if message.forward_date:
        return "forward"
    if message.via_bot:
        return "inline"
    if message.text:
        text = message.text
        if contains_link(text):
            return "link"
        if contains_hashtag(text):
            return "hashtag"
    return None


def format_user_list(users: list, title: str) -> str:
    """Format a list of users for display."""
    if not users:
        return f"\u2756 {title}:\n\u2756 لا يوجد"
    lines = [f"\u2756 {title}:"]
    for i, user in enumerate(users, 1):
        name = getattr(user, 'full_name', str(user))
        uid = getattr(user, 'user_id', '')
        lines.append(f"{i}. {name} [{uid}]")
    return "\n".join(lines)
