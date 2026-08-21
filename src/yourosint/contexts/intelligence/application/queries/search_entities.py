"""Query & Handler: Multi-modal Intelligence Search."""

from dataclasses import dataclass, field
from typing import Any

from .....shared.application.query import Query, QueryHandler
from ...domain.entity import EntityType, IntelligenceEntity
from ...ports.repositories import IntelligenceRepositoryPort


@dataclass(frozen=True, slots=True)
class SearchEntitiesQuery(Query):
    query: str
    entity_type: EntityType | None = None
    tag: str | None = None
    min_reputation: int = 0
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class SearchEntitiesResultDTO:
    query: str
    total: int
    entities: list[IntelligenceEntity] = field(default_factory=list)
    phone_lookup_info: dict[str, Any] | None = None


class SearchEntitiesHandler(QueryHandler[SearchEntitiesResultDTO]):
    """Searches intelligence database via text, blind index, and external lookups."""

    def __init__(
        self,
        intelligence_repo: IntelligenceRepositoryPort,
        blind_index_port: Any = None,
        phone_lookup_port: Any = None,
    ):
        self.intelligence_repo = intelligence_repo
        self.blind_index_port = blind_index_port
        self.phone_lookup_port = phone_lookup_port

    async def handle(self, query: SearchEntitiesQuery) -> SearchEntitiesResultDTO:
        clean_q = query.query.strip()

        entities, total = await self.intelligence_repo.search(
            query=clean_q,
            entity_type=query.entity_type,
            tag=query.tag,
            min_reputation=query.min_reputation,
            limit=query.limit,
            offset=query.offset,
        )

        phone_info = None
        digits = "".join(c for c in clean_q if c.isdigit())
        if len(digits) >= 10:
            if self.phone_lookup_port:
                phone_info = self.phone_lookup_port.lookup_phone(clean_q)
            if self.blind_index_port:
                b_val = self.blind_index_port.make_blind_index(
                    self.blind_index_port.normalize_phone(clean_q)
                )
                blind_obj = await self.intelligence_repo.get_by_blind_index(b_val.value)
                if blind_obj and blind_obj.id not in [e.id for e in entities]:
                    entities.insert(0, blind_obj)
                    total += 1

        return SearchEntitiesResultDTO(
            query=clean_q,
            total=total,
            entities=entities,
            phone_lookup_info=phone_info,
        )
