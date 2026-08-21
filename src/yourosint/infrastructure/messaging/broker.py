"""Message broker primitives and in-memory event bus."""

import contextlib
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from ...shared.domain.events import DomainEvent


class MessageBroker(Protocol):
    """Abstract message broker for asynchronous domain events."""

    async def publish(self, topic: str, event: DomainEvent) -> None: ...

    def subscribe(self, topic: str, handler: Callable[[DomainEvent], Awaitable[None]]) -> None: ...


class InMemoryMessageBroker:
    """In-memory async topic-based message broker."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe(self, topic: str, handler: Callable[[Any], Awaitable[None]]) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    async def publish(self, topic: str, event: DomainEvent) -> None:
        handlers = self._subscribers.get(topic, [])
        for h in handlers:
            with contextlib.suppress(Exception):
                await h(event)
