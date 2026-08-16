import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.island_state_layers import assemble_island_state_layers
from eog.v2.world_forecast import (
    ForecastGateDeclaration,
    forecast_from_occurrences,
    rank_worldset_forecast_frontier,
    update_worldset_forecast,
)
from eog.v2.world_reconstruction import FiniteWorld


NODES = ("a", "b", "c", "d", "e")


def _world(world_id: str, edges: list[tuple[int, int]]) -> FiniteWorld:
    operator = build_dynamic_transition_operator(
        NODES,
        [DynamicReachabilityEdge(source=i, target=j, geographic_support=1.0) for i, j in edges],
        loss_support=1.0,
    )
    return FiniteWorld(world_id=world_id, operator=operator, source_ids=("a",))


def _two_worlds() -> tuple[FiniteWorld, FiniteWorld]:
    # Both worlds explain a -> c in two steps, but through different intermediate nodes.
    left = _world("left", [(0, 1), (1, 2)])
    right = _world("right", [(0, 3), (3, 2)])
    return left, right


def _row(forecast, node_id: str):
    return next(row for row in forecast.node_envelopes if row.node_id == node_id)


def test_forecast_retains_world_identity_instead_of_collapsing_equal_frequencies():
    worlds = _two_worlds()
    forecast = forecast_from_occurrences(worlds, ("a", "c"), max_steps=2)

    assert forecast.compatible_world_ids == ("left", "right")
    assert forecast.robust_ids_by_step[0] == ("a",)
    assert "c" in forecast.robust_ids_by_step[2]

    b = _row(forecast, "b")
    d = _row(forecast, "d")
    assert b.status_by_step[2] == "contingent"
    assert d.status_by_step[2] == "contingent"
    assert b.supporting_world_fraction_by_step[2] == pytest.approx(0.5)
    assert d.supporting_world_fraction_by_step[2] == pytest.approx(0.5)
    assert b.supporting_world_ids_at_horizon == ("left",)
    assert d.supporting_world_ids_at_horizon == ("right",)
    assert b.supporting_world_ids_at_horizon != d.supporting_world_ids_at_horizon

    # Same scalar world-frequency summary, different exact structural explanation.
    assert b.earliest_possible_step == 1
    assert d.earliest_possible_step == 1
    assert b.robust_support_step is None
    assert d.robust_support_step is None


def test_forecast_sets_are_monotone_with_horizon_under_static_local_gates():
    forecast = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)

    possible = [set(r) | set(c) for r, c in zip(forecast.robust_ids_by_step, forecast.contingent_ids_by_step)]
    robust = [set(values) for values in forecast.robust_ids_by_step]
    for earlier, later in zip(possible, possible[1:]):
        assert earlier <= later
    for earlier, later in zip(robust, robust[1:]):
        assert earlier <= later

    c = _row(forecast, "c")
    assert c.status_by_step == (
        "excluded_in_all_worlds",
        "excluded_in_all_worlds",
        "robustly_supported",
    )
    assert c.earliest_possible_step == 2
    assert c.robust_support_step == 2


def test_new_positive_occurrence_eliminates_world_and_updates_forecast_without_retuning():
    worlds = _two_worlds()
    before = forecast_from_occurrences(worlds, ("a", "c"), max_steps=2)
    update = update_worldset_forecast(before, worlds, ("b",))

    assert update.status == "updated"
    assert update.after is not None
    assert update.reconstruction_update.eliminated_world_ids == ("right",)
    assert update.reconstruction_update.retained_world_ids == ("left",)
    assert update.after.compatible_world_ids == ("left",)
    assert _row(update.after, "b").status_by_step[2] == "robustly_supported"
    assert _row(update.after, "d").status_by_step[2] == "excluded_in_all_worlds"


def test_new_positive_occurrence_can_falsify_the_entire_declared_world_universe():
    worlds = _two_worlds()
    before = forecast_from_occurrences(worlds, ("a", "c"), max_steps=2)
    update = update_worldset_forecast(before, worlds, ("e",))

    assert update.status == "universe_falsified"
    assert update.after is None
    assert update.reconstruction_update.retained_world_ids == ()
    assert set(update.reconstruction_update.eliminated_world_ids) == {"left", "right"}


def test_viability_gate_can_block_a_reachable_node_without_fusing_support_layers():
    worlds = _two_worlds()
    layers = {}
    for world in worlds:
        viability = [1.0, 0.2 if world.world_id == "left" else 1.0, 1.0, 1.0, 1.0]
        layers[world.world_id] = assemble_island_state_layers(
            NODES,
            viability_support=viability,
            reachability_support=np.ones(len(NODES)),
            persistence_support=np.ones(len(NODES)),
            viability_threshold=0.0,
            reachability_threshold=0.0,
        )

    forecast = forecast_from_occurrences(
        worlds,
        ("a", "c"),
        max_steps=2,
        gate_declaration=ForecastGateDeclaration(
            reachability_threshold=1e-15,
            viability_threshold=0.5,
        ),
        state_layers_by_world=layers,
    )

    b = _row(forecast, "b")
    assert b.upper_reachability_by_step[2] > 0.0
    assert b.status_by_step[2] == "excluded_in_all_worlds"
    assert forecast.gate_declaration.active_gates == ("reachability", "viability")


def test_frontier_ranking_exposes_robust_possible_and_discriminating_views():
    forecast = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)

    discriminating = rank_worldset_forecast_frontier(forecast, mode="discriminating")
    assert {row.node_id for row in discriminating.rows[:2]} == {"b", "d"}
    assert all(row.world_split_balance == pytest.approx(1.0) for row in discriminating.rows[:2])

    possible = rank_worldset_forecast_frontier(forecast, mode="possible")
    assert possible.rows[0].status != "excluded_in_all_worlds"

    robust = rank_worldset_forecast_frontier(forecast, mode="robust")
    # Observed a/c are excluded from candidate ranking; no unobserved node is robust here.
    assert all(row.status != "robustly_supported" for row in robust.rows)
