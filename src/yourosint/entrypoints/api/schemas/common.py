"""Pydantic v2 schemas for API boundaries."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"
    timestamp: datetime


class StatsResponse(BaseModel):
    total_messages: int
    total_users: int
    total_chats: int
    total_objects: int
    active_accounts: int = 1
    autopilot_status: str = "ready"


class ParseChatRequest(BaseModel):
    chat_username: str = Field(..., description="Target Telegram channel/chat username")
    limit: int = Field(default=200, ge=1, le=10000)
    enable_pii_filter: bool = True


class ParseChatResponse(BaseModel):
    chat_username: str
    messages_parsed: int
    messages_saved: int
    duration_seconds: float


class EntityResponse(BaseModel):
    id: int
    type: str
    value: str
    masked_value: str | None = None
    first_seen: datetime
    last_seen: datetime
    reputation: int
    tags: list[str] = Field(default_factory=list)
    description: str | None = None
    source_type: str = "message"
    enrichment_data: dict[str, Any] = Field(default_factory=dict)
    last_enriched: datetime | None = None


class SearchResponse(BaseModel):
    query: str
    total_entities: int
    entities: list[EntityResponse] = Field(default_factory=list)
    total_messages: int = 0
    messages: list[dict[str, Any]] = Field(default_factory=list)
    phone_info: dict[str, Any] | None = None


class GraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    size: int
    color: str
    user_id: int | None = None
    full_name: str | None = None
    reputation: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    weight: int
    type: str
    label: str | None = None
    style: str = "solid"
    color: str = "#6366f1"


class InvestigationGraphResponse(BaseModel):
    nodes: list[GraphNodeResponse] = Field(default_factory=list)
    edges: list[GraphEdgeResponse] = Field(default_factory=list)
    target_username: str | None = None
    target_id: int | None = None
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0
