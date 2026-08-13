import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2_empirical_occurrence_validation import (
    build_fixed_source_occurrence_features,
    evaluate_fixed_source_occurrence_validation,
)


def _fixture():
    ids = tuple(f"n{i}" for i in range(8))
    edges = []
    for i in range(7):
        edges.append(DynamicReachabilityEdge(i, i + 1, 0.65))
        edges.append(DynamicReachabilityEdge(i + 1, i, 0.65))
    operator = build_dynamic_transition_operator(ids, edges, loss_support=0.5)
    viability = np.array([0.8, 0.7, 0.6, 0.5, 0.45, 0.55, 0.65, 0.75])
    sources = np.array([True, False, False, False, False, False, False, True])
    reference = {"nearest": np.array([0, 1, 2, 3, 3, 2, 1, 0], dtype=float)}
    return ids, operator, viability, sources, reference


def test_feature_builder_is_response_free_and_deterministic():
    ids, operator, viability, sources, reference = _fixture()
    first = build_fixed_source_occurrence_features(
        ids,
        viability,
        sources,
        operator,
        max_steps=5,
        reference_features=reference,
    )
    second = build_fixed_source_occurrence_features(
        ids,
        viability,
        sources,
        operator,
        max_steps=5,
        reference_features=reference,
    )
    assert first.feature_fingerprint == second.feature_fingerprint
    assert first.reference_names == ("nearest",)
    assert np.allclose(first.dynamic_reachability, second.dynamic_reachability)


def test_response_changes_do_not_change_frozen_features():
    ids, operator, viability, sources, reference = _fixture()
    features = build_fixed_source_occurrence_features(
        ids, viability, sources, operator, max_steps=5, reference_features=reference
    )
    original = features.feature_fingerprint
    response_a = np.array([np.nan, 1, 0, 1, 0, 1, 0, np.nan])
    response_b = np.array([np.nan, 0, 1, 0, 1, 0, 1, np.nan])
    assert response_a.shape == response_b.shape
    assert features.feature_fingerprint == original


def test_validation_excludes_sources_and_uses_predeclared_folds():
    ids, operator, viability, sources, reference = _fixture()
    features = build_fixed_source_occurrence_features(
        ids, viability, sources, operator, max_steps=5, reference_features=reference
    )
    response = np.array([np.nan, 1, 0, 1, 0, 1, 0, np.nan])
    folds = ("source", "a", "b", "c", "a", "b", "c", "source")
    result = evaluate_fixed_source_occurrence_validation(
        features, response, folds, l2_penalty=1.0
    )
    assert result.n_evaluated == 6
    assert result.n_missing_response == 2
    names = {score.model_name for score in result.model_scores}
    assert "viability" in names
    assert "viability_dynamic" in names
    assert "viability_ref_nearest" in names
    assert "viability_ref_nearest_dynamic" in names


def test_presence_only_unsurveyed_nodes_are_not_silently_negatives():
    ids, operator, viability, sources, reference = _fixture()
    features = build_fixed_source_occurrence_features(
        ids, viability, sources, operator, max_steps=5, reference_features=reference
    )
    response = np.array([np.nan, 1, np.nan, 1, np.nan, 1, np.nan, np.nan])
    folds = tuple("a" if i % 2 else "b" for i in range(8))
    with pytest.raises(ValueError, match="at least four"):
        evaluate_fixed_source_occurrence_validation(features, response, folds)
