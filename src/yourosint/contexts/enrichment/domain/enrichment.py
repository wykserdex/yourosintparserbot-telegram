"""Enrichment Domain: Enrichment Record entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class EnrichmentRecord:
    """External intelligence lookup result record."""

    entity_id: int
    provider_name: str
    risk_score: int
    data: dict[str, Any]
    enriched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
