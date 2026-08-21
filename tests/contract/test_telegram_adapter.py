"""Contract tests for Telegram Adapter."""

from collections.abc import AsyncIterator

import pytest

from yourosint.contexts.ingestion.adapters.telegram.client import SmartTelegramClient
from yourosint.contexts.ingestion.domain.message import RawMessage


@pytest.mark.asyncio
async def test_telegram_client_contract():
    client = SmartTelegramClient(session_name="contract_test_session")
    await client.start()

    me = await client.get_me()
    assert me is not None
    assert "username" in me

    # Test async iterator contract
    message_stream = client.iter_messages(chat="contract_chat", limit=3)
    assert isinstance(message_stream, AsyncIterator)

    messages = [msg async for msg in message_stream]
    assert len(messages) >= 1
    assert isinstance(messages[0], RawMessage)
    assert messages[0].message_id > 0

    await client.stop()
