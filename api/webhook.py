"""
Vercel serverless function — receives Telegram webhook updates.
"""
import json
import logging
import asyncio
import sys
import os
from http.server import BaseHTTPRequestHandler

# Ensure project root is on the path so `src` is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import Application

from src.config import Config
from src.handlers import register_all_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Build the Application once (reused across warm invocations) ──
_app: Application | None = None


async def _get_app() -> Application:
    """Lazily build and initialize the Application singleton."""
    global _app
    if _app is None:
        Config.validate()
        _app = Application.builder().token(Config.BOT_TOKEN).build()
        register_all_handlers(_app)
        await _app.initialize()
        logger.info("Application initialized (webhook mode)")
    return _app


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for Telegram webhook POST requests."""

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            asyncio.run(self._process_update(data))

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            logger.error("Error processing update: %s", e, exc_info=True)
            self.send_response(200)  # Always 200 to prevent Telegram retries
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Error handled")

    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({"status": "alive", "bot": Config.BOT_NAME}).encode()
        )

    @staticmethod
    async def _process_update(data: dict) -> None:
        """Deserialize the update and feed it through the bot handlers."""
        app = await _get_app()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
