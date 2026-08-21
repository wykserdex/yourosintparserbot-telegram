"""Unit tests for SmartParser streaming and jitter."""

from datetime import UTC, datetime

import pytest

from yourosint.contexts.ingestion.adapters.telegram.parser import SmartParser
from yourosint.contexts.ingestion.domain.message import RawMessage


class MockTelegramClient:
    async def iter_messages(self, chat, limit=10, min_id=0):
        for i in range(1, limit + 1):
            yield RawMessage(
                message_id=i,
                chat_id=100,
                text=f"Message {i} mentioning @durov",
                posted_at=datetime.now(UTC),
            )


@pytest.mark.asyncio
async def test_smart_parser_stream():
    client = MockTelegramClient()
    parser = SmartParser(client=client, base_delay=0.01, max_delay=0.02)

    messages = []
    async for msg in parser.parse_chat(chat="test_channel", limit=5):
        messages.append(msg)

    assert len(messages) == 5
    assert messages[0].message_id == 1
