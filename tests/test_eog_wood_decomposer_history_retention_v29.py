import numpy as np

from benchmarks.run_eog_wood_decomposer_history_retention_v29 import (
    _bray_curtis,
    _context,
    _fast_partial_distance,
    _fast_partial_scalar,
    _jaccard,
)


def test_context_is_exact_boolean_pair():
    assert _context("TRUE", "FALSE") == "N=TRUE|F=FALSE"


def test_bray_curtis_and_jaccard_have_expected_geometry():
    x = np.asarray(
        [
            [9.0, 0.0, 0.0],
            [4.5, 4.5, 0.0],
            [0.0, 0.0, 9.0],
        ]
    )
    bray = _bray_curtis(x)
    jac = _jaccard(x)
    assert np.isclose(bray[0, 1], 0.5)
    assert np.isclose(bray[0, 2], 1.0)
    assert np.isclose(jac[0, 1], 0.5)
    assert np.isclose(jac[0, 2], 1.0)


def test_fast_scalar_history_retention_is_one_for_perfect_cells():
    context = np.repeat(np.array(["c1", "c2"]), 8)
    history = np.tile(np.repeat(np.array(["h1", "h2"]), 4), 2)
    values = np.asarray(
        [0.0 if h == "h1" else 10.0 for h in history],
        dtype=float,
    )
    assert np.isclose(_fast_partial_scalar(values, context, history), 1.0)


def test_fast_distance_history_retention_is_one_for_perfect_cells():
    context = np.repeat(np.array(["c1", "c2"]), 8)
    history = np.tile(np.repeat(np.array(["h1", "h2"]), 4), 2)
    state = np.asarray(
        [[0.0, 1.0] if h == "h1" else [1.0, 0.0] for h in history],
        dtype=float,
    )
    distance = _bray_curtis(state)
    assert np.isclose(_fast_partial_distance(distance, context, history), 1.0)
