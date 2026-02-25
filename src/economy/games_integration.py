from src.economy.models import update_balance, get_user
from src.economy.decorators import needs_bank_account
from src.economy.localization import get_string

# Example: integrate with a game handler
# Usage: call award_points(update, context, points) after a win
@needs_bank_account
async def award_points(update, context, points: int):
    user_id = update.effective_user.id
    lang = "ar"  # TODO: fetch from DB per group/user
    update_balance(user_id, points)
    await update.message.reply_text(get_string(lang, "game_win", name=update.effective_user.first_name, points=points))
