from __future__ import annotations

import numpy as np

from benchmarks.finland_historical_count_grid import decode_integer_historical_counts
from benchmarks.finland_source_identity_identifiability import _individually_removable_sources


def test_integer_historical_grid_recovers_true_counts_despite_response_free_complement_overcounts():
    true = np.asarray([12, 19, 23, 44, 63, 117, 144, 179, 288], dtype=float)
    candidate = true + np.asarray([1, 0, 0, 0, 0, 3, 0, 2, 0], dtype=float)
    intercept = -3.0098005679308053
    slope = 0.7981217334649422
    released = intercept + slope * np.log1p(true)
    decoded, metadata = decode_integer_historical_counts(candidate, released, max_count=471)
    assert decoded.tolist() == true.astype(int).tolist()
    assert metadata["transform"] == "affine_lnp1_integer_grid_exact_consensus"
    assert metadata["candidate_exact_line_support"] == 6
    assert metadata["max_integer_decode_error"] < 1e-7
    assert metadata["max_released_residual"] < 1e-10


def test_individually_removable_source_is_one_never_needed_for_nearest_distance():
    coordinates = np.asarray(
        [
            [0.0, 0.0],
            [10.0, 0.0],
            [20.0, 0.0],
            [4.0, 0.0],
            [16.0, 0.0],
        ]
    )
    removable = _individually_removable_sources(
        np.asarray([0, 1, 2]),
        np.asarray([3, 4]),
        coordinates,
    )
    assert removable == (1,)


def test_tied_nearest_sources_are_conservatively_individually_removable():
    coordinates = np.asarray(
        [
            [0.0, 0.0],
            [10.0, 0.0],
            [20.0, 0.0],
            [15.0, 0.0],
        ]
    )
    removable = _individually_removable_sources(
        np.asarray([0, 1, 2]),
        np.asarray([3]),
        coordinates,
    )
    assert removable == (0, 1, 2)
