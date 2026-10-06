import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SUMMARY=ROOT/"manuscript"/"inferential_openness"/"SUMMARY_V1.json"
LEDGER=ROOT/"validation"/"paper_ready_replication"/"candidate_flow_ledger.json"

def test_eog_denominator_recomputes_exactly():
    s=json.loads(SUMMARY.read_text())
    x=json.loads(LEDGER.read_text())
    assert len(x["fresh_predictive_results"]) == 3
    assert len(x["fresh_candidate_stops"]) == 31
    assert len(x["administrative_exclusions"]) == 3
    assert s["eog_primary_denominator"]["scientific_candidates"] == 34
    assert s["eog_primary_denominator"]["scored_predictive_endpoints"] == 3
    assert s["eog_primary_denominator"]["protocol_stops"] == 31

def test_barrier_family_partition_is_complete_and_nonoverlapping():
    s=json.loads(SUMMARY.read_text())
    x=json.loads(LEDGER.read_text())
    fam=s["eog_primary_denominator"]["barrier_families"]
    stages=[]
    for value in fam.values():
        stages.extend(value["stages"])
    assert len(stages)==len(set(stages))
    stop_stages=[r["terminal_stage"] for r in x["fresh_candidate_stops"]]
    assert set(stages)==set(stop_stages)
    counts={stage:stop_stages.count(stage) for stage in set(stop_stages)}
    for value in fam.values():
        assert value["count"] == sum(counts[stage] for stage in value["stages"])
    assert sum(v["count"] for v in fam.values())==31

def test_response_access_counts_recompute():
    s=json.loads(SUMMARY.read_text())
    x=json.loads(LEDGER.read_text())
    counts={}
    for row in x["fresh_candidate_stops"]:
        counts[row["biological_response_access"]]=counts.get(row["biological_response_access"],0)+1
    assert counts=={"none":29,"header_only":1,"full_response_once":1}
    assert s["eog_primary_denominator"]["response_access_among_stops"]["no_response_rows_opened"]==30

def test_284b_case_is_not_pooled_into_denominator():
    s=json.loads(SUMMARY.read_text())
    assert "not pooled" in s["denominator_boundary"].lower()
    c=s["level_c_deeper_identifiability_case"]
    assert c["architecture_screened_candidates"]==12
    assert c["architecture_qualified_candidates"]==2
    assert c["retained_candidates_with_candidate_specific_calibration"]==0
    assert c["retained_candidates_with_raw_or_supplementary_calibration_reconstructed"]==0
    assert c["focal_cross_role_values_opened"] is False
