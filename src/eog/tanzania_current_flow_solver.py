"""Deterministic sparse solve policy for Tanzania current-flow candidates.

The grounded graph Laplacian is symmetric positive definite. SuperLU's default
dynamic diagonal pivoting can choose numerically equivalent but slightly
different elimination paths on ill-conditioned high-resistance candidates.
That variation is ecologically negligible but breaks exact reproducibility.
This module keeps the frozen COLAMD fill-reducing ordering while disabling
unneeded dynamic pivoting and declaring symmetric mode explicitly.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

SOLVER_POLICY_ID = "grounded_spd_superlu_colamd_no_dynamic_pivot_v1"
SOLVER_POLICY = {
    "solver": "scipy.sparse.linalg.splu",
    "matrix_class": "grounded_symmetric_positive_definite_graph_laplacian",
    "permc_spec": "COLAMD",
    "diag_pivot_thresh": 0.0,
    "symmetric_mode": True,
    "rationale": (
        "a connected grounded Laplacian is SPD, so dynamic diagonal pivoting "
        "is unnecessary and caused run-to-run last-bit branching in the "
        "pre-outcome candidate audit"
    ),
}


def deterministic_effective_resistance_matrix(
    laplacian: Any,
    focal_indices: Sequence[int],
) -> np.ndarray:
    """Compute focal effective resistance under the fixed SPD solve policy."""
    try:
        from scipy.sparse.linalg import splu
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "scipy is required for current-flow candidate generation"
        ) from exc

    matrix = laplacian.tocsc()
    focals = np.asarray(focal_indices, dtype=np.int64)
    if (
        focals.ndim != 1
        or len(focals) < 2
        or len(np.unique(focals)) != len(focals)
    ):
        raise ValueError(
            "focal indices must be a unique one-dimensional vector"
        )
    n_nodes = matrix.shape[0]
    if (
        matrix.shape != (n_nodes, n_nodes)
        or np.any(focals < 0)
        or np.any(focals >= n_nodes)
    ):
        raise ValueError("focal indices outside Laplacian")

    ground = int(focals[0])
    keep = np.ones(n_nodes, dtype=bool)
    keep[ground] = False
    reduced = matrix[keep][:, keep].tocsc()
    reduced_index = np.cumsum(keep, dtype=np.int64) - 1
    focal_reduced = reduced_index[focals[1:]]
    try:
        factor = splu(
            reduced,
            permc_spec="COLAMD",
            diag_pivot_thresh=0.0,
            options={"SymmetricMode": True},
        )
    except RuntimeError as exc:
        raise ValueError(
            "grid Laplacian is singular; focal landscape is disconnected"
        ) from exc

    right_hand_side = np.zeros(
        (n_nodes - 1, len(focal_reduced)), dtype=float
    )
    right_hand_side[
        focal_reduced, np.arange(len(focal_reduced))
    ] = 1.0
    solution = factor.solve(right_hand_side)
    grounded_inverse = np.zeros(
        (len(focals), len(focals)), dtype=float
    )
    grounded_inverse[1:, 1:] = solution[focal_reduced, :]
    diagonal = np.diag(grounded_inverse)
    resistance = (
        diagonal[:, None]
        + diagonal[None, :]
        - 2.0 * grounded_inverse
    )
    resistance = (resistance + resistance.T) / 2.0
    tiny_negative = (resistance < 0.0) & (resistance > -1e-9)
    resistance[tiny_negative] = 0.0
    np.fill_diagonal(resistance, 0.0)
    if not np.isfinite(resistance).all() or np.any(resistance < 0.0):
        raise RuntimeError(
            "effective resistance matrix contains invalid values"
        )
    return resistance


def install_deterministic_solver(engine_module: Any) -> None:
    """Install the fixed solver into the candidate engine used by a shard."""
    engine_module.effective_resistance_matrix = (
        deterministic_effective_resistance_matrix
    )
