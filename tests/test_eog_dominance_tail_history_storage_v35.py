import numpy as np

from benchmarks.run_eog_dominance_tail_history_storage_v35 import _rank_decompose


def test_rank_decomposition_preserves_values_and_normalizes_tail():
    x = np.asarray(
        [
            [0.5, 0.2, 0.15, 0.1, 0.05],
            [0.1, 0.4, 0.3, 0.15, 0.05],
        ],
        dtype=float,
    )
    ranked, dominance, tail = _rank_decompose(x)
    assert ranked.shape == x.shape
    assert dominance.shape == (2,)
    assert tail.shape == (2, 4)
    assert np.allclose(tail.sum(axis=1), 1.0)
    for original, transformed in zip(x, ranked, strict=True):
        assert np.array_equal(np.sort(original), np.sort(transformed))


def test_rank_decomposition_removes_identity():
    x = np.asarray(
        [
            [0.7, 0.2, 0.1, 0.0, 0.0],
            [0.0, 0.7, 0.0, 0.2, 0.1],
        ],
        dtype=float,
    )
    ranked, dominance, tail = _rank_decompose(x)
    assert np.array_equal(ranked[0], ranked[1])
    assert np.isclose(dominance[0], dominance[1])
    assert np.allclose(tail[0], tail[1])
