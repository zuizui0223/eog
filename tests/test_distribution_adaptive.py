import numpy as np

from benchmarks.distribution_gate_shrinkage import build_environment_only_landscape
from benchmarks.distribution_model_heldout_benchmark import (
    _auc,
    build_replicated_landscape,
)
from eog import BridgeGraphDeclaration, BridgeWeights, EOGDistributionConfig
from eog.distribution_adaptive import (
    ADAPTIVE_FAMILIES,
    AdaptiveEOGDistributionConfig,
    fit_adaptive_eog_distribution,
)


def _selection_folds(observed_ids):
    return [f"selection_{int(node_id[1:3]) % 3}" for node_id in observed_ids]


def _suffix_gate_folds(observed_ids):
    return ["inner_a" if node_id.endswith("_a") else "inner_b" for node_id in observed_ids]


def test_adaptive_eog_selects_environmental_family_on_exact_structural_null():
    nodes, observed_ids, response, target_ids, target_response = (
        build_environment_only_landscape(9)
    )
    model = fit_adaptive_eog_distribution(
        nodes,
        observed_ids,
        response,
        AdaptiveEOGDistributionConfig(
            base_config=EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=20.0),
                bridge_weights=BridgeWeights(
                    geographic=0.0,
                    environmental=0.0,
                    barrier=1.0,
                ),
                structural_gate_penalty=0.01,
                gate_grid_size=201,
                min_class_count=4,
            )
        ),
        selection_fold_ids=_selection_folds(observed_ids),
        gate_fold_ids=_suffix_gate_folds(observed_ids),
    )
    prediction = model.predict(target_ids)
    labels = np.asarray(target_response, dtype=int)

    assert ADAPTIVE_FAMILIES == ("environmental", "probability_gate", "stacked")
    assert model.selected_family == "environmental"
    assert np.array_equal(
        prediction.distribution_support, prediction.environmental_support
    )
    assert _auc(labels, prediction.distribution_support) == 1.0


def test_adaptive_eog_activates_structural_family_when_environment_is_tied():
    (
        nodes,
        observed_ids,
        response,
        gate_folds,
        target_ids,
        target_response,
        _sources,
    ) = build_replicated_landscape(9)
    model = fit_adaptive_eog_distribution(
        nodes,
        observed_ids,
        response,
        AdaptiveEOGDistributionConfig(
            base_config=EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
                structural_gate_penalty=0.01,
                gate_grid_size=201,
                min_class_count=4,
            )
        ),
        selection_fold_ids=_selection_folds(observed_ids),
        gate_fold_ids=gate_folds,
    )
    labels = np.asarray(target_response, dtype=int)
    prediction = model.predict(target_ids)

    assert model.selected_family in {"probability_gate", "stacked"}
    assert model.candidate_log_loss[model.selected_family] < model.candidate_log_loss[
        "environmental"
    ]
    assert _auc(labels, prediction.distribution_support) == 1.0


def test_adaptive_eog_requires_three_selection_folds():
    (
        nodes,
        observed_ids,
        response,
        gate_folds,
        _target_ids,
        _target_response,
        _sources,
    ) = build_replicated_landscape(6)
    try:
        fit_adaptive_eog_distribution(
            nodes,
            observed_ids,
            response,
            AdaptiveEOGDistributionConfig(
                base_config=EOGDistributionConfig(
                    graph_declaration=BridgeGraphDeclaration(max_geographic_km=15.0),
                    min_class_count=2,
                )
            ),
            selection_fold_ids=[f"s{index % 2}" for index in range(len(observed_ids))],
            gate_fold_ids=gate_folds,
        )
    except ValueError as exc:
        assert "at least 3 folds" in str(exc)
    else:
        raise AssertionError("adaptive selection must require at least three folds")
