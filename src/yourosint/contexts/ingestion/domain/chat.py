"""Ingestion Domain: Monitored Chat and Channel aggregate."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class Chat:
    """Monitored Telegram channel or supergroup."""

    id: int | None
    username: str
    title: str | None = None
    chat_id: int | None = None
    last_parsed_id: int = 0
    total_messages: int = 0
    is_active: bool = True
    discovered_via: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def clean_username(self) -> str:
        return self.username.lstrip("@").strip().lower()

    def advance_cursor(self, latest_message_id: int, new_messages_count: int) -> None:
        """Updates ingestion cursor and counters."""
        self.last_parsed_id = max(self.last_parsed_id, latest_message_id)
        self.total_messages += new_messages_count
        self.updated_at = datetime.now(UTC)
