"""Graph Domain: Investigation Graph Aggregate."""

from dataclasses import dataclass, field

from .edge import GraphEdge
from .node import GraphNode


@dataclass(frozen=True, slots=True)
class InvestigationGraph:
    """Network topology graph aggregate."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    target_username: str | None = None
    target_id: int | None = None
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0
