import numpy as np

from benchmarks.run_eog_history_level_leverage_v34 import (
    _rank,
    _summary,
)


def test_rank_preserves_each_row_multiset():
    x = np.asarray([[1.0, 4.0, 2.0], [3.0, 0.0, 5.0]])
    ranked = _rank(x)
    assert ranked.shape == x.shape
    for original, transformed in zip(x, ranked, strict=True):
        assert np.array_equal(np.sort(original), np.sort(transformed))


def test_summary_uses_null_median():
    null = np.asarray([0.1, 0.2, 0.3, 0.4])
    result = _summary(0.5, null)
    assert np.isclose(result["null_median"], 0.25)
    assert np.isclose(result["excess_over_null_median"], 0.25)
    assert np.isclose(result["permutation_p"], 0.2)
