import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.sequential_world_forecast import (
    build_sequential_worldset_forecast,
    finite_world_rule_fingerprint,
    initialize_sequential_world_rule_state,
    update_sequential_world_rules,
)
from eog.v2.world_reconstruction import FiniteWorld


NODES = ("a", "b", "c", "d", "e")


def _operator(edges):
    return build_dynamic_transition_operator(
        NODES,
        [
            DynamicReachabilityEdge(source=i, target=j, geographic_support=1.0)
            for i, j in edges
        ],
        loss_support=1.0,
    )


def _world(world_id, operator, sources):
    return FiniteWorld(world_id=world_id, operator=operator, source_ids=tuple(sources))


def _rules(sources):
    # Both rules explain a -> b.  Under later source d only rule left supports c,
    # while right supports e.  This deliberately makes past b unreachable from the
    # later d source so we can prove past targets are not incorrectly re-evaluated.
    left_op = _operator([(0, 1), (3, 2)])
    right_op = _operator([(0, 1), (3, 4)])
    return (
        _world("left", left_op, sources),
        _world("right", right_op, sources),
    )


def _row(forecast, node_id):
    return next(row for row in forecast.node_envelopes if row.node_id == node_id)


def test_rule_fingerprint_excludes_current_source_state_but_full_fingerprint_does_not():
    world_a = _rules(("a",))[0]
    world_d = _rules(("d",))[0]

    assert world_a.fingerprint != world_d.fingerprint
    assert finite_world_rule_fingerprint(world_a) == finite_world_rule_fingerprint(world_d)


def test_sequential_evidence_uses_each_transition_current_sources_only():
    initial_worlds = _rules(("a",))
    state0 = initialize_sequential_world_rule_state(initial_worlds)

    first = update_sequential_world_rules(
        state0,
        initial_worlds,
        ("b",),
        transition_id="t0_to_t1",
        max_steps=1,
    )
    assert first.status == "updated"
    assert first.after.surviving_world_ids == ("left", "right")
    assert first.evidence.source_ids == ("a",)
    assert first.evidence.positive_target_ids == ("b",)

    # Source state changes from a to d.  Past positive b is NOT re-tested from d.
    current_worlds = _rules(("d",))
    second = update_sequential_world_rules(
        first.after,
        current_worlds,
        ("c",),
        transition_id="t1_to_t2",
        max_steps=1,
    )
    assert second.status == "updated"
    assert second.after.surviving_world_ids == ("left",)
    assert second.evidence.retained_world_ids == ("left",)
    assert second.evidence.eliminated_world_ids == ("right",)
    assert second.evidence.source_ids == ("d",)
    assert second.evidence.positive_target_ids == ("c",)

    left_result = next(row for row in second.evidence.world_results if row.world_id == "left")
    assert left_result.unsupported_target_ids == ()
    assert tuple(target for target, _ in left_result.target_support) == ("c",)
    # b is intentionally not reachable from d in the left rule; survival proves it
    # was retained as historical evidence rather than re-evaluated under the new state.
    left_d_world = current_worlds[0]
    assert left_d_world.operator.transition[NODES.index("d"), NODES.index("b")] == 0.0


def test_surviving_rule_set_is_monotone_and_can_be_falsified():
    worlds_a = _rules(("a",))
    state = initialize_sequential_world_rule_state(worlds_a)
    first = update_sequential_world_rules(
        state,
        worlds_a,
        ("b",),
        transition_id="t0_to_t1",
        max_steps=1,
    )
    assert set(first.after.surviving_world_ids) <= set(first.before.surviving_world_ids)

    worlds_d = _rules(("d",))
    second = update_sequential_world_rules(
        first.after,
        worlds_d,
        ("c",),
        transition_id="t1_to_t2",
        max_steps=1,
    )
    assert set(second.after.surviving_world_ids) <= set(second.before.surviving_world_ids)
    assert second.after.surviving_world_ids == ("left",)

    # Under source c, left has no route to e, so the frozen remaining universe fails.
    worlds_c = _rules(("c",))
    third = update_sequential_world_rules(
        second.after,
        worlds_c,
        ("e",),
        transition_id="t2_to_t3",
        max_steps=1,
    )
    assert third.status == "universe_falsified"
    assert third.after.surviving_world_ids == ()
    assert third.evidence.eliminated_world_ids == ("left",)


def test_current_source_state_can_change_without_rule_mutation_in_forecast():
    worlds_a = _rules(("a",))
    state = initialize_sequential_world_rule_state(worlds_a)
    first = update_sequential_world_rules(
        state,
        worlds_a,
        ("b",),
        transition_id="t0_to_t1",
        max_steps=1,
    )

    worlds_d = _rules(("d",))
    forecast = build_sequential_worldset_forecast(
        first.after,
        worlds_d,
        transition_id="forecast_t1_to_t2",
        max_steps=1,
    )

    assert forecast.source_ids == ("d",)
    assert forecast.surviving_world_ids == ("left", "right")
    assert _row(forecast, "c").status_by_step[1] == "contingent"
    assert _row(forecast, "e").status_by_step[1] == "contingent"
    assert _row(forecast, "c").supporting_world_ids_at_horizon == ("left",)
    assert _row(forecast, "e").supporting_world_ids_at_horizon == ("right",)


def test_operator_or_rule_change_is_rejected_even_when_world_id_is_reused():
    original = _rules(("a",))
    state = initialize_sequential_world_rule_state(original)

    mutated_left = _world("left", _operator([(0, 1), (3, 2), (2, 4)]), ("d",))
    reused_right = _rules(("d",))[1]
    with pytest.raises(ValueError, match="rule universe changed"):
        update_sequential_world_rules(
            state,
            (mutated_left, reused_right),
            ("c",),
            transition_id="mutated",
            max_steps=1,
        )


def test_all_rule_worlds_must_share_one_current_source_state():
    left = _rules(("a",))[0]
    right = _rules(("a",))[1]
    state = initialize_sequential_world_rule_state((left, right))

    inconsistent = (
        _world("left", left.operator, ("a",)),
        _world("right", right.operator, ("d",)),
    )
    with pytest.raises(ValueError, match="same current source"):
        update_sequential_world_rules(
            state,
            inconsistent,
            ("b",),
            transition_id="bad_sources",
            max_steps=1,
        )


def test_repeated_transition_id_is_rejected():
    worlds = _rules(("a",))
    state = initialize_sequential_world_rule_state(worlds)
    first = update_sequential_world_rules(
        state,
        worlds,
        ("b",),
        transition_id="same",
        max_steps=1,
    )
    with pytest.raises(ValueError, match="already been used"):
        update_sequential_world_rules(
            first.after,
            _rules(("d",)),
            ("c",),
            transition_id="same",
            max_steps=1,
        )
