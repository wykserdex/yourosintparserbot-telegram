"""Integration tests for BulkCopyEngine and high-speed message insertion."""

from datetime import UTC, datetime

import pytest

from yourosint.contexts.ingestion.domain.message import RawMessage
from yourosint.infrastructure.database.copy import BulkCopyEngine


@pytest.mark.asyncio
async def test_bulk_copy_engine(db_session):
    engine = BulkCopyEngine(db_session)
    msgs = [
        RawMessage(
            message_id=i,
            chat_id=900,
            text=f"High speed bulk message #{i}",
            posted_at=datetime.now(UTC),
            sender_username="bulk_tester",
        )
        for i in range(1, 21)
    ]

    saved_count = await engine.bulk_insert_messages(msgs)
    assert saved_count == 20
