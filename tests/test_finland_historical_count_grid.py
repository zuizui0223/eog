from __future__ import annotations

import numpy as np

from benchmarks.finland_historical_count_grid import decode_integer_historical_counts


def test_exact_consensus_decoder_recovers_counts_with_sparse_complement_overcounts():
    true = np.asarray([12, 19, 23, 44, 63, 117, 144, 179, 288], dtype=float)
    candidate = true + np.asarray([1, 0, 0, 0, 0, 3, 0, 2, 0], dtype=float)
    intercept = -3.0098005679308053
    slope = 0.7981217334649422
    released = intercept + slope * np.log1p(true)
    decoded, metadata = decode_integer_historical_counts(candidate, released, max_count=471)
    assert decoded.tolist() == true.astype(int).tolist()
    assert metadata["candidate_exact_line_support"] == 6
    assert metadata["max_integer_decode_error"] < 1e-7
    assert metadata["max_released_residual"] < 1e-10


def test_consensus_decoder_does_not_require_all_candidate_counts_to_be_correct():
    true = np.asarray([5, 10, 20, 40, 80, 160, 300], dtype=float)
    candidate = true + np.asarray([0, 1, 0, 2, 0, 3, 0], dtype=float)
    intercept = -2.7
    slope = 0.9
    released = intercept + slope * np.log1p(true)
    decoded, metadata = decode_integer_historical_counts(candidate, released, max_count=471)
    assert decoded.tolist() == true.astype(int).tolist()
    assert metadata["candidate_exact_line_support"] == 4
