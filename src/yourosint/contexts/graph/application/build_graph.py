"""Query & Handler: Build Investigation Graph via SQL CTEs."""

import logging
from dataclasses import dataclass

from ....shared.application.query import Query, QueryHandler
from ..domain.graph import InvestigationGraph
from ..ports.graph_engine import GraphEnginePort, GraphQueryPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BuildGraphQuery(Query):
    target_username: str
    depth: int = 2
    limit: int = 200


class BuildGraphHandler(QueryHandler[InvestigationGraph]):
    """Orchestrates SQL CTE extraction and graph topology construction."""

    def __init__(self, query_port: GraphQueryPort, engine_port: GraphEnginePort):
        self.query_port = query_port
        self.engine_port = engine_port

    async def handle(self, query: BuildGraphQuery) -> InvestigationGraph:
        clean_target = query.target_username.lstrip("@").strip().lower()
        logger.info(f"Executing BuildGraphQuery for @{clean_target} (depth: {query.depth})")

        interaction_rows = await self.query_port.query_user_interactions(
            target_username=clean_target,
            limit=query.limit,
        )

        if not interaction_rows:
            return InvestigationGraph(target_username=clean_target)

        target_id = interaction_rows[0].get("target_id")
        target_name = (
            f"{interaction_rows[0].get('target_first_name') or ''} {interaction_rows[0].get('target_last_name') or ''}".strip()
            or clean_target
        )

        second_level_rows = []
        if query.depth > 1:
            contact_ids = [
                r["user_id"]
                for r in interaction_rows
                if r.get("user_id") and r.get("user_id") != target_id
            ]
            if 2 <= len(contact_ids) <= 150:
                second_level_rows = await self.query_port.query_second_level_connections(
                    contact_ids=contact_ids,
                    limit=500,
                )

        return self.engine_port.build_graph(
            target_username=clean_target,
            target_id=target_id,
            target_name=target_name,
            interaction_rows=interaction_rows,
            second_level_rows=second_level_rows,
        )
