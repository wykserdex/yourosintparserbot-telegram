"""Graph Context Router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from yourosint.bootstrap import Container, SqlAlchemyGraphQueryAdapter
from yourosint.contexts.graph.application.build_graph import BuildGraphHandler, BuildGraphQuery

from ..dependencies import get_container, get_db_session
from ..schemas.common import (
    GraphEdgeResponse,
    GraphNodeResponse,
    InvestigationGraphResponse,
)

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/user/{username}", response_model=InvestigationGraphResponse)
async def get_user_interaction_graph(
    username: str,
    depth: int = Query(
        2, ge=1, le=3, description="Analysis depth (1=direct interactions, 2=common chats)"
    ),
    limit: int = Query(200, ge=10, le=500),
    session: AsyncSession = Depends(get_db_session),
    c: Container = Depends(get_container),
):
    """Computes interaction graph for target user via single-query SQL CTEs."""
    query_adapter = SqlAlchemyGraphQueryAdapter(session)
    handler = BuildGraphHandler(query_port=query_adapter, engine_port=c.graph_engine)

    graph = await handler.handle(
        BuildGraphQuery(
            target_username=username,
            depth=depth,
            limit=limit,
        )
    )

    if not graph.nodes:
        raise HTTPException(
            status_code=404,
            detail=f"User @{username} has no recorded interactions in database",
        )

    return InvestigationGraphResponse(
        nodes=[
            GraphNodeResponse(
                id=n.id,
                label=n.label,
                type=n.type,
                size=n.size,
                color=n.color,
                user_id=n.user_id,
                full_name=n.full_name,
                reputation=n.reputation,
                metadata=n.metadata,
            )
            for n in graph.nodes
        ],
        edges=[
            GraphEdgeResponse(
                source=e.source,
                target=e.target,
                weight=e.weight,
                type=e.type,
                label=e.label,
                style=e.style,
                color=e.color,
            )
            for e in graph.edges
        ],
        target_username=graph.target_username,
        target_id=graph.target_id,
        total_nodes=graph.total_nodes,
        total_edges=graph.total_edges,
        density=graph.density,
    )
