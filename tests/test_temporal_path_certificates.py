"""Exact known-truth temporal route/path quantifier regression tests."""
from __future__ import annotations

import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    audit_temporal_path_quantifiers,
    build_dynamic_transition_operator,
    build_temporal_flow_set,
    summarize_temporal_transition_landscape,
)

NODES = ("A", "B", "C", "D", "X")
IDX = {n: i for i, n in enumerate(NODES)}


def _operator(edges):
    return build_dynamic_transition_operator(
        NODES,
        tuple(
            DynamicReachabilityEdge(
                IDX[left], IDX[right], geographic_support=float(support)
            )
            for left, right, support in edges
        ),
        loss_support=1.0,
    )


def _edges(*pairs, support=1.0):
    return tuple((left, right, support) for left, right in pairs)


def _world(name, intervals, *, sources=("A",), weights=None):
    time_labels = tuple(f"t{i}" for i in range(len(intervals) + 1))
    return TemporalWorld(
        name, time_labels, tuple(_operator(e) for e in intervals),
        sources, source_weights=weights,
    )


def _audit(worlds, *, horizon=None, floor=0.0, source="A", target="C", tolerance=1e-15):
    flow = build_temporal_flow_set(worlds, support_tolerance=tolerance)
    result = audit_temporal_path_quantifiers(
        flow, worlds, source_id=source, target_id=target,
        horizon_index=horizon, edge_support_floor=floor,
    )
    return flow, result


def test_all_worlds_can_reach_without_one_shared_timed_route():
    via_b = _world("via_b", (_edges(("A", "B")), _edges(("B", "C"))))
    via_d = _world("via_d", (_edges(("A", "D")), _edges(("D", "C"))))
    flow, audit = _audit((via_b, via_d))
    assert "C" in flow.reachable_in_all_by_time[2]
    assert audit.every_world_reachable
    assert not audit.common_time_path_exists
    assert audit.common_time_path is None
    assert dict(audit.shortest_time_path_by_world) == {
        "via_b": (("t0", "A"), ("t1", "B"), ("t2", "C")),
        "via_d": (("t0", "A"), ("t1", "D"), ("t2", "C")),
    }
    assert audit.necessary_waypoints_in_every_world == ()
    assert audit.necessary_waypoints_in_some_worlds == ("B", "D")
    assert audit.mass_based_target_status == "reachable_in_all"
    assert audit.mass_status_comparable and audit.structural_mass_status_agreement


def test_common_route_may_not_have_any_universally_mandatory_intermediate():
    narrow = _world("narrow", (_edges(("A", "B")), _edges(("B", "C"))))
    wide = _world(
        "wide",
        (
            _edges(("A", "B"), ("A", "D")),
            _edges(("B", "C"), ("D", "C")),
        ),
    )
    _, audit = _audit((narrow, wide))
    assert audit.every_world_reachable
    assert audit.common_time_path == (("t0", "A"), ("t1", "B"), ("t2", "C"))
    assert audit.common_time_path_exists
    assert dict(audit.mandatory_waypoints_by_world) == {
        "narrow": ("B",), "wide": ()
    }
    assert audit.necessary_waypoints_in_every_world == ()
    assert audit.necessary_timed_states_in_every_world == ()


def test_common_waypoint_can_be_necessary_at_different_times():
    early = _world(
        "early",
        (
            _edges(("A", "X")),
            _edges(("X", "C")),
            _edges(),
        ),
    )
    late = _world(
        "late",
        (
            _edges(("A", "D")),
            _edges(("D", "X")),
            _edges(("X", "C")),
        ),
    )
    _, audit = _audit((early, late))
    assert audit.every_world_reachable
    assert not audit.common_time_path_exists
    assert audit.necessary_waypoints_in_every_world == ("X",)
    assert audit.necessary_timed_states_in_every_world == ()
    assert dict(audit.mandatory_timed_states_by_world) == {
        "early": (("t1", "X"),),
        "late": (("t1", "D"), ("t2", "X")),
    }
    assert dict(audit.shortest_time_path_by_world)["early"][-1] == ("t2", "C")
    assert dict(audit.shortest_time_path_by_world)["late"][-1] == ("t3", "C")


def test_same_timed_waypoint_necessary_in_all_worlds():
    direct = _world("direct", (_edges(("A", "X")), _edges(("X", "C"))))
    extra_dead_end = _world(
        "extra_dead_end",
        (_edges(("A", "X"), ("A", "D")), _edges(("X", "C"))),
    )
    _, audit = _audit((direct, extra_dead_end))
    assert audit.every_world_reachable
    assert audit.common_time_path_exists
    assert audit.necessary_waypoints_in_every_world == ("X",)
    assert audit.necessary_timed_states_in_every_world == (("t1", "X"),)


def test_interval_union_creates_a_path_that_no_world_contains():
    early = _world("early", (_edges(("A", "B")), _edges()))
    late = _world("late", (_edges(), _edges(("B", "C"))))
    flow, audit = _audit((early, late))
    landscape = summarize_temporal_transition_landscape((early, late))
    assert "C" in flow.robustly_unreachable_by_time[2]
    assert not audit.any_world_reachable
    assert not audit.common_time_path_exists
    assert audit.shared_edges_by_interval == ((), ())
    assert landscape.contingent_edges_by_interval == (
        (("A", "B"),),
        (("B", "C"),),
    )
    illicit = _world(
        "illicit_temporal_union",
        (_edges(("A", "B")), _edges(("B", "C"))),
    )
    illicit_flow = build_temporal_flow_set((illicit,))
    assert illicit_flow.mass_by_world[0][-1, IDX["C"]] == pytest.approx(0.25)


def test_reachability_depends_on_declared_horizon_without_implicit_waiting():
    single = _world("single", (_edges(("A", "B")), _edges(("B", "C"))))
    _, too_early = _audit((single,), horizon=1)
    _, final = _audit((single,), horizon=2)
    assert too_early.horizon_label == "t1"
    assert not too_early.any_world_reachable
    assert final.every_world_reachable
    assert final.common_time_path[-1] == ("t2", "C")


def test_temporal_path_allows_spatial_revisit_at_later_time():
    loop = _world(
        "loop",
        (
            _edges(("A", "B")),
            _edges(("B", "A")),
            _edges(("A", "C")),
        ),
    )
    _, audit = _audit((loop,))
    assert audit.every_world_reachable
    assert audit.common_time_path == (
        ("t0", "A"), ("t1", "B"), ("t2", "A"), ("t3", "C")
    )


def test_declared_world_expansion_erodes_common_route_not_world_accessibility():
    via_b = _world("via_b", (_edges(("A", "B")), _edges(("B", "C"))))
    via_d = _world("via_d", (_edges(("A", "D")), _edges(("D", "C"))))
    _, before = _audit((via_b,))
    _, after = _audit((via_b, via_d))
    assert before.every_world_reachable and after.every_world_reachable
    assert before.common_time_path_exists and not after.common_time_path_exists
    assert before.necessary_waypoints_in_every_world == ("B",)
    assert after.necessary_waypoints_in_every_world == ()
    assert before.fingerprint != after.fingerprint


def test_raw_positive_transition_is_not_numerical_first_passage_certificate():
    weak = _world(
        "weak",
        (
            _edges(("A", "B"), support=1e-8),
            _edges(("B", "C"), support=1e-8),
        ),
    )
    flow, positive = _audit((weak,))
    assert "C" in flow.robustly_unreachable_by_time[-1]
    assert positive.every_world_reachable
    assert positive.mass_based_target_status == "robustly_unreachable"
    assert positive.mass_status_comparable
    assert positive.structural_mass_status_agreement is False
    _, strict = _audit((weak,), floor=1e-6)
    assert not strict.any_world_reachable
    assert strict.structural_mass_status_agreement is True


def test_multisource_temporal_flow_mass_not_misreported_as_selected_source():
    # D alone can reach C; A has a small, disconnected separate branch.
    mixed = _world(
        "mixed",
        (_edges(("D", "C"), ("A", "B")),),
        sources=("A", "D"),
    )
    flow, audit = _audit((mixed,))
    assert "C" in flow.reachable_in_all_by_time[1]
    assert not audit.any_world_reachable
    assert audit.mass_based_target_status == "reachable_in_all"
    assert audit.mass_status_comparable is False
    assert audit.structural_mass_status_agreement is None


def test_input_order_does_not_change_certificate_or_digest():
    b = _world("b", (_edges(("A", "B")), _edges(("B", "C"))))
    d = _world("d", (_edges(("A", "D")), _edges(("D", "C"))))
    flow, first = _audit((b, d))
    second = audit_temporal_path_quantifiers(
        flow, (d, b), source_id="A", target_id="C"
    )
    assert first == second


def test_changed_world_fingerprint_fails_closed():
    w = _world("w", (_edges(("A", "B")), _edges(("B", "C"))))
    flow, _ = _audit((w,))
    mutated = _world("w", (_edges(("A", "D")), _edges(("D", "C"))))
    with pytest.raises(ValueError, match="fingerprints"):
        audit_temporal_path_quantifiers(
            flow, (mutated,), source_id="A", target_id="C"
        )


def test_invalid_horizon_floor_and_source_are_rejected():
    w = _world("w", (_edges(("A", "B")), _edges(("B", "C"))))
    flow, _ = _audit((w,))
    for invalid in (-1, 3, True, 1.5):
        with pytest.raises(ValueError, match="horizon_index"):
            audit_temporal_path_quantifiers(
                flow, (w,), source_id="A", target_id="C",
                horizon_index=invalid,
            )
    for invalid in (-1e-3, float("nan"), float("inf"), 1.0):
        with pytest.raises(ValueError, match="edge_support_floor"):
            audit_temporal_path_quantifiers(
                flow, (w,), source_id="A", target_id="C",
                edge_support_floor=invalid,
            )
    with pytest.raises(ValueError, match="distinct declared"):
        audit_temporal_path_quantifiers(
            flow, (w,), source_id="A", target_id="missing"
        )
    with pytest.raises(ValueError, match="positive declared mass"):
        audit_temporal_path_quantifiers(
            flow, (w,), source_id="D", target_id="C"
        )


def test_zero_mass_named_source_fails_closed():
    w = _world(
        "w", (_edges(("D", "C")),), sources=("A", "D"),
        weights=(0.0, 1.0),
    )
    flow = build_temporal_flow_set((w,))
    with pytest.raises(ValueError, match="positive declared mass"):
        audit_temporal_path_quantifiers(
            flow, (w,), source_id="A", target_id="C"
        )


def test_empty_supplied_universe_fails_closed():
    w = _world("w", (_edges(("A", "B")),))
    flow = build_temporal_flow_set((w,))
    with pytest.raises(ValueError, match="nonempty"):
        audit_temporal_path_quantifiers(
            flow, (), source_id="A", target_id="C"
        )
