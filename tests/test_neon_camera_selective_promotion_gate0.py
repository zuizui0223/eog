import json
from pathlib import Path


def test_neon_gate0_contract_is_response_blind():
    p = json.loads(Path('validation/neon_camera_selective_promotion/source_selection_contract.json').read_text())
    assert p['gate0_metadata_only']['file_payload_requests_allowed'] == 0
    assert p['gate0_metadata_only']['file_payload_bytes_allowed'] == 0
    assert p['gate0_metadata_only']['csv_header_bytes_allowed'] == 0
    assert p['gate0_metadata_only']['csv_rows_allowed'] == 0
    fw = p['response_firewall']
    assert fw['camera_trap_sequences.csv_payload_open_allowed'] is False
    assert fw['camera_trap_sequences.csv_header_open_allowed'] is False
    assert fw['target_taxon_selection_allowed'] is False
    assert fw['outcome_prevalence_open_allowed'] is False
    assert fw['model_fit_allowed'] is False
    assert fw['heldout_score_allowed'] is False


def test_neon_gate0_contract_freezes_selective_promotion_question():
    p = json.loads(Path('validation/neon_camera_selective_promotion/source_selection_contract.json').read_text())
    b = p['scientific_boundary']
    assert b['closed_eog_wf_denominator_unchanged'] is True
    assert b['this_attempt_is_not_a_fourth_closed_eog_wf_endpoint'] is True
    assert b['selector_information_boundary'] == 'inner calibration only'
    assert b['outer_heldout_used_for_selection'] is False
