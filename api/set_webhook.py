"""
Vercel serverless function — one-time webhook registration.

Hit this endpoint once after deploying to register your webhook URL:
  GET https://<your-app>.vercel.app/api/set_webhook

It tells Telegram to send updates to /api/webhook on this domain.
"""
import json
import logging
import asyncio
import sys
import os
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Bot

from src.config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Determine the deployment URL
            vercel_url = os.getenv("VERCEL_URL", "")
            custom_domain = os.getenv("WEBHOOK_DOMAIN", "")

            if custom_domain:
                domain = custom_domain
            elif vercel_url:
                domain = vercel_url
            else:
                self._respond(400, {"error": "Cannot determine domain. Set WEBHOOK_DOMAIN env var."})
                return

            # Ensure https://
            if not domain.startswith("https://"):
                domain = f"https://{domain}"

            webhook_url = f"{domain}/api/webhook"

            # Set the webhook
            result = asyncio.run(self._set_webhook(webhook_url))

            self._respond(200, {
                "success": True,
                "webhook_url": webhook_url,
                "telegram_response": str(result),
            })
            logger.info("Webhook set to: %s", webhook_url)

        except Exception as e:
            logger.error("Failed to set webhook: %s", e, exc_info=True)
            self._respond(500, {"error": str(e)})

    @staticmethod
    async def _set_webhook(url: str) -> bool:
        bot = Bot(token=Config.BOT_TOKEN)
        async with bot:
            # Delete old webhook first, then set new one
            await bot.delete_webhook(drop_pending_updates=True)
            result = await bot.set_webhook(
                url=url,
                allowed_updates=["message", "callback_query", "chat_member", "my_chat_member"],
            )
            return result

    def _respond(self, status: int, body: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, indent=2).encode())
