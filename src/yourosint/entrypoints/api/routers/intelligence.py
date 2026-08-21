"""Intelligence Context Router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from yourosint.bootstrap import Container
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.application.queries.search_entities import (
    SearchEntitiesHandler,
    SearchEntitiesQuery,
)
from yourosint.contexts.intelligence.domain.entity import EntityType

from ..dependencies import get_container, get_db_session
from ..schemas.common import EntityResponse, SearchResponse

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/search", response_model=SearchResponse)
async def search_intelligence(
    q: str = Query(
        ..., description="Query for username, email, phone, IP, domain, or message text"
    ),
    type: EntityType | None = Query(None, description="Filter by entity type"),
    tag: str | None = Query(None, description="Filter by tag"),
    min_reputation: int = Query(0, description="Minimum reputation threshold (0-100)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    c: Container = Depends(get_container),
):
    """Multi-index search across intelligence entities, messages, and phone/threat-intel databases."""
    intel_repo = SQLAlchemyIntelligenceRepository(session)
    msg_repo = SQLAlchemyMessageRepository(session)

    handler = SearchEntitiesHandler(
        intelligence_repo=intel_repo,
        blind_index_port=c.blind_index_service,
        phone_lookup_port=c.phone_lookup,
    )

    result = await handler.handle(
        SearchEntitiesQuery(
            query=q,
            entity_type=type,
            tag=tag,
            min_reputation=min_reputation,
            limit=limit,
            offset=offset,
        )
    )

    # Ingestion message search
    messages, total_messages = await msg_repo.search_messages(query=q, limit=limit, offset=offset)

    return SearchResponse(
        query=q,
        total_entities=result.total,
        entities=[
            EntityResponse(
                id=e.id or 0,
                type=e.type.value,
                value=e.value,
                masked_value=e.masked_value,
                first_seen=e.first_seen,
                last_seen=e.last_seen,
                reputation=e.reputation,
                tags=e.tags,
                description=e.description,
                source_type=e.source_type,
                enrichment_data=e.enrichment_data,
                last_enriched=e.last_enriched,
            )
            for e in result.entities
        ],
        total_messages=total_messages,
        messages=[
            {
                "id": m.id,
                "message_id": m.message_id,
                "chat_username": m.chat_username,
                "sender_username": m.sender_username,
                "text": m.text,
                "posted_at": m.posted_at.isoformat(),
            }
            for m in messages
        ],
        phone_info=result.phone_lookup_info,
    )


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity_by_id(
    entity_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    """Get single entity details."""
    intel_repo = SQLAlchemyIntelligenceRepository(session)
    entity = await intel_repo.get_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return EntityResponse(
        id=entity.id or 0,
        type=entity.type.value,
        value=entity.value,
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
