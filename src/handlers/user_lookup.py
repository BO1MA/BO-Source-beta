"""
User lookup and info system - admin can get user information by ID.
"""

import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError

from src.config import Config
from src.services.user_service import UserService
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
user_svc = UserService()
redis_svc = RedisService()


async def handle_user_lookup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to lookup user info by ID."""
    if update.effective_user.id != Config.SUDO_ID:
        await update.message.reply_text("✯ أنت لا تملك صلاحيات الوصول لهذا الأمر")
        return
    
    text = (update.message.text or "").strip()
    
    # Parse: /userinfo <user_id>
    if not text.startswith("/userinfo"):
        return
    
    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text(
            "✯ الاستخدام: `/userinfo <user_id>`\n\n"
            "مثال: `/userinfo 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        lookup_user_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("❌ معرف مستخدم غير صحيح")
        return
    
    # Try to get user chat to fetch info
    try:
        user_chat = await context.bot.get_chat(lookup_user_id)
        
        # Prepare info
        info_text = f"""✯ معلومات المستخدم 👤

🔹 المعرف: `{user_chat.id}`
🔹 الاسم: {user_chat.first_name or "N/A"}
🔹 اللقب الأخير: {user_chat.last_name or "N/A"}
🔹 اسم المستخدم: @{user_chat.username or "N/A"}
🔹 الحالة: {user_chat.status}
🔹 النوع: {"مستخدم" if user_chat.type == "private" else user_chat.type}
🔹 البيو: {user_chat.bio or "N/A"}
🔹 الصورة: {"✅ نعم" if user_chat.photo else "❌ لا"}
"""
        
        # Check if user has bank account
        bank_data = redis_svc.get(f"user:bank:{lookup_user_id}")
        if bank_data:
            try:
                bank_info = json.loads(bank_data)
                info_text += f"\n💰 رصيد البنك: {bank_info.get('balance', 0)} 🪙"
            except:
                pass
        
        # Check stats
        stats_key = f"user:stats:{lookup_user_id}"
        stats_data = redis_svc.get(stats_key)
        if stats_data:
            try:
                stats = json.loads(stats_data)
                info_text += f"""
📊 الإحصائيات:
  • الرسائل: {stats.get('messages', 0)}
  • الألعاب: {stats.get('games', 0)}
  • الجوائز: {stats.get('rewards', 0)}
"""
            except:
                pass
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("إرسال رسالة", callback_data=f"send_user:{lookup_user_id}"),
                InlineKeyboardButton("حظر", callback_data=f"ban_user:{lookup_user_id}"),
            ]
        ])
        
        await update.message.reply_text(info_text, parse_mode="Markdown", reply_markup=keyboard)
        
    except TelegramError as e:
        logger.error(f"Failed to get user info: {e}")
        await update.message.reply_text(
            f"❌ لم أتمكن من الوصول إلى هذا المستخدم\n"
            f"السبب: {str(e)}"
        )


async def handle_user_lookup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user lookup action callbacks."""
    query = update.callback_query
    callback_data = query.data
    
    if callback_data.startswith("send_user:"):
        target_user_id = int(callback_data.split(":")[1])
        
        # Set admin in reply mode
        redis_svc.set(
            f"admin_reply:{query.from_user.id}",
            json.dumps({
                "target_user_id": target_user_id,
                "target_chat_id": target_user_id,
                "forwarded_msg_id": 0
            }),
            ex=300
        )
        
        await query.edit_message_text(
            f"✯ إرسال رسالة للمستخدم {target_user_id}\n\n"
            "الآن أرسل الرسالة التي تريد إرسالها",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_reply")]
            ])
        )
        
    elif callback_data.startswith("ban_user:"):
        target_user_id = int(callback_data.split(":")[1])
        
        # Ban user
        redis_svc.set(f"banned:{target_user_id}", "1", ex=31536000)  # 1 year
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="✯ تم حظرك من البوت ❌"
            )
        except:
            pass
        
        await query.edit_message_text(f"✯ تم حظر المستخدم {target_user_id} بنجاح ✅")


async def handle_group_member_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Notify admin when new member joins group."""
    if not update.message or not update.message.new_chat_members:
        return
    
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        
        group_id = update.effective_chat.id
        group_name = update.effective_chat.title or "مجموعة بدون اسم"
        
        notification = f"""✯ عضو جديد في المجموعة 👥

👤 الاسم: {member.first_name or "N/A"}
📍 اسم المستخدم: @{member.username or "N/A"}
🔹 المعرف: `{member.id}`
📌 المجموعة: {group_name} (`{group_id}`)
"""
        
        try:
            await context.bot.send_message(
                chat_id=Config.SUDO_ID,
                text=notification,
                parse_mode="Markdown"
            )
        except TelegramError as e:
            logger.error(f"Failed to notify admin of new member: {e}")


def register(app: Application) -> None:
    """Register user lookup handlers."""
    # User info command
    app.add_handler(
        MessageHandler(filters.Regex("^/userinfo"), handle_user_lookup_command),
        group=10
    )
    
    # Callbacks for user actions
    app.add_handler(
        CallbackQueryHandler(
            handle_user_lookup_callback,
            pattern="^(send_user:|ban_user:)"
        ),
        group=11
    )
    
    # Join notifications
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_group_member_join),
        group=5
    )
