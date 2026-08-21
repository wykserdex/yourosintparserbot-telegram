"""Event consumer base."""

from collections.abc import Awaitable, Callable

from ...shared.domain.events import DomainEvent
from .broker import MessageBroker


class DomainEventConsumer:
    """Subscribes handler to topic in message broker."""

    def __init__(self, broker: MessageBroker):
        self.broker = broker

    def register_handler(
        self, topic: str, handler: Callable[[DomainEvent], Awaitable[None]]
    ) -> None:
        self.broker.subscribe(topic, handler)
