import numpy as np
import pytest

from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_survival_regime import (
    RegimeForecastDeclaration,
    classify_observed_world_survival_regime,
    forecast_world_survival_regime,
    score_regime_forecasts,
)


def _symmetric(n, edges):
    adjacency = np.zeros((n, n), dtype=bool)
    for left, right in edges:
        adjacency[left, right] = True
        adjacency[right, left] = True
    return adjacency


def _complete(n):
    adjacency = np.ones((n, n), dtype=bool)
    np.fill_diagonal(adjacency, False)
    return adjacency


def _star(n, center=0):
    return _symmetric(n, [(center, node) for node in range(n) if node != center])


def _ring(n):
    return _symmetric(n, [(node, (node + 1) % n) for node in range(n)])


def _audit_and_gate(worlds, horizon=1):
    nodes = tuple(f"n{index}" for index in range(6))
    audit = audit_world_universe_structure(nodes, worlds, horizon=horizon)
    declaration = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.9,
        max_isolated_node_fraction=0.1,
    )
    gate = apply_structural_adequacy_gate(audit, declaration)
    assert gate.passed is True
    return audit, gate


def test_horizon_realization_rule_can_predict_all_three_regimes():
    cutoff = RegimeForecastDeclaration(horizon_realization_cutoff=0.5)

    audit, gate = _audit_and_gate(
        {"local_star_a": _star(6, 0), "local_star_b": _star(6, 1)}
    )
    failed = forecast_world_survival_regime(audit, gate, cutoff)
    assert failed.regime == "falsified_universe"
    assert failed.predicted_surviving_world_fraction == 0.0
    assert all(row.horizon_realization_ratio < 0.5 for row in failed.structural_rows)

    audit, gate = _audit_and_gate(
        {"local_star": _star(6), "local_complete": _complete(6)}
    )
    mixed = forecast_world_survival_regime(audit, gate, cutoff)
    assert mixed.regime == "contracting"
    assert mixed.predicted_surviving_world_fraction == 0.5

    audit, gate = _audit_and_gate(
        {"local_ring": _ring(6), "local_complete": _complete(6)}
    )
    saturated = forecast_world_survival_regime(audit, gate, cutoff)
    assert saturated.regime == "saturated"
    assert saturated.predicted_surviving_world_fraction == 1.0


def test_adequacy_gate_and_regime_predictor_cannot_reuse_horizon_reachability():
    nodes = tuple(f"n{index}" for index in range(6))
    audit = audit_world_universe_structure(
        nodes, {"world": _complete(6)}, horizon=1
    )
    declaration = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.9,
        min_median_horizon_reachable_fraction=0.5,
    )
    gate = apply_structural_adequacy_gate(audit, declaration)
    assert gate.passed is True

    with pytest.raises(ValueError, match="outside the structural adequacy gate"):
        forecast_world_survival_regime(
            audit,
            gate,
            RegimeForecastDeclaration(horizon_realization_cutoff=0.5),
        )


def test_non_falsifiable_external_open_is_not_part_of_regime_denominator():
    audit, gate = _audit_and_gate(
        {"local_star": _star(6), "external_open": _complete(6)}
    )
    forecast = forecast_world_survival_regime(
        audit,
        gate,
        RegimeForecastDeclaration(
            horizon_realization_cutoff=0.5,
            non_falsifiable_world_ids=("external_open",),
        ),
    )

    assert forecast.falsifiable_world_ids == ("local_star",)
    assert forecast.non_falsifiable_world_ids == ("external_open",)
    assert forecast.regime == "falsified_universe"
    assert forecast.predicted_surviving_world_fraction == 0.0


def test_louisiana_style_external_open_only_is_local_universe_falsification():
    observation = classify_observed_world_survival_regime(
        declared_world_ids=(
            "local_1",
            "local_2",
            "local_3",
            "external_open",
        ),
        surviving_world_ids_by_context=(
            ("local_1", "local_2", "local_3", "external_open"),
            ("local_2", "local_3", "external_open"),
            ("local_3", "external_open"),
            ("external_open",),
        ),
        non_falsifiable_world_ids=("external_open",),
    )

    assert observation.regime == "falsified_universe"
    assert observation.final_surviving_world_fraction == 0.0
    assert observation.contraction_event_count == 3
    assert observation.contraction_context_positions == (1, 2, 3)
    assert observation.surviving_falsifiable_counts == (3, 2, 1, 0)


def test_partial_local_survival_is_contracting_even_with_external_open():
    observation = classify_observed_world_survival_regime(
        declared_world_ids=("local_1", "local_2", "external_open"),
        surviving_world_ids_by_context=(
            ("local_1", "local_2", "external_open"),
            ("local_2", "external_open"),
        ),
        non_falsifiable_world_ids=("external_open",),
    )
    assert observation.regime == "contracting"
    assert observation.final_surviving_world_fraction == 0.5


def test_observed_trajectory_requires_complete_initial_state_and_monotone_contraction():
    with pytest.raises(ValueError, match="complete pre-evidence world set"):
        classify_observed_world_survival_regime(
            declared_world_ids=("a", "b"),
            surviving_world_ids_by_context=(("a",),),
        )

    with pytest.raises(ValueError, match="contract monotonically"):
        classify_observed_world_survival_regime(
            declared_world_ids=("a", "b"),
            surviving_world_ids_by_context=(
                ("a", "b"),
                ("a",),
                ("a", "b"),
            ),
        )


def test_score_reports_exact_match_and_survival_fraction_error():
    cutoff = RegimeForecastDeclaration(horizon_realization_cutoff=0.5)

    audit_a, gate_a = _audit_and_gate(
        {"a": _star(6), "b": _complete(6)}
    )
    forecast_a = forecast_world_survival_regime(audit_a, gate_a, cutoff)
    observed_a = classify_observed_world_survival_regime(
        declared_world_ids=("a", "b"),
        surviving_world_ids_by_context=(("a", "b"), ("b",)),
    )

    audit_b, gate_b = _audit_and_gate(
        {"a": _ring(6), "b": _complete(6)}
    )
    forecast_b = forecast_world_survival_regime(audit_b, gate_b, cutoff)
    observed_b = classify_observed_world_survival_regime(
        declared_world_ids=("a", "b"),
        surviving_world_ids_by_context=(("a", "b"),),
    )

    score = score_regime_forecasts(
        (forecast_a, forecast_b),
        (observed_a, observed_b),
    )
    assert score.system_count == 2
    assert score.exact_match_count == 2
    assert score.exact_match_fraction == 1.0
    assert score.mean_absolute_survival_fraction_error == 0.0
    assert 0.0 < score.one_sided_binomial_tail_p <= 1.0
