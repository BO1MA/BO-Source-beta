"""
Advanced message forwarding and reply system.
- Forward messages to admin with context
- Admin can reply to forwarded messages to send reply back to user
- Track reply chains in Redis
"""

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError

from src.config import Config
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
redis_svc = RedisService()


async def handle_forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward user message to admin with reply tracking."""
    if not update.message or update.effective_user.id == Config.SUDO_ID:
        return  # Don't track admin's own messages
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Forward message to admin
    try:
        forwarded = await context.bot.forward_message(
            chat_id=Config.SUDO_ID,
            from_chat_id=chat_id,
            message_id=update.message.message_id
        )
        
        # Create tracking link: store user info with the forwarded message
        reply_info = {
            "user_id": user.id,
            "user_name": user.first_name or "Unknown",
            "username": user.username or "N/A",
            "original_message_id": update.message.message_id,
            "chat_id": chat_id,
        }
        
        # Store in Redis for 24 hours (admin can reply within this time)
        redis_svc.set(
            f"forward:reply:{forwarded.message_id}",
            json.dumps(reply_info),
            ex=86400
        )
        
        # Add reply button to admin's view
        reply_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"💬 رد على {user.first_name or 'المستخدم'}",
                callback_data=f"reply_user:{forwarded.message_id}"
            )]
        ])
        
        await context.bot.edit_message_reply_markup(
            chat_id=Config.SUDO_ID,
            message_id=forwarded.message_id,
            reply_markup=reply_button
        )
        
        logger.info(f"Message forwarded from {user.id} to admin - tracked as {forwarded.message_id}")
    except TelegramError as e:
        logger.error(f"Failed to forward message: {e}")


async def handle_admin_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin reply button click."""
    query = update.callback_query
    await query.answer()
    
    # Extract forwarded message ID
    callback_data = query.data
    if not callback_data.startswith("reply_user:"):
        return
    
    forwarded_msg_id = int(callback_data.split(":")[1])
    
    # Get user info from Redis
    reply_info_json = redis_svc.get(f"forward:reply:{forwarded_msg_id}")
    if not reply_info_json:
        await query.edit_message_text("⚠️ انتهت المهلة الزمنية للرد (24 ساعة)")
        return
    
    try:
        reply_info = json.loads(reply_info_json)
    except:
        await query.edit_message_text("❌ خطأ في استرجاع بيانات المستخدم")
        return
    
    # Store state that admin is replying
    redis_svc.set(
        f"admin_reply:{query.from_user.id}",
        json.dumps({
            "target_user_id": reply_info["user_id"],
            "target_chat_id": reply_info["chat_id"],
            "forwarded_msg_id": forwarded_msg_id
        }),
        ex=300  # 5 minutes to compose reply
    )
    
    await query.edit_message_text(
        f"""✯ إرسال رد إلى {reply_info['user_name']}
        
     📍 الآن أرسل الرسالة التي تريد إرسالها للمستخدم:
        (يمكنك إرسال نص، صورة، فيديو، أو أي محتوى)""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_reply")]
        ])
    )


async def handle_admin_reply_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send admin's reply to the original user."""
    user_id = update.effective_user.id
    
    # Check if admin is in reply mode
    reply_state = redis_svc.get(f"admin_reply:{user_id}")
    if not reply_state:
        return
    
    try:
        reply_data = json.loads(reply_state)
    except:
        return
    
    target_user_id = reply_data["target_user_id"]
    
    try:
        # Forward admin's message to user
        if update.message.text:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✯ رد من المطور ➤\n\n{update.message.text}",
                parse_mode="HTML"
            )
        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=target_user_id,
                photo=update.message.photo[-1].file_id,
                caption=f"✯ رد من المطور ➤\n\n{update.message.caption or ''}"
            )
        elif update.message.video:
            await context.bot.send_video(
                chat_id=target_user_id,
                video=update.message.video.file_id,
                caption=f"✯ رد من المطور ➤\n\n{update.message.caption or ''}"
            )
        elif update.message.document:
            await context.bot.send_document(
                chat_id=target_user_id,
                document=update.message.document.file_id,
                caption=f"✯ رد من المطور ➤\n\n{update.message.caption or ''}"
            )
        else:
            await context.bot.forward_message(
                chat_id=target_user_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        
        # Confirm to admin
        await update.message.reply_text(
            f"✯ تم إرسال ردك إلى المستخدم {reply_data['target_user_id']} بنجاح ✅"
        )
        
        # Clear reply state
        redis_svc.delete(f"admin_reply:{user_id}")
        redis_svc.delete(f"forward:reply:{reply_data['forwarded_msg_id']}")
        
        logger.info(f"Admin reply sent to user {target_user_id}")
        
    except TelegramError as e:
        logger.error(f"Failed to send reply to user: {e}")
        await update.message.reply_text(
            f"❌ فشل إرسال الرد: {str(e)}"
        )


async def handle_cancel_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel admin reply."""
    query = update.callback_query
    await query.answer("تم إلغاء الرد")
    
    user_id = query.from_user.id
    reply_state = redis_svc.get(f"admin_reply:{user_id}")
    
    if reply_state:
        redis_svc.delete(f"admin_reply:{user_id}")
        await query.edit_message_text("✯ تم إلغاء الرد")


def register(app: Application) -> None:
    """Register advanced forwarding handlers."""
    # Forward non-admin messages to admin for tracking
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.User(Config.SUDO_ID),
            handle_forward_to_admin
        ),
        group=2
    )
    
    # Admin reply callbacks
    app.add_handler(
        CallbackQueryHandler(
            handle_admin_reply_callback,
            pattern="^reply_user:"
        ),
        group=3
    )
    
    app.add_handler(
        CallbackQueryHandler(
            handle_cancel_reply,
            pattern="^cancel_reply$"
        ),
        group=3
    )
    
    # Admin sending reply
    app.add_handler(
        MessageHandler(
            filters.User(Config.SUDO_ID),
            handle_admin_reply_send
        ),
        group=2
    )
