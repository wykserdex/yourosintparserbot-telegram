"""Unit tests for entity merging command."""

import pytest

from yourosint.contexts.intelligence.application.commands.merge_entities import (
    MergeEntitiesCommand,
    MergeEntitiesHandler,
)
from yourosint.contexts.intelligence.domain.entity import EntityType, IntelligenceEntity


class MockIntelligenceRepo:
    def __init__(self):
        self.store = {}

    async def get_by_id(self, entity_id: int):
        return self.store.get(entity_id)

    async def upsert_entity(self, entity: IntelligenceEntity):
        self.store[entity.id] = entity
        return entity


@pytest.mark.asyncio
async def test_merge_entities():
    repo = MockIntelligenceRepo()
    e1 = IntelligenceEntity(
        id=1, type=EntityType.USERNAME, value="user_a", tags=["alpha"], reputation=10
    )
    e2 = IntelligenceEntity(
        id=2, type=EntityType.USERNAME, value="user_b", tags=["beta"], reputation=40
    )
    repo.store[1] = e1
    repo.store[2] = e2

    handler = MergeEntitiesHandler(intelligence_repo=repo)
    merged = await handler.handle(
        MergeEntitiesCommand(
            primary_entity_id=1,
            secondary_entity_id=2,
            reason="Confirmed alias",
        )
    )

    assert merged is not None
    assert "alpha" in merged.tags
    assert "beta" in merged.tags
    assert merged.reputation == 40  # Max reputation preserved
