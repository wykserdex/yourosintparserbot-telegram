"""Integration tests for Intelligence Repositories."""

import pytest

from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.domain.entity import EntityType, IntelligenceEntity
from yourosint.contexts.intelligence.domain.relation import Relation, RelationType


@pytest.mark.asyncio
async def test_intelligence_entity_and_relation_persistence(db_session):
    repo = SQLAlchemyIntelligenceRepository(db_session)

    e1 = await repo.upsert_entity(
        IntelligenceEntity(type=EntityType.DOMAIN, value="scam-portal.io", tags=["scam"])
    )
    e2 = await repo.upsert_entity(
        IntelligenceEntity(type=EntityType.IP, value="185.220.101.5", tags=["c2"])
    )

    assert e1.id is not None
    assert e2.id is not None

    rel = await repo.save_relation(
        Relation(
            source_entity_id=e1.id,
            target_entity_id=e2.id,
            relation_type=RelationType.USES,
            weight=1,
        )
    )
    assert rel.weight == 1

    relations = await repo.get_relations_for_entity(e1.id)
    assert len(relations) == 1
