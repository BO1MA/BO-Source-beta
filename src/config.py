"""
Bot configuration — loads settings from environment variables / .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Config:
    # ── Bot ──
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_NAME: str = os.getenv("BOT_NAME", "MyBot")

    # ── Developer ──
    SUDO_ID: int = int(os.getenv("SUDO_ID", "") or "0")
    SUDO_USERNAME: str = os.getenv("SUDO_USERNAME", "")

    # ── Redis (supports Vercel KV env vars automatically) ──
    REDIS_URL: str = os.getenv("REDIS_URL", "") or os.getenv("KV_URL", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "") or "6379")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "") or "0")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # ── Channel (force subscribe) ──
    CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "")
    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "") or "0")

    # ── YouTube ──
    YT_COOKIES_PATH: str = os.getenv("YT_COOKIES_PATH", "")

    @classmethod
    def validate(cls) -> None:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required. Set it in .env")
        if not cls.SUDO_ID:
            raise ValueError("SUDO_ID is required. Set it in .env")
