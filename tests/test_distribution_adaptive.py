import numpy as np

from benchmarks.distribution_model_heldout_benchmark import _auc
from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    BridgeWeights,
    EOGDistributionConfig,
)
from eog.distribution_adaptive import (
    ADAPTIVE_FAMILIES,
    AdaptiveEOGDistributionConfig,
    fit_adaptive_eog_distribution,
)


def _selection_folds(observed_ids):
    offsets = {
        "fixed_a": 0,
        "fixed_b": 1,
        "positive_a": 0,
        "positive_b": 1,
        "blocked_a": 1,
        "blocked_b": 2,
        "negative_a": 2,
        "negative_b": 0,
    }
    result = []
    for node_id in observed_ids:
        module = int(node_id[1:3])
        role = node_id.split("_", 1)[1]
        result.append(f"selection_{(module + offsets[role]) % 3}")
    return result


def _build_adaptive_landscape(*, structural: bool, n_modules: int = 9):
    nodes = []
    observed_ids = []
    response = []
    gate_folds = []
    fixed_sources = []
    target_ids = []
    target_response = []

    for module in range(n_modules):
        latitude = -4.0 + module * 1.0
        prefix = f"m{module:02d}"
        fixed_a = f"{prefix}_fixed_a"
        fixed_b = f"{prefix}_fixed_b"
        positive_a = f"{prefix}_positive_a"
        positive_b = f"{prefix}_positive_b"
        blocked_a = f"{prefix}_blocked_a"
        blocked_b = f"{prefix}_blocked_b"
        negative_a = f"{prefix}_negative_a"
        negative_b = f"{prefix}_negative_b"

        if structural:
            nodes.extend(
                [
                    BridgeNode(fixed_a, latitude + 0.002, 0.00, (0.8,)),
                    BridgeNode(fixed_b, latitude - 0.002, 0.00, (0.8,)),
                    BridgeNode(f"{prefix}_path_1", latitude, 0.08, (0.8,)),
                    BridgeNode(f"{prefix}_path_2", latitude, 0.16, (0.8,)),
                    BridgeNode(positive_a, latitude + 0.002, 0.24, (0.8,)),
                    BridgeNode(positive_b, latitude - 0.002, 0.24, (0.8,)),
                    BridgeNode(blocked_a, latitude + 0.002, -0.24, (0.8,)),
                    BridgeNode(blocked_b, latitude - 0.002, -0.24, (0.8,)),
                    BridgeNode(negative_a, latitude + 0.002, 0.04, (0.1,)),
                    BridgeNode(negative_b, latitude - 0.002, 0.04, (0.1,)),
                    BridgeNode(f"{prefix}_target_positive", latitude, 0.25, (0.8,)),
                    BridgeNode(f"{prefix}_target_blocked", latitude, -0.25, (0.8,)),
                ]
            )
        else:
            rows = [
                (fixed_a, 0.00, 0.9),
                (fixed_b, 0.02, 0.9),
                (positive_a, 0.04, 0.9),
                (positive_b, 0.06, 0.9),
                (blocked_a, 0.08, 0.1),
                (blocked_b, 0.10, 0.1),
                (negative_a, 0.12, 0.1),
                (negative_b, 0.14, 0.1),
                (f"{prefix}_target_positive", 0.16, 0.9),
                (f"{prefix}_target_blocked", 0.18, 0.1),
            ]
            nodes.extend(
                [BridgeNode(node_id, latitude, longitude, (environment,)) for node_id, longitude, environment in rows]
            )

        observed_rows = [
            (fixed_a, 1, "inner_a"),
            (fixed_b, 1, "inner_b"),
            (positive_a, 1, "inner_a"),
            (positive_b, 1, "inner_b"),
            (blocked_a, 0, "inner_a"),
            (blocked_b, 0, "inner_b"),
            (negative_a, 0, "inner_a"),
            (negative_b, 0, "inner_b"),
        ]
        for node_id, label, fold in observed_rows:
            observed_ids.append(node_id)
            response.append(label)
            gate_folds.append(fold)
        fixed_sources.extend([fixed_a, fixed_b])
        target_ids.extend(
            [f"{prefix}_target_positive", f"{prefix}_target_blocked"]
        )
        target_response.extend([1, 0])

    return (
        nodes,
        observed_ids,
        response,
        gate_folds,
        fixed_sources,
        target_ids,
        target_response,
    )


def test_adaptive_eog_selects_environmental_family_on_exact_structural_null():
    (
        nodes,
        observed_ids,
        response,
        gate_folds,
        fixed_sources,
        target_ids,
        target_response,
    ) = _build_adaptive_landscape(structural=False)
    model = fit_adaptive_eog_distribution(
        nodes,
        observed_ids,
        response,
        AdaptiveEOGDistributionConfig(
            base_config=EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=30.0),
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
        gate_fold_ids=gate_folds,
        selection_fixed_source_ids=fixed_sources,
    )
    prediction = model.predict(target_ids)
    labels = np.asarray(target_response, dtype=int)

    assert ADAPTIVE_FAMILIES == ("environmental", "probability_gate", "stacked")
    assert model.selected_family == "environmental"
    assert model.selection_fixed_source_ids == tuple(sorted(fixed_sources))
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
        fixed_sources,
        target_ids,
        target_response,
    ) = _build_adaptive_landscape(structural=True)
    model = fit_adaptive_eog_distribution(
        nodes,
        observed_ids,
        response,
        AdaptiveEOGDistributionConfig(
            base_config=EOGDistributionConfig(
                graph_declaration=BridgeGraphDeclaration(max_geographic_km=12.0),
                bridge_weights=BridgeWeights(
                    geographic=1.0,
                    environmental=0.0,
                    barrier=0.0,
                ),
                structural_gate_penalty=0.01,
                gate_grid_size=201,
                min_class_count=4,
            )
        ),
        selection_fold_ids=_selection_folds(observed_ids),
        gate_fold_ids=gate_folds,
        selection_fixed_source_ids=fixed_sources,
    )
    labels = np.asarray(target_response, dtype=int)
    prediction = model.predict(target_ids)

    assert model.selected_family in {"probability_gate", "stacked"}
    assert model.candidate_log_loss[model.selected_family] < model.candidate_log_loss[
        "environmental"
    ]
    assert _auc(labels, prediction.distribution_support) == 1.0


def test_adaptive_eog_rejects_nonpositive_fixed_source():
    (
        nodes,
        observed_ids,
        response,
        gate_folds,
        fixed_sources,
        _target_ids,
        _target_response,
    ) = _build_adaptive_landscape(structural=True, n_modules=6)
    nonpositive = next(
        node_id for node_id, label in zip(observed_ids, response) if label == 0
    )
    try:
        fit_adaptive_eog_distribution(
            nodes,
            observed_ids,
            response,
            AdaptiveEOGDistributionConfig(
                base_config=EOGDistributionConfig(
                    graph_declaration=BridgeGraphDeclaration(max_geographic_km=12.0),
                    min_class_count=2,
                )
            ),
            selection_fold_ids=_selection_folds(observed_ids),
            gate_fold_ids=gate_folds,
            selection_fixed_source_ids=fixed_sources + [nonpositive],
        )
    except ValueError as exc:
        assert "must be positive" in str(exc)
    else:
        raise AssertionError("adaptive fixed sources must be positive training rows")


def test_adaptive_eog_requires_three_selection_folds():
    (
        nodes,
        observed_ids,
        response,
        gate_folds,
        fixed_sources,
        _target_ids,
        _target_response,
    ) = _build_adaptive_landscape(structural=True, n_modules=6)
    try:
        fit_adaptive_eog_distribution(
            nodes,
            observed_ids,
            response,
            AdaptiveEOGDistributionConfig(
                base_config=EOGDistributionConfig(
                    graph_declaration=BridgeGraphDeclaration(max_geographic_km=12.0),
                    min_class_count=2,
                )
            ),
            selection_fold_ids=[f"s{index % 2}" for index in range(len(observed_ids))],
            gate_fold_ids=gate_folds,
            selection_fixed_source_ids=fixed_sources,
        )
    except ValueError as exc:
        assert "at least 3 folds" in str(exc)
    else:
        raise AssertionError("adaptive selection must require at least three folds")
