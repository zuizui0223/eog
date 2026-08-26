from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
    prospective_estimability_disposition,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "gate4_prospective_estimability_contract.json"
DEFAULT_OUTPUT = (
    ROOT
    / "build"
    / "bbs_northern_bobwhite_replication_2"
    / "gate4_prospective_estimability.json"
)
COUNT_KEYS = (
    "calibration_events",
    "calibration_non_events",
    "heldout_events",
    "heldout_non_events",
    "heldout_outer_units_with_both_classes",
)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if tuple(contract["declaration"]) != COUNT_KEYS:
        raise RuntimeError("estimability declaration keys or order drifted")

    evidence_spec = contract["evidence"]
    if tuple(evidence_spec["intervals"]) != COUNT_KEYS:
        raise RuntimeError("estimability evidence keys or order drifted")

    declaration = ProspectiveEstimabilityDeclaration(**contract["declaration"])
    evidence = AggregateEstimabilityEvidence(
        source_label=evidence_spec["source_label"],
        endpoint_definition_matches=evidence_spec["endpoint_definition_matches"],
        response_rows_opened=evidence_spec["response_rows_opened"],
        intervals={
            key: AggregateCountInterval(**evidence_spec["intervals"][key])
            for key in COUNT_KEYS
        },
        note=evidence_spec["note"],
    )
    estimability = evaluate_prospective_estimability(declaration, evidence)
    disposition = prospective_estimability_disposition(estimability)

    expected = contract["expected"]
    if estimability.status != expected["status"]:
        raise RuntimeError(
            f"unexpected estimability status: {estimability.status} != {expected['status']}"
        )
    if disposition != expected["disposition"]:
        raise RuntimeError(
            f"unexpected estimability disposition: {disposition} != {expected['disposition']}"
        )
    if list(estimability.unresolved_keys) != expected["unresolved_keys"]:
        raise RuntimeError("unresolved estimability key set drifted")
    if estimability.failing_keys:
        raise RuntimeError("uncertain candidate unexpectedly has a known failing bound")
    if expected["outcome_access_authorized"] is not False:
        raise RuntimeError("prospective estimability must not authorize outcome access")

    result: dict[str, object] = {
        "schema": "eog.bbs_northern_bobwhite_replication_2.gate4_prospective_estimability.v1",
        "attempt_id": contract["attempt_id"],
        "status": estimability.status,
        "disposition": disposition,
        "estimability": asdict(estimability),
        "context_only_not_endpoint_evidence": evidence_spec[
            "context_only_not_endpoint_evidence"
        ],
        "exact_count_gate_required": expected["exact_count_gate_required"],
        "outcome_access_authorized": False,
        "response_firewall": contract["response_firewall"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "decision": (
            "UNCERTAIN: continue response-blind response-identity, full-freeze and "
            "synthetic-smoke work only; the unchanged once-only runner must apply the "
            "exact count gate before any model fit or heldout score"
        ),
    }
    result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    print(json.dumps(run(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
