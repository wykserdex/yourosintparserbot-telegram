"""Unit tests for NetworkX Graph Engine."""

from yourosint.contexts.graph.adapters.networkx.engine import NetworkXGraphEngine


def test_networkx_graph_construction():
    engine = NetworkXGraphEngine()
    interactions = [
        {
            "user_id": 200,
            "target_id": 100,
            "target_username": "target_user",
            "target_first_name": "Target",
            "target_last_name": "Boss",
            "user_username": "contact_alice",
            "user_first_name": "Alice",
            "user_last_name": "Smith",
            "total_interactions": 300,
            "total_common_chats": 3,
        }
    ]

    graph = engine.build_graph(
        target_username="target_user",
        target_id=100,
        target_name="Target Boss",
        interaction_rows=interactions,
    )

    assert graph.total_nodes == 2
    assert graph.total_edges == 1
    assert graph.density > 0
