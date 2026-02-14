"""
YouTube handler — search and download YouTube videos.
Based on yt.php and YouTube features from the Lua bot.
Uses yt-dlp for downloading.
"""
import logging
import os
import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from telegram.error import TelegramError

from src.constants.messages import MSG_YT_CHOOSE, MSG_YT_SEARCHING, MSG_YT_NOT_FOUND
from src.utils.keyboard import build_yt_keyboard

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


async def handle_youtube_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle YouTube search command: بحث يوتيوب <query> or يوتيوب <query>"""
    text = (update.message.text or "").strip()

    # Extract search query
    for prefix in ("بحث يوتيوب", "يوتيوب"):
        if text.startswith(prefix):
            query = text[len(prefix):].strip()
            break
    else:
        return

    if not query:
        await update.message.reply_text("\u2756 ارسل الكلمه للبحث عنها")
        return

    await update.message.reply_text(
        MSG_YT_CHOOSE,
        reply_markup=build_yt_keyboard(query),
    )


async def handle_yt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle YouTube download button press."""
    query = update.callback_query
    await query.answer()
    data = query.data  # yt:mp3:searchquery or yt:mp4:searchquery

    parts = data.split(":", 2)
    if len(parts) != 3:
        return

    fmt = parts[1]  # mp3 or mp4
    search_query = parts[2]

    await query.message.reply_text(MSG_YT_SEARCHING.format(query=search_query))

    try:
        output_path = DOWNLOAD_DIR / f"%(title)s.%(ext)s"

        if fmt == "mp3":
            cmd = [
                "yt-dlp",
                f"ytsearch1:{search_query}",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                "-o", str(output_path),
                "--no-playlist",
                "--max-filesize", "50M",
            ]
        else:  # mp4
            cmd = [
                "yt-dlp",
                f"ytsearch1:{search_query}",
                "-f", "best[filesize<50M]",
                "-o", str(output_path),
                "--no-playlist",
            ]

        # Run yt-dlp
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

        if process.returncode != 0:
            logger.error(f"yt-dlp error: {stderr.decode()}")
            await query.message.reply_text(MSG_YT_NOT_FOUND)
            return

        # Find the downloaded file
        downloaded_files = sorted(DOWNLOAD_DIR.glob("*"), key=os.path.getmtime, reverse=True)
        if not downloaded_files:
            await query.message.reply_text(MSG_YT_NOT_FOUND)
            return

        file_path = downloaded_files[0]

        # Send the file
        try:
            if fmt == "mp3":
                with open(file_path, "rb") as f:
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=f,
                        title=file_path.stem,
                    )
            else:
                with open(file_path, "rb") as f:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=f,
                        caption=file_path.stem,
                    )
        finally:
            # Clean up downloaded file
            try:
                file_path.unlink()
            except OSError:
                pass

    except asyncio.TimeoutError:
        await query.message.reply_text("\u2756 انتهى الوقت المحدد للتحميل \u23F0")
    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        await query.message.reply_text(f"\u2756 حدث خطأ: {str(e)[:100]}")


def register(app: Application) -> None:
    """Register YouTube handlers."""
    app.add_handler(MessageHandler(
        filters.Regex("^(بحث يوتيوب|يوتيوب)"),
        handle_youtube_search,
    ), group=20)

    app.add_handler(CallbackQueryHandler(handle_yt_callback, pattern="^yt:"))
