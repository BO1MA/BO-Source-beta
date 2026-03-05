"""User contact system - send location, phone, profile info to admin."""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler

from src.config import Config
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
redis_svc = RedisService()


async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu with contact options."""
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("📍 ارسل موقعي"), KeyboardButton("📞 ارسل جهه اتصالي")],
        [KeyboardButton("👤 معلومات المدير"), KeyboardButton("☎️ جهه اتصال المدير")],
        [KeyboardButton("ℹ️ نبذة البوت"), KeyboardButton("⚠️ القوانين")],
        [KeyboardButton("💡 المساعده")],
    ], resize_keyboard=True)
    
    help_text = redis_svc.get("bot:help_text")
    if not help_text:
        help_text = """
✯ مرحبا بك في خدمات البوت 🤖

استخدم الأزرار أدناه:

📍 ارسل موقعي - شارك موقعك مع المدير
📞 ارسل جهه اتصالي - شارك رقم هاتفك
👤 معلومات المدير - معلومات عن مالك البوت
☎️ جهه اتصال المدير - رقم الاتصال المباشر
ℹ️ نبذة البوت - معلومات عن هذا البوت
⚠️ القوانين - قوانين استخدام البوت
💡 المساعده - شرح الأوامر المتاحة
"""
    
    await update.message.reply_text(help_text, reply_markup=keyboard)


async def handle_send_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle send location button."""
    await update.message.reply_text(
        "✯ لمشاركة موقعك، استخدم الزر أدناه:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📍 موقعي", request_location=True)],
            [KeyboardButton("❌ إلغاء")]
        ], resize_keyboard=True)
    )


async def handle_send_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle send contact button."""
    await update.message.reply_text(
        "✯ لمشاركة رقم هاتفك، استخدم الزر أدناه:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("📞 رقمي", request_contact=True)],
            [KeyboardButton("❌ إلغاء")]
        ], resize_keyboard=True)
    )


async def handle_admin_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send admin information."""
    admin_info = redis_svc.get("admin:info")
    if not admin_info:
        admin_info = "لم يتم تعيين معلومات المدير بعد"
    
    await update.message.reply_text(
        f"👤 معلومات المدير:\n\n{admin_info}",
        parse_mode="Markdown"
    )


async def handle_admin_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send admin contact."""
    admin_phone = redis_svc.get("admin:phone")
    admin_name = redis_svc.get("admin:name") or "المدير"
    
    if admin_phone:
        await update.message.reply_contact(
            phone_number=admin_phone.replace("+", "").replace(" ", "").replace("-", ""),
            first_name=admin_name
        )
    else:
        await update.message.reply_text("❌ لم يتم تعيين رقم المدير بعد")


async def handle_bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send bot information."""
    bot_info = redis_svc.get("bot:info")
    if not bot_info:
        bot_info = "بوت متطور مع ميزات عديدة 🤖"
    
    await update.message.reply_text(f"ℹ️ نبذة البوت:\n\n{bot_info}")


async def handle_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send bot rules."""
    rules = redis_svc.get("bot:rules")
    if not rules:
        rules = "لم يتم تعيين القوانين بعد"
    
    await update.message.reply_text(f"⚠️ القوانين:\n\n{rules}")


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help text."""
    help_text = redis_svc.get("bot:help_text")
    if not help_text:
        help_text = """
✯ دليل استخدام البوت 💡

1️⃣ **ارسل موقعي**
   شارك موقعك مع المدير (آمن تماً)

2️⃣ **ارسل جهه اتصالي**
   شارك رقم هاتفك إذا أردت

3️⃣ **معلومات المدير**
   معلومات شاملة عن مالك البوت

4️⃣ **جهه اتصال المدير**
   رقم الاتصال المباشر

5️⃣ **نبذة البوت**
   وصف لميزات هذا البوت

6️⃣ **القوانين**
   قواعد استخدام البوت

شكراً لاستخدامك هذا البوت! 💝
"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_location_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle received location."""
    location = update.message.location
    user = update.effective_user
    
    # Send to admin
    await context.bot.send_location(
        chat_id=Config.SUDO_ID,
        latitude=location.latitude,
        longitude=location.longitude,
        caption=f"📍 موقع من {user.mention_html()}",
        parse_mode="HTML"
    )
    
    await update.message.reply_text(
        "✯ تم إرسال موقعك للمدير بنجاح ✅\n"
        "شكراً لك 💝"
    )
    
    # Log in Redis
    redis_svc.set(
        f"user:location:{user.id}",
        f"{location.latitude},{location.longitude}",
        ex=86400*30
    )


async def handle_contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle received contact."""
    contact = update.message.contact
    user = update.effective_user
    
    # Send to admin
    await context.bot.send_contact(
        chat_id=Config.SUDO_ID,
        phone_number=contact.phone_number,
        first_name=contact.first_name,
        caption=f"📞 جهة اتصال من {user.mention_html()}",
        parse_mode="HTML"
    )
    
    await update.message.reply_text(
        "✯ تم إرسال بيانات الاتصال للمدير بنجاح ✅\n"
        "شكراً لك 💝"
    )
    
    # Log in Redis
    redis_svc.set(
        f"user:phone:{user.id}",
        contact.phone_number,
        ex=86400*30
    )


async def handle_text_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text button presses."""
    text = update.message.text
    
    if text == "📍 ارسل موقعي":
        await handle_send_location(update, context)
    elif text == "📞 ارسل جهه اتصالي":
        await handle_send_contact(update, context)
    elif text == "👤 معلومات المدير":
        await handle_admin_info(update, context)
    elif text == "☎️ جهه اتصال المدير":
        await handle_admin_contact(update, context)
    elif text == "ℹ️ نبذة البوت":
        await handle_bot_info(update, context)
    elif text == "⚠️ القوانين":
        await handle_rules(update, context)
    elif text == "💡 المساعده":
        await handle_help(update, context)


def register(app: Application) -> None:
    """Register user contact handlers."""
    # Commands
    app.add_handler(
        MessageHandler(filters.Regex("^/help$"), handle_help_command),
        group=10
    )
    
    # Text buttons
    app.add_handler(
        MessageHandler(
            filters.Regex("^(📍 ارسل موقعي|📞 ارسل جهه اتصالي|👤 معلومات المدير|☎️ جهه اتصال المدير|ℹ️ نبذة البوت|⚠️ القوانين|💡 المساعده)$"),
            handle_text_buttons
        ),
        group=10
    )
    
    # Location and contact
    app.add_handler(
        MessageHandler(filters.LOCATION, handle_location_received),
        group=10
    )
    app.add_handler(
        MessageHandler(filters.CONTACT, handle_contact_received),
        group=10
    )
