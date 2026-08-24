from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "source_contract.json"
PREFLIGHT_PATH = HERE / "preflight_result.json"
HEADER_PATH = HERE / "header_preflight_result.json"
OUTPUT_PATH = HERE / "full_freeze_candidate.json"

LAYER_B_FEATURE_NAMES = (
    "surviving_world_fraction",
    "support_mean",
    "support_std",
    "support_min",
    "support_max",
    "support_q25",
    "support_q50",
    "support_q75",
    "positive_support_fraction",
    "support_range",
)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hard_suffix(world_id: str) -> str:
    if not world_id.startswith("geo_lcc"):
        raise ValueError(f"unexpected hard-world ID: {world_id!r}")
    return world_id.removeprefix("geo_")


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    header = json.loads(HEADER_PATH.read_text(encoding="utf-8"))
    if preflight.get("status") != "ready_for_next_response_blind_freeze":
        raise SystemExit("geometry/effort preflight is not green")
    if header.get("status") != "response_header_schema_ready_for_final_freeze":
        raise SystemExit("physical response-header preflight is not green")
    if preflight.get("response_rows_opened") is not False or header.get("response_rows_opened") is not False:
        raise SystemExit("row-level response was already opened")
    if preflight.get("response_bytes") != 0 or header.get("response_payload_bytes_opened") != 0:
        raise SystemExit("row-level response bytes were opened before full freeze")

    hard_worlds = tuple(preflight["hard_worlds"])
    hard_ids = tuple(str(row["world_id"]) for row in hard_worlds)
    full_world_id = str(preflight["full_world_id"])
    world_ids = (*hard_ids, full_world_id)
    suffixes = tuple(hard_suffix(world_id) for world_id in hard_ids)

    baseline_feature_names = (
        "target_month_index",
        "target_month_index_squared",
        "target_month_sin",
        "target_month_cos",
        "longitude_centered_km",
        "latitude_centered_km",
        "target_mean_distance_km",
        "target_nearest_other_site_km",
        *(f"target_degree_{suffix}" for suffix in suffixes),
        "source_month_active_days",
        "target_month_active_days",
        "current_source_count",
        "log1p_current_source_detection_days",
        "nearest_current_source_distance_km",
        "target_never_previously_detected",
        "target_months_since_last_detection",
        "target_prior_detected_month_count",
        "log1p_target_cumulative_prior_detection_days",
        *(f"source_count_{suffix}" for suffix in suffixes),
        *(f"source_exponential_exposure_{suffix}" for suffix in suffixes),
        "source_exponential_exposure_full",
        *(f"detection_day_weighted_exposure_{suffix}" for suffix in suffixes),
        "detection_day_weighted_exposure_full",
    )

    expected_outer_units = int(preflight["expected_outer_score_units"])
    expected_wins = expected_outer_units // 2 + 1
    if expected_wins != int(preflight["favorable_min_augmented_wins"]):
        raise SystemExit("response-independent strict-majority threshold drift")
    if expected_outer_units < 4:
        raise SystemExit("fewer than four response-independent heldout score units")

    result = {
        "schema": "eog.peneda_roedeer_full_freeze_candidate.v1",
        "attempt_id": contract["candidate_id"],
        "source_identity": {
            "paper_doi": contract["study"]["paper_doi"],
            "sampling_event_doi": contract["study"]["sampling_event_doi"],
            "deployment_attachment_name": contract["response_firewall"]["deployment_attachment_name"],
            "deployment_bytes": preflight["deployment_bytes"],
            "deployment_sha256": preflight["deployment_sha256"],
            "response_attachment_name": contract["response_firewall"]["response_attachment_name"],
            "response_physical_header_text": header["physical_header_text"],
            "response_physical_header_fields": header["physical_header_fields"],
            "response_physical_header_sha256": header["response_header_sha256"],
            "response_physical_terminator_prefix": header["physical_terminator_prefix"],
        },
        "node_geometry": {
            "node_ids": preflight["node_ids"],
            "median_coordinates": preflight["median_coordinates"],
            "coordinate_rule": contract["geometry_semantics"]["coordinate_rule"],
            "distance": contract["geometry_semantics"]["distance"],
            "earth_radius_km": contract["geometry_semantics"]["earth_radius_km"],
            "geometry_effort_fingerprint": preflight["geometry_effort_fingerprint"],
        },
        "response_semantics": {
            "focal_scientific_name": contract["focal_taxon"]["scientific_name"],
            "endpoint": contract["temporal_semantics"]["endpoint"],
            "deployment_join": "every observation deploymentID must exist exactly in the pinned deployment attachment and maps to its frozen locationID; unknown deployment IDs are terminal schema/identity failure",
            "time_field": "timestamp; exact ISO-8601 parse; calendar date and month are derived from the timestamp without changing the supplied timezone offset",
            "normal_nonfocal_rows": "blank, unknown, unclassified, human and vehicle observation types and empty scientificName values are valid Camtrap DP rows and are not schema failures",
            "focal_detection": "observationType must equal animal and scientificName after surrounding-whitespace stripping must equal exactly Capreolus capreolus; no fuzzy taxonomy, synonym rescue or post-open token remapping",
            "detection_day_collapse": "collapse focal observations to unique locationID x calendar date before any endpoint counts; multiple sequences/images on one date contribute one detection day",
            "site_month_state": "1 if the location has >=20 frozen active calendar dates and >=1 focal detection day; 0 if >=20 active dates and no focal detection day; -1 otherwise",
            "event": "risk-set location is state 0 in source month, observed in target month, and state 1 in target month",
            "non_event": "risk-set location is state 0 in source month, observed in target month, and state 0 in target month",
            "source_state": "all adequately observed locations in state 1 in the source month",
            "claim_limit": "observed internal source-conditioned camera-contact reappearance support; not latent occupancy, individual movement, biological closure, ancestry or colonisation history",
        },
        "temporal_split": {
            "scored_transitions": preflight["scored_transitions"],
            "calibration_scored_transition_count": preflight["calibration_scored_transitions"],
            "heldout_scored_transition_count": preflight["heldout_scored_transitions"],
            "heldout_outer_ids": preflight["heldout_outer_ids"],
            "outer_score_unit": contract["temporal_semantics"]["final_score_outer_unit"],
            "fit_policy": "fit exactly once on pooled calibration risk rows only; never refit on heldout outcomes",
            "sequential_layer_a_policy": "each transition is represented and scored before that transition's outcomes may monotonically update Layer A for later transitions",
        },
        "count_gate": {
            "must_be_first_outcome_dependent_analytical_operation": True,
            **contract["exact_outcome_count_minima"],
            "heldout_outer_units_with_rows": expected_outer_units,
            "require_every_scored_transition_has_current_internal_source": True,
            "failure_action": "terminal non-estimable result with zero Layer-A updates, zero model fits and zero heldout scores",
        },
        "world_scale": {
            "raw_structural_ladder": preflight["structural_ladder"],
            "hard_worlds": list(hard_worlds),
            "full_world_id": full_world_id,
            "world_ids": list(world_ids),
            "kernel_scale_km": preflight["kernel_scale_km"],
            "kernel_scale_basis": "response-blind 50-percent LCC threshold; analytical decay scale, not fitted movement distance",
            "loss_support": 1.0,
            "support_tolerance": 1e-15,
            "duplicate_threshold_policy": contract["geometry_semantics"]["duplicate_threshold_policy"],
        },
        "layer_a_rules": {
            "declared_world_count": len(world_ids),
            "current_sources": "all adequately observed locations with >=1 focal detection day in the source month",
            "source_weights": "equal normalized weight across current internal source locations",
            "hard_world_support": "exp(-distance/kernel_scale) for distinct location pairs at or below each frozen response-blind LCC threshold, otherwise zero",
            "full_world_support": "exp(-distance/kernel_scale) for every distinct internal location pair",
            "transition_normalization": "Q[s,j]=W[s,j]/(1+sum_k W[s,k]); target support is the equal-current-source mean of Q[s,j]",
            "update": "after each observed transition, eliminate a surviving world if any newly detected risk-set target has support at or below 1e-15",
            "monotonicity": "worlds may only remain or be eliminated; eliminated worlds never return",
            "all_eliminated": "terminal frozen-universe falsification; no scale/source rescue",
            "world_labels_used_for_prediction": False,
        },
        "layer_b_representation": {
            "implementation": "eog.v2.world_predictive_summary.summarize_worldset_for_prediction",
            "representation_name": "symmetric_world_support_summary_v1",
            "feature_names": list(LAYER_B_FEATURE_NAMES),
            "world_label_invariant": True,
            "exact_world_id_exposed_to_learner": False,
            "unchanged_from_production_implementation": True,
        },
        "comparators": {
            "baseline_feature_names": list(baseline_feature_names),
            "baseline": "strong conventional calendar + geography + effort + source exposure + strictly lagged detection-history feature block",
            "augmented": "identical rows, labels, split, preprocessing, learner and baseline features plus the unchanged ten-column Layer-B block",
            "only_augmented_difference": list(LAYER_B_FEATURE_NAMES),
            "exact_site_id_supervised": False,
            "exact_world_id_supervised": False,
        },
        "preprocessing_model_fit": {
            **contract["paired_endpoint"]["frozen_environment"],
            "seed": contract["paired_endpoint"]["learner_hyperparameters"]["random_state"],
            "learner": contract["paired_endpoint"]["learner_family"],
            "hyperparameters": contract["paired_endpoint"]["learner_hyperparameters"],
            "missing_value_policy": "no predictor imputation; any nonfinite predictor or unresolved identity is terminal before fit",
        },
        "metrics_decision": {
            "primary_metric": contract["paired_endpoint"]["primary_score"],
            "probability_clip": contract["paired_endpoint"]["probability_clip"],
            "macro_unit": contract["temporal_semantics"]["final_score_outer_unit"],
            "expected_outer_unit_count": expected_outer_units,
            "lower_is_better": True,
            "favorable_min_augmented_wins": expected_wins,
            "adverse_min_baseline_wins": expected_wins,
            "tie_tolerance": contract["paired_endpoint"]["tie_tolerance"],
            "favorable": "favorable_complementary_added_value",
            "null": "no_confirmed_complementary_added_value",
            "adverse": "adverse_complementary_added_value",
        },
        "non_estimable_stop": {
            "exact_count_gate_first": True,
            "zero_layer_a_update_on_count_failure": True,
            "zero_fit_on_count_failure": True,
            "zero_score_on_count_failure": True,
            "no_post_open_redesign": True,
            "no_post_open_retry": True,
            "schema_or_identity_failure_after_open_is_terminal": True,
        },
        "audit": {
            "contract_sha256": file_sha256(CONTRACT_PATH),
            "preflight_result_sha256": file_sha256(PREFLIGHT_PATH),
            "header_preflight_result_sha256": file_sha256(HEADER_PATH),
            "response_full_payload_requests": 0,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": False,
            "response_values_opened": False,
            "layer_a_updates": 0,
            "model_fits": 0,
            "heldout_scores": 0,
        },
        "stage_boundary": {
            "stage": "response_blind_full_freeze_candidate",
            "outcome_access_authorized": False,
            "next_if_green": "bind a deterministic synthetic smoke and runner fingerprint, then create a marker-only once authorization commit",
        },
    }
    result["fingerprint"] = canonical_sha256(result)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "full_freeze_candidate_ready",
        "fingerprint": result["fingerprint"],
        "world_ids": list(world_ids),
        "baseline_feature_count": len(baseline_feature_names),
        "heldout_outer_ids": preflight["heldout_outer_ids"],
        "favorable_min_augmented_wins": expected_wins,
        "response_rows_opened": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
