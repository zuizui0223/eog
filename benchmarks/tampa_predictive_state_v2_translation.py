"""Response-free Tampa translation into the EOG-WF v2 predictive-state gate.

This benchmark reads only frozen pre-response design contracts and the later
response-independent geometry-signature audit. It does not read the Tampa occurrence
response, does not use the observed adverse log-loss result, and does not refit a model.

Question:
    Would the v2 prediction-facing eligibility gate have stopped the historical Tampa
    Layer-B design before predictive outcome access, based only on its declared feature
    generation semantics?
"""

from __future__ import annotations

import json
from pathlib import Path

from eog.v2.predictive_state_gate import (
    PredictiveStateDesign,
    evaluate_predictive_state_design,
)
from eog.v2.worldset_contraction_audit import audit_worldset_contraction


ROOT = Path(__file__).resolve().parents[1]
FINAL_CONTRACT = (
    ROOT / "validation" / "tampa_seagrass_endpoint3" / "final_endpoint_contract.json"
)
GEOMETRY_AUDIT = (
    ROOT
    / "validation"
    / "tampa_seagrass_endpoint3"
    / "geometry_signature_audit_v1.json"
)


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def run_replay() -> dict[str, object]:
    contract = _load(FINAL_CONTRACT)
    geometry = _load(GEOMETRY_AUDIT)

    if contract["attempt_id"] != "tampa_seagrass_endpoint3_v1":
        raise AssertionError("Tampa final contract identity drift")
    if geometry["response_reopened"] is not False or int(geometry["models_refit"]) != 0:
        raise AssertionError("geometry audit is no longer response-independent")

    candidate = contract["candidate_and_split"]
    layer_a = contract["layer_a"]
    baseline = contract["baseline"]
    worlds = contract["worlds"]

    node_count = int(candidate["node_count"])
    context_count = int(candidate["context_count"])
    candidate_count = int(candidate["candidate_unit_count"])
    if (node_count, context_count, candidate_count) != (71, 29, 1497):
        raise AssertionError("frozen Tampa candidate universe drift")

    numeric_names = {
        str(field["name"]) for field in baseline["numeric_fields"]
    }
    baseline_has_coordinates = {"longitude", "latitude"} <= numeric_names
    if not baseline_has_coordinates:
        raise AssertionError("frozen Tampa baseline no longer contains coordinates")

    layer_type = str(layer_a["type"])
    train_rule = str(layer_a["training_row_cross_fit"])
    serve_rule = str(layer_a["heldout_row_layer_b_features"])
    source_rule = str(layer_a["fixed_source_rule"])

    if "reused across repeated candidate visits" not in layer_type:
        raise AssertionError("frozen repeated static Layer-A contract drift")
    if "remove that row's entire stable node" not in train_rule:
        raise AssertionError("frozen training feature generator drift")
    if "one common node-level reconstruction per fold" not in serve_rule:
        raise AssertionError("frozen serving feature generator drift")
    if "lexicographically smallest nodeID" not in source_rule:
        raise AssertionError("frozen source-selection rule drift")

    design = PredictiveStateDesign(
        repeated_measure_endpoint=True,
        train_generator_id="leave_entire_stable_node_out_static_reconstruction",
        serve_generator_id="common_fold_static_reconstruction",
        refresh_policy="static_reused",
        source_policy="lexicographic_single_source",
        source_label_invariant=False,
        baseline_contains_spatial_coordinates=True,
    )
    eligibility = evaluate_predictive_state_design(design)

    if eligibility.status != "ineligible_generation_shift":
        raise AssertionError(eligibility.status)
    if eligibility.predictive_use_allowed:
        raise AssertionError("historical Tampa design must be prediction-ineligible in v2")

    required_reasons = {
        "train_and_serve_feature_generators_differ",
        "prediction_facing_source_policy_depends_on_arbitrary_source_labels",
        "repeated_endpoint_reuses_static_state_without_predictive_opt_in",
    }
    if not required_reasons <= set(eligibility.reasons):
        raise AssertionError((eligibility.reasons, required_reasons))
    if "static_state_may_duplicate_or_reencode_baseline_spatial_identity" not in eligibility.warnings:
        raise AssertionError("expected coordinate-redundancy warning missing")

    declared_world_count = int(geometry["frozen_world_family"]["declared_world_count"])
    surviving_world_count = int(
        geometry["frozen_world_family"]["surviving_world_count_in_every_consumed_fold"]
    )
    if declared_world_count != int(worlds["world_count"]) or declared_world_count != 5:
        raise AssertionError("Tampa world-count identity drift")
    if surviving_world_count != 5:
        raise AssertionError("Tampa geometry audit no longer reports full saturation")

    saturation = audit_worldset_contraction(
        declared_world_count,
        (surviving_world_count,) * 5,
    )
    if saturation.contraction_event_count != 0:
        raise AssertionError("Tampa fold-level world state unexpectedly contracts")
    if saturation.fully_saturated_context_fraction != 1.0:
        raise AssertionError("Tampa fold-level world state is no longer fully saturated")

    checks = tuple(geometry["reconstruction_checks"])
    if len(checks) != 2:
        raise AssertionError("expected two response-independent source reconstructions")
    for check in checks:
        if check["exact_fingerprint_match"] is not True:
            raise AssertionError("geometry reconstruction fingerprint mismatch")
        if int(check["unique_node_feature_vectors"]) != node_count:
            raise AssertionError("Layer-B node signature is no longer injective")
        if int(check["node_count"]) != node_count:
            raise AssertionError("geometry audit node-count drift")

    return {
        "schema": "eog.tampa_predictive_state_v2_translation.v1",
        "uses_biological_response": False,
        "uses_observed_tampa_predictive_score": False,
        "reruns_frozen_endpoint": False,
        "counts_as_predictive_evidence": False,
        "frozen_candidate_universe": {
            "node_count": node_count,
            "context_count": context_count,
            "candidate_unit_count": candidate_count,
            "baseline_contains_spatial_coordinates": baseline_has_coordinates,
        },
        "frozen_feature_generation": {
            "repeated_static_state": True,
            "train_generator_id": design.train_generator_id,
            "serve_generator_id": design.serve_generator_id,
            "source_policy": design.source_policy,
            "source_label_invariant": design.source_label_invariant,
        },
        "world_state": {
            "declared_world_count": declared_world_count,
            "surviving_world_count_every_fold": surviving_world_count,
            "contraction_event_count": saturation.contraction_event_count,
            "fully_saturated_context_fraction": (
                saturation.fully_saturated_context_fraction
            ),
            "fingerprint": saturation.fingerprint,
        },
        "geometry_signature": {
            "source_reconstruction_count": len(checks),
            "all_exact_fingerprint_match": all(
                bool(check["exact_fingerprint_match"]) for check in checks
            ),
            "unique_node_feature_vectors_each_source": [
                int(check["unique_node_feature_vectors"]) for check in checks
            ],
            "centered_feature_matrix_rank_each_source": [
                int(check["centered_feature_matrix_rank"]) for check in checks
            ],
        },
        "v2_predictive_state_gate": {
            "status": eligibility.status,
            "predictive_use_allowed": eligibility.predictive_use_allowed,
            "reasons": list(eligibility.reasons),
            "warnings": list(eligibility.warnings),
            "fingerprint": eligibility.fingerprint,
        },
        "interpretation": (
            "Before consulting the observed Tampa predictive score, the frozen design "
            "already violates three v2 prediction-facing contracts: train/serve feature "
            "generation differs, the sole source depends on lexicographic node labels, "
            "and one static node state is reused across repeated visits. The fully "
            "saturated world set then acts as an injective spatial signature rather "
            "than reporting world-set contraction. V2 would retain Layer A for "
            "structural work but withhold this Layer-B design from default supervised "
            "augmentation."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
