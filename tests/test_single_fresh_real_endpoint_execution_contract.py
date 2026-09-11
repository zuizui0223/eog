import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'validation/layer_b_mechanism_v2/single_fresh_real_endpoint_execution_contract_v1.json'
INDIA_STATUS = ROOT / 'validation/layer_b_mechanism_v2/india_tiger_qualification_v2_status_v1.json'
ILLINOIS_SELECTION = ROOT / 'validation/layer_b_mechanism_v2/illinois_coyote_stage0_selection_v1.json'
QUALIFICATION = ROOT / 'validation/layer_b_mechanism_v2/fresh_real_candidate_qualification_v2.json'


def _load(path):
    return json.loads(path.read_text())


def test_single_active_system_and_one_outer_endpoint_only():
    p = _load(CONTRACT)
    budget = p['execution_budget']
    assert budget['maximum_active_real_systems'] == 1
    assert budget['maximum_scored_outer_endpoints'] == 1
    assert budget['parallel_candidate_attempts_allowed'] is False
    assert budget['candidate_hunting_to_improve_result_allowed'] is False
    assert budget['gate_weakening_to_obtain_score_allowed'] is False
    assert p['active_candidate_lock']['candidate'] == 'illinois_coyote_2021_2024'
    assert p['active_candidate_lock']['response_open_authorized'] is False


def test_all_qualification_v2_domains_are_required_before_response():
    p = _load(CONTRACT)['qualification_before_response']
    q = _load(QUALIFICATION)['required_before_response_payload_access']
    assert p['all_required_v2_checks_must_pass'] is True
    assert p['source_identity_must_pass'] is True and 'source_identity' in q
    assert p['response_semantics_must_pass'] is True and 'response_semantics' in q
    assert p['target_estimability_must_pass'] is True and 'target' in q
    assert p['geometry_and_effort_must_pass'] is True and 'geometry_and_effort' in q
    assert p['validation_design_must_pass'] is True and 'validation_design' in q
    assert p['independent_both_class_support_required'] is True
    assert p['minimum_unique_spatial_nodes'] == q['geometry_and_effort']['minimum_unique_spatial_nodes'] == 50


def test_inner_selection_cannot_see_outer_and_outer_is_once_only():
    p = _load(CONTRACT)
    inner = p['inner_selection']
    outer = p['outer_endpoint']
    assert inner['inner_train_only_for_fitting_before_selection'] is True
    assert inner['inner_validation_only_for_arm_selection'] is True
    assert inner['outer_feedback_for_selection'] is False
    assert inner['selection_decision_revisited_after_outer'] is False
    assert outer['untouched_before_selection'] is True
    assert outer['score_after_selection_only'] is True
    assert outer['maximum_outer_scoring_runs'] == 1
    assert outer['terminal_after_scoring'] is True
    assert outer['post_outer_rescue_tuning_allowed'] is False


def test_india_tiger_is_terminal_and_never_consumed_response():
    p = _load(INDIA_STATUS)
    assert p['terminal_status'] == 'terminal_pre_response_transport_stop'
    assert p['candidate_attempt_closed'] is True
    assert p['response_consumed'] is False
    assert p['response_open_authorized'] is False
    assert p['qualification_v2_complete'] is False
    assert p['counts_as_predictive_evidence'] is False
    assert p['counts_as_biological_negative'] is False
    t = p['terminal_transport_evidence']
    assert t['response_payload_requests'] == 0
    assert t['response_bytes_opened'] == 0
    assert t['forbidden_response_queried'] is False
    assert t['forbidden_response_resolved'] is False
    assert t['forbidden_response_downloaded'] is False


def test_illinois_selection_is_response_blind_and_not_yet_authorized():
    p = _load(ILLINOIS_SELECTION)
    assert p['selected_before_response_payload_access'] is True
    assert p['parallel_candidate_attempts_allowed'] is False
    assert p['dataset']['response_file'] == 'Coyote_Detection_History.csv'
    firewall = p['response_firewall']
    assert firewall['response_file_payload_requests_allowed_stage0'] == 0
    assert firewall['response_file_header_bytes_allowed_stage0'] == 0
    assert firewall['response_values_allowed_stage0'] is False
    assert firewall['outer_scores_allowed_stage0'] == 0
    q = p['qualification_v2_status_at_selection']
    assert q['qualification_v2_complete'] is False
    assert q['response_open_authorized'] is False
    assert p['prospective_nested_partition']['untouched_outer'] == '2023/24'
    assert p['prospective_nested_partition']['outer_feedback_for_selection'] is False


def test_closed_eog_wf_boundary_is_not_reopened():
    p = _load(CONTRACT)
    scope = p['scientific_scope']
    claim = p['claim_boundary']
    assert scope['separate_from_closed_eog_wf'] is True
    assert scope['changes_closed_eog_wf_synthesis'] is False
    assert scope['counts_as_fourth_eog_wf_endpoint'] is False
    assert claim['one_real_system_can_change_closed_eog_wf_pattern'] is False
    assert claim['outer_result_must_be_reported_regardless_of_direction'] is True
    assert claim['qualification_or_transport_stop_is_not_a_biological_negative'] is True
