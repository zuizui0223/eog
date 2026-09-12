from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eog.v2.outcome_access import (
    REQUIRED_FREEZE_KEYS,
    FrozenOutcomeAccessContract,
    evaluate_outcome_access_gate,
)
from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration
from eog.v2.prospective_estimability import (
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)
from eog.v2.world_predictive_summary import PREDICTIVE_FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "validation/azores_yellow_eel_paired_complementarity"
OUT_DIR = ROOT / "build/azores_yellow_eel_pre_response"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "pre_response_finalize.json"


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


def fail(reason: str) -> None:
    payload = {
        "status": "stop_pre_response_finalize",
        "reason": reason,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(3)


def main() -> None:
    spec = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))
    stage1 = json.loads((HERE / "stage1_certificate.json").read_text(encoding="utf-8"))
    header = json.loads((HERE / "header_certificate.json").read_text(encoding="utf-8"))

    attempt_id = str(spec["attempt_id"])
    if stage1.get("attempt_id") != attempt_id or header.get("attempt_id") != attempt_id:
        fail("pre-response certificates refer to different attempts")
    if stage1.get("status") != "stage1_registry_availability_and_structural_pass":
        fail("Stage 1 certificate is not green")
    if header.get("status") != "response_header_schema_pass":
        fail("response header certificate is not green")
    if header.get("authoritative_ci", {}).get("run_id") != 32798983182:
        fail("unexpected response-header certificate run identity")
    if header.get("response_rows_opened") is not False or header.get("response_values_opened") is not False:
        fail("row-level response was already opened")
    if header.get("response_payload_bytes_opened") != 0:
        fail("response payload bytes were already opened")

    section_names = tuple(key for key in spec if key not in {"schema", "attempt_id"})
    if set(section_names) != set(REQUIRED_FREEZE_KEYS) or len(section_names) != len(REQUIRED_FREEZE_KEYS):
        fail(
            "full freeze does not contain exactly the 16 required outcome-access sections: "
            + repr(sorted(section_names))
        )

    layer_b_names = tuple(spec["layer_b_representation"]["feature_names"])
    if layer_b_names != PREDICTIVE_FEATURE_NAMES:
        fail("Layer-B feature names differ from the unchanged package representation")
    if spec["world_scale"]["declared_world_count"] != 6:
        fail("declared world universe must contain exactly 3 geometry x 2 source worlds")
    if spec["metrics_decision"]["primary_outer_unit_count"] != 5:
        fail("primary paired endpoint must contain exactly five frozen blocks")
    if spec["metrics_decision"]["favorable_min_augmented_wins"] != 3:
        fail("favorable win threshold drifted from strict majority 3/5")
    if spec["metrics_decision"]["adverse_min_baseline_wins"] != 3:
        fail("adverse win threshold drifted from strict majority 3/5")

    section_fingerprints = {
        key: canonical_sha256(spec[key])
        for key in REQUIRED_FREEZE_KEYS
    }

    count_gate = spec["count_gate"]
    estimability_declaration = ProspectiveEstimabilityDeclaration(
        calibration_events=int(count_gate["calibration_events_min"]),
        calibration_non_events=int(count_gate["calibration_non_events_min"]),
        heldout_events=int(count_gate["heldout_events_min"]),
        heldout_non_events=int(count_gate["heldout_non_events_min"]),
        heldout_outer_units_with_both_classes=int(count_gate["primary_outer_units_with_both_classes_min"]),
    )
    estimability_evidence = AggregateEstimabilityEvidence(
        source_label="Azores paper/public repository before receiver-week row access",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={},
        note=(
            "No published aggregate evidence exactly supplies the frozen receiver-week "
            "calibration/heldout event, non-event, and both-class block counts."
        ),
    )
    estimability = evaluate_prospective_estimability(
        estimability_declaration,
        estimability_evidence,
    )
    if estimability.status != "uncertain_pre_response":
        fail("prospective estimability must remain uncertain before exact row-level count gate")

    access_contract = FrozenOutcomeAccessContract(
        attempt_id=attempt_id,
        freeze_fingerprints=section_fingerprints,
        response_rows_opened=False,
        exact_count_gate_first=True,
        zero_fit_on_count_failure=True,
        no_post_open_redesign=True,
        note="Azores yellow-eel receiver-week fresh paired endpoint; all 16 freezes complete.",
    )
    access_gate = evaluate_outcome_access_gate(access_contract, estimability)
    if access_gate.status != "authorized_once_only_exact_count_gate_required" or not access_gate.authorized:
        fail("machine-checkable once-only outcome-access gate did not authorize")

    metric = spec["metrics_decision"]
    complementarity = PredictiveComplementarityDeclaration(
        metric_name=str(metric["primary_metric"]),
        lower_is_better=bool(metric["lower_is_better"]),
        expected_outer_unit_count=int(metric["primary_outer_unit_count"]),
        favorable_min_augmented_wins=int(metric["favorable_min_augmented_wins"]),
        adverse_min_baseline_wins=int(metric["adverse_min_baseline_wins"]),
        learner_fit_fingerprint=section_fingerprints["preprocessing_model_fit"],
        response_endpoint_fingerprint=section_fingerprints["response_semantics"],
        split_fingerprint=section_fingerprints["temporal_split"],
        external_feature_fingerprint=canonical_sha256(spec["comparators"]["conventional_feature_names"]),
        eog_feature_fingerprint=section_fingerprints["layer_b_representation"],
    )

    payload = {
        "schema": "eog.azores_yellow_eel_pre_response_finalize.v1",
        "attempt_id": attempt_id,
        "status": "authorized_once_only_exact_count_gate_required",
        "full_freeze_spec_sha256": canonical_sha256(spec),
        "stage1_certificate_sha256": canonical_sha256(stage1),
        "header_certificate_sha256": canonical_sha256(header),
        "required_freeze_keys": list(REQUIRED_FREEZE_KEYS),
        "section_fingerprints": section_fingerprints,
        "prospective_estimability_status": estimability.status,
        "prospective_estimability_fingerprint": estimability.fingerprint,
        "outcome_access_contract_fingerprint": access_contract.fingerprint,
        "outcome_access_gate_fingerprint": access_gate.fingerprint,
        "predictive_complementarity_declaration_fingerprint": complementarity.fingerprint,
        "runtime": spec["preprocessing_model_fit"]["runtime"],
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
