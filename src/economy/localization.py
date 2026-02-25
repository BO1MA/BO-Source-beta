STRINGS = {
    "ar": {
        "start": "أهلاً بك {name} في بوت الإدارة والألعاب! 🎮",
        "no_admin": "❌ عذراً، هذا الأمر للمديرين فقط!",
        "game_win": "مبروك {name}! ربحت {points} نقطة. 🎉",
        "lang_set": "تم تغيير لغة البوت إلى العربية بنجاح. ✅",
        "bank_balance": "🏦 رصيدك الحالي هو: {amount} نقطة.",
        "bank_daily": "💰 لقد حصلت على هدية يومية: {amount} نقطة!",
        "bank_no_money": "❌ رصيدك لا يكفي للقيام بهذه العملية!",
        "bank_transfer": "✅ تم تحويل {amount} نقطة إلى {target}.",
        "need_account": "⚠️ يجب فتح حساب بنكي أولاً! استخدم أمر /open_bank"
    },
    "en": {
        "start": "Welcome {name} to the Admin & Games bot! 🎮",
        "no_admin": "❌ Sorry, this command is for admins only!",
        "game_win": "Congrats {name}! You won {points} points. 🎉",
        "lang_set": "Bot language has been set to English successfully. ✅",
        "bank_balance": "🏦 Your current balance is: {amount} points.",
        "bank_daily": "💰 You received a daily gift: {amount} points!",
        "bank_no_money": "❌ You don't have enough balance!",
        "bank_transfer": "✅ Transferred {amount} points to {target}.",
        "need_account": "⚠️ You must open a bank account first! Use /open_bank"
    }
}

def get_string(lang: str, key: str, **kwargs) -> str:
    return STRINGS.get(lang, STRINGS["ar"]).get(key, "").format(**kwargs)
