"""Ingestion Context Router."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from yourosint.bootstrap import Container
from yourosint.contexts.ingestion.adapters.persistence.repositories import (
    SQLAlchemyChatRepository,
    SQLAlchemyMessageRepository,
)
from yourosint.contexts.ingestion.application.commands.parse_chat import (
    ParseChatCommand,
    ParseChatHandler,
)
from yourosint.contexts.intelligence.adapters.persistence.repositories import (
    SQLAlchemyIntelligenceRepository,
)
from yourosint.contexts.intelligence.application.commands.extract_entities import (
    ExtractEntitiesHandler,
)

from ..dependencies import get_container, get_db_session
from ..schemas.common import ParseChatRequest, ParseChatResponse

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/parse", response_model=ParseChatResponse)
async def trigger_chat_parsing(
    body: ParseChatRequest,
    session: AsyncSession = Depends(get_db_session),
    c: Container = Depends(get_container),
):
    """Triggers Telegram chat ingestion with rate limits and extraction."""
    msg_repo = SQLAlchemyMessageRepository(session)
    chat_repo = SQLAlchemyChatRepository(session)
    intel_repo = SQLAlchemyIntelligenceRepository(session)

    ExtractEntitiesHandler(
        extractor=c.regex_extractor,
        intelligence_repo=intel_repo,
        blind_index_port=c.blind_index_service,
        event_bus=c.event_bus,
    )

    parse_handler = ParseChatHandler(
        account_pool=c.account_pool,
        message_repo=msg_repo,
        chat_repo=chat_repo,
        event_bus=c.event_bus,
    )

    try:
        res = await parse_handler.handle(
            ParseChatCommand(
                chat_username=body.chat_username,
                limit=body.limit,
                enable_pii_filter=body.enable_pii_filter,
            )
        )
        return ParseChatResponse(
            chat_username=res.chat_username,
            messages_parsed=res.messages_parsed,
            messages_saved=res.messages_saved,
            duration_seconds=res.duration_seconds,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/accounts/stats")
async def get_accounts_metrics(c: Container = Depends(get_container)) -> dict[str, Any]:
    """AccountPool status, RPM rates, flood wait, and health states."""
    return await c.account_pool.get_stats()


@router.post("/accounts/{session_name}/rotate")
async def rotate_account_session(
    session_name: str, c: Container = Depends(get_container)
) -> dict[str, str]:
    """Force rotate session credentials."""
    try:
        await c.account_pool.rotate_session(session_name)
        return {"status": "rotated", "session": session_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
