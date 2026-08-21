"""Graph Domain: Node entity."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GraphNode:
    """Node in OSINT network graph."""

    id: str
    label: str
    type: str  # 'target', 'contact', 'entity', 'channel'
    size: int = 25
    color: str = "#3b82f6"
    user_id: int | None = None
    object_id: int | None = None
    total_msgs: int = 0
    unique_chats: int = 0
    full_name: str | None = None
    reputation: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
