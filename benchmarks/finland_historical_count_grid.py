"""Robustly decode released SW Finland historical island counts without outcome access."""
from __future__ import annotations

import math
import numpy as np


def decode_integer_historical_counts(
    candidate_counts: np.ndarray,
    released_scaled: np.ndarray,
    *,
    max_count: int,
    exact_line_tolerance: float = 1e-10,
) -> tuple[np.ndarray, dict[str, object]]:
    """Recover the shared affine ``ln(count+1)`` integer grid.

    The potential-target complement is known to be nearly, but not perfectly, equal to
    the released historical count.  We therefore do not fit all complement counts by OLS.
    Instead every pair of distinct complement-count levels proposes the hypothesis that
    those two species are exact complements.  The line with the largest exact support
    across all species is selected deterministically, then every released value is decoded
    to its nearest integer historical count.  The final decoded grid must reproduce every
    released value to machine-level tolerance.
    """
    candidate = np.asarray(candidate_counts, dtype=float)
    released = np.asarray(released_scaled, dtype=float)
    if candidate.shape != released.shape or candidate.ndim != 1 or len(candidate) < 3:
        raise ValueError("historical count decoding requires aligned vectors")
    if not np.isfinite(candidate).all() or not np.isfinite(released).all():
        raise ValueError("historical count decoding requires finite values")
    if np.any(candidate < 0) or np.any(candidate > max_count):
        raise ValueError("candidate count outside island universe")

    log_candidate = np.log1p(candidate)
    best: tuple[int, float, float, float] | None = None
    n = len(candidate)
    for i in range(n):
        for j in range(i + 1, n):
            dx = float(log_candidate[j] - log_candidate[i])
            if abs(dx) <= 1e-15:
                continue
            slope = float((released[j] - released[i]) / dx)
            if not math.isfinite(slope) or slope <= 0.0:
                continue
            intercept = float(released[i] - slope * log_candidate[i])
            residual = np.abs(released - (intercept + slope * log_candidate))
            support = int(np.sum(residual <= exact_line_tolerance))
            support_sse = float(np.sum(np.square(residual[residual <= exact_line_tolerance])))
            candidate_key = (support, -support_sse, -abs(intercept), -abs(slope))
            if best is None:
                best = (support, support_sse, intercept, slope)
            else:
                best_key = (best[0], -best[1], -abs(best[2]), -abs(best[3]))
                if candidate_key > best_key:
                    best = (support, support_sse, intercept, slope)

    if best is None or best[0] < 3:
        raise RuntimeError("no response-free exact historical-count standardization line was identified")
    line_support, _, intercept, slope = best

    continuous = np.exp((released - intercept) / slope) - 1.0
    decoded = np.rint(continuous).astype(int)
    if np.any(decoded < 0) or np.any(decoded > max_count):
        raise RuntimeError("decoded historical count outside island universe")

    # Refit the common standardization line to the decoded integer grid, then require exact
    # reproduction. This rejects an accidental high-support line that does not explain all
    # released values as one integer-count transform.
    z = np.log1p(decoded.astype(float))
    design = np.column_stack([np.ones(len(z)), z])
    beta = np.linalg.lstsq(design, released, rcond=None)[0]
    intercept = float(beta[0])
    slope = float(beta[1])
    if not np.isfinite(beta).all() or slope <= 0.0:
        raise RuntimeError("invalid decoded historical-count standardization")
    continuous = np.exp((released - intercept) / slope) - 1.0
    decoded_final = np.rint(continuous).astype(int)
    integer_error = np.abs(continuous - decoded_final)
    residual = released - (intercept + slope * np.log1p(decoded_final.astype(float)))
    if (
        not np.array_equal(decoded_final, decoded)
        or float(np.max(integer_error)) > 1e-7
        or float(np.max(np.abs(residual))) > 1e-10
    ):
        raise RuntimeError("released Historical_total_log is not one exact affine log1p integer grid")

    return decoded_final, {
        "transform": "affine_lnp1_integer_grid_exact_consensus",
        "intercept": intercept,
        "slope": slope,
        "candidate_exact_line_support": line_support,
        "candidate_exact_line_support_fraction": float(line_support / len(candidate)),
        "max_integer_decode_error": float(np.max(integer_error)),
        "max_released_residual": float(np.max(np.abs(residual))),
    }
