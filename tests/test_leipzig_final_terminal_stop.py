import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation" / "paper_ready_replication" / "candidate_flow_ledger.json"
CERTIFICATE = (
    ROOT
    / "validation"
    / "leipzig_roedeer_endpoint3"
    / "final_terminal_stop_certificate.json"
)


def test_leipzig_is_full_response_consumed_protocol_stop():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    stops = {row["issue"]: row for row in ledger["fresh_candidate_stops"]}
    leipzig = stops[384]
    summary = ledger["current_denominator_summary"]

    assert summary["fresh_predictive_endpoints_with_scores"] == 2
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 31
    assert summary["administrative_exclusions"] == 3
    assert summary["third_fresh_predictive_endpoint_still_required"] is True

    assert leipzig["terminal_stage"] == "full_response_schema_or_linkage"
    assert leipzig["biological_response_access"] == "full_response_once"
    assert leipzig["response_bytes_opened"] == 2480328
    assert leipzig["gate_final_run_id"] == 34022855350
    assert leipzig["gate_final_job_id"] == 101458564307
    assert leipzig["retry_allowed"] is False
    assert leipzig["counts_as_predictive_evidence"] is False


def test_leipzig_terminal_certificate_forbids_retry_and_retuning():
    cert = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    assert cert["status"] == "stop_full_response_schema_or_linkage"
    assert cert["terminal_class"] == "protocol_or_estimability_stop"
    assert cert["reason"] == "focal eventStart lies outside raw deployment interval at row 1926"
    assert cert["counts_as_predictive_evidence"] is False
    assert cert["candidate_hunting_hard_stop"] is False
    assert cert["response_access"]["biological_response_access"] == "full_response_once"
    assert cert["response_access"]["response_bytes_opened"] == 2480328
    assert cert["response_access"]["retry_allowed"] is False
    assert cert["response_access"]["post_response_repair_or_retune_allowed"] is False
    assert cert["authoritative_execution"]["run_id"] == 34022855350
    assert cert["authoritative_execution"]["live_job_id"] == 101458564307
    assert cert["authoritative_execution"]["artifact_id"] == 9986083072
    assert cert["authoritative_execution"]["result_fingerprint"] == (
        "aef1c9c82657c06d9522011bcf0c284653da80217ec38c3c2c64bd16aa33c5e7"
    )
