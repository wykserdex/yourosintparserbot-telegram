"""SQLAlchemy 2.0 Async Repositories for Intelligence context."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entity import EntityType, IntelligenceEntity
from ...domain.evidence import Evidence
from ...domain.relation import Relation, RelationType
from ...ports.repositories import IntelligenceRepositoryPort
from .models import EvidenceORM, ObjectORM, RelationORM


class SQLAlchemyIntelligenceRepository(IntelligenceRepositoryPort):
    """Async repository for Intelligence Entities, Relations, and Provenance Evidence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_entity(self, entity: IntelligenceEntity) -> IntelligenceEntity:
        stmt = select(ObjectORM).where(
            ObjectORM.type == entity.type.value,
            ObjectORM.value == entity.value,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if existing:
            existing.last_seen = now
            existing.updated_at = now
            if entity.tags:
                combined = list(set(existing.tags + entity.tags))
                existing.tags = combined
            if entity.description and not existing.description:
                existing.description = entity.description
            if entity.reputation > existing.reputation:
                existing.reputation = entity.reputation
            if entity.blind_index:
                existing.blind_index = entity.blind_index
            if entity.masked_value:
                existing.masked_value = entity.masked_value
            await self.session.flush()
            return self._orm_to_entity(existing)

        orm = ObjectORM(
            type=entity.type.value,
            value=entity.value,
            blind_index=entity.blind_index,
            masked_value=entity.masked_value,
            first_seen=entity.first_seen,
            last_seen=entity.last_seen,
            reputation=entity.reputation,
            tags=entity.tags,
            description=entity.description,
            source_type=entity.source_type,
            enrichment_data=entity.enrichment_data,
            last_enriched=entity.last_enriched,
        )
        self.session.add(orm)
        await self.session.flush()
        return self._orm_to_entity(orm)

    async def get_by_id(self, entity_id: int) -> IntelligenceEntity | None:
        stmt = select(ObjectORM).where(ObjectORM.id == entity_id)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._orm_to_entity(orm) if orm else None

    async def get_by_value(self, entity_type: EntityType, value: str) -> IntelligenceEntity | None:
        stmt = select(ObjectORM).where(
            ObjectORM.type == entity_type.value,
            ObjectORM.value == value,
        )
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._orm_to_entity(orm) if orm else None

    async def get_by_blind_index(self, blind_index: str) -> IntelligenceEntity | None:
        stmt = select(ObjectORM).where(ObjectORM.blind_index == blind_index)
        result = await self.session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._orm_to_entity(orm) if orm else None

    async def search(
        self,
        query: str | None = None,
        entity_type: EntityType | None = None,
        tag: str | None = None,
        min_reputation: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[IntelligenceEntity], int]:
        stmt = select(ObjectORM)
        count_stmt = select(func.count(ObjectORM.id))

        filters: list[Any] = []
        if query:
            filters.append(
                or_(
                    ObjectORM.value.ilike(f"%{query}%"),
                    ObjectORM.description.ilike(f"%{query}%"),
                    ObjectORM.masked_value.ilike(f"%{query}%"),
                )
            )
        if entity_type:
            filters.append(ObjectORM.type == entity_type.value)
        if min_reputation > 0:
            filters.append(ObjectORM.reputation >= min_reputation)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one() or 0

        stmt = stmt.order_by(ObjectORM.last_seen.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        orms = result.scalars().all()

        entities = [self._orm_to_entity(o) for o in orms]
        if tag:
            entities = [e for e in entities if tag in e.tags]

        return entities, total

    async def save_evidence(self, evidence: Evidence) -> Evidence:
        orm = EvidenceORM(
            object_id=evidence.entity_id,
            source_type=evidence.source_type,
            source_id=evidence.source_id,
            raw_context=evidence.raw_context,
            chat_username=evidence.chat_username,
            chat_id=evidence.chat_id,
            message_id=evidence.message_id,
            extracted_at=evidence.extracted_at,
        )
        self.session.add(orm)
        await self.session.flush()
        return Evidence(
            id=orm.id,
            entity_id=orm.object_id,
            source_id=orm.source_id or "",
            source_type=orm.source_type,
            raw_context=orm.raw_context,
            content_hash=evidence.content_hash,
            extractor_version=evidence.extractor_version,
            confidence=evidence.confidence,
            observed_at=evidence.observed_at,
            extracted_at=orm.extracted_at,
            chat_username=orm.chat_username,
            chat_id=orm.chat_id,
            message_id=orm.message_id,
        )

    async def get_evidence_for_entity(self, entity_id: int, limit: int = 100) -> list[Evidence]:
        stmt = (
            select(EvidenceORM)
            .where(EvidenceORM.object_id == entity_id)
            .order_by(EvidenceORM.extracted_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        orms = result.scalars().all()
        return [
            Evidence(
                id=o.id,
                entity_id=o.object_id,
                source_id=o.source_id or "",
                source_type=o.source_type,
                raw_context=o.raw_context,
                content_hash="",
                chat_username=o.chat_username,
                chat_id=o.chat_id,
                message_id=o.message_id,
                extracted_at=o.extracted_at,
            )
            for o in orms
        ]

    async def save_relation(self, rel: Relation) -> Relation:
        stmt = select(RelationORM).where(
            RelationORM.object1_id == rel.source_entity_id,
            RelationORM.object2_id == rel.target_entity_id,
            RelationORM.relation_type == rel.relation_type.value,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.weight += rel.weight
            existing.last_seen = datetime.now(UTC)
            if rel.context:
                existing.context = rel.context
            await self.session.flush()
            return self._orm_to_relation(existing)

        orm = RelationORM(
            object1_id=rel.source_entity_id,
            object2_id=rel.target_entity_id,
            relation_type=rel.relation_type.value,
            weight=rel.weight,
            context=rel.context,
            first_seen=rel.first_seen,
            last_seen=rel.last_seen,
        )
        self.session.add(orm)
        await self.session.flush()
        return self._orm_to_relation(orm)

    async def get_relations_for_entity(self, entity_id: int) -> list[Relation]:
        stmt = (
            select(RelationORM)
            .where(
                or_(
                    RelationORM.object1_id == entity_id,
                    RelationORM.object2_id == entity_id,
                )
            )
            .order_by(RelationORM.weight.desc())
        )
        result = await self.session.execute(stmt)
        orms = result.scalars().all()
        return [self._orm_to_relation(r) for r in orms]

    def _orm_to_entity(self, orm: ObjectORM) -> IntelligenceEntity:
        return IntelligenceEntity(
            id=orm.id,
            type=EntityType(orm.type),
            value=orm.value,
            blind_index=orm.blind_index,
            masked_value=orm.masked_value,
            first_seen=orm.first_seen,
            last_seen=orm.last_seen,
            reputation=orm.reputation,
            tags=orm.tags if isinstance(orm.tags, list) else [],
            description=orm.description,
            source_type=orm.source_type,
            enrichment_data=orm.enrichment_data if isinstance(orm.enrichment_data, dict) else {},
            last_enriched=orm.last_enriched,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def _orm_to_relation(self, orm: RelationORM) -> Relation:
        return Relation(
            id=orm.id,
            source_entity_id=orm.object1_id,
            target_entity_id=orm.object2_id,
            relation_type=RelationType(orm.relation_type),
            weight=orm.weight,
            context=orm.context,
            first_seen=orm.first_seen,
            last_seen=orm.last_seen,
            created_at=orm.created_at,
        )
