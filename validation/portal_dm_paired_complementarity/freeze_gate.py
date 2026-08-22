#!/usr/bin/env python3
"""Bind Portal stage-one evidence, synthetic smoke and the 16-key outcome freeze."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

from eog.v2.outcome_access import (
    FrozenOutcomeAccessContract,
    REQUIRED_FREEZE_KEYS,
    evaluate_outcome_access_gate,
)
from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "source_contract.json"
RUNNER_PATH = ROOT / "benchmarks/run_portal_dm_paired_complementarity_once.py"


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


def path_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prospective_estimability(contract: dict):  # noqa: ANN201
    frozen = contract["freezes"]["count_gate"]
    declaration = ProspectiveEstimabilityDeclaration(
        calibration_events=int(frozen["calibration_events"]),
        calibration_non_events=int(frozen["calibration_non_events"]),
        heldout_events=int(frozen["heldout_events"]),
        heldout_non_events=int(frozen["heldout_non_events"]),
        heldout_outer_units_with_both_classes=int(
            frozen["heldout_outer_units_with_both_classes"]
        ),
    )
    evidence = AggregateEstimabilityEvidence(
        source_label=(
            "official Portal metadata and living-data paper provide no endpoint-matched "
            "split-specific counts for the frozen monthly zero-to-positive DM risk rows"
        ),
        endpoint_definition_matches=False,
        response_rows_opened=False,
        intervals={
            key: AggregateCountInterval()
            for key in (
                "calibration_events",
                "calibration_non_events",
                "heldout_events",
                "heldout_non_events",
                "heldout_outer_units_with_both_classes",
            )
        },
        note=(
            "unknown is retained as uncertain_pre_response; the unchanged exact count "
            "gate is the first outcome-dependent analytical operation"
        ),
    )
    result = evaluate_prospective_estimability(declaration, evidence)
    if result.status != "uncertain_pre_response":
        raise RuntimeError("Portal prospective estimability did not remain uncertain")
    return declaration, evidence, result


def audit_stage_one(stage_one: dict, contract: dict) -> dict[str, object]:
    if stage_one.get("status") != "response_blind_candidate_header_ready_for_full_freeze":
        raise RuntimeError("stage-one response-blind gate is not green")
    for key in (
        "response_payload_bytes_opened",
        "model_fits",
        "heldout_scores",
    ):
        if stage_one.get(key) != 0:
            raise RuntimeError(f"stage-one safety boundary failed: {key}")
    for key in ("response_rows_opened", "response_values_opened"):
        if stage_one.get(key) is not False:
            raise RuntimeError(f"stage-one opened response content: {key}")
    if stage_one.get("outcome_access_authorized") is not False:
        raise RuntimeError("stage-one prematurely authorized outcome access")

    header = stage_one["response_header_gate"]
    firewall = contract["response_header_firewall"]
    if header["selected_header_text"] != firewall["expected_header_text"]:
        raise RuntimeError("stage-one header text differs from the final freeze")
    if header["selected_exact_columns"] != firewall["expected_columns"]:
        raise RuntimeError("stage-one header columns differ from the final freeze")
    if header["transport"]["header_sha256"] != firewall["expected_header_sha256"]:
        raise RuntimeError("stage-one header SHA-256 differs from the final freeze")
    if header["transport"]["terminator"] != firewall["expected_terminator"]:
        raise RuntimeError("stage-one header terminator differs from the final freeze")
    if header["transport"]["bytes_consumed_including_terminator"] != int(
        firewall["expected_bytes_consumed_including_terminator"]
    ):
        raise RuntimeError("stage-one header length differs from the final freeze")

    freezes = contract["freezes"]
    geometry = stage_one["geometry_audit"]
    if geometry["center_fingerprint"] != freezes["node_geometry"]["center_fingerprint"]:
        raise RuntimeError("stage-one plot centers differ from the final freeze")
    if stage_one["structural_gates"]["thresholds_m"] != freezes["world_scale"][
        "thresholds_m"
    ]:
        raise RuntimeError("stage-one thresholds differ from the final freeze")
    if stage_one["structural_gates"]["adequacy_gate"]["fingerprint"] != freezes[
        "structural_adequacy"
    ]["stage_one_gate_fingerprint"]:
        raise RuntimeError("stage-one adequacy fingerprint differs from the final freeze")
    effort = stage_one["effort_time_audit"]
    split = freezes["temporal_split"]
    expected_counts = {
        "declared_transition_count": split["declared_scored_transition_count"],
        "calibration_transition_count": split["calibration_transition_count"],
        "calibration_potential_plot_rows": split["calibration_potential_plot_rows"],
        "heldout_transition_count": split["heldout_transition_count"],
        "heldout_potential_plot_rows": split["heldout_potential_plot_rows"],
    }
    if any(effort[key] != value for key, value in expected_counts.items()):
        raise RuntimeError("stage-one response-independent transition counts drifted")
    closure = effort["closure_result"]
    if closure["status"] != "temporal_source_closure_pass":
        raise RuntimeError("stage-one temporal source closure is not green")
    if closure["declaration_fingerprint"] != freezes["process_source"][
        "response_blind_closure_declaration_fingerprint"
    ]:
        raise RuntimeError("stage-one closure fingerprint differs from the final freeze")
    return {
        "stage_one_fingerprint": stage_one["fingerprint"],
        "header_gate_fingerprint": header["result"]["fingerprint"],
        "geometry_center_fingerprint": geometry["center_fingerprint"],
        "structural_adequacy_fingerprint": stage_one["structural_gates"][
            "adequacy_gate"
        ]["fingerprint"],
        "closure_declaration_fingerprint": closure["declaration_fingerprint"],
    }


def audit_smoke(smoke: dict, contract: dict) -> dict[str, object]:
    if smoke.get("status") != "smoke_pass":
        raise RuntimeError("synthetic full-path smoke is not green")
    if smoke.get("response_download_requests") != []:
        raise RuntimeError("synthetic smoke attempted a response download")
    if smoke.get("response_payload_bytes_opened") != 0:
        raise RuntimeError("synthetic smoke opened response payload bytes")
    if smoke.get("response_rows_opened") is not False:
        raise RuntimeError("synthetic smoke opened response rows")
    gate = smoke["exact_count_gate"]
    if gate.get("passed") is not True or gate.get("outcome_dependent_operation_index") != 1:
        raise RuntimeError("synthetic smoke did not pass exact-count-first execution")
    if gate.get("executed_before_any_layer_a_update_or_model_fit") is not True:
        raise RuntimeError("synthetic smoke count gate ordering drifted")
    if smoke.get("models_fit") != 2 or smoke.get("heldout_scores") != 16:
        raise RuntimeError("synthetic smoke paired fit/score count drifted")
    feature = smoke["model_feature_audit"]
    if feature.get("exact_world_id_supervised") is not False:
        raise RuntimeError("synthetic smoke exposed exact world ID")
    if feature.get("only_augmented_difference") != contract["freezes"][
        "layer_b_representation"
    ]["feature_names"]:
        raise RuntimeError("synthetic smoke augmented difference is not unchanged Layer B")
    expected = contract["freezes"]["runtime_runner"].get(
        "synthetic_smoke_core_fingerprint"
    )
    if not isinstance(expected, str) or not expected:
        raise RuntimeError("synthetic smoke core fingerprint is still pending")
    if smoke.get("smoke_core_fingerprint") != expected:
        raise RuntimeError("synthetic smoke core fingerprint differs from final freeze")
    return {
        "smoke_result_fingerprint": smoke["fingerprint"],
        "smoke_core_fingerprint": expected,
        "synthetic_fixture_fingerprint": smoke["response_provenance"][
            "synthetic_fixture_fingerprint"
        ],
        "paired_declaration_fingerprint": smoke["paired_declaration_fingerprint"],
    }


def run(stage_one_path: Path, smoke_path: Path, output: Path) -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    stage_one = json.loads(stage_one_path.read_text(encoding="utf-8"))
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    if contract["stage_boundary"]["complete_outcome_access_freeze_present"] is not True:
        raise RuntimeError("contract has not declared the complete outcome-access freeze")
    if contract["stage_boundary"]["outcome_access_authorized"] is not False:
        raise RuntimeError("marker-free contract must not claim an outcome execution")
    if set(contract["freezes"]) != set(REQUIRED_FREEZE_KEYS):
        raise RuntimeError("16-key freeze ledger surface drift")
    if path_sha256(RUNNER_PATH) != contract["freezes"]["runtime_runner"]["sha256"]:
        raise RuntimeError("frozen runner SHA-256 mismatch")
    stage_audit = audit_stage_one(stage_one, contract)
    smoke_audit = audit_smoke(smoke, contract)
    declaration, evidence, estimability = prospective_estimability(contract)
    freeze_fingerprints = {
        key: canonical_sha256(contract["freezes"][key]) for key in REQUIRED_FREEZE_KEYS
    }
    access_contract = FrozenOutcomeAccessContract(
        attempt_id=contract["attempt_id"],
        freeze_fingerprints=freeze_fingerprints,
        response_rows_opened=False,
        exact_count_gate_first=True,
        zero_fit_on_count_failure=True,
        no_post_open_redesign=True,
        note="fresh Portal DM paired complementarity; marker-gated one response opening only",
    )
    access = evaluate_outcome_access_gate(access_contract, estimability)
    if not access.authorized:
        raise RuntimeError(f"outcome access freeze was not authorized: {access.status}")
    result = {
        "status": access.status,
        "attempt_id": contract["attempt_id"],
        "contract_sha256": path_sha256(CONTRACT_PATH),
        "runner_sha256": path_sha256(RUNNER_PATH),
        "response_download_requests": [],
        "response_payload_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "stage_one_audit": stage_audit,
        "synthetic_smoke_audit": smoke_audit,
        "prospective_declaration": asdict(declaration),
        "prospective_evidence": asdict(evidence),
        "prospective_estimability": asdict(estimability),
        "freeze_fingerprints": freeze_fingerprints,
        "outcome_access_contract_fingerprint": access_contract.fingerprint,
        "outcome_access_gate": asdict(access),
    }
    result["fingerprint"] = canonical_sha256(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: freeze_gate.py STAGE_ONE_JSON SMOKE_JSON OUTPUT_JSON")
    try:
        result = run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"Portal DM full freeze gate stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "prospective_status": result["prospective_estimability"]["status"],
                "response_rows_opened": False,
                "models_fit": 0,
                "heldout_scores": 0,
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
