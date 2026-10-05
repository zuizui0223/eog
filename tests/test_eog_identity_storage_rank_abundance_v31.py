import numpy as np

from benchmarks.run_eog_identity_storage_rank_abundance_v31 import (
    _rank_matrix,
    _shannon,
)


def test_rank_matrix_preserves_each_row_values_and_dimensions():
    x = np.asarray([[1.0, 3.0, 2.0], [5.0, 0.0, 4.0]])
    ranked = _rank_matrix(x)
    assert ranked.shape == x.shape
    assert np.array_equal(ranked, np.asarray([[3.0, 2.0, 1.0], [5.0, 4.0, 0.0]]))
    for original, transformed in zip(x, ranked, strict=True):
        assert np.array_equal(np.sort(original), np.sort(transformed))


def test_rank_matrix_removes_identity_but_keeps_abundance_shape():
    a = np.asarray([[9.0, 1.0, 0.0], [0.0, 9.0, 1.0]])
    ranked = _rank_matrix(a)
    assert np.array_equal(ranked[0], ranked[1])


def test_shannon_is_label_invariant():
    a = np.asarray([[9.0, 1.0, 0.0], [0.0, 9.0, 1.0]])
    h = _shannon(a)
    assert np.isclose(h[0], h[1])
