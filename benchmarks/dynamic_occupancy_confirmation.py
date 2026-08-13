"""Fresh-seed confirmation for the dynamic-occupancy reference boundary.

The seeds, gates and source blobs are frozen before these confirmation outcomes are
inspected. A failed confirmation is retained and must not be rescued by changing the
process truth, thresholds, folds, EOG construction or confirmation seeds.
"""
from __future__ import annotations

import hashlib
import json

import dynamic_occupancy_reference_boundary as benchmark

CONFIRMATION_SEEDS = (3301, 3407, 3511, 3607, 3701, 3803, 3907, 4001)

CONTRACT = {
    "status": "frozen-before-dynamic-occupancy-confirmation-outcomes",
    "confirmation_seeds": list(CONFIRMATION_SEEDS),
    "benchmark_blob": "9f50a279cebacc58d7368bc47362739f1fe0bd59",
    "dynamic_core_blob": "d3d57a8bef431c34f5d2c13e5e061ade40bcb64f",
    "primary_metric": "whole-motif-held-out mean log loss",
    "gates": {
        "process_gain_over_state_environment_min": 0.03,
        "process_gain_over_static_eog_min": 0.02,
        "eog_increment_over_process_min": -0.005,
        "process_favourable_seed_count_min": 6,
    },
    "failure_policy": (
        "retain failed confirmation; do not change seeds, gates, process truth, "
        "folds or EOG construction to rescue it"
    ),
    "interpretation": (
        "correctly specified repeated-incidence process reference should retain "
        "primacy when it generated the truth"
    ),
}
CONTRACT_FINGERPRINT = "ee967ddb36e670eb8946cce9e1c96ac51cd78b392a393cc6036958a010b31848"


def _contract_fingerprint() -> str:
    encoded = json.dumps(
        CONTRACT,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    if _contract_fingerprint() != CONTRACT_FINGERPRINT:
        raise RuntimeError("dynamic-occupancy confirmation contract fingerprint drifted")

    benchmark.SEEDS = CONFIRMATION_SEEDS
    result = benchmark.evaluate()
    if result["seeds"] != list(CONFIRMATION_SEEDS):
        raise RuntimeError("confirmation seed substitution failed")

    output = {
        "status": "frozen-dynamic-occupancy-confirmation",
        "contract": CONTRACT,
        "contract_fingerprint": CONTRACT_FINGERPRINT,
        "decision": result["decision"],
        "mean_models": result["mean_models"],
        "rows": result["rows"],
        "operator_fingerprint": result["operator_fingerprint"],
        "scientific_boundary": result["scientific_boundary"],
    }
    print(json.dumps(output, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
