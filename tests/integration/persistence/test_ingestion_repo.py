"""Integration tests for Ingestion Repositories."""

from datetime import UTC, datetime

import pytest

from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyChatRepository,
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.ingestion.domain.chat import Chat
from yourosint.contexts.ingestion.domain.message import RawMessage


@pytest.mark.asyncio
async def test_save_and_search_messages(db_session):
    repo = SQLAlchemyMessageRepository(db_session)
    msg = RawMessage(
        message_id=10,
        chat_id=500,
        chat_username="threat_feed",
        sender_id=700,
        sender_username="analyst_x",
        text="Observed active credential stuffing campaign",
        posted_at=datetime.now(UTC),
    )
    saved = await repo.save_message(msg)
    assert saved.id is not None

    found, total = await repo.search_messages("credential")
    assert total == 1
    assert found[0].sender_username == "analyst_x"


@pytest.mark.asyncio
async def test_monitored_chats_crud(db_session):
    repo = SQLAlchemyChatRepository(db_session)
    chat = Chat(id=None, username="cyber_intel", title="Cyber Intel")
    added = await repo.add_chat(chat)
    assert added.id is not None

    all_chats = await repo.list_chats()
    assert len(all_chats) == 1
    assert all_chats[0].clean_username == "cyber_intel"
