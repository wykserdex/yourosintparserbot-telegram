"""Integration tests for SQL CTE graph query adapter."""

from datetime import UTC, datetime

import pytest

from yourosint.bootstrap import SqlAlchemyGraphQueryAdapter
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.ingestion.domain.message import RawMessage


@pytest.mark.asyncio
async def test_graph_cte_queries(db_session):
    msg_repo = SQLAlchemyMessageRepository(db_session)
    query_adapter = SqlAlchemyGraphQueryAdapter(db_session)

    # Ingest interacting messages
    now = datetime.now(UTC)
    await msg_repo.save_message(
        RawMessage(
            message_id=1,
            chat_id=10,
            sender_id=100,
            sender_username="target_user",
            text="Hello from target",
            posted_at=now,
        )
    )
    await msg_repo.save_message(
        RawMessage(
            message_id=2,
            chat_id=10,
            sender_id=200,
            sender_username="contact_one",
            text="Replying to target_user",
            posted_at=now,
        )
    )

    rows = await query_adapter.query_user_interactions("target_user")
    assert len(rows) >= 1
    assert any(r["user_id"] == 200 for r in rows)
