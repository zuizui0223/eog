from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

from eog.tanzania_current_flow_candidates import array_sha256


ROOT = Path(__file__).resolve().parents[1]
AGGREGATOR = ROOT / "benchmarks" / "aggregate_tanzania_current_flow_candidates.py"
SPEC = importlib.util.spec_from_file_location("tanzania_current_flow_aggregate", AGGREGATOR)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_cross_runner_lu_noise_has_stable_library_fingerprint() -> None:
    baseline = np.asarray([1.2345672, 10.0000002, 4069.7396872], dtype=float)
    runner_variant = baseline + np.asarray([4.0e-10, -4.0e-10, 4.5e-10])

    assert MODULE.LIBRARY_FINGERPRINT_DECIMALS == 7
    assert MODULE._library_array_sha256(baseline) == MODULE._library_array_sha256(
        runner_variant
    )
    assert array_sha256(baseline, decimals=12) != array_sha256(
        runner_variant, decimals=12
    )


def test_meaningful_numerical_change_still_changes_fingerprint() -> None:
    baseline = np.asarray([1.2345672, 10.0000002, 4069.7396872], dtype=float)
    changed = baseline.copy()
    changed[0] += 2.0e-6

    assert MODULE._library_array_sha256(baseline) != MODULE._library_array_sha256(
        changed
    )


def test_scalar_policy_normalizes_signed_zero_only_for_manifest() -> None:
    assert MODULE._stable_float(-1.0e-12) == 0.0
    assert not np.signbit(MODULE._stable_float(-1.0e-12))
    assert MODULE._stable_float(1.2e-6) == 1.2e-6


def test_committed_expected_contract_declares_same_policy() -> None:
    expected = json.loads(
        (ROOT / "benchmarks" / "tanzania_current_flow_candidates_expected.json").read_text(
            encoding="utf-8"
        )
    )
    policy = expected["fingerprint_policy"]
    assert policy["raw_array_storage"] == "float64_unmodified"
    assert policy["run_local_shard_hash_decimals"] == MODULE.SHARD_HASH_DECIMALS
    assert (
        policy["cross_run_library_hash_decimals"]
        == MODULE.LIBRARY_FINGERPRINT_DECIMALS
    )
    assert policy["cross_run_absolute_resolution"] == 1e-7
