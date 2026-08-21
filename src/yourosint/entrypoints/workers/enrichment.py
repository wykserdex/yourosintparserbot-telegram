"""Background Enrichment Worker Entrypoint."""

import asyncio
import contextlib
import logging

from yourosint.bootstrap import Container
from yourosint.contexts.enrichment.application.enrich_entity import (
    EnrichEntityCommand,
    EnrichEntityHandler,
)
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.domain.entity import EntityType

logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """Periodically queries threat intelligence providers for unenriched IOCs."""

    def __init__(self, container: Container, interval_seconds: int = 60):
        self.container = container
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Enrichment worker started")

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        logger.info("Enrichment worker stopped")

    async def _loop(self) -> None:
        while self.is_running:
            try:
                async with self.container.db.session() as session:
                    intel_repo = SQLAlchemyIntelligenceRepository(session)
                    handler = EnrichEntityHandler(
                        phone_lookup=self.container.phone_lookup,
                        network_lookup=self.container.network_lookup,
                        event_bus=self.container.event_bus,
                    )

                    for e_type in [EntityType.PHONE, EntityType.IP, EntityType.DOMAIN]:
                        entities, _ = await intel_repo.search(entity_type=e_type, limit=10)
                        for entity in entities:
                            if not self.is_running:
                                break
                            if entity.last_enriched is None and entity.id:
                                try:
                                    res = await handler.handle(
                                        EnrichEntityCommand(
                                            entity_id=entity.id,
                                            entity_type=entity.type.value,
                                            value=entity.value,
                                        )
                                    )
                                    entity.enrichment_data.update(res.details)
                                    entity.update_reputation(res.risk_score)
                                    await intel_repo.upsert_entity(entity)
                                except Exception as e:
                                    logger.debug(f"Failed to enrich {entity.id}: {e}")
                                await asyncio.sleep(2)

                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Enrichment worker loop error: {e}")
                await asyncio.sleep(15)
