from eog.v2.known_truth_biogeography_fast import (
    FROZEN_REFERENCE_FINGERPRINT,
    run_witness_factorial_benchmark_fast,
)


def test_fast_bitset_replay_matches_frozen_scientific_fingerprint():
    result = run_witness_factorial_benchmark_fast()

    assert result["reference_fingerprint_match"] is True
    assert result["fingerprint"] == FROZEN_REFERENCE_FINGERPRINT
