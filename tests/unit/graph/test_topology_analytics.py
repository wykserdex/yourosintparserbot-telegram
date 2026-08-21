"""Unit tests for NetworkX graph layout and density."""

from yourosint.contexts.graph.adapters.networkx.engine import NetworkXGraphEngine


def test_multi_node_graph_analytics():
    engine = NetworkXGraphEngine()
    interactions = [
        {
            "user_id": 201,
            "target_id": 100,
            "target_username": "target_admin",
            "target_first_name": "Target",
            "target_last_name": "Admin",
            "user_username": "node_1",
            "user_first_name": "Node",
            "user_last_name": "One",
            "total_interactions": 150,
            "total_common_chats": 2,
        },
        {
            "user_id": 202,
            "target_id": 100,
            "target_username": "target_admin",
            "target_first_name": "Target",
            "target_last_name": "Admin",
            "user_username": "node_2",
            "user_first_name": "Node",
            "user_last_name": "Two",
            "total_interactions": 40,
            "total_common_chats": 1,
        },
    ]
    second_level = [{"user1_id": 201, "user2_id": 202, "common_chats": 3}]

    graph = engine.build_graph(
        target_username="target_admin",
        target_id=100,
        target_name="Target Admin",
        interaction_rows=interactions,
        second_level_rows=second_level,
    )

    assert graph.total_nodes == 3
    assert graph.total_edges == 3
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 3
    assert any(e.type == "second_level" for e in graph.edges)
