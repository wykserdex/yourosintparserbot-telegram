"""Stats & Health Check Router."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from yourosint.bootstrap import Container
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)

from ..dependencies import get_container, get_db_session
from ..schemas.common import HealthResponse, StatsResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service liveness probe."""
    return HealthResponse(
        status="ok",
        version="2.0.0",
        timestamp=datetime.now(UTC),
    )


@router.get("/stats", response_model=StatsResponse)
async def get_system_stats(
    session: AsyncSession = Depends(get_db_session),
    c: Container = Depends(get_container),
):
    """Aggregated system metrics across Ingestion and Intelligence contexts."""
    msg_repo = SQLAlchemyMessageRepository(session)
    intel_repo = SQLAlchemyIntelligenceRepository(session)

    ingestion_stats = await msg_repo.get_total_stats()
    _, total_objects = await intel_repo.search(limit=1)
    acc_stats = await c.account_pool.get_stats()

    return StatsResponse(
        total_messages=ingestion_stats["total_messages"],
        total_users=ingestion_stats["total_users"],
        total_chats=ingestion_stats["total_chats"],
        total_objects=total_objects,
        active_accounts=acc_stats["active"],
        autopilot_status="ready",
    )
