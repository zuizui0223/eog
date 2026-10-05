import numpy as np

from benchmarks.run_eog_grassland_above_below_history_retention_v30 import (
    _bray_curtis,
    _designs,
    _partial_distance,
    _partial_scalar,
    _permute_within_block,
)


def test_bray_curtis_geometry():
    x = np.asarray([[1, 0, 0], [0.5, 0.5, 0], [0, 0, 1]], dtype=float)
    d = _bray_curtis(x)
    assert np.isclose(d[0, 1], 0.5)
    assert np.isclose(d[0, 2], 1.0)
    assert np.allclose(d, d.T)


def test_blocked_history_design_adds_history_subspace():
    block = np.asarray(["1","1","1","2","2","2"], dtype=object)
    history = np.asarray(["F","G","L","F","G","L"], dtype=object)
    reduced, full = _designs(block, history)
    assert np.linalg.matrix_rank(full) > np.linalg.matrix_rank(reduced)


def test_blocked_permutation_preserves_block_labels():
    block = np.asarray(["1","1","1","2","2"], dtype=object)
    history = np.asarray(["F","G","L","F","G"], dtype=object)
    rng = np.random.default_rng(1)
    permuted = _permute_within_block(history, block, rng)
    for level in set(block):
        idx = block == level
        assert sorted(permuted[idx].tolist()) == sorted(history[idx].tolist())


def test_fast_scalar_and_distance_detect_perfect_history():
    block = np.asarray(["1","1","1","2","2","2"], dtype=object)
    history = np.asarray(["F","G","L","F","G","L"], dtype=object)
    reduced, full = _designs(block, history)
    values = np.asarray([0, 5, 10, 0, 5, 10], dtype=float)
    state = np.column_stack([values + 1, 11 - values])
    distance = _bray_curtis(state)
    assert np.isclose(_partial_scalar(values, reduced, full), 1.0)
    assert np.isclose(_partial_distance(distance, reduced, full), 1.0)
