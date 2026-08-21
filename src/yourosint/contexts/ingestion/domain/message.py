"""Ingestion Domain: Raw Message entity."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RawMessage:
    """Ingested Telegram message representation (pure dataclass)."""

    message_id: int
    chat_id: int
    text: str
    posted_at: datetime
    id: int | None = None
    chat_title: str | None = None
    chat_username: str | None = None
    sender_id: int | None = None
    sender_username: str | None = None
    sender_first_name: str | None = None
    sender_last_name: str | None = None
    has_media: bool = False
    media_type: str | None = None
    is_pii_filtered: bool = False
    metadata: dict = field(default_factory=dict)

    @property
    def sender_full_name(self) -> str:
        parts = [self.sender_first_name or "", self.sender_last_name or ""]
        name = " ".join(p for p in parts if p).strip()
        return (
            name
            if name
            else (f"@{self.sender_username}" if self.sender_username else f"User {self.sender_id}")
        )
