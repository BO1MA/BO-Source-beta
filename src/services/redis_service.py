"""
Redis service — wraps redis connection and provides typed helpers.
Mirrors the Redis usage in bian.lua / AVIRA.lua.
"""
import json
import logging
from typing import Any

import redis

from src.config import Config

logger = logging.getLogger(__name__)


class RedisService:
    """Singleton-style Redis wrapper used by all services."""

    _instance: "RedisService | None" = None
    _pool: redis.ConnectionPool | None = None

    def __new__(cls) -> "RedisService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Prefer REDIS_URL (supports Upstash, Redis Cloud, etc.)
            if Config.REDIS_URL:
                cls._pool = redis.ConnectionPool.from_url(
                    Config.REDIS_URL,
                    decode_responses=True,
                )
            else:
                pool_kwargs: dict = {
                    "host": Config.REDIS_HOST,
                    "port": Config.REDIS_PORT,
                    "db": Config.REDIS_DB,
                    "decode_responses": True,
                }
                if Config.REDIS_PASSWORD:
                    pool_kwargs["password"] = Config.REDIS_PASSWORD
                cls._pool = redis.ConnectionPool(**pool_kwargs)
        return cls._instance

    @property
    def client(self) -> redis.Redis:
        return redis.Redis(connection_pool=self._pool)

    # ── Primitive helpers ──

    def get(self, key: str) -> str | None:
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.client.set(key, value, ex=ex)

    def delete(self, key: str) -> None:
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def incr(self, key: str) -> int:
        return self.client.incr(key)

    def decr(self, key: str) -> int:
        return self.client.decr(key)

    # ── Hash helpers ──

    def hset(self, name: str, key: str, value: str) -> None:
        self.client.hset(name, key, value)

    def hget(self, name: str, key: str) -> str | None:
        return self.client.hget(name, key)

    def hgetall(self, name: str) -> dict:
        return self.client.hgetall(name)

    def hdel(self, name: str, key: str) -> None:
        self.client.hdel(name, key)

    def hkeys(self, name: str) -> list[str]:
        return self.client.hkeys(name)

    # ── Set helpers ──

    def sadd(self, name: str, *values: str) -> None:
        self.client.sadd(name, *values)

    def srem(self, name: str, *values: str) -> None:
        self.client.srem(name, *values)

    def smembers(self, name: str) -> set[str]:
        return self.client.smembers(name)

    def sismember(self, name: str, value: str) -> bool:
        return bool(self.client.sismember(name, value))

    def scard(self, name: str) -> int:
        return self.client.scard(name)

    # ── JSON helpers ──

    def set_json(self, key: str, data: Any) -> None:
        self.client.set(key, json.dumps(data, ensure_ascii=False))

    def get_json(self, key: str) -> Any | None:
        raw = self.client.get(key)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None
        return None

    # ── Key pattern helpers ──

    def keys(self, pattern: str) -> list[str]:
        return self.client.keys(pattern)

    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count deleted."""
        keys = self.client.keys(pattern)
        if keys:
            return self.client.delete(*keys)
        return 0
