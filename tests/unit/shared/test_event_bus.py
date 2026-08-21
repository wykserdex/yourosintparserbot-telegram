"""Unit tests for in-memory event bus."""

from dataclasses import dataclass

import pytest

from yourosint.shared.domain.events import DomainEvent, InMemoryEventBus


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleEvent(DomainEvent):
    value: str


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = InMemoryEventBus()
    received = []

    async def handler(event: SampleEvent):
        received.append(event.value)

    bus.subscribe(SampleEvent, handler)

    await bus.publish(SampleEvent(event_id="e1", value="test_payload"))
    assert len(received) == 1
    assert received[0] == "test_payload"
