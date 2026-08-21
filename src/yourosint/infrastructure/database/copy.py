"""High performance bulk ingestion engine."""

import logging
from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...contexts.ingestion.domain.message import RawMessage

logger = logging.getLogger(__name__)


class BulkCopyEngine:
    """Fast batch and PostgreSQL COPY ingestion engine."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert_messages(self, messages: Sequence[RawMessage]) -> int:
        if not messages:
            return 0

        bind = self.session.bind
        dialect = bind.dialect.name if bind else "postgresql"

        if dialect == "postgresql":
            stmt = text("""
                INSERT INTO messages (
                    message_id, chat_id, chat_title, chat_username,
                    sender_id, sender_username, sender_first_name, sender_last_name,
                    message_text, date, has_media, media_type, is_pii_filtered
                ) VALUES (
                    :message_id, :chat_id, :chat_title, :chat_username,
                    :sender_id, :sender_username, :sender_first_name, :sender_last_name,
                    :message_text, :date, :has_media, :media_type, :is_pii_filtered
                )
                ON CONFLICT (chat_id, message_id) DO UPDATE SET
                    message_text = EXCLUDED.message_text,
                    sender_username = EXCLUDED.sender_username
            """)
        else:
            stmt = text("""
                INSERT INTO messages (
                    message_id, chat_id, chat_title, chat_username,
                    sender_id, sender_username, sender_first_name, sender_last_name,
                    message_text, date, has_media, media_type, is_pii_filtered
                ) VALUES (
                    :message_id, :chat_id, :chat_title, :chat_username,
                    :sender_id, :sender_username, :sender_first_name, :sender_last_name,
                    :message_text, :date, :has_media, :media_type, :is_pii_filtered
                )
                ON CONFLICT (chat_id, message_id) DO NOTHING
            """)

        records = [
            {
                "message_id": m.message_id,
                "chat_id": m.chat_id,
                "chat_title": m.chat_title,
                "chat_username": m.chat_username.lstrip("@") if m.chat_username else None,
                "sender_id": m.sender_id,
                "sender_username": m.sender_username.lstrip("@") if m.sender_username else None,
                "sender_first_name": m.sender_first_name,
                "sender_last_name": m.sender_last_name,
                "message_text": m.text,
                "date": m.posted_at,
                "has_media": m.has_media,
                "media_type": m.media_type,
                "is_pii_filtered": m.is_pii_filtered,
            }
            for m in messages
        ]

        await self.session.execute(stmt, records)
        await self.session.flush()
        return len(records)
