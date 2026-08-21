"""Domain event primitives and publisher protocols."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base immutable domain event."""

    event_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


class EventBus(Protocol):
    """Protocol for publishing and subscribing to domain events."""

    async def publish(self, event: DomainEvent) -> None: ...

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], Awaitable[None]]
    ) -> None: ...


class InMemoryEventBus:
    """In-memory async implementation of EventBus."""

    def __init__(self):
        self._handlers: dict[type[DomainEvent], list[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[Any], Awaitable[None]]
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler failed for {event.event_name}: {e}", exc_info=True)


# Core Domain Events across Bounded Contexts
@dataclass(frozen=True, slots=True, kw_only=True)
class MessageImported(DomainEvent):
    message_id: int
    chat_username: str | None
    chat_id: int
    text_content: str
    sender_username: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class EntitiesExtracted(DomainEvent):
    source_id: str
    source_type: str
    entities_count: int
    entity_types: list[str]


@dataclass(frozen=True, slots=True, kw_only=True)
class EntityEnriched(DomainEvent):
    entity_id: int
    entity_type: str
    reputation_score: int
    provider_name: str
