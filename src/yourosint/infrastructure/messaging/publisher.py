"""Event publisher wrapper."""

from ...shared.domain.events import DomainEvent
from .broker import MessageBroker


class DomainEventPublisher:
    """Publishes domain events to the message broker."""

    def __init__(self, broker: MessageBroker):
        self.broker = broker

    async def publish(self, event: DomainEvent) -> None:
        await self.broker.publish(event.event_name, event)
