from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration
from eog.v2.world_predictive_summary import PREDICTIVE_FEATURE_NAMES

HERE = Path(__file__).resolve().parent
OUT = Path("build/louisiana_marsh_bird_replication_1/pre_response_finalize.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

REQUIRED_SECTIONS = (
    "source_identity",
    "response_identity",
    "node_geometry",
    "response_semantics",
    "temporal_split",
    "count_gate",
    "process_source",
    "world_scale",
    "structural_adequacy",
    "layer_a_rules",
    "layer_b_representation",
    "comparators",
    "preprocessing_model_fit",
    "metrics_decision",
    "runtime_runner",
    "non_estimable_stop",
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main() -> None:
    freeze = load_json("full_freeze_spec.json")
    gate0 = load_json("gate0_certificate.json")
    gate1 = load_json("gate1_certificate.json")
    gate2 = load_json("gate2_header_certificate.json")
    focal = load_json("focal_species_selection_certificate.json")

    expected_keys = {"schema", "attempt_id", *REQUIRED_SECTIONS}
    if set(freeze) != expected_keys:
        raise RuntimeError(
            f"full freeze key drift: missing={sorted(expected_keys-set(freeze))}, "
            f"unexpected={sorted(set(freeze)-expected_keys)}"
        )

    if freeze["attempt_id"] != "southwest_louisiana_king_rail_site_occasion_fresh_paired_v1":
        raise RuntimeError("attempt id drift")

    layer_b = freeze["layer_b_representation"]
    if tuple(layer_b["feature_names"]) != tuple(PREDICTIVE_FEATURE_NAMES):
        raise RuntimeError("Layer-B feature identity differs from package surface")
    if layer_b["representation_name"] != "symmetric_world_support_summary_v1":
        raise RuntimeError("Layer-B representation name drift")

    conventional = tuple(freeze["comparators"]["conventional_feature_names"])
    if len(conventional) != 34 or len(set(conventional)) != 34:
        raise RuntimeError(f"conventional feature contract must contain 34 unique names, got {len(conventional)}")
    if freeze["comparators"]["only_allowed_arm_difference"] != "Layer-B feature block":
        raise RuntimeError("paired arm-difference contract drift")

    thresholds = tuple(float(x) for x in freeze["world_scale"]["geometry_thresholds_km"])
    if len(thresholds) != 3 or len(set(thresholds)) != 3 or not all(x > 0 for x in thresholds):
        raise RuntimeError("geometry threshold contract must contain three distinct positive values")
    if int(freeze["world_scale"]["declared_world_count"]) != 7:
        raise RuntimeError("declared world universe must contain exactly seven worlds")

    if gate0["gate0_fingerprint"] != "5ce556acd5b119a7b451a3b8cca0fdb254ded2461014c1e2e8388abdaf6802cf":
        raise RuntimeError("Gate0 certificate fingerprint drift")
    if gate1["gate1_fingerprint"] != "4f3dd443ba06bbd0d2bd8a47ead538700522df4df58eb58d2afd8577e3428586":
        raise RuntimeError("Gate1 certificate fingerprint drift")
    if gate2["result_fingerprint"] != freeze["response_identity"]["header_certificate_fingerprint"]:
        raise RuntimeError("Gate2 header fingerprint drift")
    if gate2["selected_response"]["physical_header"] != freeze["response_identity"]["physical_header"]:
        raise RuntimeError("frozen physical header differs from authoritative header certificate")
    if gate2["response_firewall"]["selected_response_rows_opened"] is not False:
        raise RuntimeError("selected response rows already opened before finalization")
    if gate2["response_firewall"]["selected_response_values_opened"] is not False:
        raise RuntimeError("selected response values already opened before finalization")
    if focal["selected_species"]["selected_response_file"] != "KIRA.csv":
        raise RuntimeError("focal species response file drift")
    if focal["response_firewall_at_selection"]["biological_response_rows_opened"] is not False:
        raise RuntimeError("species rows were opened before focal selection")

    runtime = freeze["preprocessing_model_fit"]["runtime"]
    required_runtime = {
        "python": "3.12",
        "numpy": "2.3.5",
        "scikit_learn": "1.8.0",
        "scipy": "1.18.1",
        "joblib": "1.5.3",
        "threadpoolctl": "3.6.0",
    }
    if runtime != required_runtime:
        raise RuntimeError(f"runtime contract drift: {runtime}")

    section_fingerprints = {name: canonical_sha256(freeze[name]) for name in REQUIRED_SECTIONS}
    learner_fit_fingerprint = canonical_sha256({
        "learner": freeze["preprocessing_model_fit"]["learner"],
        "hyperparameters": freeze["preprocessing_model_fit"]["hyperparameters"],
        "fit_policy": freeze["preprocessing_model_fit"]["fit_policy"],
        "runtime": runtime,
    })
    external_feature_fingerprint = canonical_sha256({
        "feature_names": list(conventional),
        "definitions": freeze["preprocessing_model_fit"],
    })
    eog_feature_fingerprint = canonical_sha256({
        "representation_name": layer_b["representation_name"],
        "feature_names": layer_b["feature_names"],
        "support_value": layer_b["support_value"],
    })

    metrics = freeze["metrics_decision"]
    declaration = PredictiveComplementarityDeclaration(
        metric_name=metrics["primary_metric"],
        lower_is_better=bool(metrics["lower_is_better"]),
        expected_outer_unit_count=int(metrics["primary_outer_unit_count"]),
        favorable_min_augmented_wins=int(metrics["favorable_min_augmented_wins"]),
        adverse_min_baseline_wins=int(metrics["adverse_min_baseline_wins"]),
        learner_fit_fingerprint=learner_fit_fingerprint,
        response_endpoint_fingerprint=section_fingerprints["response_semantics"],
        split_fingerprint=section_fingerprints["temporal_split"],
        external_feature_fingerprint=external_feature_fingerprint,
        eog_feature_fingerprint=eog_feature_fingerprint,
    )

    payload = {
        "schema": "eog.louisiana_marsh_bird_pre_response_finalize.v1",
        "attempt_id": freeze["attempt_id"],
        "status": "full_freeze_machine_validated_response_rows_still_closed",
        "full_freeze_spec_sha256": canonical_sha256(freeze),
        "section_fingerprints": section_fingerprints,
        "learner_fit_fingerprint": learner_fit_fingerprint,
        "external_feature_fingerprint": external_feature_fingerprint,
        "eog_feature_fingerprint": eog_feature_fingerprint,
        "predictive_complementarity_declaration_fingerprint": declaration.fingerprint,
        "response_endpoint_fingerprint": section_fingerprints["response_semantics"],
        "split_fingerprint": section_fingerprints["temporal_split"],
        "header_certificate_fingerprint": gate2["result_fingerprint"],
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "authorization_state": "not_authorized_until_separate_once_only_marker",
    }
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
