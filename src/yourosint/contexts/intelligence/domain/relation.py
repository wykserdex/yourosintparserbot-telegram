"""Intelligence Domain: Graph Relationship entity."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RelationType(StrEnum):
    """Types of edges between intelligence entities."""

    MENTIONS = "mentions"
    OWNS = "owns"
    USES = "uses"
    CONTROLS = "controls"
    ASSOCIATES = "associates"
    COLLABORATES = "collaborates"
    MEMBER_OF = "member_of"
    INTERACTS = "interacts"


@dataclass(slots=True)
class Relation:
    """Relationship connecting two intelligence entities."""

    source_entity_id: int
    target_entity_id: int
    relation_type: RelationType = RelationType.MENTIONS
    weight: int = 1
    context: str | None = None
    first_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def increment_weight(self, amount: int = 1) -> None:
        self.weight += amount
        self.last_seen = datetime.now(UTC)
