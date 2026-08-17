import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.sequential_world_forecast import (
    build_sequential_worldset_forecast,
    initialize_sequential_world_rule_state,
)
from eog.v2.world_forecast import forecast_from_occurrences
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)
from eog.v2.world_reconstruction import FiniteWorld


NODES = ("a", "b", "c", "d")


def _world(world_id, edges, sources=("a",)):
    operator = build_dynamic_transition_operator(
        NODES,
        [
            DynamicReachabilityEdge(source=i, target=j, geographic_support=1.0)
            for i, j in edges
        ],
        loss_support=1.0,
    )
    return FiniteWorld(world_id=world_id, operator=operator, source_ids=tuple(sources))


def _two_worlds(left_id="left", right_id="right", sources=("a",)):
    return (
        _world(left_id, [(0, 1), (1, 2)], sources=sources),
        _world(right_id, [(0, 3), (3, 2)], sources=sources),
    )


def test_summary_has_the_frozen_symmetric_ten_feature_surface():
    forecast = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)
    summary = summarize_worldset_for_prediction(forecast)

    assert summary.feature_names == PREDICTIVE_FEATURE_NAMES
    assert summary.feature_matrix.shape == (4, 10)
    assert summary.declared_world_count == 2
    assert summary.surviving_world_count == 2

    b = next(row for row in summary.rows if row.node_id == "b")
    mapping = b.feature_mapping
    assert mapping["surviving_world_fraction"] == pytest.approx(1.0)
    assert mapping["positive_support_fraction"] == pytest.approx(0.5)
    assert mapping["support_range"] > 0.0
    assert b.status == "contingent"


def test_predictive_features_are_invariant_to_world_id_renaming():
    original_forecast = forecast_from_occurrences(
        _two_worlds("left", "right"), ("a", "c"), max_steps=2
    )
    renamed_forecast = forecast_from_occurrences(
        _two_worlds("banana", "saffron"), ("a", "c"), max_steps=2
    )

    original = summarize_worldset_for_prediction(original_forecast)
    renamed = summarize_worldset_for_prediction(renamed_forecast)

    # The exact latent forecast identity changes, as it should.
    assert original.source_forecast_fingerprint != renamed.source_forecast_fingerprint
    # The predictive representation does not care what the worlds are called.
    assert original.feature_fingerprint == renamed.feature_fingerprint
    assert np.array_equal(original.feature_matrix, renamed.feature_matrix)
    assert [row.status for row in original.rows] == [row.status for row in renamed.rows]


def test_predictive_features_are_invariant_to_member_order():
    forward = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)
    reverse = forecast_from_occurrences(tuple(reversed(_two_worlds())), ("a", "c"), max_steps=2)

    forward_summary = summarize_worldset_for_prediction(forward)
    reverse_summary = summarize_worldset_for_prediction(reverse)

    assert forward_summary.feature_fingerprint == reverse_summary.feature_fingerprint
    assert np.array_equal(forward_summary.feature_matrix, reverse_summary.feature_matrix)


def test_summary_can_project_an_intermediate_horizon_without_changing_latent_state():
    forecast = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)
    at_one = summarize_worldset_for_prediction(forecast, step=1)
    at_two = summarize_worldset_for_prediction(forecast, step=2)

    assert at_one.source_forecast_fingerprint == at_two.source_forecast_fingerprint
    assert at_one.step == 1
    assert at_two.step == 2
    assert at_one.feature_fingerprint != at_two.feature_fingerprint
    c1 = next(row for row in at_one.rows if row.node_id == "c")
    c2 = next(row for row in at_two.rows if row.node_id == "c")
    assert c1.status == "excluded_in_all_worlds"
    assert c2.status == "robustly_supported"


def test_sequential_forecast_uses_original_rule_universe_for_survival_fraction():
    worlds = _two_worlds(sources=("a",))
    state = initialize_sequential_world_rule_state(worlds)
    forecast = build_sequential_worldset_forecast(
        state,
        worlds,
        transition_id="t0_to_t1",
        max_steps=1,
    )
    summary = summarize_worldset_for_prediction(forecast)

    assert summary.declared_world_count == 2
    assert summary.surviving_world_count == 2
    assert all(
        row.feature_mapping["surviving_world_fraction"] == pytest.approx(1.0)
        for row in summary.rows
    )


def test_summary_does_not_expose_world_ids_as_predictive_columns():
    forecast = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)
    summary = summarize_worldset_for_prediction(forecast)

    feature_text = " ".join(summary.feature_names).lower()
    assert "world_id" not in feature_text
    assert "left" not in feature_text
    assert "right" not in feature_text
    assert all(len(row.feature_values) == 10 for row in summary.rows)


def test_invalid_step_is_rejected():
    forecast = forecast_from_occurrences(_two_worlds(), ("a", "c"), max_steps=2)
    with pytest.raises(ValueError, match="within the forecast horizon"):
        summarize_worldset_for_prediction(forecast, step=3)
