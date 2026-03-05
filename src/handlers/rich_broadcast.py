"""
Enhanced broadcast system with inline keyboard buttons support.
Allows broadcasting messages with custom buttons (text + URL pairs).
"""

import asyncio
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError

from src.config import Config
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
redis_svc = RedisService()


async def handle_rich_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to broadcast with inline buttons."""
    if update.effective_user.id != Config.SUDO_ID:
        await update.message.reply_text("✯ أنت لا تملك صلاحيات الوصول لهذا الأمر")
        return
    
    text = (update.message.text or "").strip()
    
    if not text.startswith("/richbroadcast"):
        return
    
    await update.message.reply_text(
        """✯ الإذاعة الغنية مع الأزرار 🎯

**الاستخدام:**
1. أرسل الرسالة التي تريد بثها
2. أضف الأزرار بهذا الصيغة في رسالة منفصلة:

```
زر 1 = https://link1.com
زر 2 = https://link2.com
```

أو للأزرار المتعددة بصف واحد:
```
زر A = https://link1.com | زر B = https://link2.com
```

اكتب `/startrich` لبدء الإذاعة""",
        parse_mode="Markdown"
    )


async def handle_rich_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start rich broadcast process."""
    if update.effective_user.id != Config.SUDO_ID:
        await update.message.reply_text("✯ أنت لا تملك صلاحيات الوصول")
        return
    
    # Set state for capturing message
    redis_svc.set(
        f"broadcast_state:{update.effective_user.id}",
        json.dumps({
            "stage": "message",
            "timestamp": int(update.message.date)
        }),
        ex=600  # 10 minutes
    )
    
    await update.message.reply_text(
        "✯ الآن أرسل الرسالة التي تريد بثها\n"
        "(يمكنك إرسال نص، صورة، فيديو، إلخ)"
    )


async def handle_broadcast_message_capture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Capture message for broadcast."""
    user_id = update.effective_user.id
    
    if user_id != Config.SUDO_ID:
        return
    
    # Check if in broadcast mode
    state_data = redis_svc.get(f"broadcast_state:{user_id}")
    if not state_data:
        return
    
    try:
        state = json.loads(state_data)
    except:
        return
    
    if state.get("stage") != "message":
        return
    
    # Skip if it's a command
    if (update.message.text or "").startswith("/"):
        return
    
    # Store the message to broadcast
    message_data = {
        "has_text": bool(update.message.text),
        "text": update.message.text or update.message.caption or "",
        "has_photo": bool(update.message.photo),
        "photo_id": update.message.photo[-1].file_id if update.message.photo else None,
        "has_video": bool(update.message.video),
        "video_id": update.message.video.file_id if update.message.video else None,
        "has_document": bool(update.message.document),
        "document_id": update.message.document.file_id if update.message.document else None,
        "message_id": update.message.message_id,
        "chat_id": update.effective_chat.id,
    }
    
    redis_svc.set(
        f"broadcast_message:{user_id}",
        json.dumps(message_data),
        ex=600
    )
    
    # Update state to buttons
    state["stage"] = "buttons"
    redis_svc.set(
        f"broadcast_state:{user_id}",
        json.dumps(state),
        ex=600
    )
    
    await update.message.reply_text(
        "✅ تم حفظ الرسالة\n\n"
        "الآن أرسل الأزرار (أو اكتب 'بدون' إذا لم تريد أزرار)\n\n"
        "الصيغة:\n"
        "`زر 1 = https://link1.com`\n"
        "`زر 2 = https://link2.com`\n\n"
        "أو بصف واحد:\n"
        "`زر 1 = https://link1.com | زر 2 = https://link2.com`",
        parse_mode="Markdown"
    )


async def handle_broadcast_buttons_capture(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Capture buttons for broadcast."""
    user_id = update.effective_user.id
    
    if user_id != Config.SUDO_ID:
        return
    
    # Check if in buttons stage
    state_data = redis_svc.get(f"broadcast_state:{user_id}")
    if not state_data:
        return
    
    try:
        state = json.loads(state_data)
    except:
        return
    
    if state.get("stage") != "buttons":
        return
    
    text = (update.message.text or "").strip()
    
    if text.lower() == "بدون":
        # No buttons
        redis_svc.set(
            f"broadcast_buttons:{user_id}",
            json.dumps([]),
            ex=600
        )
    else:
        # Parse buttons
        buttons = parse_buttons(text)
        if not buttons:
            await update.message.reply_text("❌ صيغة الأزرار غير صحيحة")
            return
        
        redis_svc.set(
            f"broadcast_buttons:{user_id}",
            json.dumps(buttons),
            ex=600
        )
    
    # Confirm and ask for target
    await update.message.reply_text(
        "✅ تم حفظ الأزرار\n\n"
        "اختر المستقبل:\n"
        "اكتب: `all` - لجميع المستخدمين\n"
        "اكتب: `groups` - للمجموعات فقط",
        parse_mode="Markdown"
    )
    
    state["stage"] = "target"
    redis_svc.set(
        f"broadcast_state:{user_id}",
        json.dumps(state),
        ex=600
    )


async def handle_broadcast_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute the broadcast."""
    user_id = update.effective_user.id
    
    if user_id != Config.SUDO_ID:
        return
    
    # Check if in target stage
    state_data = redis_svc.get(f"broadcast_state:{user_id}")
    if not state_data:
        return
    
    try:
        state = json.loads(state_data)
    except:
        return
    
    if state.get("stage") != "target":
        return
    
    target = (update.message.text or "").strip().lower()
    
    if target not in ("all", "groups"):
        await update.message.reply_text("❌ خيار غير صحيح (all أو groups)")
        return
    
    # Get message and buttons
    msg_data = json.loads(redis_svc.get(f"broadcast_message:{user_id}") or "{}")
    buttons_data = json.loads(redis_svc.get(f"broadcast_buttons:{user_id}") or "[]")
    
    if not msg_data:
        await update.message.reply_text("❌ لم أجد الرسالة المحفوظة")
        return
    
    # Build reply markup
    reply_markup = None
    if buttons_data:
        keyboard = []
        for button_row in buttons_data:
            row = []
            for btn in button_row:
                row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✯ جاري البث إلى {target} المستقبلين... ⏳"
    )
    
    success = 0
    failed = 0
    
    # Get recipients
    recipients = []
    if target == "all":
        recipients = redis_svc.smembers("bot:users")
    else:  # groups
        recipients = redis_svc.smembers("bot:groups")
    
    for recipient_id in recipients:
        try:
            recipient_id = int(recipient_id)
            
            if msg_data.get("has_photo"):
                await context.bot.send_photo(
                    chat_id=recipient_id,
                    photo=msg_data["photo_id"],
                    caption=msg_data["text"],
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif msg_data.get("has_video"):
                await context.bot.send_video(
                    chat_id=recipient_id,
                    video=msg_data["video_id"],
                    caption=msg_data["text"],
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif msg_data.get("has_document"):
                await context.bot.send_document(
                    chat_id=recipient_id,
                    document=msg_data["document_id"],
                    caption=msg_data["text"],
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            else:
                await context.bot.send_message(
                    chat_id=recipient_id,
                    text=msg_data["text"],
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            
            success += 1
            await asyncio.sleep(0.05)
        except TelegramError as e:
            logger.warning(f"Broadcast failed for {recipient_id}: {e}")
            failed += 1
    
    # Cleanup
    redis_svc.delete(f"broadcast_state:{user_id}")
    redis_svc.delete(f"broadcast_message:{user_id}")
    redis_svc.delete(f"broadcast_buttons:{user_id}")
    
    await update.message.reply_text(
        f"✅ اكتمل البث!\n\n"
        f"✓ نجح: {success}\n"
        f"✗ فشل: {failed}"
    )


def parse_buttons(text: str) -> list:
    """
    Parse button text into 2D array.
    Format: "button1 = url1 | button2 = url2" (same row)
    or: "button1 = url1\nbutton2 = url2" (different rows)
    """
    rows = []
    
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        row = []
        # Split by | for same row
        buttons_in_row = line.split("|")
        
        for btn_text in buttons_in_row:
            btn_text = btn_text.strip()
            if "=" not in btn_text:
                return None  # Invalid format
            
            parts = btn_text.split("=", 1)
            if len(parts) != 2:
                return None
            
            btn_label = parts[0].strip()
            btn_url = parts[1].strip()
            
            if not btn_label or not btn_url:
                return None
            
            row.append({"text": btn_label, "url": btn_url})
        
        if row:
            rows.append(row)
    
    return rows if rows else None


def register(app: Application) -> None:
    """Register rich broadcast handlers."""
    app.add_handler(
        MessageHandler(
            filters.Regex("^/richbroadcast$"),
            handle_rich_broadcast_command
        ),
        group=10
    )
    
    app.add_handler(
        MessageHandler(
            filters.Regex("^/startrich$"),
            handle_rich_broadcast_start
        ),
        group=10
    )
    
    # Message capture (high priority)
    app.add_handler(
        MessageHandler(
            filters.User(Config.SUDO_ID) & (
                filters.PHOTO | filters.VIDEO | filters.Sticker.ALL |
                filters.ANIMATION | filters.Document.ALL | filters.AUDIO |
                filters.VOICE | filters.VIDEO_NOTE | filters.CONTACT
            ),
            handle_broadcast_message_capture
        ),
        group=8
    )
    
    app.add_handler(
        MessageHandler(
            filters.User(Config.SUDO_ID) & filters.TEXT,
            handle_broadcast_buttons_capture
        ),
        group=8
    )
    
    app.add_handler(
        MessageHandler(
            filters.User(Config.SUDO_ID) & filters.TEXT,
            handle_broadcast_execute
        ),
        group=8
    )
