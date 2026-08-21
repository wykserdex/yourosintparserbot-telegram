"""Intelligence Domain: Provenance Evidence entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .confidence import Confidence


@dataclass(frozen=True, slots=True)
class Evidence:
    """Verifiable source proof showing origin, confidence, and context of an entity."""

    source_id: str
    source_type: str
    raw_context: str
    content_hash: str
    extractor_version: str = "regex_v2.0"
    confidence: Confidence = field(default_factory=lambda: Confidence.from_float(0.95))
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    extracted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    chat_username: str | None = None
    chat_id: str | None = None
    message_id: int | None = None
    id: int | None = None
    entity_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
