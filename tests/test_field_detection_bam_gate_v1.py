"""Field ingestion gate: structural PASS is not ecological validation."""
from benchmarks.field_detection_bam_gate_v1 import check

def row(site,visit,day,detected="0"):
    return dict(site_id=site,visit_id=visit,survey_date=day,detected=detected,
        effort_minutes="20",method_id="trap",observer_id="observer",
        latitude="35.0",longitude="139.0",A_measure="1.2",
        B_measure="0.5",M_measure="0.2",A_method="climate",
        B_method="host",M_method="movement")

def good():
    return [row("a","1","2026-06-01","1"),row("a","2","2026-06-02"),
            row("b","1","2026-06-01"),row("b","2","2026-06-02")]

def test_complete_repeated_survey_is_only_schema_ready():
    r=check(good())
    assert r["status"]=="PASS_SCHEMA_ONLY"
    assert r["sites_with_repeated_visits"]==2

def test_single_visit_is_not_occupancy_replication():
    x=good()[:-1]
    assert any("NO_REPEATS" in reason for reason in check(x)["reasons"])

def test_missing_independent_M_method_stops():
    x=good();x[0]["M_method"]=""
    assert check(x)["status"]=="STOP"

def test_duplicate_site_visit_stops():
    x=good();x[1]["visit_id"]="1"
    assert any("DUPLICATE" in reason for reason in check(x)["reasons"])

def test_invalid_effort_and_detection_stop():
    x=good();x[0]["effort_minutes"]="0";x[0]["detected"]="unknown"
    assert check(x)["status"]=="STOP"

def test_closure_window_stops():
    x=good();x[1]["survey_date"]="2026-08-01"
    assert any("CLOSURE" in reason for reason in check(x)["reasons"])

def test_invalid_coordinate_stops():
    x=good();x[0]["latitude"]="100"
    assert check(x)["status"]=="STOP"
