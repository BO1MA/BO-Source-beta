"""Admin dashboard - manage bot settings and configuration."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler

from src.config import Config
from src.services.redis_service import RedisService

logger = logging.getLogger(__name__)
redis_svc = RedisService()


async def handle_admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin dashboard."""
    if update.effective_user.id != Config.SUDO_ID:
        await update.message.reply_text("✯ أنت لا تملك صلاحيات الوصول لهذا الأمر")
        return
    
    await update.message.reply_text(
        "✯ لوحة التحكم الخاصة بالمطور 👨🏻‍✈️\n\n"
        "اختر ما تريد تعديله:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("معلومات المدير 📋", callback_data="admin_info_edit")],
            [InlineKeyboardButton("رسالة الترحيب 🗒", callback_data="welcome_msg_edit")],
            [InlineKeyboardButton("الرسالة التلقائية 📝", callback_data="auto_reply_edit")],
            [InlineKeyboardButton("القوانين ⚠️", callback_data="rules_edit")],
            [InlineKeyboardButton("نبذة البوت 📇", callback_data="bot_info_edit")],
            [InlineKeyboardButton("القنوات المطلوبة 📡", callback_data="channels_edit")],
            [InlineKeyboardButton("الإحصائيات 📊", callback_data="stats_view")],
            [InlineKeyboardButton("الإذاعة 🗣", callback_data="broadcast_menu")],
        ])
    )


async def handle_admin_info_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit admin information."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل معلومات المدير الآن\n\n"
        "يمكنك تضمين: الاسم، اللقب، البلد، البيو، أي معلومات تريدها",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="dashboard")]
        ])
    )
    
    # Store state
    redis_svc.set(f"edit_mode:admin_info:{query.from_user.id}", "1", ex=300)


async def handle_welcome_msg_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit welcome message."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل رسالة الترحيب الآن\n\n"
        "هذه الرسالة ستظهر عند استخدام الأمر /start",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="dashboard")]
        ])
    )
    
    redis_svc.set(f"edit_mode:welcome:{query.from_user.id}", "1", ex=300)


async def handle_auto_reply_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit auto reply message."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل الرسالة التلقائية (الرد على الرسائل)\n\n"
        "يمكنك إضافة رابط قناتك أو أي نص تريده",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="dashboard")]
        ])
    )
    
    redis_svc.set(f"edit_mode:auto_reply:{query.from_user.id}", "1", ex=300)


async def handle_rules_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit rules/laws."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل القوانين الآن\n\n"
        "صيغة الرد عندما يسأل المستخدم عن القوانين",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="dashboard")]
        ])
    )
    
    redis_svc.set(f"edit_mode:rules:{query.from_user.id}", "1", ex=300)


async def handle_bot_info_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit bot info/description."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل نبذة عن البوت\n\n"
        "وصف ما يفعله هذا البوت والميزات التي يوفرها",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="dashboard")]
        ])
    )
    
    redis_svc.set(f"edit_mode:bot_info:{query.from_user.id}", "1", ex=300)


async def handle_channels_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Edit required channels."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل معرفات القنوات المطلوبة\n\n"
        "افصل كل قناة بسطر جديد\n"
        "مثال:\n"
        "@channel1\n"
        "@channel2\n"
        "@channel3",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="dashboard")]
        ])
    )
    
    redis_svc.set(f"edit_mode:channels:{query.from_user.id}", "1", ex=300)


async def handle_stats_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View bot statistics."""
    query = update.callback_query
    
    # Get stats from Redis
    total_users = len(redis_svc.keys("user:*"))
    banned_users = len(redis_svc.keys("ban:*"))
    muted_users = len(redis_svc.keys("mute:*"))
    
    await query.edit_message_text(
        f"""✯ إحصائيات البوت 📊

👥 إجمالي المستخدمين: {total_users}
🚫 المحظورين: {banned_users}
🔇 المكتومين: {muted_users}
""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("رجوع ↩️", callback_data="dashboard")]
        ])
    )


async def handle_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show broadcast menu."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ خيارات الإذاعة 🗣\n\n"
        "اختر نوع الإذاعة:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إرسال رسالة عادية 📝", callback_data="broadcast_text")],
            [InlineKeyboardButton("إعادة توجيه رسالة ↪️", callback_data="broadcast_forward")],
            [InlineKeyboardButton("تفاصيل الإذاعة ℹ️", callback_data="broadcast_info")],
            [InlineKeyboardButton("رجوع ↩️", callback_data="dashboard")]
        ])
    )


async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start text broadcast."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ أرسل الرسالة التي تريد إرسالها لجميع المستخدمين",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="broadcast_menu")]
        ])
    )
    
    redis_svc.set(f"broadcast_mode:{query.from_user.id}", "text", ex=300)


async def handle_broadcast_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start forward broadcast."""
    query = update.callback_query
    
    await query.edit_message_text(
        "✯ رد على الرسالة التي تريد إعادة توجيهها\n\n"
        "ثم أرسل أي رسالة بعدها لبدء الإذاعة",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إلغاء ❌", callback_data="broadcast_menu")]
        ])
    )
    
    redis_svc.set(f"broadcast_mode:{query.from_user.id}", "forward", ex=300)


async def handle_broadcast_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show broadcast info."""
    query = update.callback_query
    
    # Count users
    users_list = redis_svc.smembers("bot:users")
    user_count = len(users_list) if users_list else 0
    
    await query.edit_message_text(
        f"""✯ معلومات الإذاعة ℹ️

سيتم إرسال الرسالة لـ: {user_count} مستخدم
الوقت: قد يستغرق بعض الوقت حسب عدد المستخدمين
الحالة: جاهز للإرسال

⚠️ تنبيه: تأكد من الرسالة قبل الإرسال!
""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("رجوع ↩️", callback_data="broadcast_menu")]
        ])
    )


async def handle_dashboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle dashboard button."""
    query = update.callback_query
    
    if query.data == "dashboard":
        await handle_admin_dashboard(update, context)
    elif query.data == "admin_info_edit":
        await handle_admin_info_edit(update, context)
    elif query.data == "welcome_msg_edit":
        await handle_welcome_msg_edit(update, context)
    elif query.data == "auto_reply_edit":
        await handle_auto_reply_edit(update, context)
    elif query.data == "rules_edit":
        await handle_rules_edit(update, context)
    elif query.data == "bot_info_edit":
        await handle_bot_info_edit(update, context)
    elif query.data == "channels_edit":
        await handle_channels_edit(update, context)
    elif query.data == "stats_view":
        await handle_stats_view(update, context)
    elif query.data == "broadcast_menu":
        await handle_broadcast_menu(update, context)
    elif query.data == "broadcast_text":
        await handle_broadcast_text(update, context)
    elif query.data == "broadcast_forward":
        await handle_broadcast_forward(update, context)
    elif query.data == "broadcast_info":
        await handle_broadcast_info(update, context)


async def handle_settings_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for settings."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if text == "/dashboard" and user_id == Config.SUDO_ID:
        await handle_admin_dashboard(update, context)
        return
    
    # Check what setting is being edited
    if redis_svc.get(f"edit_mode:admin_info:{user_id}"):
        redis_svc.set("admin:info", text, ex=86400*365)
        await update.message.reply_text("✯ تم حفظ معلومات المدير بنجاح ✅")
        redis_svc.delete(f"edit_mode:admin_info:{user_id}")
        return
    
    if redis_svc.get(f"edit_mode:welcome:{user_id}"):
        redis_svc.set("bot:welcome", text, ex=86400*365)
        await update.message.reply_text("✯ تم حفظ رسالة الترحيب بنجاح ✅")
        redis_svc.delete(f"edit_mode:welcome:{user_id}")
        return
    
    if redis_svc.get(f"edit_mode:auto_reply:{user_id}"):
        redis_svc.set("bot:auto_reply", text, ex=86400*365)
        await update.message.reply_text("✯ تم حفظ الرسالة التلقائية بنجاح ✅")
        redis_svc.delete(f"edit_mode:auto_reply:{user_id}")
        return
    
    if redis_svc.get(f"edit_mode:rules:{user_id}"):
        redis_svc.set("bot:rules", text, ex=86400*365)
        await update.message.reply_text("✯ تم حفظ القوانين بنجاح ✅")
        redis_svc.delete(f"edit_mode:rules:{user_id}")
        return
    
    if redis_svc.get(f"edit_mode:bot_info:{user_id}"):
        redis_svc.set("bot:info", text, ex=86400*365)
        await update.message.reply_text("✯ تم حفظ نبذة البوت بنجاح ✅")
        redis_svc.delete(f"edit_mode:bot_info:{user_id}")
        return
    
    if redis_svc.get(f"edit_mode:channels:{user_id}"):
        channels = [ch.strip() for ch in text.split("\n") if ch.strip()]
        redis_svc.set("bot:required_channels", ";".join(channels), ex=86400*365)
        await update.message.reply_text(f"✯ تم حفظ {len(channels)} قنوات مطلوبة بنجاح ✅")
        redis_svc.delete(f"edit_mode:channels:{user_id}")
        return
    
    # Broadcast mode
    if redis_svc.get(f"broadcast_mode:{user_id}") == "text":
        await execute_text_broadcast(context, user_id, text)
        redis_svc.delete(f"broadcast_mode:{user_id}")
        return


async def execute_text_broadcast(context, user_id: int, text: str) -> None:
    """Execute text broadcast to all users."""
    users = redis_svc.smembers("bot:users")
    
    if not users:
        return
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(int(user), text)
            sent += 1
        except:
            failed += 1
    
    await context.bot.send_message(
        user_id,
        f"✯ انتهت الإذاعة ✅\n\n"
        f"✓ تم الإرسال لـ: {sent}\n"
        f"✗ فشل الإرسال لـ: {failed}"
    )


def register(app: Application) -> None:
    """Register admin dashboard handlers."""
    app.add_handler(
        MessageHandler(filters.Regex("^/dashboard$"), handle_admin_dashboard),
        group=5
    )
    app.add_handler(
        CallbackQueryHandler(handle_dashboard_button, pattern="^(dashboard|admin_info_edit|welcome_msg_edit|auto_reply_edit|rules_edit|bot_info_edit|channels_edit|stats_view|broadcast_menu|broadcast_text|broadcast_forward|broadcast_info)$"),
        group=5
    )
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_text),
        group=50
    )
