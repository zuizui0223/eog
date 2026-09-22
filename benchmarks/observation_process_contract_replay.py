"""Response-free replay of frozen EOG-WF observation semantics.

This benchmark reads only frozen contracts already stored in the repository. It does
not open any biological response table. Its purpose is to show that heterogeneous
monitoring modalities can share a small observation-process interface without erasing
their endpoint-specific semantics.
"""

from __future__ import annotations

import json
from pathlib import Path

from eog.v2.observation_process import BinaryObservationContract


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def run_replay() -> dict[str, object]:
    azores = _load(
        "validation/azores_yellow_eel_paired_complementarity/full_freeze_spec.json"
    )["response_semantics"]
    louisiana = _load(
        "validation/louisiana_marsh_bird_replication_1/full_freeze_spec.json"
    )["response_semantics"]
    tampa = _load(
        "validation/tampa_seagrass_endpoint3/source_contract.json"
    )["observation_semantics"]

    contracts = {
        "azores_yellow_eel_telemetry": BinaryObservationContract(
            mode="complete_source_zero",
            endpoint_name=str(azores["endpoint"]),
            positive_semantics=str(azores["positive_label"]),
            negative_semantics=str(azores["negative_label"]),
            unavailable_semantics=(
                "rows outside the frozen target cohort/study receiver rules are not "
                "eligible scored units"
            ),
            zero_interpretation=str(azores["negative_label"]),
        ),
        "louisiana_king_rail_acoustics": BinaryObservationContract(
            mode="explicit_binary_tokens",
            endpoint_name=str(louisiana["endpoint"]),
            positive_semantics=str(louisiana["positive_label"]),
            negative_semantics=str(louisiana["negative_label"]),
            unavailable_semantics=(
                "case-sensitive unavailable tokens are excluded from the unit risk set"
            ),
            zero_interpretation=str(louisiana["negative_label"]),
        ),
        "tampa_seagrass_transects": BinaryObservationContract(
            mode="complete_source_zero",
            endpoint_name="eligible parent Transect visit x focal detection",
            positive_semantics=str(tampa["positive_rule"]),
            negative_semantics=str(tampa["negative_rule"]),
            unavailable_semantics=str(tampa["unsurveyed_rule"]),
            zero_interpretation=str(tampa["zero_interpretation"]),
        ),
    }

    expected = {
        "azores_yellow_eel_telemetry": "complete_source_zero",
        "louisiana_king_rail_acoustics": "explicit_binary_tokens",
        "tampa_seagrass_transects": "complete_source_zero",
    }
    observed = {name: contract.mode for name, contract in contracts.items()}
    if observed != expected:
        raise AssertionError((observed, expected))

    return {
        "schema": "eog.observation_process_contract_replay.v1",
        "uses_biological_response": False,
        "counts_as_predictive_evidence": False,
        "systems": {
            name: {
                "mode": contract.mode,
                "endpoint_name": contract.endpoint_name,
                "contract_fingerprint": contract.fingerprint,
            }
            for name, contract in contracts.items()
        },
        "mode_count": len(set(observed.values())),
        "modality_count": len(contracts),
        "interpretation": (
            "Telemetry and transect event aggregation share complete-source-zero "
            "semantics once effort eligibility is frozen, whereas the acoustic matrix "
            "uses explicit binary tokens. Missing rows are not a universal zero rule."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
