import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation" / "eogwf_v2_manifest_fresh_real_v1"
PROTOCOL = BASE / "protocol_v1.json"
LOCK = BASE / "protocol_lock_v1.json"
STATUS = BASE / "status_v1.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha1(path):
    raw = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def test_protocol_is_locked_before_any_candidate_roster_or_response_access():
    protocol = _load(PROTOCOL)
    lock = _load(LOCK)
    status = _load(STATUS)

    assert lock["protocol_git_blob_sha1"] == _git_blob_sha1(PROTOCOL)
    assert lock["lock_state"] == "frozen_before_candidate_roster_capture"
    assert lock["candidate_roster_captured"] is False
    assert lock["candidate_data_entity_payload_requests"] == 0
    assert lock["biological_response_payload_requests"] == 0
    assert lock["model_fits"] == 0
    assert lock["outer_scores"] == 0

    assert status["current_stage"] == "pre_roster_protocol_locked"
    assert status["roster_capture_status"] == "not_started"
    assert status["pre_response_candidate_attempts_used"] == 0
    assert status["active_candidate"] is None
    assert status["response_payload_opened"] is False
    assert status["response_payload_open_count"] == 0
    assert status["model_fits"] == 0
    assert status["outer_scoring_runs"] == 0
    assert status["counts_as_predictive_evidence"] is False

    assert protocol["current_status"] == "protocol_frozen_before_roster_capture"


def test_discovery_query_target_and_budget_cannot_expand_after_results():
    protocol = _load(PROTOCOL)
    discovery = protocol["target_and_discovery"]
    budget = protocol["execution_budget"]

    assert discovery["catalog"] == "Environmental Data Initiative (EDI) Data Portal"
    assert discovery["exact_search_string"] == "Peromyscus maniculatus"
    assert discovery["target_scientific_name"] == "Peromyscus maniculatus"
    assert discovery["target_change_after_roster_capture_allowed"] is False
    assert discovery["fallback_search_strings_allowed"] is False
    assert discovery["result_capture_limit"] == 50
    assert discovery[
        "roster_capture_must_precede_any_candidate_data_entity_payload_access"
    ] is True

    assert budget["maximum_pre_response_candidate_attempts"] == 3
    assert budget["maximum_active_candidate_at_once"] == 1
    assert budget["maximum_response_payload_openings"] == 1
    assert budget["maximum_scored_outer_endpoints"] == 1
    assert budget["parallel_candidate_attempts_allowed"] is False
    assert budget["replacement_after_any_response_payload_open"] is False
    assert budget["candidate_hunting_after_budget_exhaustion"] is False
    assert budget["gate_weakening_to_obtain_score"] is False


def test_new_programme_is_separate_from_all_closed_eogwf_denominators():
    protocol = _load(PROTOCOL)
    separation = protocol["scientific_separation"]
    claims = protocol["claim_boundary"]

    assert separation["separate_from_closed_eog_wf"] is True
    assert separation["changes_closed_eog_wf_synthesis"] is False
    assert separation["counts_as_fourth_eog_wf_endpoint"] is False
    assert separation["separate_from_closed_layer_b_mechanism_v2_programme"] is True
    assert separation["prior_consumed_or_stopped_candidates_may_be_reused"] is False
    assert claims["result_changes_closed_eog_wf"] is False
    assert claims["one_system_establishes_universal_benefit"] is False


def test_pre_response_geometry_and_prediction_contracts_are_fixed():
    protocol = _load(PROTOCOL)
    qualification = protocol["pre_response_qualification"]
    world = protocol["manifest_world_design"]
    prediction = protocol["predictive_state_design"]

    preflight = qualification["candidate_preflight"]
    assert preflight["minimum_unique_spatial_nodes"] == 50
    assert preflight["minimum_temporal_contexts"] == 17
    assert preflight["minimum_candidate_units"] == 500
    assert preflight["minimum_repeated_nodes"] == 50
    assert preflight["geometry_response_separable_required"] is True

    assert qualification["source_integrity"]["manifest_strict_content_identity_required"] is True
    assert qualification["response_semantics"]["no_post_response_alias_discovery"] is True

    assert world["generator_type"] == "coordinate_threshold_worlds_v1"
    assert world["metric"] == "haversine_km"
    assert world["construction_mode"] == "structural_lcc_ladder"
    assert world["target_lcc_fractions"] == [0.25, 0.5, 0.75, 0.9]
    assert world["biological_dispersal_distance_inferred_from_ladder"] is False

    assert prediction["refresh_policy"] == "sequential_context"
    assert prediction["train_generator_id"] == prediction["serve_generator_id"]
    assert prediction["source_label_invariant"] is True
    assert prediction["predictive_state_gate_must_return"] == "predictive_complement_candidate"


def test_inner_selection_and_outer_endpoint_have_no_outer_feedback():
    protocol = _load(PROTOCOL)
    selection = protocol["calibration_only_selection"]
    outer = protocol["outer_endpoint"]
    count_gate = protocol["post_response_estimability_gate"]

    assert selection["selection_data"] == "inner_validation only"
    assert selection["outer_feedback_for_selection"] is False
    assert selection["selection_revisited_after_outer"] is False

    assert outer["untouched_before_selection"] is True
    assert outer["maximum_outer_scoring_runs"] == 1
    assert outer["post_outer_rescue_tuning_allowed"] is False

    assert count_gate["must_be_first_outcome_dependent_operation"] is True
    assert count_gate["initialization_positive_minimum"] == 1
    assert count_gate["inner_train_positive_minimum"] == 30
    assert count_gate["inner_train_negative_minimum"] == 30
    assert count_gate["inner_validation_positive_minimum"] == 10
    assert count_gate["inner_validation_negative_minimum"] == 10
    assert count_gate["outer_positive_minimum"] == 10
    assert count_gate["outer_negative_minimum"] == 10
    assert count_gate["outer_contexts_with_both_classes_minimum"] == 4
