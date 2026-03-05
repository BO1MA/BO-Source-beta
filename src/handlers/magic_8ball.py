"""Magic 8-ball fortune telling feature - answer ANY question with random responses."""

import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters, CallbackQueryHandler

from src.services.redis_service import RedisService

logger = __import__("logging").getLogger(__name__)
redis_svc = RedisService()

# Magic 8-ball responses - from PHP bot (plora.php)
MAGIC_RESPONSES = [
    "👻 نـعم",
    "كـلا",
    "🎚️ قليـلا",
    "اتوقع ذلـك",
    "بكل جداره وثقه نعم",
    "• بكـل تأكيد نعم",
    "كلا والف كلا",
    "لا صديقي التفكير خاطئ",
    "Ofcorse ✅",
    "بعض الشـيئ",
    "🤔 اتوقـع ذالك",
    "😕 لا اضـن",
    "احتمال ضئيـل",
    "لاتفـكر في هذا الشيئ اصلا",
    "عقلك مشوش اذهب للراحه 😴",
    "لم استطع قرائة افكارك 🌀",
    "نعم نعم نعم 🔮",
]


async def handle_magic_8ball_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - welcome message."""
    name = update.effective_user.first_name
    
    await update.message.reply_text(
        f"❤️ | اهلا عزيزي {name}\n\n"
        f"🔮 | مرحبا بك في بوت البلورة السحرية 🪄\n\n"
        f"📝 | ارسل لي سؤال وسأقوم بالإجابة عن الاسئله بنعم أو لا 👀",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("𝐒𝐚𝐖 𝟔𝟔𝟔 𖢣", url="https://t.me/BO1MA"),
                InlineKeyboardButton("قناتنا 𝟔𝟔𝟔 Ch𖢣", url="https://t.me/BO_MR")
            ],
        ])
    )


async def handle_magic_8ball_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message as a magic 8-ball question."""
    text = (update.message.text or "").strip()
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Skip if it's a command
    if text.startswith("/"):
        return
    
    # Get random response
    response = random.choice(MAGIC_RESPONSES)
    
    # Store in Redis for stats
    redis_svc.incr(f"magic_8ball:questions:{chat_id}")
    redis_svc.incr(f"magic_8ball:user:{user.id}")
    
    # Send response with share button (switch_inline_query)
    await update.message.reply_text(
        f"📝 | سـؤالـك هـو ( {text} )\n\n"
        f"🔮 | البلـورة السـحرية تقـول ( {response} )",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "• مشاركة الاجابه مع اصدقائك ، 🌐",
                switch_inline_query=text
            )],
        ])
    )


async def handle_voice_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reject voice messages."""
    await update.message.reply_text(
        "🔮 || البلوره تقوم بتخمين افكارك المكتوبة فقط لاترسل بصمات",
        reply_to_message_id=update.message.message_id
    )


async def handle_magic_8ball_lucky_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a lucky number."""
    text = (update.message.text or "").strip()
    
    if text not in ("رقم الحظ", "lucky number", "البرج"):
        return
    
    lucky_num = random.randint(1, 100)
    
    await update.message.reply_text(
        f"✯ رقم الحظ اليوم: {lucky_num} 🍀\n\n"
        f"احتفظ بهذا الرقم! قد يجلب لك الحظ 😊"
    )


async def handle_magic_8ball_yes_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simple yes/no game."""
    text = (update.message.text or "").strip()
    
    if text not in ("نعم لا", "yes no"):
        return
    
    answer = random.choice(["✯ نعم ✅", "✯ لا ❌"])
    
    await update.message.reply_text(
        f"🎲 عملة الحظ تقول:\n{answer}"
    )


def register(app: Application) -> None:
    """Register magic 8-ball handlers."""
    # Start command (high priority)
    app.add_handler(
        MessageHandler(filters.Regex("^/start$"), handle_magic_8ball_start),
        group=1
    )
    
    # Voice rejection (high priority)
    app.add_handler(
        MessageHandler(filters.VOICE, handle_voice_rejection),
        group=5
    )
    
    # Lucky number and yes/no games
    app.add_handler(
        MessageHandler(filters.Regex("^(رقم الحظ|lucky number|البرج)$"), handle_magic_8ball_lucky_number),
        group=20
    )
    
    app.add_handler(
        MessageHandler(filters.Regex("^(نعم لا|yes no)$"), handle_magic_8ball_yes_no),
        group=20
    )
    
    # Main 8-ball questions - accepts ANY text message (lowest priority)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_magic_8ball_question),
        group=90  # Very low priority to not interfere with other handlers
    )
