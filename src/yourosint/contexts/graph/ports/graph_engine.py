"""Graph Ports: Engine and Query interfaces."""

from typing import Any, Protocol

from ..domain.graph import InvestigationGraph


class GraphQueryPort(Protocol):
    """Port for querying user interaction graphs in database using single-query SQL CTEs."""

    async def query_user_interactions(
        self, target_username: str, limit: int = 200
    ) -> list[dict[str, Any]]: ...

    async def query_second_level_connections(
        self, contact_ids: list[int], limit: int = 500
    ) -> list[dict[str, Any]]: ...


class GraphEnginePort(Protocol):
    """Port for building, layouting, and analyzing Network graphs."""

    def build_graph(
        self,
        target_username: str,
        target_id: int | None,
        target_name: str | None,
        interaction_rows: list[dict[str, Any]],
        second_level_rows: list[dict[str, Any]] | None = None,
    ) -> InvestigationGraph: ...
