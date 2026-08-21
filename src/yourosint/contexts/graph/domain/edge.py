"""Graph Domain: Edge entity."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """Relationship edge in OSINT network graph."""

    source: str
    target: str
    weight: int = 1
    type: str = "direct"  # 'direct', 'second_level', 'relation'
    label: str | None = None
    style: str = "solid"  # 'solid', 'dashed'
    color: str = "#6366f1"
