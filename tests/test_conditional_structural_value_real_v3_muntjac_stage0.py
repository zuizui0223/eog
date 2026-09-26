import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROSTER=ROOT/"validation/conditional_structural_value_real_v3/finite_candidate_roster_v1.json"
CONTRACT=ROOT/"validation/conditional_structural_value_real_v3/muntjac_stage0_contract_v1.json"
RUNNER=ROOT/"validation/conditional_structural_value_real_v3/muntjac_stage0_archive_screen.py"

def test_roster_is_finite_and_ends_at_candidate2():
    p=json.loads(ROSTER.read_text())
    assert p["maximum_candidates"]==2
    assert len(p["ordered_candidates"])==2
    assert p["hard_stop"]["after_candidate2_terminal"] is True
    assert p["hard_stop"]["third_candidate_allowed"] is False

def test_muntjac_stage0_opens_no_member_body():
    p=json.loads(CONTRACT.read_text())
    a=p["authorized_stage0_access"]
    assert a["full_archive_download"] is False
    assert a["member_body_reads"]==0
    assert a["observations_body_reads"]==0
    assert a["deployments_body_reads"]==0
    assert a["archive_tail_range_gets_max"]==1

def test_runner_only_reads_page_head_and_archive_tail():
    text=RUNNER.read_text()
    assert "zipfile.ZipFile" not in text
    assert "observations.csv" in text
    assert "deployments.csv" in text
    assert "PK\\x01\\x02" in text
