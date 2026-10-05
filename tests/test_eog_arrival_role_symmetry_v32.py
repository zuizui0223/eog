import numpy as np

from benchmarks.run_eog_arrival_role_symmetry_v32 import _role_align


def test_role_alignment_preserves_values_and_puts_first_arriver_first():
    matrix = np.asarray([[0.1, 0.6, 0.3], [0.7, 0.2, 0.1]], dtype=float)
    history = np.asarray(["B", "A"], dtype=object)
    aligned, share = _role_align(matrix, history, ["A", "B", "C"])
    assert np.allclose(aligned[0], [0.6, 0.3, 0.1])
    assert np.allclose(aligned[1], [0.7, 0.2, 0.1])
    assert np.allclose(share, [0.6, 0.7])
    for original, transformed in zip(matrix, aligned, strict=True):
        assert np.array_equal(np.sort(original), np.sort(transformed))


def test_role_alignment_supports_history_to_identity_mapping():
    matrix = np.asarray([[5.0, 2.0, 1.0], [1.0, 6.0, 2.0]])
    history = np.asarray(["F-first", "G-first"], dtype=object)
    aligned, _ = _role_align(
        matrix,
        history,
        ["Forbs", "Grasses", "Legumes"],
        {"F-first": "Forbs", "G-first": "Grasses"},
    )
    assert np.array_equal(aligned[0], [5.0, 2.0, 1.0])
    assert np.array_equal(aligned[1], [6.0, 2.0, 1.0])
