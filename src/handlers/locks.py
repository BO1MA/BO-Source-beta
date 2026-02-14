"""
Locks handler — content filtering and auto-moderation.
Based on GetSetieng from bian.lua. Locks specific content types
and applies punishments (delete, warn, kick, mute, ban).
Supports Arabic punishment suffixes: بالتقيد, بالطرد, بالكتم, بالحظر.
Also includes profanity filter and Persian character filter.
"""
import re
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

from src.config import Config
from src.constants.messages import (
    MSG_LOCKED, MSG_UNLOCKED, MSG_NO_PERMISSION, MSG_BOT_NOT_ADMIN,
    MSG_WARNED, MSG_KICKED, MSG_MUTED, MSG_BANNED, MSG_WARN_LIMIT,
    contains_bad_word,
)
from src.constants.commands import LOCK_FEATURES, LOCK_PUNISHMENTS, LOCK_ALIASES
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.utils.text_utils import (
    get_message_content_type, contains_link, contains_hashtag,
    is_arabic_only, is_english_only, is_long_message, extract_command_arg,
)
from src.utils.api_helpers import (
    is_bot_admin, delete_message_safe, kick_member, mute_member, ban_member,
)
from src.utils.keyboard import build_lock_keyboard, build_protection_keyboard

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()

# Arabic punishment suffix → punishment key
PUNISHMENT_SUFFIXES = {
    "بالتقيد": "mute",
    "بالكتم": "mute",
    "بالطرد": "kick",
    "بالحظر": "ban",
    "بالتحذير": "warn",
    "بالحذف": "delete",
}

# Persian character range for filter
PERSIAN_PATTERN = re.compile(r'[\u0600-\u06FF]*[\u067E\u0686\u0698\u06AF\u06CC\u06A9]')


def _parse_lock_args(text: str):
    """Parse 'قفل <feature> [punishment]' supporting Arabic suffixes.
    Returns (feature_key, punishment_key) or (None, None)."""
    arg = text.replace("قفل", "", 1).strip()
    if not arg:
        return None, None

    # Check for Arabic suffix punishment patterns
    punishment_key = "delete"  # default
    for suffix, pkey in PUNISHMENT_SUFFIXES.items():
        if arg.endswith(suffix):
            punishment_key = pkey
            arg = arg[:-(len(suffix))].strip()
            break

    # Also check for regular punishment words
    parts = arg.split()
    if len(parts) > 1:
        last = parts[-1]
        for key, arabic in LOCK_PUNISHMENTS.items():
            if last == arabic or last == key:
                punishment_key = key
                parts = parts[:-1]
                break
        arg = " ".join(parts)

    # Match feature (check LOCK_ALIASES first, then LOCK_FEATURES)
    feature_key = LOCK_ALIASES.get(arg)
    if not feature_key:
        for key, arabic in LOCK_FEATURES.items():
            if arg == arabic or arg == key:
                feature_key = key
                break

    return feature_key, punishment_key


@group_only
async def handle_lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lock a content type: قفل <feature> [punishment] or قفل <feature>بالتقيد"""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    feature_key, punishment_key = _parse_lock_args(text)

    if not feature_key:
        # No feature specified — show interactive keyboard
        arg = text.replace("قفل", "", 1).strip()
        if arg:
            await update.message.reply_text(f"✯ لا يوجد ميزه باسم: {arg}")
        else:
            await update.message.reply_text(
                "✯ اختر ما تريد قفله:",
                reply_markup=build_lock_keyboard(chat_id),
            )
        return

    group_svc.set_lock(chat_id, feature_key, punishment_key)
    await update.message.reply_text(
        MSG_LOCKED.format(feature=LOCK_FEATURES[feature_key])
        + f"\n✯ العقوبه: {LOCK_PUNISHMENTS[punishment_key]}"
    )


@group_only
async def handle_unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unlock a content type: فتح <feature>"""
    chat_id = update.effective_chat.id
    from_user = update.effective_user
    text = (update.message.text or "").strip()

    if not user_svc.is_group_admin(from_user.id, chat_id) and from_user.id != Config.SUDO_ID:
        await update.message.reply_text(MSG_NO_PERMISSION)
        return

    feature_name = text.replace("فتح", "", 1).strip()
    if not feature_name:
        await update.message.reply_text(
            "✯ اختر ما تريد فتحه:",
            reply_markup=build_lock_keyboard(chat_id),
        )
        return

    feature_key = LOCK_ALIASES.get(feature_name)
    if not feature_key:
        for key, arabic in LOCK_FEATURES.items():
            if feature_name == arabic or feature_name == key:
                feature_key = key
                break

    if not feature_key:
        await update.message.reply_text(f"✯ لا يوجد ميزه باسم: {feature_name}")
        return

    group_svc.remove_lock(chat_id, feature_key)
    await update.message.reply_text(MSG_UNLOCKED.format(feature=LOCK_FEATURES[feature_key]))


@group_only
async def handle_protection_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show protection settings / current locks."""
    chat_id = update.effective_chat.id
    locks = group_svc.get_all_locks(chat_id)

    if locks:
        lines = ["✯ اعدادات الحمايه 🛡:"]
        for feature, punishment in locks.items():
            arabic_feature = LOCK_FEATURES.get(feature, feature)
            arabic_punishment = LOCK_PUNISHMENTS.get(punishment, punishment)
            lines.append(f"🔒 {arabic_feature} → {arabic_punishment}")
        text = "\n".join(lines)
    else:
        text = "✯ لا توجد اقفال مفعله"

    await update.message.reply_text(text, reply_markup=build_protection_keyboard(chat_id))


async def handle_lock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle lock/unlock button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split(":")
    if len(parts) != 3:
        return

    chat_id = int(parts[1])
    feature = parts[2]

    if group_svc.is_locked(chat_id, feature):
        group_svc.remove_lock(chat_id, feature)
        await query.message.reply_text(
            MSG_UNLOCKED.format(feature=LOCK_FEATURES.get(feature, feature))
        )
    else:
        group_svc.set_lock(chat_id, feature, "delete")
        await query.message.reply_text(
            MSG_LOCKED.format(feature=LOCK_FEATURES.get(feature, feature))
        )


async def handle_protection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle protection menu button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split(":")
    if len(parts) != 3:
        return

    action = parts[1]
    chat_id = int(parts[2])

    if action == "lock":
        await query.message.reply_text(
            "✯ اختر ما تريد قفله:",
            reply_markup=build_lock_keyboard(chat_id),
        )
    elif action == "unlock":
        await query.message.reply_text(
            "✯ اختر ما تريد فتحه:",
            reply_markup=build_lock_keyboard(chat_id),
        )
    elif action == "list":
        locks = group_svc.get_all_locks(chat_id)
        if locks:
            lines = ["✯ الاقفال الحاليه:"]
            for f, p in locks.items():
                lines.append(f"🔒 {LOCK_FEATURES.get(f, f)} → {LOCK_PUNISHMENTS.get(p, p)}")
            await query.message.reply_text("\n".join(lines))
        else:
            await query.message.reply_text("✯ لا توجد اقفال")


def _contains_persian(text: str) -> bool:
    """Check if text contains Persian-specific characters."""
    return bool(PERSIAN_PATTERN.search(text))


async def enforce_locks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check every message against active locks and apply punishment.
    This runs at a high priority group number to intercept early."""
    if not update.message or not update.effective_chat:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    if not update.effective_user:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Skip admins and sudo
    if user_svc.is_group_admin(user_id, chat_id) or user_svc.is_sudo(user_id):
        return

    # Get all locks for this group
    locks = group_svc.get_all_locks(chat_id)
    if not locks:
        return

    message = update.message
    content_type = get_message_content_type(message)

    violated_feature = None

    # ── Check content type locks (photo, video, sticker, etc.) ──
    if content_type and content_type in locks:
        violated_feature = content_type

    # ── Check forwarded messages ──
    elif message.forward_date and "forward" in locks:
        violated_feature = "forward"

    # ── Check edited messages ──
    # (edit lock is checked separately in handle_edited_message)

    # ── Check new member (bot lock) ──
    elif message.new_chat_members:
        if "bot" in locks:
            for member in message.new_chat_members:
                if member.is_bot and member.id != context.bot.id:
                    # Kick the bot
                    try:
                        await kick_member(context.bot, chat_id, member.id)
                        await context.bot.send_message(
                            chat_id, f"✯ تم طرد البوت {member.first_name} (البوتات مقفله) 🤖🔒"
                        )
                    except Exception:
                        pass
            return

    # ── Text-based locks ──
    elif message.text:
        text = message.text

        if "link" in locks and contains_link(text):
            violated_feature = "link"
        elif "hashtag" in locks and contains_hashtag(text):
            violated_feature = "hashtag"
        elif "arabic_only" in locks and not is_arabic_only(text):
            violated_feature = "arabic_only"
        elif "english_only" in locks and not is_english_only(text):
            violated_feature = "english_only"
        elif "long_message" in locks and is_long_message(text):
            violated_feature = "long_message"
        elif "command" in locks and text.startswith("/"):
            violated_feature = "command"
        elif "profanity" in locks and contains_bad_word(text):
            violated_feature = "profanity"
        elif "persian" in locks and _contains_persian(text):
            violated_feature = "persian"

    # ── Flood check ──
    if not violated_feature and "flood" in locks:
        settings = group_svc.get_settings(chat_id)
        flood_count = group_svc.track_flood(chat_id, user_id)
        if flood_count > settings.flood_limit:
            violated_feature = "flood"

    if not violated_feature:
        return

    punishment = locks[violated_feature]

    if not await is_bot_admin(context.bot, chat_id):
        return

    # Always delete the offending message
    await delete_message_safe(context.bot, chat_id, message.message_id)

    target = user_svc.get_user(user_id)
    feature_name = LOCK_FEATURES.get(violated_feature, violated_feature)

    if punishment == "delete":
        pass  # Already deleted
    elif punishment == "warn":
        settings = group_svc.get_settings(chat_id)
        count = user_svc.add_warning(user_id, chat_id)
        if count >= settings.max_warnings:
            user_svc.reset_warnings(user_id, chat_id)
            await kick_member(context.bot, chat_id, user_id)
            await context.bot.send_message(
                chat_id, MSG_WARN_LIMIT.format(name=target.full_name)
            )
        else:
            await context.bot.send_message(
                chat_id,
                MSG_WARNED.format(name=target.full_name, count=count, max=settings.max_warnings)
                + f"\n✯ السبب: {feature_name}"
            )
    elif punishment == "kick":
        await kick_member(context.bot, chat_id, user_id)
        await context.bot.send_message(
            chat_id, MSG_KICKED.format(name=target.full_name) + f"\n✯ السبب: {feature_name}"
        )
    elif punishment == "mute":
        user_svc.mute_user(user_id, chat_id)
        await mute_member(context.bot, chat_id, user_id)
        await context.bot.send_message(
            chat_id, f"✯ تم كتم {target.full_name} 🔇\n✯ السبب: {feature_name}"
        )
    elif punishment == "ban":
        user_svc.ban_user(user_id, chat_id)
        await ban_member(context.bot, chat_id, user_id)
        await context.bot.send_message(
            chat_id, MSG_BANNED.format(name=target.full_name) + f"\n✯ السبب: {feature_name}"
        )


async def enforce_edit_lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """If 'edit' lock is active, delete edited messages from non-admins."""
    if not update.edited_message or not update.effective_chat:
        return
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    if not update.effective_user:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_svc.is_group_admin(user_id, chat_id) or user_svc.is_sudo(user_id):
        return

    if not group_svc.is_locked(chat_id, "edit"):
        return

    if await is_bot_admin(context.bot, chat_id):
        await delete_message_safe(context.bot, chat_id, update.edited_message.message_id)


def register(app: Application) -> None:
    """Register lock handlers."""
    G = filters.ChatType.GROUPS

    # Lock enforcement — highest priority (group=1) to intercept before other handlers
    app.add_handler(MessageHandler(filters.ALL & G, enforce_locks), group=1)

    # Edit lock enforcement
    app.add_handler(MessageHandler(filters.UpdateType.EDITED_MESSAGE & G, enforce_edit_lock), group=1)

    # Lock/Unlock commands
    app.add_handler(MessageHandler(filters.Regex("^قفل") & G, handle_lock_command), group=6)
    app.add_handler(MessageHandler(filters.Regex("^فتح") & G, handle_unlock_command), group=6)
    app.add_handler(MessageHandler(
        filters.Regex("^(اعدادات الحمايه|الحمايه)$") & G,
        handle_protection_settings,
    ), group=6)

    # Callback queries
    app.add_handler(CallbackQueryHandler(handle_lock_callback, pattern="^lock:"))
    app.add_handler(CallbackQueryHandler(handle_protection_callback, pattern="^protection:"))
