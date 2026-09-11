from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "validation/layer_b_mechanism_v2/real_translation_programme_closure_v1.json"
NCRN = ROOT / "validation/layer_b_mechanism_v2/ncrn_final_terminal_result_v1.json"
KNOWN_TRUTH = ROOT / "validation/layer_b_mechanism_v2/selective_promotion_known_truth_result_v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_real_translation_programme_is_closed_without_real_predictive_score() -> None:
    closure = load(CLOSURE)
    assert closure["status"] == "closed_without_scored_fresh_real_predictive_endpoint"
    assert closure["closed_eog_wf_synthesis_changed"] is False
    assert closure["counts_as_fourth_eog_wf_endpoint"] is False
    assert closure["candidate_hunting_hard_stop"] is True

    estimand = closure["programme_estimand"]
    assert estimand["answered"] is False
    assert estimand["scored_fresh_real_endpoints"] == 0
    assert estimand["favorable"] == 0
    assert estimand["null_or_protective"] == 0
    assert estimand["adverse"] == 0

    attempts = closure["real_system_attempts"]
    assert [a["candidate"] for a in attempts] == [
        "india_tiger",
        "illinois_coyote",
        "ncrn_red_bellied_woodpecker_2007_2019",
    ]
    assert all(a["counts_as_predictive_evidence"] is False for a in attempts)
    assert all(a["counts_as_biological_negative"] is False for a in attempts)


def test_ncrn_terminal_is_schema_integrity_stop_before_fitting() -> None:
    ncrn = load(NCRN)
    assert ncrn["terminal"]["status"] == "terminal_schema_or_transport_stop_after_response"
    assert ncrn["terminal"]["first_reported_unmatched_point_code"] == "2550"
    assert ncrn["response_consumption"]["payload_requests"] == 1
    assert ncrn["response_consumption"]["second_request_allowed"] is False
    assert ncrn["downstream_execution"]["site_year_response_construction_completed"] is False
    assert ncrn["downstream_execution"]["model_fits"] == 0
    assert ncrn["downstream_execution"]["inner_selection_decisions"] == 0
    assert ncrn["downstream_execution"]["outer_scoring_runs"] == 0
    assert ncrn["downstream_execution"]["counts_as_predictive_evidence"] is False
    assert ncrn["scientific_interpretation"]["fresh_real_predictive_question_answered"] is False


def test_known_truth_support_survives_without_becoming_real_system_evidence() -> None:
    closure = load(CLOSURE)
    known_truth = load(KNOWN_TRUTH)
    assert known_truth["scientific_status"] == "known_truth_support_for_calibration_only_selective_promotion"
    assert known_truth["predeclared_checks_all_passed"] is True
    assert known_truth["counts_as_fresh_predictive_endpoint"] is False
    assert closure["known_truth_basis"]["scientific_status"] == known_truth["scientific_status"]

    policy = closure["terminal_policy"]
    assert policy["rerun_any_consumed_attempt_as_fresh_allowed"] is False
    assert policy["repair_ncrn_registry_after_response_allowed"] is False
    assert policy["discover_post_response_aliases_for_rescue_allowed"] is False
    assert policy["lower_qualification_v2_gates_allowed"] is False
    assert policy["hunt_replacement_candidate_inside_this_programme_allowed"] is False
    assert policy["future_real_test_requires_new_protocol_version"] is True
