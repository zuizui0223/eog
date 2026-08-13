from __future__ import annotations

import numpy as np
import pytest

from eog.traversable_state_space import (
    NODE_STATES,
    PathwiseIsolation,
    TransitionHypothesis,
    TraversabilityError,
    evaluate_traversability,
)


CONTINUOUS = TransitionHypothesis(
    hypothesis_id="continuous_60km",
    kind="continuous",
    max_edge_geographic_km=60.0,
    requires_transit_viability=True,
    minimum_transit_viability=0.4,
)

LONG_JUMP = TransitionHypothesis(
    hypothesis_id="long_jump_400km",
    kind="long_jump",
    max_edge_geographic_km=400.0,
    requires_transit_viability=False,
)


def _row(result, hypothesis_id: str, source: str, target: str) -> PathwiseIsolation:
    matches = [
        row
        for row in result.rows
        if row.hypothesis_id == hypothesis_id and row.source_id == source and row.target_id == target
    ]
    assert len(matches) == 1
    return matches[0]


def _chain(count: int, spacing_km: float = 50.0):
    """A west-to-east chain of nodes spaced along the equator."""
    degrees_per_km = 1.0 / 111.195
    ids = tuple(f"n{index}" for index in range(count))
    lat = [0.0] * count
    lon = [index * spacing_km * degrees_per_km for index in range(count)]
    return ids, lat, lon


def _states(ids, **overrides) -> dict[str, str]:
    states = {node: "surveyed_absent" for node in ids}
    states[ids[0]] = "current_occurrence"
    states[ids[-1]] = "current_occurrence"
    states.update(overrides)
    return states


def test_continuous_viable_bridge_is_supported_with_a_small_pathwise_step() -> None:
    ids, lat, lon = _chain(4)
    env = np.array([[0.0], [0.1], [0.2], [0.3]])
    viability = [0.9, 0.8, 0.8, 0.9]

    result = evaluate_traversability(
        ids, lat, lon, env, viability, _states(ids), [("n0", "n3")], [CONTINUOUS]
    )
    row = _row(result, "continuous_60km", "n0", "n3")

    assert row.status == "supported"
    assert row.reachable and row.reachable_through_surveyed_only
    assert row.minimax_environmental_step == pytest.approx(0.1)
    assert row.cumulative_environmental_cost == pytest.approx(0.3)
    assert row.maximin_transit_viability == pytest.approx(0.8)


def test_niche_desert_blocks_continuous_propagation_but_not_a_long_jump() -> None:
    """Endpoints are habitable and environmentally near-identical; the middle is not."""
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [0.05], [0.1]])
    viability = [0.9, 0.05, 0.9]
    states = _states(ids)
    pairs = [("n0", "n2")]

    result = evaluate_traversability(
        ids, lat, lon, env, viability, states, pairs, [CONTINUOUS, LONG_JUMP]
    )

    continuous = _row(result, "continuous_60km", "n0", "n2")
    assert continuous.status == "incompatible"
    assert not continuous.reachable
    assert continuous.minimax_environmental_step is None

    jump = _row(result, "long_jump_400km", "n0", "n2")
    assert jump.status == "supported"
    assert jump.reachable
    # The jump crosses directly, so no intermediate constrains it.
    assert jump.maximin_transit_viability is None

    # Endpoint environmental distance is small under both hypotheses: an endpoint-only
    # IBE comparison cannot see the desert that separates them.
    assert continuous.endpoint_environmental_distance == pytest.approx(0.1)
    assert jump.endpoint_environmental_distance == pytest.approx(0.1)


def test_pathwise_environmental_bottleneck_is_invisible_to_endpoint_ibe() -> None:
    """Identical endpoints, one unavoidable niche jump in the middle."""
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [5.0], [0.0]])
    viability = [0.9, 0.9, 0.9]

    result = evaluate_traversability(
        ids, lat, lon, env, viability, _states(ids), [("n0", "n2")], [CONTINUOUS]
    )
    row = _row(result, "continuous_60km", "n0", "n2")

    assert row.endpoint_environmental_distance == pytest.approx(0.0)
    assert row.minimax_environmental_step == pytest.approx(5.0)
    assert row.limiting_edge in {("n0", "n1"), ("n1", "n2")}
    assert row.status == "supported"


def test_environmental_step_ceiling_makes_the_bottleneck_incompatible() -> None:
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [5.0], [0.0]])
    viability = [0.9, 0.9, 0.9]
    capped = TransitionHypothesis(
        hypothesis_id="continuous_capped",
        kind="continuous",
        max_edge_geographic_km=60.0,
        max_environmental_step=1.0,
    )

    result = evaluate_traversability(
        ids, lat, lon, env, viability, _states(ids), [("n0", "n2")], [capped]
    )
    assert _row(result, "continuous_capped", "n0", "n2").status == "incompatible"


def test_geographic_barrier_is_incompatible_only_for_the_short_range_hypothesis() -> None:
    ids, lat, lon = _chain(2, spacing_km=300.0)
    env = np.array([[0.0], [0.1]])
    viability = [0.9, 0.9]
    states = _states(ids)

    result = evaluate_traversability(
        ids, lat, lon, env, viability, states, [("n0", "n1")], [CONTINUOUS, LONG_JUMP]
    )
    assert _row(result, "continuous_60km", "n0", "n1").status == "incompatible"
    assert _row(result, "long_jump_400km", "n0", "n1").status == "supported"


def test_unsuitable_stepping_stone_is_separated_from_a_viable_one() -> None:
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [0.1], [0.2]])

    viable = evaluate_traversability(
        ids, lat, lon, env, [0.9, 0.7, 0.9], _states(ids), [("n0", "n2")], [CONTINUOUS]
    )
    unsuitable = evaluate_traversability(
        ids, lat, lon, env, [0.9, 0.42, 0.9], _states(ids), [("n0", "n2")], [CONTINUOUS]
    )

    strong = _row(viable, "continuous_60km", "n0", "n2")
    weak = _row(unsuitable, "continuous_60km", "n0", "n2")

    assert strong.maximin_transit_viability == pytest.approx(0.7)
    assert weak.maximin_transit_viability == pytest.approx(0.42)
    assert weak.limiting_node == "n1"
    # Both clear the declared transit floor, so the difference must show up in the
    # reported viability, not by silently reclassifying the weaker route.
    assert strong.status == weak.status == "supported"
    assert weak.cumulative_niche_cost > strong.cumulative_niche_cost


def test_declared_weak_support_cutoff_downgrades_without_excluding() -> None:
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [0.1], [0.2]])
    hypothesis = TransitionHypothesis(
        hypothesis_id="continuous_with_weak_cutoff",
        kind="continuous",
        max_edge_geographic_km=60.0,
        minimum_transit_viability=0.3,
        weak_support_viability=0.6,
    )

    result = evaluate_traversability(
        ids, lat, lon, env, [0.9, 0.45, 0.9], _states(ids), [("n0", "n2")], [hypothesis]
    )
    row = _row(result, "continuous_with_weak_cutoff", "n0", "n2")
    assert row.status == "weakly_supported"
    assert row.reachable


def test_unsurveyed_intermediate_yields_unresolved_not_supported() -> None:
    """A blank node is a sampling gap, never evidence for or against the route."""
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [0.1], [0.2]])
    viability = [0.9, 0.8, 0.9]

    surveyed = evaluate_traversability(
        ids, lat, lon, env, viability, _states(ids), [("n0", "n2")], [CONTINUOUS]
    )
    blank = evaluate_traversability(
        ids,
        lat,
        lon,
        env,
        viability,
        _states(ids, n1="unsurveyed"),
        [("n0", "n2")],
        [CONTINUOUS],
    )

    assert _row(surveyed, "continuous_60km", "n0", "n2").status == "supported"
    gap = _row(blank, "continuous_60km", "n0", "n2")
    assert gap.status == "unresolved"
    assert gap.reachable and not gap.reachable_through_surveyed_only


def test_unsurveyed_node_off_the_route_does_not_make_a_pair_unresolved() -> None:
    ids, lat, lon = _chain(4)
    env = np.array([[0.0], [0.1], [0.2], [0.3]])
    viability = [0.9, 0.8, 0.8, 0.9]

    result = evaluate_traversability(
        ids,
        lat,
        lon,
        env,
        viability,
        _states(ids, n3="unsurveyed"),
        [("n0", "n2")],
        [CONTINUOUS],
    )
    assert _row(result, "continuous_60km", "n0", "n2").status == "supported"


def test_historical_occurrence_is_a_distinct_state_from_surveyed_absence() -> None:
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [0.1], [0.2]])
    viability = [0.9, 0.8, 0.9]
    result = evaluate_traversability(
        ids,
        lat,
        lon,
        env,
        viability,
        _states(ids, n1="historical_occurrence"),
        [("n0", "n2")],
        [CONTINUOUS],
    )
    # An extinct intermediate is surveyed information, so the route stays resolvable.
    assert _row(result, "continuous_60km", "n0", "n2").status == "supported"
    assert set(NODE_STATES) == {
        "current_occurrence",
        "historical_occurrence",
        "surveyed_absent",
        "unsurveyed",
    }


def test_results_are_deterministic_and_fingerprinted() -> None:
    ids, lat, lon = _chain(4)
    env = np.array([[0.0], [0.1], [0.2], [0.3]])
    viability = [0.9, 0.8, 0.8, 0.9]
    arguments = (ids, lat, lon, env, viability, _states(ids), [("n0", "n3")], [CONTINUOUS, LONG_JUMP])

    first = evaluate_traversability(*arguments)
    second = evaluate_traversability(*arguments)
    assert first.fingerprint == second.fingerprint
    assert len(first.rows) == 2

    changed = evaluate_traversability(
        ids, lat, lon, env, [0.9, 0.8, 0.5, 0.9], _states(ids), [("n0", "n3")], [CONTINUOUS, LONG_JUMP]
    )
    assert changed.fingerprint != first.fingerprint


def test_every_declared_hypothesis_is_retained() -> None:
    ids, lat, lon = _chain(3)
    env = np.array([[0.0], [0.1], [0.2]])
    result = evaluate_traversability(
        ids, lat, lon, env, [0.9, 0.05, 0.9], _states(ids), [("n0", "n2")], [CONTINUOUS, LONG_JUMP]
    )
    assert result.hypotheses == ("continuous_60km", "long_jump_400km")
    assert {row.hypothesis_id for row in result.rows} == set(result.hypotheses)


def test_long_jump_hypothesis_may_not_require_transit_viability() -> None:
    with pytest.raises(TraversabilityError, match="long_jump"):
        TransitionHypothesis(
            hypothesis_id="contradictory",
            kind="long_jump",
            max_edge_geographic_km=400.0,
            requires_transit_viability=True,
        )


def test_unknown_node_state_is_rejected() -> None:
    ids, lat, lon = _chain(2)
    env = np.array([[0.0], [0.1]])
    with pytest.raises(TraversabilityError, match="unknown node states"):
        evaluate_traversability(
            ids,
            lat,
            lon,
            env,
            [0.9, 0.9],
            {"n0": "current_occurrence", "n1": "absent"},
            [("n0", "n1")],
            [CONTINUOUS],
        )


def test_viability_outside_unit_interval_is_rejected() -> None:
    ids, lat, lon = _chain(2)
    env = np.array([[0.0], [0.1]])
    with pytest.raises(TraversabilityError, match="viability"):
        evaluate_traversability(
            ids, lat, lon, env, [0.9, 1.4], _states(ids), [("n0", "n1")], [CONTINUOUS]
        )
