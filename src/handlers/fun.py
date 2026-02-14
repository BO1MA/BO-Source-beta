"""
Fun handler — حكمه, نكته, قصيده/شعر, خيرني, زخرفه, نسبه جمالي/حب/كره,
تويت, نصح, دول/اعلام, and other entertainment commands.
Ported from bian.lua / AVIRA.lua fun commands.
"""
import random
import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.constants.messages import (
    get_random_wisdom, get_random_joke, get_random_poetry,
    decorate_text, CHOICES, COUNTRY_FLAGS, BEAUTY_PHRASES,
    LOVE_PHRASES, HATE_PHRASES, WOULD_YOU_RATHER,
)
from src.utils.decorators import group_only
from src.utils.text_utils import extract_command_arg

logger = logging.getLogger(__name__)


@group_only
async def handle_wisdom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حكمه — send a random wisdom."""
    await update.message.reply_text(f"✯ حكمة اليوم:\n{get_random_wisdom()}")


@group_only
async def handle_joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نكته — send a random joke."""
    await update.message.reply_text(f"✯ نكته:\n{get_random_joke()}")


@group_only
async def handle_poetry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """قصيده / شعر — send a random poetry line."""
    await update.message.reply_text(f"✯ شعر:\n{get_random_poetry()}")


@group_only
async def handle_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """خيرني — random choice."""
    text = (update.message.text or "").strip()
    arg = text.replace("خيرني", "", 1).strip()

    if arg:
        # If user gives options separated by "او"
        options = [o.strip() for o in arg.split("او") if o.strip()]
        if len(options) >= 2:
            choice = random.choice(options)
            await update.message.reply_text(f"✯ اختياري هو: {choice}")
        else:
            await update.message.reply_text(f"✯ {random.choice(CHOICES)}")
    else:
        await update.message.reply_text(f"✯ {random.choice(CHOICES)}")


@group_only
async def handle_decorate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """زخرفه — decorate Arabic text."""
    text = (update.message.text or "").strip()
    arg = text.replace("زخرفه", "", 1).strip()

    if not arg and update.message.reply_to_message and update.message.reply_to_message.text:
        arg = update.message.reply_to_message.text

    if arg:
        decorated = decorate_text(arg)
        await update.message.reply_text(f"✯ الزخرفه:\n{decorated}")
    else:
        await update.message.reply_text("✯ اكتب نص بعد الامر للزخرفه")


@group_only
async def handle_beauty_pct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نسبه جمالي — random beauty percentage."""
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    pct = random.randint(1, 100)
    phrase = random.choice(BEAUTY_PHRASES).format(pct=pct)
    await update.message.reply_text(f"✯ {target.first_name}\n✯ {phrase}")


@group_only
async def handle_love_pct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نسبه حب — random love percentage."""
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    pct = random.randint(1, 100)
    phrase = random.choice(LOVE_PHRASES).format(pct=pct)
    await update.message.reply_text(f"✯ {target.first_name}\n✯ {phrase}")


@group_only
async def handle_hate_pct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نسبه كره — random hate percentage."""
    target = update.message.reply_to_message.from_user if update.message.reply_to_message else update.effective_user
    pct = random.randint(1, 100)
    phrase = random.choice(HATE_PHRASES).format(pct=pct)
    await update.message.reply_text(f"✯ {target.first_name}\n✯ {phrase}")


@group_only
async def handle_tweet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تويت — format text as a tweet-style message."""
    text = (update.message.text or "").strip()
    arg = text.replace("تويت", "", 1).strip()

    if not arg and update.message.reply_to_message and update.message.reply_to_message.text:
        arg = update.message.reply_to_message.text

    if arg:
        user = update.effective_user
        tweet = (
            f"┌─────────────────\n"
            f"│ 🐦 تغريده\n"
            f"│\n"
            f"│ {arg}\n"
            f"│\n"
            f"│ ✍️ {user.first_name}\n"
            f"└─────────────────"
        )
        await update.message.reply_text(tweet)
    else:
        await update.message.reply_text("✯ اكتب نص بعد الامر")


@group_only
async def handle_advice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نصح — give advice to a replied-to user."""
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
        advice = get_random_wisdom()
        await update.message.reply_text(f"✯ نصيحه لك يا {target.first_name}:\n{advice}")
    else:
        await update.message.reply_text(f"✯ نصيحة اليوم:\n{get_random_wisdom()}")


@group_only
async def handle_country_flag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دول / اعلام — show country flags."""
    text = (update.message.text or "").strip()

    if text in ("اعلام", "دول"):
        # Show all flags
        lines = ["✯ اعلام الدول:"]
        for country, flag in COUNTRY_FLAGS.items():
            lines.append(f"  {flag} {country}")
        await update.message.reply_text("\n".join(lines))
        return

    # Check if the text is a country name
    arg = text.replace("علم", "").strip()
    if arg in COUNTRY_FLAGS:
        await update.message.reply_text(f"✯ علم {arg}: {COUNTRY_FLAGS[arg]}")


@group_only
async def handle_say(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """قول — bot repeats what you say."""
    text = (update.message.text or "").strip()
    arg = text.replace("قول", "", 1).strip()
    if arg:
        await update.message.reply_text(arg)


@group_only
async def handle_who_is(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """مين — randomly pick someone from the group."""
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    # If "مين" is followed by text, pick from group members
    arg = text.replace("مين", "", 1).strip()

    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        # Gather all admin members (non-bot) as pool
        members = [a.user for a in admins if not a.user.is_bot]
        if members:
            chosen = random.choice(members)
            if arg:
                await update.message.reply_text(
                    f"✯ {arg}: {chosen.first_name}"
                )
            else:
                await update.message.reply_text(
                    f"✯ الاختيار العشوائي: {chosen.first_name}"
                )
        else:
            await update.message.reply_text("✯ لا يمكن اختيار شخص")
    except Exception:
        await update.message.reply_text("✯ لا يمكن اختيار شخص")


@group_only
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الوقت / الساعه — show current time."""
    import datetime
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))  # Baghdad time
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%Y/%m/%d")
    day_names = {
        "Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الاربعاء",
        "Thursday": "الخميس", "Friday": "الجمعه", "Saturday": "السبت",
        "Sunday": "الاحد",
    }
    day = day_names.get(now.strftime("%A"), now.strftime("%A"))
    await update.message.reply_text(
        f"✯ الوقت: {time_str}\n"
        f"✯ التاريخ: {date_str}\n"
        f"✯ اليوم: {day}"
    )


@group_only
async def handle_would_you_rather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """خيروك / لو خيروك — would you rather game."""
    option_a, option_b = random.choice(WOULD_YOU_RATHER)
    await update.message.reply_text(
        f"✯ لو خيروك 🤔\n"
        f"1. {option_a}\n"
        f"2. {option_b}"
    )


def register(app: Application) -> None:
    """Register fun command handlers."""
    G = filters.ChatType.GROUPS

    app.add_handler(MessageHandler(filters.Regex("^حكمه$") & G, handle_wisdom), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(نكته|عايز اضحك|قولي نكته)$") & G, handle_joke), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(قصيده|شعر)$") & G, handle_poetry), group=16)
    app.add_handler(MessageHandler(filters.Regex("^خيرني") & G, handle_choose), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(زخرفه|زخرف)") & G, handle_decorate), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(نسبه جمالي|نسبة جمالي|جمالي)$") & G, handle_beauty_pct), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(نسبه حب|نسبة حب)$") & G, handle_love_pct), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(نسبه كره|نسبة كره)$") & G, handle_hate_pct), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(تويت|كت تويت)") & G, handle_tweet), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(نصح|نصيحه|انصح|انصحنى|انصحني)$") & G, handle_advice), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(اعلام|دول|اعلام ودول|اعلام و دول)$") & G, handle_country_flag), group=16)
    app.add_handler(MessageHandler(filters.Regex("^علم ") & G, handle_country_flag), group=16)
    app.add_handler(MessageHandler(filters.Regex("^قول ") & G, handle_say), group=16)
    app.add_handler(MessageHandler(filters.Regex("^مين( |$)") & G, handle_who_is), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(الوقت|الساعه)$") & G, handle_time), group=16)
    app.add_handler(MessageHandler(filters.Regex("^(خيروك|لو خيروك)$") & G, handle_would_you_rather), group=16)
