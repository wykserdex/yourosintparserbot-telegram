"""Ingestion Domain: Sources and Ingestion state."""

from dataclasses import dataclass
from enum import StrEnum


class SourceType(StrEnum):
    """Source system origins."""

    TELEGRAM_CHANNEL = "telegram_channel"
    TELEGRAM_GROUP = "telegram_group"
    API_INGEST = "api_ingest"
    FILE_IMPORT = "file_import"
    DISCOVERY = "discovery"


@dataclass(frozen=True, slots=True)
class IngestionCursor:
    """Cursor position marker for incremental parsing."""

    chat_id: int
    chat_username: str
    last_message_id: int
    total_ingested: int
