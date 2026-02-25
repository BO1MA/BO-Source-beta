from src.economy.models import set_cheater, set_banned, seize_assets
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# /ban_seize <user_id>
async def ban_seize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /ban_seize <user_id>")
        return
    user_id = int(context.args[0])
    set_banned(user_id, True)
    seize_assets(user_id)
    await update.message.reply_text(f"تم حظر المستخدم {user_id} ومصادرة جميع أملاكه.")

# /pardon <user_id>
async def pardon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /pardon <user_id>")
        return
    user_id = int(context.args[0])
    set_banned(user_id, False)
    set_cheater(user_id, False)
    await update.message.reply_text(f"تم العفو عن المستخدم {user_id}.")

# Register admin commands
def register_economy_admin(app):
    app.add_handler(CommandHandler("ban_seize", ban_seize))
    app.add_handler(CommandHandler("pardon", pardon))
