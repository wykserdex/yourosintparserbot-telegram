"""Integration test for enrichment handler with persistence."""

import pytest

from yourosint.contexts.enrichment.adapters.phone.phone_adapter import LibphonenumberAdapter
from yourosint.contexts.enrichment.adapters.threat_intel.network_adapter import (
    NetworkThreatIntelAdapter,
)
from yourosint.contexts.enrichment.application.enrich_entity import (
    EnrichEntityCommand,
    EnrichEntityHandler,
)
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.domain.entity import EntityType, IntelligenceEntity


@pytest.mark.asyncio
async def test_enrich_entity_flow(db_session):
    repo = SQLAlchemyIntelligenceRepository(db_session)
    phone_adapter = LibphonenumberAdapter()
    network_adapter = NetworkThreatIntelAdapter()

    entity = await repo.upsert_entity(
        IntelligenceEntity(type=EntityType.PHONE, value="+79991234567")
    )
    assert entity.id is not None

    handler = EnrichEntityHandler(phone_lookup=phone_adapter, network_lookup=network_adapter)
    res = await handler.handle(
        EnrichEntityCommand(
            entity_id=entity.id,
            entity_type="phone",
            value=entity.value,
        )
    )

    assert res.is_valid is True
    assert res.provider == "phone_libphonenumber"
    assert "e164" in res.details
