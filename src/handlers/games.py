"""
Games handler — 12 games ported from games.lua / AVIRA.lua:
1. السمايلات (emoji race)      2. تخمين (number guess)
3. الاسرع (leaderboard)        4. الحروف (find letter)
5. حزوره (riddles)             6. معاني (emoji meanings)
7. محيبس (hidden ring)         8. المختلف (spot difference)
9. رياضيات (math quiz)         10. انكليزي (translation)
11. امثله (proverbs)           12. كلمات (word scramble)
+ اشتم (insult)
"""
import random
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters

from src.config import Config
from src.constants.messages import (
    MSG_GAME_EMOJI_PROMPT, MSG_GAME_EMOJI_WIN, MSG_GAME_GUESS_PROMPT,
    MSG_GAME_GUESS_WIN, MSG_GAME_GUESS_WRONG, MSG_GAMES_LOCKED,
    MSG_GAME_MENU, MSG_FORCE_SUBSCRIBE, MSG_NO_PERMISSION,
    get_random_insult, get_random_riddle, get_random_emoji_meaning,
    get_random_proverb, get_random_english_word, generate_math_question,
)
from src.services.user_service import UserService
from src.services.group_service import GroupService
from src.services.redis_service import RedisService
from src.utils.decorators import group_only
from src.utils.keyboard import build_games_keyboard
from src.utils.api_helpers import check_channel_membership

logger = logging.getLogger(__name__)
user_svc = UserService()
group_svc = GroupService()
redis_svc = RedisService()

# Emoji pool
EMOJI_POOL = [
    "😂", "😍", "🤣", "😎", "🤩", "😜", "😘", "🤪",
    "👍", "❤️", "🔥", "⭐", "🌟", "🌈", "🚀", "🏆",
    "🎉", "🎊", "👑", "💎", "🦁", "🐯", "🦅", "🐻",
    "🌹", "🦋", "🐸", "🐧", "🦊", "🐼", "🦄", "🐬",
    "🍎", "🍕", "⚽", "🎸", "🎯", "🎲", "🎮", "🎪",
]

ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")

# Arabic words for word scramble game
SCRAMBLE_WORDS = [
    "مدرسه", "كتاب", "قلم", "حياه", "سماء", "بحر", "جبل",
    "شجره", "ورده", "نجمه", "قمر", "شمس", "بيت", "باب",
    "سياره", "طائره", "هاتف", "حاسوب", "صديق", "عائله",
    "مسجد", "حديقه", "مطبخ", "غرفه", "شارع", "مدينه",
]


# ── Helpers ──

async def _check_games_enabled(update, context) -> bool:
    """Check games enabled + force subscribe."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    settings = group_svc.get_settings(chat_id)

    if not settings.games_enabled:
        await update.message.reply_text(MSG_GAMES_LOCKED)
        return False

    if settings.force_subscribe_enabled and settings.force_subscribe_channel:
        try:
            channel_id = int(settings.force_subscribe_channel) if settings.force_subscribe_channel.lstrip('-').isdigit() else Config.CHANNEL_ID
            if not await check_channel_membership(context.bot, channel_id, user_id):
                channel_name = settings.force_subscribe_channel if settings.force_subscribe_channel.startswith("@") else Config.CHANNEL_USERNAME
                await update.message.reply_text(MSG_FORCE_SUBSCRIBE.format(channel=channel_name))
                return False
        except Exception:
            pass
    return True


def _game_key(game_type: str, chat_id: int) -> str:
    return f"game:{game_type}:{chat_id}"


def _score_key(chat_id: int, user_id: int) -> str:
    return f"game:fastest:{chat_id}:{user_id}"


async def _award_point(chat_id: int, user_id: int) -> None:
    redis_svc.incr(_score_key(chat_id, user_id))


# ══════════════════════════════════════════════════
# 1) السمايلات — Emoji Race
# ══════════════════════════════════════════════════

@group_only
async def handle_emoji_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    emoji = random.choice(EMOJI_POOL)
    redis_svc.set(_game_key("emoji", update.effective_chat.id), emoji, ex=120)
    await update.message.reply_text(MSG_GAME_EMOJI_PROMPT.format(emoji=emoji))


@group_only
async def handle_emoji_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("emoji", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("emoji", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(MSG_GAME_EMOJI_WIN.format(name=winner.first_name))


# ══════════════════════════════════════════════════
# 2) تخمين — Number Guess
# ══════════════════════════════════════════════════

@group_only
async def handle_guess_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    number = random.randint(1, 10)
    redis_svc.set(_game_key("guess", update.effective_chat.id), str(number), ex=120)
    await update.message.reply_text(MSG_GAME_GUESS_PROMPT.format(max=10))


@group_only
async def handle_guess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    if not text.isdigit():
        return
    active = redis_svc.get(_game_key("guess", chat_id))
    if not active:
        return
    if text == active:
        redis_svc.delete(_game_key("guess", chat_id))
        winner = update.effective_user
        await _award_point(chat_id, winner.id)
        await update.message.reply_text(MSG_GAME_GUESS_WIN.format(name=winner.first_name))
    else:
        await update.message.reply_text(MSG_GAME_GUESS_WRONG)


# ══════════════════════════════════════════════════
# 3) الاسرع — Leaderboard
# ══════════════════════════════════════════════════

@group_only
async def handle_fastest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    keys = redis_svc.keys(f"game:fastest:{chat_id}:*")
    scores = []
    for key in keys:
        uid = int(key.rsplit(":", 1)[-1])
        count = int(redis_svc.get(key) or 0)
        user = user_svc.get_user(uid)
        scores.append((user.full_name, count))
    scores.sort(key=lambda x: x[1], reverse=True)

    if not scores:
        await update.message.reply_text("✯ لا توجد نتائج بعد")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = ["✯ ترتيب الاسرع 🏆:"]
    for i, (name, count) in enumerate(scores[:10]):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        lines.append(f"{medal} {name} — {count} فوز")
    await update.message.reply_text("\n".join(lines))


# ══════════════════════════════════════════════════
# 4) الحروف — Find the Different Letter
# ══════════════════════════════════════════════════

@group_only
async def handle_letters_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    main_letter = random.choice(ARABIC_LETTERS)
    diff_letter = random.choice([l for l in ARABIC_LETTERS if l != main_letter])
    grid = [main_letter] * 25
    grid[random.randint(0, 24)] = diff_letter
    rows = [" ".join(grid[i:i+5]) for i in range(0, 25, 5)]
    redis_svc.set(_game_key("letter", chat_id), diff_letter, ex=120)
    await update.message.reply_text(
        f"✯ لعبة الحروف 🔤\n✯ جد الحرف المختلف:\n\n" + "\n".join(rows)
    )


@group_only
async def handle_letter_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    if len(text) != 1:
        return
    active = redis_svc.get(_game_key("letter", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("letter", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(f"✯ مبروك {winner.first_name}! الحرف الصحيح 🎉")


# ══════════════════════════════════════════════════
# 5) حزوره — Riddles
# ══════════════════════════════════════════════════

@group_only
async def handle_riddle_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    riddle = get_random_riddle()
    redis_svc.set(_game_key("riddle", chat_id), riddle["answer"], ex=180)
    await update.message.reply_text(f"✯ حزوره ❓\n✯ {riddle['question']}")


@group_only
async def handle_riddle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("riddle", chat_id))
    if not active:
        return
    if text == active or text in active.split(" - "):
        redis_svc.delete(_game_key("riddle", chat_id))
        winner = update.effective_user
        await _award_point(chat_id, winner.id)
        await update.message.reply_text(f"✯ مبروك {winner.first_name}! الجواب الصحيح: {active} 🎉")


# ══════════════════════════════════════════════════
# 6) معاني — Emoji Meaning
# ══════════════════════════════════════════════════

@group_only
async def handle_meaning_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    em = get_random_emoji_meaning()
    redis_svc.set(_game_key("meaning", chat_id), em["answer"], ex=120)
    await update.message.reply_text(f"✯ ما معنى هاذا الايموجي؟ 🤔\n\n{em['emoji']}")


@group_only
async def handle_meaning_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("meaning", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("meaning", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(f"✯ مبروك {winner.first_name}! الجواب: {active} 🎉")


# ══════════════════════════════════════════════════
# 7) محيبس — Hidden Ring (pick a hand)
# ══════════════════════════════════════════════════

@group_only
async def handle_ring_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    hand = random.choice(["يمين", "يسار"])
    redis_svc.set(_game_key("ring", chat_id), hand, ex=60)
    await update.message.reply_text(
        "✯ لعبة المحيبس 💍\n"
        "✯ وين المحبس؟\n"
        "✯ ارسل: يمين او يسار"
    )


@group_only
async def handle_ring_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    if text not in ("يمين", "يسار"):
        return
    active = redis_svc.get(_game_key("ring", chat_id))
    if not active:
        return
    redis_svc.delete(_game_key("ring", chat_id))
    if text == active:
        winner = update.effective_user
        await _award_point(chat_id, winner.id)
        await update.message.reply_text(f"✯ مبروك {winner.first_name}! المحبس بال{active} 💍🎉")
    else:
        await update.message.reply_text(f"✯ خطأ! المحبس كان بال{active} 💍❌")


# ══════════════════════════════════════════════════
# 8) المختلف — Spot the Different Emoji
# ══════════════════════════════════════════════════

@group_only
async def handle_different_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    pairs = [
        ("😀", "😃"), ("🐶", "🐕"), ("🌹", "🌺"), ("⭐", "🌟"),
        ("🔴", "🟡"), ("🟢", "🔵"), ("🐱", "🐈"), ("🍎", "🍏"),
        ("🌙", "🌛"), ("❤️", "🧡"), ("🐻", "🧸"), ("☀️", "🌤"),
    ]
    main_emoji, diff_emoji = random.choice(pairs)
    grid = [main_emoji] * 16
    diff_pos = random.randint(0, 15)
    grid[diff_pos] = diff_emoji
    rows = [" ".join(grid[i:i+4]) for i in range(0, 16, 4)]
    # Store answer as row,col (1-based)
    row = diff_pos // 4 + 1
    col = diff_pos % 4 + 1
    redis_svc.set(_game_key("diff", chat_id), diff_emoji, ex=120)
    await update.message.reply_text(
        f"✯ جد المختلف 🔍\n\n" + "\n".join(rows)
    )


@group_only
async def handle_different_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("diff", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("diff", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(f"✯ مبروك {winner.first_name}! عيونك حاده 👁🎉")


# ══════════════════════════════════════════════════
# 9) رياضيات — Math Quiz
# ══════════════════════════════════════════════════

@group_only
async def handle_math_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    question, answer = generate_math_question()
    redis_svc.set(_game_key("math", chat_id), str(answer), ex=120)
    await update.message.reply_text(f"✯ رياضيات 🔢\n✯ {question}")


@group_only
async def handle_math_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    if not text.lstrip('-').isdigit():
        return
    active = redis_svc.get(_game_key("math", chat_id))
    if not active:
        return
    if text == active:
        redis_svc.delete(_game_key("math", chat_id))
        winner = update.effective_user
        await _award_point(chat_id, winner.id)
        await update.message.reply_text(f"✯ مبروك {winner.first_name}! الجواب الصحيح: {active} 🎉")


# ══════════════════════════════════════════════════
# 10) انكليزي — English Translation
# ══════════════════════════════════════════════════

@group_only
async def handle_english_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    word = get_random_english_word()
    redis_svc.set(_game_key("english", chat_id), word["answer"], ex=120)
    await update.message.reply_text(f"✯ ترجم الكلمه الى الانجليزيه 🇬🇧\n✯ {word['word']}")


@group_only
async def handle_english_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip().lower()
    active = redis_svc.get(_game_key("english", chat_id))
    if not active or text != active.lower():
        return
    redis_svc.delete(_game_key("english", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(f"✯ مبروك {winner.first_name}! الترجمه: {active} 🎉")


# ══════════════════════════════════════════════════
# 11) امثله — Proverb Completion
# ══════════════════════════════════════════════════

@group_only
async def handle_proverb_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    proverb = get_random_proverb()
    redis_svc.set(_game_key("proverb", chat_id), proverb["answer"], ex=120)
    await update.message.reply_text(f"✯ اكمل المثل 📜\n✯ {proverb['proverb']}")


@group_only
async def handle_proverb_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("proverb", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("proverb", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(f"✯ مبروك {winner.first_name}! الاكمال: {active} 🎉")


# ══════════════════════════════════════════════════
# 12) كلمات — Word Scramble
# ══════════════════════════════════════════════════

@group_only
async def handle_scramble_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    word = random.choice(SCRAMBLE_WORDS)
    letters = list(word)
    random.shuffle(letters)
    scrambled = " ".join(letters)
    redis_svc.set(_game_key("scramble", chat_id), word, ex=120)
    await update.message.reply_text(f"✯ رتب الحروف لتكوين كلمه 🔠\n✯ {scrambled}")


@group_only
async def handle_scramble_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("scramble", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("scramble", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text(f"✯ مبروك {winner.first_name}! الكلمه: {active} 🎉")


# ══════════════════════════════════════════════════
# Games Menu + Insult
# ══════════════════════════════════════════════════

@group_only
async def handle_games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = group_svc.get_settings(update.effective_chat.id)
    if not settings.games_enabled:
        await update.message.reply_text(MSG_GAMES_LOCKED)
        return
    await update.message.reply_text(MSG_GAME_MENU, reply_markup=build_games_keyboard())


@group_only
async def handle_insult(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target_name = update.message.reply_to_message.from_user.first_name
        await update.message.reply_text(f"{target_name} {get_random_insult()}")
    else:
        await update.message.reply_text(get_random_insult())


async def handle_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    game_help = {
        "game:emoji": "ارسل 'السمايلات' لبدء اللعبه",
        "game:guess": "ارسل 'تخمين' لبدء اللعبه",
        "game:fastest": "ارسل 'الاسرع' لعرض الترتيب",
        "game:letters": "ارسل 'الحروف' لبدء اللعبه",
        "game:riddle": "ارسل 'حزوره' لبدء اللعبه",
        "game:meaning": "ارسل 'معاني' لبدء اللعبه",
        "game:ring": "ارسل 'محيبس' لبدء اللعبه",
        "game:different": "ارسل 'المختلف' لبدء اللعبه",
        "game:math": "ارسل 'رياضيات' لبدء اللعبه",
        "game:english": "ارسل 'انكليزي' لبدء اللعبه",
        "game:proverb": "ارسل 'امثله' لبدء اللعبه",
        "game:scramble": "ارسل 'كلمات' لبدء اللعبه",
    }
    if data in game_help:
        await query.message.reply_text(game_help[data])


# ══════════════════════════════════════════════════
# Registration
# ══════════════════════════════════════════════════

def register(app: Application) -> None:
    """Register all 12 game handlers."""
    G = filters.ChatType.GROUPS

    # Game starters
    app.add_handler(MessageHandler(filters.Regex("^الالعاب$") & G, handle_games_menu), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(السمايلات|السمايل|سمايل|سمايلات)$") & G, handle_emoji_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(تخمين|خمن)$") & G, handle_guess_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(الاسرع|ترتيب|ترتيب الاوامر)$") & G, handle_fastest), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(الحروف|حروف|حرف)$") & G, handle_letters_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(حزوره|الحزوره)$") & G, handle_riddle_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(معاني|المعاني)$") & G, handle_meaning_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(محيبس|المحيبس)$") & G, handle_ring_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^المختلف$") & G, handle_different_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^رياضيات$") & G, handle_math_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^انكليزي$") & G, handle_english_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(امثله|الامثله)$") & G, handle_proverb_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(كلمات|الكلمات)$") & G, handle_scramble_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(اشتم|اشتمو)$") & G, handle_insult), group=15)

    # Answer checkers — low priority so they don't conflict with commands
    app.add_handler(MessageHandler(filters.TEXT & G, handle_emoji_answer), group=90)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_guess_answer), group=91)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_letter_answer), group=92)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_riddle_answer), group=93)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_meaning_answer), group=94)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_ring_answer), group=95)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_different_answer), group=96)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_math_answer), group=97)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_english_answer), group=98)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_proverb_answer), group=100)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_scramble_answer), group=101)

    # Callback query
    app.add_handler(CallbackQueryHandler(handle_game_callback, pattern="^game:"))
