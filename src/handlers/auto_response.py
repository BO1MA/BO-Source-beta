import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatType
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from src.constants.messages import (
    GREETING_RESPONSES, CHAT_RESPONSES, WOULD_YOU_RATHER,
    MSG_DEVELOPER_INFO, ADVICE_RESPONSES, INSULT_RESPONSES,
)
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.config import Config
# Private welcome handler with inline buttons
async def handle_private_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with buttons in private chat (on /start or 'start')."""
    if update.effective_chat.type != ChatType.PRIVATE:
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("طلب البوت", url="https://t.me/BO1MA")],
        [InlineKeyboardButton("الدعم", url="https://t.me/BO_MR")],
    ])
    msg = (
        "✯ اهلا بك في بوت الحماية!\n"
        "يمكنك طلب البوت لمجموعتك أو التواصل مع الدعم عبر الازرار بالاسفل."
    )
    await update.message.reply_text(msg, reply_markup=keyboard)
"""
Auto-response handler — responds to greetings and common phrases automatically.
Also includes developer contact commands and "Would You Rather" game.
Ported from bian.lua / AVIRA.lua auto-response and rdodsudos.lua.

Features:
- Greeting responses (السلام عليكم, صباح الخير, etc.)
- Chat responses (انا جيت, باي, حبيبي, etc.)
- Developer contact (مين نصبلك, عايزه بوت)
- Would you rather (لو خيروك)
- Reverse text (العكس)
"""
import random
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.constants.messages import (
    GREETING_RESPONSES, CHAT_RESPONSES, WOULD_YOU_RATHER,
    MSG_DEVELOPER_INFO, ADVICE_RESPONSES, INSULT_RESPONSES,
)
from src.services.group_service import GroupService
from src.utils.decorators import group_only
from src.config import Config

logger = logging.getLogger(__name__)
group_svc = GroupService()


@group_only
async def handle_greetings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to common greetings."""
    text = (update.message.text or "").strip()

    # Check GREETING_RESPONSES
    for trigger, responses in GREETING_RESPONSES.items():
        if trigger in text:
            await update.message.reply_text(random.choice(responses))
            return

    # Check CHAT_RESPONSES (exact match)
    if text in CHAT_RESPONSES:
        await update.message.reply_text(CHAT_RESPONSES[text])
        return


@group_only
async def handle_developer_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle developer contact commands (مين نصبلك, عايزه بوت)."""
    chat_id = update.effective_chat.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("إيمو / أشموديل / احمد", url="https://t.me/BO1MA")],
        [InlineKeyboardButton("قناة السورس", url="https://t.me/BO_MR")],
    ])

    caption = (
        "◍ لو عايز بوت مميز بدون توقف وامان  .\n"
        "◍قم بـ التواصل مع المطورين عبر الازرار تاليه ."
    )

    await context.bot.send_photo(
        chat_id=chat_id,
        photo="https://t.me/BO_MR/45",
        caption=caption,
        reply_markup=keyboard,
    )


@group_only
async def handle_taki_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إيمو / أشموديل / احمد — contact card."""
    chat_id = update.effective_chat.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("إيمو", url="https://t.me/BO1MA")],
        [InlineKeyboardButton("أشموديل", url="https://t.me/BO1MA")],
        [InlineKeyboardButton("احمد", url="https://t.me/BO1MA")],
    ])

    await context.bot.send_photo(
        chat_id=chat_id,
        photo="https://t.me/BO_MR/45",
        caption="مطور السورس للتواصل اضغط علي الازرار",
        reply_markup=keyboard,
    )


@group_only
async def handle_developer_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show developer info (المطور, المبرمج)."""
    await update.message.reply_text(
        MSG_DEVELOPER_INFO.format(developer=Config.DEVELOPER_USERNAME)
    )



@group_only
async def handle_bot_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to 'بوت' with photo, caption, and inline buttons (ported from rdodsudos.lua)."""
    chat_id = update.effective_chat.id
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('⌯ تــاكــي الــكـبـيـرر ⊁', url='https://t.me/D_k_j'),
        ],
        [
            InlineKeyboardButton('00:00', url='https://t.me/x_clasic_x'),
        ],
    ])
    caption = (
        '◍ لو عايز بوت مميز بدون توقف وامان  .\n'
        '◍قم بـ التواصل مع المطورين عبر الازرار تاليه .'
    )
    await context.bot.send_photo(
        chat_id=chat_id,
        photo='https://t.me/F_R_M1/407',
        caption=caption,
        reply_markup=keyboard,
        parse_mode='HTML',
        disable_web_page_preview=True
    )


@group_only
async def handle_source_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """السورس / سورس — send source card with contact buttons."""
    chat_id = update.effective_chat.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("إيمو / أشموديل / احمد", url="https://t.me/BO1MA")],
        [InlineKeyboardButton("قناة السورس", url="https://t.me/BO_MR")],
    ])

    caption = (
        "◍ سورس البوت مفتوح وكامل.\n"
        "◍ للتواصل مع المطور او الحصول على السورس اضغط الازرار."
    )

    await context.bot.send_photo(
        chat_id=chat_id,
        photo="https://t.me/BO_MR/45",
        caption=caption,
        reply_markup=keyboard,
    )


@group_only
async def handle_would_you_rather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """لو خيروك — Would you rather game."""
    option1, option2 = random.choice(WOULD_YOU_RATHER)
    user = update.effective_user

    await update.message.reply_text(
        f"✯ لو خيروك يا {user.first_name}:\n\n"
        f"1️⃣ {option1}\n"
        f"              أو\n"
        f"2️⃣ {option2}"
    )


@group_only
async def handle_reverse_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """العكس — reverse text."""
    text = (update.message.text or "").strip()
    arg = text.replace("العكس", "", 1).strip()

    if not arg and update.message.reply_to_message and update.message.reply_to_message.text:
        arg = update.message.reply_to_message.text

    if arg:
        reversed_text = arg[::-1]
        await update.message.reply_text(f"✯ العكس:\n{reversed_text}")
    else:
        await update.message.reply_text("✯ اكتب نص بعد الامر او رد على رساله")



@group_only
async def handle_kick_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اطردني — kick the user who asks."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    await update.message.reply_text(f"✯ لا استطيع طردك يا {user.first_name} 😂")

        
@group_only
async def handle_marry_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تتجوزيني — marriage proposal joke."""
    responses = [
        "✯ لا شكرا مو وقته 😂💍",
        "✯ خليني افكر... لا 😂",
        "✯ انا بوت ما اتزوج 🤖😂",
        "✯ اسأل احد ثاني 😂",
    ]
    await update.message.reply_text(random.choice(responses))


@group_only
async def handle_sing_for_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """غنيلي — sing for user."""
    songs = [
        "🎵 يا ليل يا عين... يا ليلي يا عيني 🎶",
        "🎵 حبيبي يا نور العين... 🎶",
        "🎵 الله الله يا بدر... 🎶",
        "🎵 واحشني يا صاحبي... 🎶",
        "🎵 لو على قلبي... 🎶",
    ]
    await update.message.reply_text(random.choice(songs))


@group_only
async def handle_pronounce(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """وش بيقول — voice recognition placeholder (from yt.php)."""
    if update.message.reply_to_message and update.message.reply_to_message.voice:
        await update.message.reply_text("✯ هذه الميزه غير متوفره حالياً 🎙️")
    else:
        await update.message.reply_text("✯ رد على رساله صوتيه")


@group_only
async def handle_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الاحصائيات — show bot statistics."""
    from src.services.user_service import UserService
    user_svc = UserService()

    total_groups = group_svc.get_total_groups()
    total_users = user_svc.get_total_users()
    total_messages = group_svc.get_total_messages()

    await update.message.reply_text(
        f"✯ احصائيات البوت:\n"
        f"├─ المجموعات: {total_groups}\n"
        f"├─ المستخدمين: {total_users}\n"
        f"└─ الرسائل: {total_messages}"
    )


@group_only
async def handle_advice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """انصح / انصحني — give advice."""
    user = update.effective_user
    advice = random.choice(ADVICE_RESPONSES)
    await update.message.reply_text(f"✯ يا {user.first_name}:\n{advice}")


@group_only
async def handle_insult_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اشتمو — insult the replied-to user (playful)."""
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user.first_name
        insult = random.choice(INSULT_RESPONSES)
        await update.message.reply_text(f"✯ {target}:\n{insult}")
    else:
        await update.message.reply_text("✯ رد على شخص لاشتمه 😂")


def register(app: Application) -> None:
    # Private welcome handler
    app.add_handler(MessageHandler(
        filters.Regex("^(start|/start)$") & filters.ChatType.PRIVATE,
        handle_private_start
    ), group=0)
    """Register auto-response handlers."""
    G = filters.ChatType.GROUPS

    # Contact card (إيمو / أشموديل / احمد)
    app.add_handler(MessageHandler(
        filters.Regex("^(ايمو|إيمو|اشموديل|أشموديل|احمد)$") & G,
        handle_taki_contact
    ), group=40)

    # Developer contact
    app.add_handler(MessageHandler(
        filters.Regex("^(مين نصبلك|عايزه بوت|عايز بوت)$") & G,
        handle_developer_contact
    ), group=40)

    # Developer info
    app.add_handler(MessageHandler(
        filters.Regex("^(المطور|المبرمج|مطور البوت|المبرمج أشموديل|المبرمج إيمو|المبرمج احمد)$") & G,
        handle_developer_info
    ), group=40)

    # Source info
    app.add_handler(MessageHandler(
        filters.Regex("^(السورس|سورس|يا سورس)$") & G,
        handle_source_info
    ), group=40)

    # Bot info
    app.add_handler(MessageHandler(
        filters.Regex("^(البوت|بوت)$") & G,
        handle_bot_info
    ), group=40)

    # Would you rather
    app.add_handler(MessageHandler(
        filters.Regex("^(لو خيروك|خيروك)$") & G,
        handle_would_you_rather
    ), group=40)

    # Reverse text
    app.add_handler(MessageHandler(
        filters.Regex("^العكس") & G,
        handle_reverse_text
    ), group=40)

    # Kick me joke
    app.add_handler(MessageHandler(
        filters.Regex("^(اطردني|طردني)$") & G,
        handle_kick_me
    ), group=40)

    # Marry me joke
    app.add_handler(MessageHandler(
        filters.Regex("^تتجوزيني$") & G,
        handle_marry_me
    ), group=40)

    # Sing for me
    app.add_handler(MessageHandler(
        filters.Regex("^غنيلي$") & G,
        handle_sing_for_me
    ), group=40)

    # Voice recognition placeholder
    app.add_handler(MessageHandler(
        filters.Regex("^(وش بيقول|بيقول اي|\\?\\?|؟؟)$") & G,
        handle_pronounce
    ), group=40)

    # Statistics
    app.add_handler(MessageHandler(
        filters.Regex("^الاحصائيات$") & G,
        handle_statistics
    ), group=40)

    # Advice
    app.add_handler(MessageHandler(
        filters.Regex("^(انصح|انصحني|انصحيني|انصحنى|نصيحه|نصيحة)$") & G,
        handle_advice
    ), group=40)

    # Insult target (playful)
    app.add_handler(MessageHandler(
        filters.Regex("^(اشتم|اشتمو|اشتمه|شتمو|شتمه)$") & G,
        handle_insult_target
    ), group=40)

    # Auto-greetings (lowest priority in this group so specific commands go first)
    app.add_handler(MessageHandler(
        filters.TEXT & G,
        handle_greetings
    ), group=150)
