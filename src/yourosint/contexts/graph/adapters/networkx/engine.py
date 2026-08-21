"""NetworkX Graph Engine Adapter."""

import logging
from typing import Any

import networkx as nx

from ...domain.edge import GraphEdge
from ...domain.graph import InvestigationGraph
from ...domain.node import GraphNode
from ...ports.graph_engine import GraphEnginePort

logger = logging.getLogger(__name__)


class NetworkXGraphEngine(GraphEnginePort):
    """Builds and analyzes OSINT interaction graphs using NetworkX."""

    def __init__(self):
        self.graph = nx.Graph()

    def build_graph(
        self,
        target_username: str,
        target_id: int | None,
        target_name: str | None,
        interaction_rows: list[dict[str, Any]],
        second_level_rows: list[dict[str, Any]] | None = None,
    ) -> InvestigationGraph:
        self.graph.clear()
        clean_target = target_username.lstrip("@").strip().lower()
        target_node_id = f"@{clean_target}"

        # 1. Add Target Node
        self.graph.add_node(
            target_node_id,
            label=f"@{clean_target}",
            type="target",
            size=60,
            color="#ef4444",
            user_id=target_id,
            full_name=target_name or clean_target,
            reputation=0,
            metadata={"is_target": True},
        )

        # 2. Add Contacts
        for row in interaction_rows:
            user_id = row.get("user_id")
            if not user_id or user_id == target_id:
                continue

            username = row.get("user_username")
            first_name = row.get("user_first_name") or ""
            last_name = row.get("user_last_name") or ""
            interactions = row.get("total_interactions", 1)
            common_chats = row.get("total_common_chats", 1)

            if username:
                node_id = f"@{username.lstrip('@')}"
                label = f"@{username.lstrip('@')}"
            else:
                full = f"{first_name} {last_name}".strip()
                node_id = f"user_{user_id}"
                label = full if full else f"User {user_id}"

            if node_id == target_node_id:
                continue

            full_name = f"{first_name} {last_name}".strip() or None

            if interactions > 500:
                color = "#8b5cf6"
            elif interactions > 100:
                color = "#3b82f6"
            elif interactions > 20:
                color = "#06b6d4"
            else:
                color = "#64748b"

            if not self.graph.has_node(node_id):
                self.graph.add_node(
                    node_id,
                    label=label,
                    type="contact",
                    size=min(25 + (interactions // 20), 55),
                    color=color,
                    user_id=user_id,
                    total_msgs=interactions,
                    unique_chats=common_chats,
                    full_name=full_name,
                    reputation=0,
                    metadata={"interactions": interactions, "common_chats": common_chats},
                )

            self.graph.add_edge(
                target_node_id,
                node_id,
                weight=interactions,
                type="direct",
                label=f"{interactions} msgs",
                style="solid",
                color="#6366f1",
            )

        # 3. Add Second-Level Common Chat Edges
        if second_level_rows:
            user_to_node = {}
            for n, data in self.graph.nodes(data=True):
                if data.get("user_id"):
                    user_to_node[data["user_id"]] = n

            for row in second_level_rows:
                u1 = row.get("user1_id")
                u2 = row.get("user2_id")
                common = row.get("common_chats", 1)

                if u1 in user_to_node and u2 in user_to_node:
                    n1 = user_to_node[u1]
                    n2 = user_to_node[u2]
                    if not self.graph.has_edge(n1, n2) and n1 != n2:
                        self.graph.add_edge(
                            n1,
                            n2,
                            weight=common,
                            type="second_level",
                            label=f"{common} chats",
                            style="dashed",
                            color="#94a3b8",
                        )

        nodes: list[GraphNode] = []
        for n_id, data in self.graph.nodes(data=True):
            nodes.append(
                GraphNode(
                    id=str(n_id),
                    label=data.get("label", str(n_id)),
                    type=data.get("type", "contact"),
                    size=data.get("size", 25),
                    color=data.get("color", "#3b82f6"),
                    user_id=data.get("user_id"),
                    total_msgs=data.get("total_msgs", 0),
                    unique_chats=data.get("unique_chats", 0),
                    full_name=data.get("full_name"),
                    reputation=data.get("reputation", 0),
                    metadata=data.get("metadata", {}),
                )
            )

        edges: list[GraphEdge] = []
        for u, v, data in self.graph.edges(data=True):
            edges.append(
                GraphEdge(
                    source=str(u),
                    target=str(v),
                    weight=data.get("weight", 1),
                    type=data.get("type", "direct"),
                    label=data.get("label"),
                    style=data.get("style", "solid"),
                    color=data.get("color", "#6366f1"),
                )
            )

        density = nx.density(self.graph) if len(self.graph.nodes) > 1 else 0.0

        return InvestigationGraph(
            nodes=nodes,
            edges=edges,
            target_username=clean_target,
            target_id=target_id,
            total_nodes=len(nodes),
            total_edges=len(edges),
            density=round(density, 4),
        )
