"""Auto-response handler for common chat triggers and utility commands."""

import logging
import random
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.config import Config
from src.constants.messages import (
    ADVICE_RESPONSES,
    CHAT_RESPONSES,
    GREETING_RESPONSES,
    INSULT_RESPONSES,
    MSG_DEVELOPER_INFO,
    WOULD_YOU_RATHER,
)
from src.economy.bank_system import claim_daily, get_balance, open_bank_account, transfer_points
from src.economy.marketplace import add_item, buy_item, list_items
from src.services.group_service import GroupService
from src.services.redis_service import RedisService
from src.utils.decorators import group_only

redis_svc = RedisService()


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

logger = logging.getLogger(__name__)
group_svc = GroupService()


@group_only
async def handle_greetings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to common greetings with sequential cycling through responses."""
    text = (update.message.text or "").strip()

    # Check GREETING_RESPONSES
    for trigger, responses in GREETING_RESPONSES.items():
        if trigger in text:
            # Get current index from Redis
            redis_key = f"greeting_cycle:{trigger}"
            current_index = int(redis_svc.get(redis_key) or 0)
            
            # Get the response at current index (ensure it's a string)
            response = str(responses[current_index])
            
            # Update index for next time (cycle back to 0 when reaching end)
            next_index = (current_index + 1) % len(responses)
            redis_svc.set(redis_key, str(next_index))
            
            await update.message.reply_text(response)
            return

    # Check CHAT_RESPONSES (exact match)
    if text in CHAT_RESPONSES:
        response = CHAT_RESPONSES[text]
        
        # If it's a list/tuple of responses, cycle through them
        if isinstance(response, (list, tuple)):
            redis_key = f"chat_cycle:{text}"
            current_index = int(redis_svc.get(redis_key) or 0)
            
            # Get the response at current index (ensure it's a string)
            msg_response = str(response[current_index])
            
            # Update index for next time (cycle back to 0 when reaching end)
            next_index = (current_index + 1) % len(response)
            redis_svc.set(redis_key, str(next_index))
        else:
            msg_response = str(response)
        
        await update.message.reply_text(msg_response)
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
    """Respond to 'بوت' with photo, caption, and inline buttons."""
    logger.info("handle_bot_info triggered for user: %s", update.effective_user.id)
    chat_id = update.effective_chat.id
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('⌯ أشموديل ⊁', url='https://t.me/BO1MA'),
        ],
        [
            InlineKeyboardButton('⌯ قناتنا ⊁', url='https://t.me/BO_MR'),
        ],
    ])
    caption = (
        '◍ لو عايز بوت مميز بدون توقف وامان  .\n'
        '◍قم بـ التواصل مع المطورين عبر الازرار تاليه .'
    )
    await context.bot.send_photo(
        chat_id=chat_id,
        photo='https://t.me/BO_MR/45',
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
    """Respond to 'لو خيروك' with a random would-you-rather option."""
    # Show one random option from all available
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


@group_only
async def handle_open_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    response = open_bank_account(user_id)
    await update.message.reply_text(response)

@group_only
async def handle_check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    await update.message.reply_text(f"🏦 رصيدك الحالي هو: {balance} نقطة.")

@group_only
async def handle_claim_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    response = claim_daily(user_id)
    await update.message.reply_text(response)

@group_only
async def handle_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ استخدم الأمر كالتالي: /transfer [المعرف] [المبلغ]")
        return

    try:
        target_id = int(args[0])
        amount = int(args[1])
        user_id = update.effective_user.id
        response = transfer_points(user_id, target_id, amount)
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("❌ تأكد من إدخال معرف صحيح ومبلغ صحيح.")


@group_only
async def handle_list_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = list_items()
    if not items:
        await update.message.reply_text("❌ السوق فارغ حاليًا.")
        return

    response = "📦 العناصر المتوفرة في السوق:\n"
    for item in items:
        item_id, seller_id, item_name, item_rarity, price = item
        response += f"🔹 [{item_id}] {item_name} ({item_rarity}) - {price} نقطة\n"
    await update.message.reply_text(response)

@group_only
async def handle_add_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("❌ استخدم الأمر كالتالي: /add_market [اسم العنصر] [الندرة] [السعر]")
        return

    item_name = args[0]
    item_rarity = args[1]
    try:
        price = int(args[2])
        user_id = update.effective_user.id
        response = add_item(user_id, item_name, item_rarity, price)
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("❌ تأكد من إدخال سعر صحيح.")


@group_only
async def handle_buy_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ استخدم الأمر كالتالي: /buy_market [رقم العنصر]")
        return

    try:
        item_id = int(args[0])
        user_id = update.effective_user.id
        response = buy_item(user_id, item_id)
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("❌ تأكد من إدخال رقم عنصر صحيح.")


@group_only
async def handle_multi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle multiple commands and send all related responses."""
    text = (update.message.text or "")
    responses = []

    if "بوت" in text or "البوت" in text:
        responses.append("◍ ينعم.")

    if "الالعاب" in text:
        responses.append("🎮 قائمة الألعاب: تخمين، الاسرع، الحروف، حزوره، والمزيد!")

    if "سي في" in text or "سيفي" in text:
        responses.append("📄 السيرة الذاتية: مطور محترف في تطوير البوتات.")

    if responses:
        await update.message.reply_text("\n".join(responses))


# Multi-command handler registration is already handled inside the register function.
def register(app: Application) -> None:
    """Register all auto-response handlers with the application."""
    G = filters.ChatType.GROUPS

    # Private welcome handler
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(?:start|/start)$") & filters.ChatType.PRIVATE,
        handle_private_start
    ), group=0)

    # Contact card (إيمو / أشموديل / احمد)
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(ايمو|إيمو|اشموديل|أشموديل|احمد)$") & G,
        handle_taki_contact
    ), group=40)

    # Developer contact
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(مين نصبلك|عايزه بوت|عايز بوت)$") & G,
        handle_developer_contact
    ), group=30)

    # Developer info
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(المطور|المبرمج|مطور البوت|المبرمج أشموديل|المبرمج إيمو|المبرمج احمد)$") & G,
        handle_developer_info
    ), group=40)

    # Source info
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(السورس|سورس|يا سورس)$") & G,
        handle_source_info
    ), group=40)

    # Bot info
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(البوت|بوت)$") & G,
        handle_bot_info
    ), group=10)

    # Would you rather
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(لو خيروك|خيروك)$") & G,
        handle_would_you_rather
    ), group=40)

    # Reverse text
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^العكس") & G,
        handle_reverse_text
    ), group=40)

    # Kick me joke
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(اطردني|طردني)$") & G,
        handle_kick_me
    ), group=40)

    # Marry me joke
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^تتجوزيني$") & G,
        handle_marry_me
    ), group=40)

    # Sing for me
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^غنيلي$") & G,
        handle_sing_for_me
    ), group=40)

    # Voice recognition placeholder
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(وش بيقول|بيقول اي|\?\?|؟؟)$") & G,
        handle_pronounce
    ), group=40)

    # Statistics
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^الاحصائيات$") & G,
        handle_statistics
    ), group=40)

    # Advice
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(انصح|انصحني|انصحيني|انصحنى|نصيحه|نصيحة)$") & G,
        handle_advice
    ), group=40)

    # Insult target (playful)
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)^(اشتم|اشتمو|اشتمه|شتمو|شتمه)$") & G,
        handle_insult_target
    ), group=40)

    # Auto-greetings (lowest priority in this group so specific commands go first)
    app.add_handler(MessageHandler(
        filters.TEXT & G,
        handle_greetings
    ), group=150)

    # Multi-keyword responder
    app.add_handler(MessageHandler(
        filters.Regex(r"(?i)(البوت|بوت|الالعاب|سي في|سيفي)") & G,
        handle_multi_command
    ), group=35)

    # New commands
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/open_bank$") & G, handle_open_bank), group=40)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/balance$") & G, handle_check_balance), group=40)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/daily$") & G, handle_claim_daily), group=40)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/transfer(?:\s+\d+\s+\d+)?$") & G, handle_transfer), group=40)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/list_market$") & G, handle_list_market), group=40)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/add_market(?:\s+.+\s+\S+\s+\d+)?$") & G, handle_add_market), group=40)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^/buy_market(?:\s+\d+)?$") & G, handle_buy_market), group=40)
