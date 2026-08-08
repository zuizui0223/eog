"""Execute the authoritative A-Islands benchmark with fold-level graph caching.

The statistical runner remains ``run_aislands_authoritative_benchmark.py``. This thin
wrapper fixes two execution-only issues without changing the frozen analysis:

1. the frozen cohort CSV is an audit table containing all 1,060 distribution-eligible
   taxa plus ``primary_cohort_included``; only the 886 rows flagged ``1`` are primary;
2. fold-specific graph geometry is prepared once and reused across focal taxa.

Prepared/full graph equivalence for the primary fields is regression-tested.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

import run_aislands_authoritative_benchmark as runner
from eog.prepared_island_connectivity import (
    evaluate_prepared_connectivity,
    prepare_island_connectivity,
)


_CACHE: dict[bytes, object] = {}
_ORIGINAL_READ = runner._read


def _read_primary_cohort(path: Path):
    rows = _ORIGINAL_READ(path)
    if rows and "primary_cohort_included" in rows[0]:
        included = [row for row in rows if row["primary_cohort_included"].strip() == "1"]
        if len(included) != 886:
            raise ValueError(
                f"frozen cohort audit must contain exactly 886 primary rows, got {len(included)}"
            )
        return included
    return rows


def _cached_evaluate(
    node_ids,
    latitudes,
    longitudes,
    environmental_values,
    training_mask,
    anchor_mask,
    scenarios=None,
):
    training = np.asarray(training_mask, dtype=bool)
    # The authoritative runner uses the same nodes, coordinates and environmental
    # matrix for all taxa; only the five frozen training masks differ. The training
    # bytes therefore identify the fold-level geometry within one execution process.
    key = training.tobytes()
    prepared = _CACHE.get(key)
    if prepared is None:
        prepared = prepare_island_connectivity(
            node_ids,
            latitudes,
            longitudes,
            environmental_values,
            training,
            scenarios,
        )
        _CACHE[key] = prepared
    return evaluate_prepared_connectivity(prepared, anchor_mask)


runner._read = _read_primary_cohort
runner.evaluate_island_reachability = _cached_evaluate


if __name__ == "__main__":
    runner.main()
