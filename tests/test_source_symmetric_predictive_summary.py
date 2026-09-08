import numpy as np

from eog.v2.source_symmetric_predictive_summary import (
    SOURCE_SYMMETRIC_FEATURE_NAMES,
    summarize_source_symmetric_support,
)


def _support():
    # source x world x node
    return np.asarray(
        [
            [[1.0, 0.2, 0.0], [1.0, 0.8, 0.0]],
            [[0.0, 0.6, 1.0], [0.0, 0.4, 1.0]],
        ],
        dtype=float,
    )


def test_source_order_is_prediction_fingerprint_invariant():
    support = _support()
    forward = summarize_source_symmetric_support(
        support,
        source_ids=("source_a", "source_b"),
        world_ids=("world_1", "world_2"),
        node_ids=("a", "b", "c"),
        declared_world_count=3,
    )
    reverse = summarize_source_symmetric_support(
        support[::-1],
        source_ids=("source_b", "source_a"),
        world_ids=("world_1", "world_2"),
        node_ids=("a", "b", "c"),
        declared_world_count=3,
    )
    assert np.array_equal(forward.feature_matrix, reverse.feature_matrix)
    assert forward.feature_fingerprint == reverse.feature_fingerprint
    assert forward.latent_state_fingerprint != reverse.latent_state_fingerprint


def test_source_renaming_changes_latent_identity_not_predictive_features():
    support = _support()
    original = summarize_source_symmetric_support(
        support,
        source_ids=("source_a", "source_b"),
        world_ids=("world_1", "world_2"),
        node_ids=("a", "b", "c"),
        declared_world_count=2,
    )
    renamed = summarize_source_symmetric_support(
        support,
        source_ids=("banana", "saffron"),
        world_ids=("world_1", "world_2"),
        node_ids=("a", "b", "c"),
        declared_world_count=2,
    )
    assert np.array_equal(original.feature_matrix, renamed.feature_matrix)
    assert original.feature_fingerprint == renamed.feature_fingerprint
    assert original.latent_state_fingerprint != renamed.latent_state_fingerprint


def test_world_order_and_names_do_not_change_prediction_features():
    support = _support()
    original = summarize_source_symmetric_support(
        support,
        source_ids=("s1", "s2"),
        world_ids=("w1", "w2"),
        node_ids=("a", "b", "c"),
        declared_world_count=2,
    )
    changed = summarize_source_symmetric_support(
        support[:, ::-1, :],
        source_ids=("s1", "s2"),
        world_ids=("renamed_2", "renamed_1"),
        node_ids=("a", "b", "c"),
        declared_world_count=2,
    )
    assert np.array_equal(original.feature_matrix, changed.feature_matrix)
    assert original.feature_fingerprint == changed.feature_fingerprint


def test_summary_uses_equal_weight_source_aggregation_then_world_summary():
    summary = summarize_source_symmetric_support(
        _support(),
        source_ids=("s1", "s2"),
        world_ids=("w1", "w2"),
        node_ids=("a", "b", "c"),
        declared_world_count=4,
    )
    assert summary.feature_names == SOURCE_SYMMETRIC_FEATURE_NAMES
    assert summary.feature_matrix.shape == (3, 10)
    assert np.allclose(summary.feature_matrix[:, 0], 0.5)
    # node a has source-mean support 0.5 in both surviving worlds.
    assert summary.feature_matrix[0, 1] == 0.5
    assert summary.feature_matrix[0, 2] == 0.0
    assert summary.statuses[0] == "robustly_supported"
