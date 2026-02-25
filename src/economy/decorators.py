from functools import wraps
from src.economy.models import get_user
from src.economy.localization import get_string

# Decorator to require a bank account

def needs_bank_account(handler):
    @wraps(handler)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user = get_user(user_id)
        lang = "ar"  # TODO: fetch from DB per group/user
        if not user or not user.get("has_account"):
            await update.message.reply_text(get_string(lang, "need_account"))
            return
        return await handler(update, context, *args, **kwargs)
    return wrapper
