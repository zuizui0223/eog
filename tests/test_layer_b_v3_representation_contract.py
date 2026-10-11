import numpy as np
import pytest

from eog.v2.compact_source_symmetric_summary import (
    COMPACT_SOURCE_SYMMETRIC_FEATURE_NAMES,
    summarize_compact_source_symmetric_support,
)
from eog.v2.paired_seed_evaluation import evaluate_paired_seed_scores
from eog.v2.structure_preserving_placebo import (
    permute_group_vectors,
    permute_joint_rows,
)


def _support():
    # source x world x node
    return np.asarray(
        [
            [
                [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
                [0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            ],
            [
                [0.2, 0.1, 0.4, 0.3, 0.6, 0.5],
                [0.3, 0.2, 0.5, 0.4, 0.7, 0.6],
                [0.4, 0.3, 0.6, 0.5, 0.8, 0.7],
                [0.5, 0.4, 0.7, 0.6, 0.9, 0.8],
                [0.6, 0.5, 0.8, 0.7, 1.0, 0.9],
            ],
        ],
        dtype=float,
    )


def _summary(support=None, source_ids=("s1", "s2"), world_ids=None):
    if support is None:
        support = _support()
    if world_ids is None:
        world_ids = tuple(f"w{i}" for i in range(1, 6))
    return summarize_compact_source_symmetric_support(
        support,
        source_ids=source_ids,
        world_ids=world_ids,
        node_ids=tuple(f"n{i}" for i in range(1, 7)),
        declared_world_count=5,
    )


def test_compact_projection_has_only_four_declared_columns():
    summary = _summary()
    assert summary.feature_names == COMPACT_SOURCE_SYMMETRIC_FEATURE_NAMES
    assert summary.feature_matrix.shape == (6, 4)
    assert "support_range" not in summary.feature_names
    assert "support_q25" not in summary.feature_names
    assert "support_q50" not in summary.feature_names
    assert "support_q75" not in summary.feature_names
    assert "support_max" not in summary.feature_names
    assert summary.latent_dimension_upper_bound == 5


def test_surviving_fraction_is_explicitly_reported_as_constant_within_one_state():
    summary = _summary()
    assert "surviving_world_fraction" in summary.constant_feature_names
    assert np.all(summary.feature_matrix[:, 0] == 1.0)
    # At one frozen state the constant survival column cannot increase centered rank.
    assert summary.centered_feature_rank <= 3


def test_compact_projection_is_source_and_world_label_order_invariant():
    support = _support()
    original = _summary(support=support)
    changed = _summary(
        support=support[::-1, ::-1, :],
        source_ids=("renamed_b", "renamed_a"),
        world_ids=("z5", "z4", "z3", "z2", "z1"),
    )
    assert np.array_equal(original.feature_matrix, changed.feature_matrix)
    assert original.feature_fingerprint == changed.feature_fingerprint
    assert original.latent_state_fingerprint != changed.latent_state_fingerprint


def _sorted_rows(matrix):
    return sorted(tuple(float(value) for value in row) for row in matrix)


def test_joint_row_placebo_preserves_full_row_multiset_and_covariance():
    matrix = np.asarray(
        [
            [0.0, 1.0, 2.0],
            [1.0, 3.0, 5.0],
            [2.0, 5.0, 8.0],
            [3.0, 7.0, 11.0],
            [4.0, 9.0, 14.0],
        ],
        dtype=float,
    )
    result = permute_joint_rows(matrix, seed=20260925)
    assert _sorted_rows(result.feature_matrix) == _sorted_rows(matrix)
    assert np.allclose(
        np.cov(result.feature_matrix, rowvar=False),
        np.cov(matrix, rowvar=False),
    )


def test_group_placebo_preserves_static_reuse_and_group_level_vectors():
    matrix = np.asarray(
        [
            [1.0, 10.0],
            [1.0, 10.0],
            [2.0, 20.0],
            [2.0, 20.0],
            [2.0, 20.0],
            [3.0, 30.0],
            [3.0, 30.0],
        ],
        dtype=float,
    )
    groups = ("a", "a", "b", "b", "b", "c", "c")
    result = permute_group_vectors(matrix, group_ids=groups, seed=20260925)

    original_group_vectors = {
        group: tuple(matrix[list(groups).index(group), :])
        for group in sorted(set(groups))
    }
    placebo_group_vectors = {
        group: tuple(result.feature_matrix[list(groups).index(group), :])
        for group in sorted(set(groups))
    }
    assert sorted(original_group_vectors.values()) == sorted(placebo_group_vectors.values())

    for group in sorted(set(groups)):
        idx = [i for i, value in enumerate(groups) if value == group]
        block = result.feature_matrix[np.asarray(idx, dtype=int), :]
        assert np.all(block == block[0, :])


def test_group_placebo_rejects_nonstatic_within_group_features():
    matrix = np.asarray([[1.0, 2.0], [1.0, 3.0]], dtype=float)
    with pytest.raises(ValueError, match="identical feature vector per group"):
        permute_group_vectors(matrix, group_ids=("same", "same"), seed=1)


def test_primary_seed_contract_pairs_the_same_multiple_seeds():
    baseline_calls = []
    augmented_calls = []

    def baseline(seed):
        baseline_calls.append(seed)
        return 0.4 + seed * 0.0

    def augmented(seed):
        augmented_calls.append(seed)
        return 0.35 + seed * 0.0

    seeds = (101, 202, 303, 404)
    result = evaluate_paired_seed_scores(
        seeds=seeds,
        baseline_score=baseline,
        augmented_score=augmented,
    )
    assert tuple(baseline_calls) == seeds
    assert tuple(augmented_calls) == seeds
    assert result.seeds == seeds
    assert result.mean_delta == pytest.approx(-0.05)
    assert result.augmented_win_fraction == 1.0


def test_primary_seed_contract_rejects_single_seed_by_default():
    with pytest.raises(ValueError, match="requires multiple learner seeds"):
        evaluate_paired_seed_scores(
            seeds=(101,),
            baseline_score=lambda seed: 0.4,
            augmented_score=lambda seed: 0.3,
        )
