import json
from pathlib import Path


def _contract():
    return json.loads(Path('validation/layer_b_mechanism_v2/fresh_real_candidate_qualification_v2.json').read_text())


def test_gate_requires_independent_response_semantics_and_target_inclusion():
    p = _contract()['required_before_response_payload_access']
    assert p['response_semantics']['exact_header_from_independent_README_data_dictionary_or_publication'] is True
    assert p['response_semantics']['response_algebra_fully_defined_from_independent_documentation'] is True
    assert p['response_semantics']['no_post_response_alias_discovery'] is True
    assert p['target']['independent_evidence_target_occurs_in_the_dataset'] is True
    assert p['target']['target_change_after_response'] is False


def test_gate_requires_noncollapsed_geometry_and_no_outer_feedback():
    p = _contract()['required_before_response_payload_access']
    assert p['geometry_and_effort']['minimum_unique_spatial_nodes'] == 50
    assert p['geometry_and_effort']['station_or_node_level_coordinates_required'] is True
    assert p['validation_design']['outer_heldout_feedback_for_selection'] is False


def test_gate_cannot_be_lowered_to_force_a_score():
    b = _contract()['scientific_boundary']
    assert b['closed_eog_wf_unchanged'] is True
    assert b['qualification_failures_are_not_predictive_evidence'] is True
    assert b['do_not_lower_gate_to_obtain_a_scored_result'] is True
