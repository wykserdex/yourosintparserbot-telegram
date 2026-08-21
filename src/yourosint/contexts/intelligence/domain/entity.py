"""Intelligence Domain: Core Intelligence Entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class EntityType(StrEnum):
    """Supported intelligence entity types."""

    PERSON = "person"
    DOMAIN = "domain"
    IP = "ip"
    EMAIL = "email"
    PHONE = "phone"
    CARD = "card"
    CHANNEL = "channel"
    USERNAME = "username"
    CRYPTO_BTC = "crypto_btc"
    CRYPTO_ETH = "crypto_eth"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class IntelligenceEntity:
    """Core intelligence entity (dataclass)."""

    type: EntityType
    value: str
    id: int | None = None
    blind_index: str | None = None
    masked_value: str | None = None
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    reputation: int = 0
    tags: list[str] = field(default_factory=list)
    description: str | None = None
    source_type: str = "message"
    enrichment_data: dict[str, Any] = field(default_factory=dict)
    last_enriched: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(UTC)

    def update_reputation(self, score: int) -> None:
        self.reputation = max(0, min(100, score))
        self.updated_at = datetime.now(UTC)
