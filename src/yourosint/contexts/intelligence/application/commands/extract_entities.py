"""Command & Handler: Extract and persist entities with provenance evidence."""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from .....shared.application.command import Command, CommandHandler
from .....shared.domain.events import EntitiesExtracted, EventBus
from ...domain.confidence import Confidence
from ...domain.entity import EntityType, IntelligenceEntity
from ...domain.evidence import Evidence
from ...ports.extractor import EntityExtractorPort
from ...ports.repositories import IntelligenceRepositoryPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExtractEntitiesCommand(Command):
    text: str
    source_id: str
    source_type: str = "message"
    chat_username: str | None = None
    chat_id: str | None = None
    message_id: int | None = None


@dataclass(frozen=True, slots=True)
class ExtractedEntitiesResultDTO:
    total_extracted: int
    entities_by_type: dict[str, int]
    entities: list[IntelligenceEntity] = field(default_factory=list)


class ExtractEntitiesHandler(CommandHandler[ExtractedEntitiesResultDTO]):
    """Extracts IOCs from raw text, attaches cryptographic evidence, and persists."""

    def __init__(
        self,
        extractor: EntityExtractorPort,
        intelligence_repo: IntelligenceRepositoryPort,
        blind_index_port: Any = None,
        event_bus: EventBus | None = None,
    ):
        self.extractor = extractor
        self.intelligence_repo = intelligence_repo
        self.blind_index_port = blind_index_port
        self.event_bus = event_bus

    async def handle(self, cmd: ExtractEntitiesCommand) -> ExtractedEntitiesResultDTO:
        extracted = self.extractor.extract_all(cmd.text)
        saved_entities: list[IntelligenceEntity] = []
        counts_by_type: dict[str, int] = {}
        content_hash = hashlib.sha256(cmd.text.encode("utf-8")).hexdigest()[:16]

        for entity_type, values in extracted.items():
            counts_by_type[entity_type.value] = len(values)
            for value in values:
                blind_idx = None
                masked = None
                if self.blind_index_port and entity_type in [
                    EntityType.CARD,
                    EntityType.PHONE,
                    EntityType.EMAIL,
                ]:
                    b_val = self.blind_index_port.make_blind_index(value)
                    blind_idx = b_val.value
                    masked = self.blind_index_port.mask_value(value, entity_type)

                entity = IntelligenceEntity(
                    type=entity_type,
                    value=value,
                    blind_index=blind_idx,
                    masked_value=masked,
                    tags=["extracted", f"source:{cmd.chat_username or 'unknown'}"],
                    source_type=cmd.source_type,
                )
                saved = await self.intelligence_repo.upsert_entity(entity)
                saved_entities.append(saved)

                if saved.id:
                    evidence = Evidence(
                        entity_id=saved.id,
                        source_id=cmd.source_id,
                        source_type=cmd.source_type,
                        raw_context=cmd.text[:300],
                        content_hash=content_hash,
                        extractor_version="regex_v2.0",
                        confidence=Confidence.from_float(0.95),
                        chat_username=cmd.chat_username,
                        chat_id=cmd.chat_id,
                        message_id=cmd.message_id,
                    )
                    await self.intelligence_repo.save_evidence(evidence)

        if self.event_bus and saved_entities:
            await self.event_bus.publish(
                EntitiesExtracted(
                    event_id=f"ext_{cmd.source_id}",
                    source_id=cmd.source_id,
                    source_type=cmd.source_type,
                    entities_count=len(saved_entities),
                    entity_types=list(counts_by_type.keys()),
                )
            )

        return ExtractedEntitiesResultDTO(
            total_extracted=len(saved_entities),
            entities_by_type=counts_by_type,
            entities=saved_entities,
        )
