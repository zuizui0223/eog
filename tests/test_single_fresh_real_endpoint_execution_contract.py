import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'validation/layer_b_mechanism_v2/single_fresh_real_endpoint_execution_contract_v1.json'
INDIA_STATUS = ROOT / 'validation/layer_b_mechanism_v2/india_tiger_qualification_v2_status_v1.json'
ILLINOIS_STATUS = ROOT / 'validation/layer_b_mechanism_v2/illinois_coyote_qualification_v2_status_v1.json'
NCRN_SELECTION = ROOT / 'validation/layer_b_mechanism_v2/ncrn_redbellied_stage0_selection_v1.json'
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
    active = p['active_candidate_lock']
    assert active['candidate'] == 'ncrn_red_bellied_woodpecker_2007_2019'
    assert active['selection_contract'].endswith('ncrn_redbellied_stage0_selection_v1.json')
    assert active['response_open_authorized'] is False


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


def _assert_terminal_unconsumed_status(p):
    assert p['terminal_status'] == 'terminal_pre_response_transport_stop'
    assert p['candidate_attempt_closed'] is True
    assert p['response_consumed'] is False
    assert p['response_open_authorized'] is False
    assert p['qualification_v2_complete'] is False
    assert p['counts_as_predictive_evidence'] is False
    assert p['counts_as_biological_negative'] is False


def test_india_tiger_is_terminal_and_never_consumed_response():
    p = _load(INDIA_STATUS)
    _assert_terminal_unconsumed_status(p)
    t = p['terminal_transport_evidence']
    assert t['response_payload_requests'] == 0
    assert t['response_bytes_opened'] == 0
    assert t['forbidden_response_queried'] is False
    assert t['forbidden_response_resolved'] is False
    assert t['forbidden_response_downloaded'] is False


def test_illinois_coyote_is_terminal_and_never_consumed_response():
    p = _load(ILLINOIS_STATUS)
    _assert_terminal_unconsumed_status(p)
    t = p['terminal_transport_evidence']
    assert t['response_file'] == 'Coyote_Detection_History.csv'
    assert t['response_payload_requests'] == 0
    assert t['response_header_bytes_opened'] == 0
    assert t['response_bytes_opened'] == 0
    assert t['response_values_opened'] is False
    assert t['allowed_nonresponse_payloads_successfully_acquired'] == 0
    assert p['amendment_boundary']['further_retry_allowed'] is False


def test_ncrn_selection_is_response_blind_and_prequalified_for_both_classes():
    p = _load(NCRN_SELECTION)
    assert p['selected_before_response_payload_access'] is True
    assert p['parallel_candidate_attempts_allowed'] is False
    initial = p['source']['initial_forest_response_resource']
    assert initial['name'] == 'ncrn_birds_forest_counts.csv'
    assert initial['download_file_id'] == 757399
    assert initial['payload_opened'] is False
    f = p['response_firewall']
    assert f['counts_payload_requests_stage0'] == 0
    assert f['counts_header_bytes_stage0'] == 0
    assert f['counts_values_stage0'] is False
    assert f['flattened_R1_payload_requests_stage0'] == 0
    assert f['fielddata_payload_requests_stage0'] == 0
    cert = p['independent_estimability_certificate_basis']
    assert cert['sites_by_period'] == {'2007': 246, '2008-2013': 255, '2014-2019': 277}
    assert cert['conservative_yearly_positive_lower_bound'] == 123
    assert cert['conservative_yearly_negative_lower_bound_minimum'] == 41
    minima = p['prospective_nested_partition']['frozen_estimability_minima_per_partition']
    assert cert['conservative_yearly_positive_lower_bound'] >= minima['positive_site_years']
    assert cert['conservative_yearly_negative_lower_bound_minimum'] >= minima['negative_site_years']
    assert minima['unique_spatial_nodes'] == 50
    assert p['qualification_v2_status_at_selection']['qualification_v2_complete'] is False
    assert p['qualification_v2_status_at_selection']['response_open_authorized'] is False


def test_closed_candidate_ledgers_match_active_slot_contract():
    p = _load(CONTRACT)
    closed = {x['candidate']: x for x in p['prior_closed_candidates']}
    assert set(closed) == {'india_tiger', 'illinois_coyote_2021_2024'}
    assert all(x['terminal_status'] == 'terminal_pre_response_transport_stop' for x in closed.values())
    assert all(x['response_consumed'] is False for x in closed.values())
    assert all(x['may_be_reopened_or_retried'] is False for x in closed.values())


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
