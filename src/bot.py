"""
Main bot entry point — initializes the Application, registers all handlers,
and starts polling.
"""
import logging
import sys

from telegram.ext import Application

from src.config import Config
from src.handlers import register_all_handlers

# ── Logging ──
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# Silence httpx noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    """Build the bot application, register handlers, and run."""
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)

    logger.info("Starting bot: %s", Config.BOT_NAME)

    # Build application
    app = Application.builder().token(Config.BOT_TOKEN).build()

    # Register all handler modules
    register_all_handlers(app)

    logger.info("All handlers registered. Starting polling...")

    # Start polling
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=[
            "message",
            "callback_query",
            "chat_member",
            "my_chat_member",
        ],
    )


if __name__ == "__main__":
    main()
