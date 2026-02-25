
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from src.economy.models import init_db, create_account, get_user, update_balance
from src.economy.localization import get_string
from src.economy.decorators import needs_bank_account
from src.utils.decorators import group_only

init_db()

async def _check_games_enabled(update, context) -> bool:
    from src.services.group_service import GroupService
    group_svc = GroupService()
    chat_id = update.effective_chat.id
    settings = group_svc.get_settings(chat_id)
    if not settings.games_enabled:
        await update.message.reply_text("✯ الألعاب معطلة في هذه المجموعة.")
        return False
    return True

@group_only
async def open_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _check_games_enabled(update, context):
        return
    user_id = update.effective_user.id
    lang = "ar"  # TODO: fetch from DB per group/user
    user = get_user(user_id)
    if user and user.get("has_account"):
        await update.message.reply_text("لديك حساب بنكي بالفعل! / You already have a bank account!")
        return
    create_account(user_id)
    await update.message.reply_text(get_string(lang, "bank_balance", amount=100))

@group_only
@needs_bank_account
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _check_games_enabled(update, context):
        return
    user_id = update.effective_user.id
    lang = "ar"  # TODO: fetch from DB per group/user
    user = get_user(user_id)
    await update.message.reply_text(get_string(lang, "bank_balance", amount=user["bank_balance"]))

@group_only
@needs_bank_account
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _check_games_enabled(update, context):
        return
    import random
    user_id = update.effective_user.id
    lang = "ar"  # TODO: fetch from DB per group/user
    gift = random.randint(50, 200)
    update_balance(user_id, gift)
    await update.message.reply_text(get_string(lang, "bank_daily", amount=gift))

def register_economy_handlers(app):
    G = filters.ChatType.GROUPS
    app.add_handler(MessageHandler(filters.Regex("^(فتح حساب|open bank)$") & G, open_bank), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(رصيدي|balance)$") & G, balance), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(يومي|daily)$") & G, daily), group=15)
