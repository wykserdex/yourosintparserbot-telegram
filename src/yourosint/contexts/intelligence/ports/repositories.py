"""Intelligence Ports: Entity Extractor and Persistence interfaces."""

from typing import Protocol

from ..domain.entity import EntityType, IntelligenceEntity
from ..domain.evidence import Evidence
from ..domain.relation import Relation


class EntityExtractorPort(Protocol):
    """Port for extracting IOCs / entities from unstructured text."""

    def extract_all(self, text: str) -> dict[EntityType, list[str]]: ...


class IntelligenceRepositoryPort(Protocol):
    """Repository port for intelligence entities, relationships, and evidence."""

    async def upsert_entity(self, entity: IntelligenceEntity) -> IntelligenceEntity: ...

    async def get_by_id(self, entity_id: int) -> IntelligenceEntity | None: ...

    async def get_by_value(
        self, entity_type: EntityType, value: str
    ) -> IntelligenceEntity | None: ...

    async def get_by_blind_index(self, blind_index: str) -> IntelligenceEntity | None: ...

    async def search(
        self,
        query: str | None = None,
        entity_type: EntityType | None = None,
        tag: str | None = None,
        min_reputation: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[IntelligenceEntity], int]: ...

    async def save_evidence(self, evidence: Evidence) -> Evidence: ...

    async def get_evidence_for_entity(self, entity_id: int, limit: int = 100) -> list[Evidence]: ...

    async def save_relation(self, relation: Relation) -> Relation: ...

    async def get_relations_for_entity(self, entity_id: int) -> list[Relation]: ...
