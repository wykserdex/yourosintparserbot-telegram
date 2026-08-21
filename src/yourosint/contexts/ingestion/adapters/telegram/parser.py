"""Ingestion Smart Parser with realistic jitter and delays."""

import asyncio
import logging
import random
from collections.abc import AsyncIterator
from typing import Any

from ...domain.message import RawMessage

logger = logging.getLogger(__name__)


class SmartParser:
    """Streams messages with human-like rate limiting and jitter."""

    def __init__(
        self,
        client: Any,
        base_delay: float = 0.8,
        max_delay: float = 4.0,
    ):
        self.client = client
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._profile = {
            "delay_variance": random.uniform(0.8, 1.3),
            "batch_size": random.randint(40, 80),
            "jitter": random.uniform(0.1, 0.4),
        }

    async def parse_chat(
        self, chat: str | int, limit: int = 100, min_id: int = 0
    ) -> AsyncIterator[RawMessage]:
        count = 0
        async for msg in self.client.iter_messages(chat=chat, limit=limit, min_id=min_id):
            yield msg
            count += 1

            if count % int(self._profile["batch_size"]) == 0:
                pause = self.base_delay * self._profile["delay_variance"] + random.uniform(0.5, 1.5)
                await asyncio.sleep(pause)
            else:
                await asyncio.sleep(self._profile["jitter"])
