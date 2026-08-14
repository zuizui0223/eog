import numpy as np
import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    build_temporal_flow_set,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    declared = []
    for edge in edges:
        source, target = edge[0], edge[1]
        support = edge[2] if len(edge) > 2 else 1.0
        declared.append(
            DynamicReachabilityEdge(
                source=index[source],
                target=index[target],
                geographic_support=float(support),
            )
        )
    return build_dynamic_transition_operator(node_ids, declared, loss_support=1.0)


def test_temporal_order_changes_reachability_even_with_the_same_edges():
    nodes = ("A", "B", "C")
    ab = _operator(nodes, (("A", "B"),))
    bc = _operator(nodes, (("B", "C"),))

    open_in_order = TemporalWorld("open_in_order", ("t0", "t1", "t2"), (ab, bc), ("A",))
    wrong_order = TemporalWorld("wrong_order", ("t0", "t1", "t2"), (bc, ab), ("A",))
    result = build_temporal_flow_set((open_in_order, wrong_order))

    assert result.world_ids == ("open_in_order", "wrong_order")
    assert result.reachable_in_all_by_time[0] == ("A",)
    assert result.robustly_unreachable_by_time[0] == ("B", "C")
    assert result.contingent_by_time[1] == ("B",)
    assert result.robustly_unreachable_by_time[1] == ("C",)
    assert result.contingent_by_time[2] == ("B", "C")
    assert result.reachable_in_all_by_time[2] == ("A",)
    assert result.coverage_certificate == "exhaustive_declared_temporal_world_set"


def test_source_mass_is_not_reinjected_after_the_initial_state():
    nodes = ("A", "B", "C")
    world = TemporalWorld(
        "opening_bridge",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B"),)), _operator(nodes, (("B", "C"),))),
        ("A",),
    )
    result = build_temporal_flow_set((world,))
    mass = result.mass_by_world[0]

    assert mass[0, 0] == pytest.approx(1.0)
    assert mass[1, 0] == pytest.approx(0.0)
    assert mass[2, 0] == pytest.approx(0.0)
    assert mass[1, 1] > 0.0
    assert mass[2, 2] > 0.0
    assert result.first_arrival_by_world[0].tolist() == [0, 1, 2]


def test_reachability_is_cumulative_by_declared_time_while_mass_remains_exact_time():
    nodes = ("A", "B", "C")
    world = TemporalWorld(
        "bridge_then_drain",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B"),)), _operator(nodes, ())),
        ("A",),
    )
    result = build_temporal_flow_set((world,))

    assert result.mass_by_world[0][2, 1] == pytest.approx(0.0)
    assert result.reached_by_world[0][1, 1]
    assert result.reached_by_world[0][2, 1]
    assert result.reachable_in_all_by_time[2] == ("A", "B")
    assert result.robustly_unreachable_by_time[2] == ("C",)


def test_target_can_be_robustly_reached_across_different_temporal_support_worlds():
    nodes = ("A", "B", "C")
    strong = TemporalWorld(
        "strong",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B", 1.0),)), _operator(nodes, (("B", "C", 1.0),))),
        ("A",),
    )
    weak = TemporalWorld(
        "weak",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B", 0.2),)), _operator(nodes, (("B", "C", 0.2),))),
        ("A",),
    )
    result = build_temporal_flow_set((strong, weak))

    assert result.reachable_in_all_by_time[2] == ("A", "B", "C")
    assert result.contingent_by_time[2] == ()
    assert result.robustly_unreachable_by_time[2] == ()
    assert result.mass_lower_envelope[2, 2] > 0.0
    assert np.all(result.mass_lower_envelope <= result.mass_upper_envelope)


def test_hard_temporal_barrier_is_robustly_unreachable_across_declared_worlds():
    nodes = ("A", "B", "C")
    world_a = TemporalWorld(
        "barrier_a",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B"),)), _operator(nodes, (("B", "C", 0.0),))),
        ("A",),
    )
    world_b = TemporalWorld(
        "barrier_b",
        ("t0", "t1", "t2"),
        (_operator(nodes, (("A", "B", 0.5),)), _operator(nodes, ())),
        ("A",),
    )
    result = build_temporal_flow_set((world_a, world_b))

    assert "C" in result.robustly_unreachable_by_time[2]
    assert "C" not in result.contingent_by_time[2]


def test_temporal_contract_rejects_incomparable_worlds():
    nodes = ("A", "B", "C")
    ab = _operator(nodes, (("A", "B"),))
    bc = _operator(nodes, (("B", "C"),))

    with pytest.raises(ValueError, match="one more entry"):
        TemporalWorld("bad_labels", ("t0", "t1"), (ab, bc), ("A",))

    other_nodes = ("A", "B", "D")
    bd = _operator(other_nodes, (("B", "D"),))
    with pytest.raises(ValueError, match="same node IDs"):
        TemporalWorld("bad_nodes", ("t0", "t1", "t2"), (ab, bd), ("A",))

    first = TemporalWorld("first", ("t0", "t1", "t2"), (ab, bc), ("A",))
    different_labels = TemporalWorld("labels", ("start", "middle", "end"), (ab, bc), ("A",))
    with pytest.raises(ValueError, match="same ordered time labels"):
        build_temporal_flow_set((first, different_labels))

    different_source = TemporalWorld("source_b", ("t0", "t1", "t2"), (ab, bc), ("B",))
    with pytest.raises(ValueError, match="same source IDs"):
        build_temporal_flow_set((first, different_source))
