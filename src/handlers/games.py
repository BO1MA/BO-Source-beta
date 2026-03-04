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
from src.economy.bank_system import update_balance, get_balance, has_bank_account, open_bank_account

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

# Speed words (Lua: الاسرع / ترتيب)
SPEED_WORDS = [
    "سحور", "سياره", "استقبال", "قنفه", "ايفون", "بزونه", "مطبخ", "كرستيانو",
    "دجاجه", "مدرسه", "الوان", "غرفه", "ثلاجه", "كهوه", "سفينه", "العراق",
    "محطه", "طياره", "رادار", "منزل", "مستشفى", "كهرباء", "تفاحه", "اخطبوط",
    "سلمون", "فرنسا", "برتقاله", "تفاح", "مطرقه", "بتيته", "لهانه", "شباك",
    "باص", "سمكه", "ذباب", "تلفاز", "حاسوب", "انترنيت", "ساحه", "جسر",
]

# Arabic words for word scramble game
SCRAMBLE_WORDS = [
    "مدرسه", "كتاب", "قلم", "حياه", "سماء", "بحر", "جبل",
    "شجره", "ورده", "نجمه", "قمر", "شمس", "بيت", "باب",
    "سياره", "طائره", "هاتف", "حاسوب", "صديق", "عائله",
    "مسجد", "حديقه", "مطبخ", "غرفه", "شارع", "مدينه",
]

OPPOSITE_PAIRS = {
    "باي": "هلو",
    "فهمت": "مافهمت",
    "موزين": "زين",
    "اسمعك": "ماسمعك",
    "احبك": "ماحبك",
    "موحلو": "حلو",
    "نضيف": "وصخ",
    "حاره": "بارده",
    "ناصي": "عالي",
    "جوه": "فوك",
    "سريع": "بطيء",
    "ونسه": "ضوجه",
    "طويل": "قزم",
    "سمين": "ضعيف",
    "ضعيف": "قوي",
    "شريف": "كواد",
    "شجاع": "جبان",
    "رحت": "اجيت",
    "عدل": "ميت",
    "نشيط": "خامل",
    "شبعان": "جوعان",
    "موعطشان": "عطشان",
    "خوش ولد": "موخوش ولد",
    "اني": "موب اني",
    "هادئ": "عصبي",
}


# ── Helpers ──

async def _check_games_enabled(update, context) -> bool:
    """Check games enabled + force subscribe."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    settings = group_svc.get_settings(chat_id)

    if not settings.games_enabled:
        await update.message.reply_text(MSG_GAMES_LOCKED)
        return False

    if settings.force_subscribe_enabled:
        # Use per-group channel or fall back to global default from Config
        channel_ref = settings.force_subscribe_channel or Config.CHANNEL_USERNAME or ""
        if not channel_ref and Config.CHANNEL_ID:
            channel_ref = str(Config.CHANNEL_ID)
        
        if channel_ref:
            try:
                # Try numeric channel ID first, then username
                if channel_ref.lstrip('-').isdigit():
                    channel_id = int(channel_ref)
                else:
                    channel_id = channel_ref if channel_ref.startswith("@") else f"@{channel_ref}"
                if not await check_channel_membership(context.bot, channel_id, user_id):
                    channel_display = channel_ref if channel_ref.startswith("@") else f"@{channel_ref}"
                    await update.message.reply_text(MSG_FORCE_SUBSCRIBE.format(channel=channel_display))
                    return False
            except Exception:
                pass
    return True

async def _check_user_has_bank_account(update, context):
    """Ensure the user has a bank account before playing games."""
    user_id = update.effective_user.id
    if not has_bank_account(user_id):
        await update.message.reply_text("❌ You need a bank account to play games. Creating one for you...")
        open_bank_account(user_id)
        await update.message.reply_text("✅ Bank account created successfully! You can now play games.")

def _game_key(game_type: str, chat_id: int) -> str:
    return f"game:{game_type}:{chat_id}"


def _score_key(chat_id: int, user_id: int) -> str:
    return f"game:fastest:{chat_id}:{user_id}"


async def _award_point(chat_id: int, user_id: int) -> None:
    redis_svc.incr(_score_key(chat_id, user_id))


def _normalize_answer(text: str) -> str:
    return (
        (text or "")
        .strip()
        .lower()
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ى", "ي")
        .replace("ة", "ه")
        .replace("ـ", "")
    )


# ══════════════════════════════════════════════════
# 1) السمايلات — Emoji Race
# ══════════════════════════════════════════════════

@group_only
async def handle_emoji_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    emoji = random.choice(EMOJI_POOL)
    redis_svc.set(_game_key("emoji", update.effective_chat.id), emoji, ex=120)
    await update.message.reply_text(f"✯اسرع واحد يدز هاذا السمايل ? » {{{emoji}}}")


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
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ السمايلات , السمايلات }")


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
# 3) الاسرع — Speed Word Game (Lua parity)
# ══════════════════════════════════════════════════

@group_only
async def handle_speed_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    word = random.choice(SPEED_WORDS)
    letters = list(word)
    random.shuffle(letters)
    scrambled = " ".join(letters)
    redis_svc.set(_game_key("speed", chat_id), word, ex=120)
    await update.message.reply_text(f"✯اسرع واحد يرتبها » {{{scrambled}}}")


@group_only
async def handle_speed_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("speed", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("speed", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text("✯الف مبروك لقد فزت\n✯للعب مره اخره ارسل »{ الاسرع , ترتيب }")


# ══════════════════════════════════════════════════
# Leaderboard (kept as extra utility)
# ══════════════════════════════════════════════════

@group_only
async def handle_fastest_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        f"✯اسرع واحد يلكه الحرف المختلف ↓\n\n" + "\n".join(rows)
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
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ حروف , الحروف }")


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
    await update.message.reply_text(f"✯اسرع واحد يحل الحزوره ↓\n {{{riddle['question']}}}")


@group_only
async def handle_riddle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("riddle", chat_id))
    if not active:
        return
    norm_text = _normalize_answer(text)
    choices = [c.strip() for c in active.replace("/", " - ").split(" - ") if c.strip()]
    if any(_normalize_answer(choice) == norm_text for choice in choices):
        redis_svc.delete(_game_key("riddle", chat_id))
        winner = update.effective_user
        await _award_point(chat_id, winner.id)
        await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ حزوره }")


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
    await update.message.reply_text(f"✯اسرع واحد يدز معنى السمايل » {{{em['emoji']}}}")


@group_only
async def handle_meaning_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("meaning", chat_id))
    if not active:
        return
    if _normalize_answer(text) != _normalize_answer(active):
        return
    redis_svc.delete(_game_key("meaning", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text("✯ الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ معاني }")


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
        "✯ وين المحبس؟ (يمين / يسار)"
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
        await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ محيبس }")
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
        f"✯اسرع واحد يلكه المختلف ↓\n\n" + "\n".join(rows)
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
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ المختلف }")


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
    await update.message.reply_text(f"✯اسرع واحد يحل المساله ↓\n {{{question}}}")


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
        await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ رياضيات }")


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
    await update.message.reply_text(f"✯اسرع واحد يترجمها انكليزي ↓\n {{{word['word']}}}")


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
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ انكليزي }")


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
    await update.message.reply_text(f"✯اسرع واحد يكمل المثل ↓\n {{{proverb['proverb']}}}")


@group_only
async def handle_proverb_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("proverb", chat_id))
    if not active or _normalize_answer(text) != _normalize_answer(active):
        return
    redis_svc.delete(_game_key("proverb", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ امثله }")


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
    await update.message.reply_text(f"✯اسرع واحد يرتبها ↓\n {{{scrambled}}}")


@group_only
async def handle_scramble_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("scramble", chat_id))
    if not active or _normalize_answer(text) != _normalize_answer(active):
        return
    redis_svc.delete(_game_key("scramble", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ كلمات }")


# ══════════════════════════════════════════════════
# Extra) عكس — Opposite Word Game (Lua-inspired)
# ══════════════════════════════════════════════════

@group_only
async def handle_opposite_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_games_enabled(update, context):
        return
    chat_id = update.effective_chat.id
    prompt, answer = random.choice(list(OPPOSITE_PAIRS.items()))
    redis_svc.set(_game_key("opposite", chat_id), answer, ex=120)
    await update.message.reply_text(f"✯ لعبة العكس\n✯ هات عكس: {prompt}")


@group_only
async def handle_opposite_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    active = redis_svc.get(_game_key("opposite", chat_id))
    if not active or text != active:
        return
    redis_svc.delete(_game_key("opposite", chat_id))
    winner = update.effective_user
    await _award_point(chat_id, winner.id)
    await update.message.reply_text("✯الف مبروك لقد فزت\n ✯للعب مره اخره ارسل »{ عكس , العكس }")


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
        "game:emoji": "ارسل 'الالعاب$"
    }
    app.add_handler(MessageHandler(filters.Regex("^(تخمين|خمن)$") & G, handle_guess_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(اسرع|الاسرع|ترتيب|ترتيب الاوامر)$") & G, handle_speed_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^ترتيب الاسرع$") & G, handle_fastest_leaderboard), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(الحروف|حروف|حرف)$") & G, handle_letters_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(حزوره|الحزوره)$") & G, handle_riddle_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(معاني|المعاني)$") & G, handle_meaning_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(محيبس|المحيبس)$") & G, handle_ring_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^المختلف$") & G, handle_different_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^رياضيات$") & G, handle_math_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^انكليزي$") & G, handle_english_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(امثله|الامثله)$") & G, handle_proverb_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(كلمات|الكلمات|كتبات)$") & G, handle_scramble_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(عكس|العكس)$") & G, handle_opposite_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(اشتم|اشتمو)$") & G, handle_insult), group=15)

    # Answer checkers — low priority so they don't conflict with commands
    app.add_handler(MessageHandler(filters.TEXT & G, handle_emoji_answer), group=90)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_guess_answer), group=91)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_speed_answer), group=91)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_letter_answer), group=92)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_riddle_answer), group=93)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_meaning_answer), group=94)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_ring_answer), group=95)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_different_answer), group=96)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_math_answer), group=97)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_english_answer), group=98)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_proverb_answer), group=100)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_scramble_answer), group=101)
    app.add_handler(MessageHandler(filters.TEXT & G, handle_opposite_answer), group=102)

    # Callback query
    app.add_handler(CallbackQueryHandler(handle_game_callback, pattern="^game:"))

def register(app):
    """Register all game-related handlers with the application."""
    app.add_handler(MessageHandler(filters.Regex("^(تخمين|خمن)$"), handle_guess_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(اسرع|الاسرع|ترتيب|ترتيب الاوامر)$"), handle_speed_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(الحروف|حروف|حرف)$"), handle_letters_game), group=15)
    app.add_handler(MessageHandler(filters.Regex("^(حزوره|الحزوره)$"), handle_riddle_game), group=15)
