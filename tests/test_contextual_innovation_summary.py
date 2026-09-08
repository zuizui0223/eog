from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from eog.v2.contextual_innovation_summary import summarize_contextual_innovation
from eog.v2.source_symmetric_predictive_summary import (
    summarize_source_symmetric_support,
)


def _summary(tensor: np.ndarray, *, sources=("s1", "s2"), worlds=("w1", "w2")):
    return summarize_source_symmetric_support(
        tensor,
        source_ids=sources,
        world_ids=worlds,
        node_ids=("n1", "n2", "n3"),
        declared_world_count=2,
    )


def test_identical_state_maps_exactly_to_zero() -> None:
    tensor = np.asarray(
        [
            [[1.0, 0.2, 0.0], [1.0, 0.8, 0.1]],
            [[0.0, 0.6, 1.0], [0.2, 0.4, 1.0]],
        ],
        dtype=float,
    )
    state = _summary(tensor)
    result = summarize_contextual_innovation(state, state)
    assert np.array_equal(result.feature_matrix, np.zeros((3, 10)))
    assert result.exact_zero_matrix is True
    assert result.changed_node_fraction == 0.0
    assert result.mean_absolute_innovation == 0.0
    assert result.max_absolute_innovation == 0.0


def test_shared_static_node_signature_cancels_exactly() -> None:
    reference_tensor = np.asarray(
        [
            [[0.8, 0.2, 0.1], [0.7, 0.5, 0.2]],
            [[0.3, 0.4, 0.9], [0.4, 0.6, 0.8]],
        ],
        dtype=float,
    )
    current_tensor = np.asarray(
        [
            [[0.9, 0.4, 0.1], [0.8, 0.7, 0.3]],
            [[0.5, 0.5, 0.9], [0.6, 0.8, 0.9]],
        ],
        dtype=float,
    )
    reference = _summary(reference_tensor)
    current = _summary(current_tensor)
    base = summarize_contextual_innovation(reference, current)

    # Mimic an arbitrary node-static geometry/topology signature already present in
    # both contexts. Algebraically it cancels exactly; binary floating arithmetic may
    # differ at machine epsilon depending on addition/subtraction association.
    static_offset = np.arange(30, dtype=float).reshape(3, 10) / 100.0
    shifted_reference = replace(
        reference,
        feature_matrix=reference.feature_matrix + static_offset,
        feature_fingerprint="shifted-reference",
    )
    shifted_current = replace(
        current,
        feature_matrix=current.feature_matrix + static_offset,
        feature_fingerprint="shifted-current",
    )
    shifted = summarize_contextual_innovation(shifted_reference, shifted_current)
    np.testing.assert_allclose(base.feature_matrix, shifted.feature_matrix, rtol=0.0, atol=1e-15)


def test_context_change_remains_nonzero() -> None:
    reference = _summary(
        np.asarray(
            [
                [[0.8, 0.2, 0.1], [0.7, 0.5, 0.2]],
                [[0.3, 0.4, 0.9], [0.4, 0.6, 0.8]],
            ],
            dtype=float,
        )
    )
    current = _summary(
        np.asarray(
            [
                [[0.9, 0.4, 0.1], [0.8, 0.7, 0.3]],
                [[0.5, 0.5, 0.9], [0.6, 0.8, 0.9]],
            ],
            dtype=float,
        )
    )
    result = summarize_contextual_innovation(reference, current)
    assert result.exact_zero_matrix is False
    assert result.changed_node_fraction > 0.0
    assert result.mean_absolute_innovation > 0.0
    assert result.max_absolute_innovation > 0.0


def test_source_and_world_renaming_reordering_do_not_change_innovation() -> None:
    ref_tensor = np.asarray(
        [
            [[0.8, 0.2, 0.1], [0.7, 0.5, 0.2]],
            [[0.3, 0.4, 0.9], [0.4, 0.6, 0.8]],
        ],
        dtype=float,
    )
    cur_tensor = np.asarray(
        [
            [[0.9, 0.4, 0.1], [0.8, 0.7, 0.3]],
            [[0.5, 0.5, 0.9], [0.6, 0.8, 0.9]],
        ],
        dtype=float,
    )
    original = summarize_contextual_innovation(_summary(ref_tensor), _summary(cur_tensor))
    renamed = summarize_contextual_innovation(
        _summary(ref_tensor[::-1, ::-1, :], sources=("banana", "saffron"), worlds=("x", "y")),
        _summary(cur_tensor[::-1, ::-1, :], sources=("banana", "saffron"), worlds=("x", "y")),
    )
    assert np.array_equal(original.feature_matrix, renamed.feature_matrix)
    assert original.innovation_feature_fingerprint == renamed.innovation_feature_fingerprint


def test_node_mismatch_fails_closed() -> None:
    state = _summary(
        np.asarray(
            [
                [[0.8, 0.2, 0.1], [0.7, 0.5, 0.2]],
                [[0.3, 0.4, 0.9], [0.4, 0.6, 0.8]],
            ],
            dtype=float,
        )
    )
    mismatched = replace(state, node_ids=("n1", "n3", "n2"))
    with pytest.raises(ValueError, match="node_ids"):
        summarize_contextual_innovation(state, mismatched)
