"""Execute the authoritative A-Islands benchmark with fold-level graph caching.

The statistical runner remains ``run_aislands_authoritative_benchmark.py``. This thin
wrapper replaces only its repeated graph-construction call with a prepared equivalent
whose connected-frequency and nearest-anchor-distance outputs are regression-tested
against the full implementation.
"""
from __future__ import annotations

import numpy as np

import run_aislands_authoritative_benchmark as runner
from eog.prepared_island_connectivity import (
    evaluate_prepared_connectivity,
    prepare_island_connectivity,
)


_CACHE: dict[bytes, object] = {}


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


runner.evaluate_island_reachability = _cached_evaluate


if __name__ == "__main__":
    runner.main()
