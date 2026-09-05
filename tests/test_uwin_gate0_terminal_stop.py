import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation" / "paper_ready_replication" / "candidate_flow_ledger.json"
CERTIFICATE = ROOT / "validation" / "uwin_multicity_endpoint3" / "gate0_terminal_stop_certificate.json"


def test_uwin_is_28th_response_unconsumed_protocol_stop():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    stops = {row["issue"]: row for row in ledger["fresh_candidate_stops"]}
    uwin = stops[375]
    summary = ledger["current_denominator_summary"]

    assert summary["fresh_predictive_endpoints_with_scores"] == 2
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 28
    assert summary["administrative_exclusions"] == 3
    assert summary["third_fresh_predictive_endpoint_still_required"] is True

    assert uwin["terminal_stage"] == "response_independent_baseline_covariate_value"
    assert uwin["gate0_run_id"] == 33949107244
    assert uwin["gate0_job_id"] == 101260451576
    assert uwin["safe_file_requests"] == 4
    assert uwin["safe_file_bytes_opened"] == 1130264
    assert uwin["response_file_requests"] == 0
    assert uwin["response_header_bytes_opened"] == 0
    assert uwin["response_payload_bytes_opened"] == 0
    assert uwin["response_rows_opened"] == 0
    assert uwin["response_values_opened"] is False
    assert uwin["model_fits"] == uwin["heldout_scores"] == 0
    assert uwin["counts_as_predictive_evidence"] is False


def test_uwin_stop_certificate_preserves_no_repair_and_genericity_lesson():
    cert = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    assert cert["status"] == "stop_pre_response_source_registry_or_geometry"
    assert cert["reason"] == "Ndvi for jams|ALP|JU16 is not numeric"
    assert cert["retry_or_post_result_repair_allowed"] is False
    assert cert["response_firewall"]["capture_history_requests"] == 0
    assert cert["response_firewall"]["capture_history_values_opened"] is False
    assert cert["genericity_lesson"]["retroactive_repair_of_issue_375"] is False
    assert "fail-closed" in cert["genericity_lesson"]["structural_fields"]
    assert "fold-safe" in cert["genericity_lesson"]["optional_baseline_fields"]
