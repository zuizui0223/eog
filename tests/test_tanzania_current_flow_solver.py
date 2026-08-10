from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("scipy")

from eog.tanzania_current_flow_candidates import build_grid_laplacian
from eog.tanzania_current_flow_solver import (
    SOLVER_POLICY,
    SOLVER_POLICY_ID,
    deterministic_effective_resistance_matrix,
)


def _focals(compact: np.ndarray, cells: list[tuple[int, int]]) -> np.ndarray:
    return np.asarray([compact[cell] for cell in cells], dtype=np.int64)


def test_solver_policy_is_explicit_and_disables_dynamic_pivoting() -> None:
    assert SOLVER_POLICY_ID == (
        "grounded_spd_superlu_colamd_no_dynamic_pivot_v1"
    )
    assert SOLVER_POLICY["permc_spec"] == "COLAMD"
    assert SOLVER_POLICY["diag_pivot_thresh"] == 0.0
    assert SOLVER_POLICY["symmetric_mode"] is True


def test_fixed_solver_recovers_exact_line_network() -> None:
    laplacian, compact = build_grid_laplacian(
        np.ones((1, 4)),
        connect_four_neighbors_only=True,
    )
    observed = deterministic_effective_resistance_matrix(
        laplacian,
        _focals(compact, [(0, 0), (0, 1), (0, 2), (0, 3)]),
    )
    expected = np.abs(
        np.arange(4, dtype=float)[:, None]
        - np.arange(4, dtype=float)[None, :]
    )
    assert np.allclose(observed, expected, atol=1e-10)


def test_fixed_solver_is_bit_identical_on_ill_conditioned_grid() -> None:
    resistance = np.ones((18, 20), dtype=float)
    resistance[:, 5:10] = 8.0
    resistance[:, 10:15] = 64.0
    resistance[:, 15:] = 128.0
    laplacian, compact = build_grid_laplacian(resistance)
    cells = [
        (0, 0),
        (0, 19),
        (17, 0),
        (17, 19),
        (8, 4),
        (8, 9),
        (8, 14),
        (8, 18),
    ]
    focal_indices = _focals(compact, cells)
    first = deterministic_effective_resistance_matrix(
        laplacian, focal_indices
    )
    second = deterministic_effective_resistance_matrix(
        laplacian, focal_indices
    )
    assert np.array_equal(first, second)
    assert np.allclose(first, first.T, atol=0.0)
    assert np.array_equal(np.diag(first), np.zeros(len(cells)))
