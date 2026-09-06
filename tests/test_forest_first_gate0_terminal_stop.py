import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation" / "paper_ready_replication" / "candidate_flow_ledger.json"
CERT = ROOT / "validation" / "forest_first_endpoint3" / "gate0_terminal_stop_certificate.json"


def test_forest_first_is_30th_response_unconsumed_protocol_stop():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    stops = {row["issue"]: row for row in ledger["fresh_candidate_stops"]}
    row = stops[381]
    summary = ledger["current_denominator_summary"]

    assert summary["fresh_predictive_endpoints_with_scores"] == 2
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 30
    assert summary["administrative_exclusions"] == 3
    assert summary["third_fresh_predictive_endpoint_still_required"] is True

    assert row["terminal_stage"] == "response_blind_archive_range_transport"
    assert row["range_requests"] == 1
    assert row["size_probe_http_status"] == 200
    assert row["archive_metadata_bytes_opened"] == 0
    assert row["member_payload_bytes_opened"] == 0
    assert row["observations_header_bytes_opened"] == 0
    assert row["observations_payload_bytes_opened"] == 0
    assert row["observations_rows_opened"] == 0
    assert row["observations_values_opened"] is False
    assert row["media_payload_bytes_opened"] == 0
    assert row["model_fits"] == row["heldout_scores"] == 0
    assert row["gate0_run_id"] == 34006584422
    assert row["gate0_job_id"] == 101414854670
    assert row["gate0_artifact_id"] == 9981128987
    assert row["gate0_fingerprint"] == "8d5361707550d92ba4895622b41f0b6edcc36063a57920b50351ccab909e39c6"
    assert row["counts_as_predictive_evidence"] is False


def test_forest_first_certificate_preserves_body_free_http_200_stop():
    cert = json.loads(CERT.read_text(encoding="utf-8"))
    assert cert["status"] == "stop_pre_response_zip_transport_or_inventory"
    assert cert["classification"] == "response_blind_archive_range_transport_stop"
    assert cert["authoritative_execution"]["run_id"] == 34006584422
    assert cert["authoritative_execution"]["artifact_digest"] == (
        "sha256:30af4701ac2a54aefac33dea4221368995d17cc69d3b429cf2746376114982a4"
    )
    audit = cert["transport_audit"]
    assert audit["range_requests"] == 1
    assert audit["size_probe_status"] == 200
    assert audit["archive_metadata_bytes_opened"] == 0
    assert audit["member_payload_bytes_opened"] == 0
    assert audit["observations_values_opened"] is False
    assert cert["protocol_boundary"]["retry_allowed"] is False
    assert cert["protocol_boundary"]["http_200_body_fallback_allowed"] is False
    assert cert["protocol_boundary"]["counts_as_predictive_evidence"] is False
