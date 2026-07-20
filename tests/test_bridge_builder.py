import numpy as np
import pytest

from eog import fit_robust_reference, infer_bridge
from eog.bridge_builder import BridgeGraphDeclaration, BridgeNode, build_bridge_graph, haversine_km


def node(node_id, lon, env, *, lat=0.0, time=None):
    return BridgeNode(node_id, lat, lon, tuple(env), time_order=time)


def test_haversine_is_symmetric_and_geographic():
    a = node("a", 0.0, [0.0])
    b = node("b", 1.0, [0.0])
    assert haversine_km(a, b) == pytest.approx(haversine_km(b, a))
    assert haversine_km(a, b) == pytest.approx(111.195, rel=1e-3)


def test_radius_builder_recovers_stepping_stone_bridge():
    nodes = [node("source", 0.0, [0.0]), node("middle", 1.0, [0.2]), node("target", 2.0, [0.0])]
    ref = fit_robust_reference(np.array([[0.0], [1.0], [-1.0]]), provenance="test")
    graph = build_bridge_graph(nodes, ref, BridgeGraphDeclaration(max_geographic_km=120.0))
    result = infer_bridge(len(graph.nodes), graph.edges, graph.node_index["source"], graph.node_index["target"])
    assert tuple(graph.nodes[i].node_id for i in result.minimum_cost_path.nodes) == ("source", "middle", "target")


def test_environmental_filter_can_disconnect_geographically_close_nodes():
    nodes = [node("a", 0.0, [0.0]), node("b", 0.1, [10.0])]
    ref = fit_robust_reference(np.array([[-1.0], [0.0], [1.0]]), provenance="test")
    graph = build_bridge_graph(
        nodes,
        ref,
        BridgeGraphDeclaration(max_geographic_km=100.0, max_environmental_distance=2.0),
    )
    assert graph.edges == ()


def test_barrier_cost_is_explicit_and_symmetric():
    nodes = [node("a", 0.0, [0.0]), node("b", 0.2, [0.0])]
    ref = fit_robust_reference(np.array([[-1.0], [0.0], [1.0]]), provenance="test")
    graph = build_bridge_graph(
        nodes,
        ref,
        BridgeGraphDeclaration(max_geographic_km=100.0),
        barriers={("b", "a"): 7.0},
    )
    assert graph.edges[0].barrier_cost == 7.0


def test_k_nearest_ties_are_stable_by_node_id():
    nodes = [node("c", 0.0, [0.0]), node("a", -1.0, [0.0]), node("b", 1.0, [0.0])]
    ref = fit_robust_reference(np.array([[-1.0], [0.0], [1.0]]), provenance="test")
    declaration = BridgeGraphDeclaration(k_nearest=1, max_geographic_km=200.0)
    first = build_bridge_graph(nodes, ref, declaration)
    second = build_bridge_graph(list(reversed(nodes)), ref, declaration)
    assert first.fingerprint == second.fingerprint
    assert first.edges == second.edges


def test_time_directed_mode_requires_time_order_and_removes_ties():
    ref = fit_robust_reference(np.array([[-1.0], [0.0], [1.0]]), provenance="test")
    with pytest.raises(ValueError, match="time_order"):
        build_bridge_graph(
            [node("a", 0.0, [0.0]), node("b", 0.1, [0.0])],
            ref,
            BridgeGraphDeclaration(max_geographic_km=100.0, directed_by_time=True),
        )
    graph = build_bridge_graph(
        [node("a", 0.0, [0.0], time=1), node("b", 0.1, [0.0], time=1)],
        ref,
        BridgeGraphDeclaration(max_geographic_km=100.0, directed_by_time=True),
    )
    assert graph.edges == ()
