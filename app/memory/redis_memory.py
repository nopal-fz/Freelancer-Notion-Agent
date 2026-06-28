from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from app.config import settings

TELEGRAM_CHAT_IDS_KEY = "freelanceros:telegram:chat_ids"
RECENT_MESSAGES_KEY_PREFIX = "freelanceros:telegram:recent_messages"


class RedisMemory:
    def __init__(self) -> None:
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    async def ping(self) -> bool:
        return bool(await self.redis.ping())

    async def save_chat_id(self, chat_id: int) -> None:
        await self.redis.sadd(TELEGRAM_CHAT_IDS_KEY, str(chat_id))

    async def get_chat_ids(self) -> list[int]:
        values = await self.redis.smembers(TELEGRAM_CHAT_IDS_KEY)
        return [int(value) for value in values]

    async def save_recent_message(
        self,
        chat_id: int,
        user_id: int,
        text: str,
        role: str = "user",
        max_messages: int = 20,
    ) -> None:
        key = self._recent_messages_key(chat_id)

        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "role": role,
            "text": text,
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.redis.lpush(key, json.dumps(payload))
        await self.redis.ltrim(key, 0, max_messages - 1)

    async def get_recent_messages(
        self,
        chat_id: int,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        key = self._recent_messages_key(chat_id)

        values = await self.redis.lrange(key, 0, limit - 1)

        messages = []
        for value in values:
            try:
                messages.append(json.loads(value))
            except json.JSONDecodeError:
                continue

        return messages

    async def close(self) -> None:
        await self.redis.aclose()

    def _recent_messages_key(self, chat_id: int) -> str:
        return f"{RECENT_MESSAGES_KEY_PREFIX}:{chat_id}"