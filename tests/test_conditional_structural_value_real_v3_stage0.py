from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"validation/conditional_structural_value_real_v3/stage0_source_contract_v1.json"
RUNNER=ROOT/"validation/conditional_structural_value_real_v3/stage0_source_screen.py"

def test_stage0_is_response_blind_and_single_candidate():
    p=json.loads(CONTRACT.read_text())
    assert p["candidate_id"]=="wildintel_ictpr1d1_camtrapdp_v1"
    assert p["selected_before_any_observations_payload_access"] is True
    assert p["authorized_stage0_access"]["response_file_gets"]==0
    assert p["authorized_stage0_access"]["response_header_bytes"]==0
    assert p["authorized_stage0_access"]["response_rows"]==0
    assert p["authorized_stage0_access"]["response_values"] is False
    assert "observations.csv" not in p["authorized_stage0_access"]["allowed_files"]

def test_stage0_has_strong_architecture_minima():
    p=json.loads(CONTRACT.read_text())
    g=p["stage0_gates"]
    assert g["minimum_complete_deployments"]>=50
    assert g["minimum_unique_coordinates"]>=50
    assert g["minimum_temporal_weeks"]>=12
    assert g["minimum_active_deployments_per_time_third"]>=20

def test_runner_never_gets_response_file():
    text=RUNNER.read_text()
    assert 'payload["observations.csv"]' not in text
    assert 'allowed_files' in text
    assert 'response_file_gets":0' in text
