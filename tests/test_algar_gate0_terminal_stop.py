import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation" / "paper_ready_replication" / "candidate_flow_ledger.json"
CERTIFICATE = ROOT / "validation" / "algar_whitetail_endpoint3" / "gate0_terminal_stop_certificate.json"


def test_algar_is_29th_response_unconsumed_protocol_stop():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    stops = {row["issue"]: row for row in ledger["fresh_candidate_stops"]}
    algar = stops[378]
    summary = ledger["current_denominator_summary"]

    assert summary["fresh_predictive_endpoints_with_scores"] == 2
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 29
    assert summary["administrative_exclusions"] == 3
    assert summary["third_fresh_predictive_endpoint_still_required"] is True

    assert algar["terminal_stage"] == "response_independent_geometry_registry"
    assert algar["gate0_run_id"] == 34004544321
    assert algar["gate0_job_id"] == 101409317204
    assert algar["safe_file_requests"] == 5
    assert algar["safe_file_bytes_opened"] == 64276
    assert algar["images_requests"] == 0
    assert algar["images_header_bytes_opened"] == 0
    assert algar["images_payload_bytes_opened"] == 0
    assert algar["images_rows_opened"] == 0
    assert algar["response_values_opened"] is False
    assert algar["model_fits"] == algar["heldout_scores"] == 0
    assert algar["counts_as_predictive_evidence"] is False
    assert algar["gate0_fingerprint"] == (
        "8bfb521bb6add68bf3fda1cee56115258141c45901bddb11a64df6ba0f94a426"
    )


def test_algar_certificate_preserves_fail_closed_generic_adapter_boundary():
    cert = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    assert cert["status"] == "stop_pre_response_source_registry_or_geometry"
    assert cert["terminal_stage"] == "response_independent_geometry_registry"
    assert cert["reason"] == "coordinate drift across deployments for ALG069"
    assert cert["response_firewall"]["images_requests"] == 0
    assert cert["response_firewall"]["images_values_opened"] is False
    assert cert["protocol_boundary"]["coordinate_averaging_allowed"] is False
    assert cert["protocol_boundary"]["site_drop_allowed"] is False
    assert cert["protocol_boundary"]["coordinate_tolerance_retuning_allowed"] is False
    assert cert["protocol_boundary"]["retry_allowed"] is False
    assert cert["genericity_lesson"]["adapter_boundary_worked"] is True
    assert cert["genericity_lesson"]["core_layer_a_or_layer_b_changed"] is False
