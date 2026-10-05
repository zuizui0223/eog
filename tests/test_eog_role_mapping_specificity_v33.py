import numpy as np

from benchmarks.run_eog_role_mapping_specificity_v33 import (
    _all_bijections,
    _mapping_key,
    _summarize_mapping_ensemble,
)


def test_complete_bijection_counts():
    assert len(_all_bijections(["a", "b", "c"], ["x", "y", "z"])) == 6
    assert len(
        _all_bijections(
            ["a", "b", "c", "d", "e"],
            ["v", "w", "x", "y", "z"],
        )
    ) == 120


def test_mapping_key_is_history_ordered():
    mapping = {"b": "y", "a": "x"}
    assert _mapping_key(mapping, ["a", "b"]) == "a->x|b->y"


def test_specificity_summary_uses_incorrect_median_and_exact_tail():
    rows = [
        {"mapping": "correct", "partial_r2": 0.9},
        {"mapping": "wrong1", "partial_r2": 0.1},
        {"mapping": "wrong2", "partial_r2": 0.2},
        {"mapping": "wrong3", "partial_r2": 0.3},
    ]
    summary = _summarize_mapping_ensemble(rows, "correct")
    assert np.isclose(summary["incorrect_mapping_median_r2"], 0.2)
    assert np.isclose(summary["correct_minus_incorrect_median"], 0.7)
    assert summary["correct_rank_descending"] == 1
    assert np.isclose(summary["exact_upper_tail_mapping_probability"], 0.25)
