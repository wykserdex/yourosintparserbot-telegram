"""Ingestion Application DTOs."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParseChatRequestDTO:
    chat_username: str
    limit: int = 500
    enable_pii_filter: bool = True


@dataclass(frozen=True, slots=True)
class ParseChatResultDTO:
    chat_username: str
    messages_parsed: int
    messages_saved: int
    duration_seconds: float
    error: str | None = None
