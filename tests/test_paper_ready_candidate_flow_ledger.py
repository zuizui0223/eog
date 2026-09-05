import json
from pathlib import Path


LEDGER = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "paper_ready_replication"
    / "candidate_flow_ledger.json"
)
HOKKAIDO_CAPTURE_FAILURE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "hokkaido_streamfish_endpoint3"
    / "final_output_capture_failure_certificate.json"
)
COLUMBIA_GATE1_STOP = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "columbia_shrubsteppe_endpoint3"
    / "gate1_terminal_stop_certificate.json"
)


def _load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_candidate_flow_summary_matches_the_frozen_denominator():
    ledger = _load_ledger()
    results = ledger["fresh_predictive_results"]
    stops = ledger["fresh_candidate_stops"]
    exclusions = ledger["administrative_exclusions"]
    summary = ledger["current_denominator_summary"]

    assert ledger["schema"] == "eog.paper_ready_replication.candidate_flow_ledger.v1"
    assert summary["fresh_predictive_endpoints_with_scores"] == len(results) == 2
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 27
    assert summary["administrative_exclusions"] == len(exclusions) == 3
    assert summary["third_fresh_predictive_endpoint_still_required"] is True
    assert len({row["issue"] for row in stops}) == len(stops)
    assert all(row["counts_as_predictive_evidence"] is False for row in stops)


def test_hokkaido_response_consumed_capture_failure_is_administrative_only():
    ledger = _load_ledger()
    exclusions = {row["issue"]: row for row in ledger["administrative_exclusions"]}
    hokkaido = exclusions[364]
    assert hokkaido["classification"] == "response_consumed_output_capture_failure"
    assert hokkaido["biological_response_access"] == "full_response_once"
    assert hokkaido["full_response_execution_run_id"] == 33937721963
    assert hokkaido["full_response_live_job_id"] == 101228856240
    assert hokkaido["full_endpoint_step_conclusion"] == "success"
    assert hokkaido["scientific_terminal_status_recoverable"] is False
    assert hokkaido["counts_as_predictive_evidence"] is False
    assert hokkaido["retry_allowed"] is False
    assert 364 not in {row["issue"] for row in ledger["fresh_candidate_stops"]}

    certificate = json.loads(HOKKAIDO_CAPTURE_FAILURE.read_text(encoding="utf-8"))
    assert certificate["classification"] == "administrative_response_consumed_output_capture_failure"
    assert certificate["fresh_attempt_consumed"] is True
    assert certificate["scientific_terminal_status_recoverable"] is False
    assert certificate["response_access"]["retry_allowed"] is False
    assert certificate["capture_failure"]["runner_default_output_path"].endswith(
        "final_endpoint_certificate.json"
    )
    assert certificate["capture_failure"]["workflow_audit_expected_path"].endswith(
        "final_endpoint_result.json"
    )


def test_latest_gate_stops_remain_response_unconsumed_and_non_scientific():
    by_issue = {
        row["issue"]: row
        for row in _load_ledger()["fresh_candidate_stops"]
    }

    portal = by_issue[314]
    assert portal["terminal_stage"] == "response_independent_calendar_value"
    assert portal["gate0_run_id"] == 32954719035
    assert portal["response_payload_bytes_opened"] == 0
    assert portal["model_fits"] == portal["heldout_scores"] == 0

    andrews = by_issue[315]
    assert andrews["terminal_stage"] == "source_transport"
    assert andrews["gate0_run_id"] == 33140901154
    assert andrews["response_payload_bytes_opened"] == 0
    assert andrews["gate0_fingerprint"] == (
        "2642d550130817740bef9343a2386f29e9429f6701f36b36876efb0bce97c358"
    )

    mica = by_issue[327]
    assert mica["terminal_stage"] == "source_transport"
    assert mica["gate0_run_id"] == 33484335166
    assert mica["archive_metadata_bytes_opened"] == 0
    assert mica["deployment_payload_bytes_opened"] == 0
    assert mica["observation_payload_bytes_opened"] == 0

    illinois = by_issue[331]
    assert illinois["terminal_stage"] == "metadata_identity_or_transport"
    assert illinois["gate0_run_id"] == 33581329294
    assert illinois["file_payload_bytes_opened"] == 0
    assert illinois["response_rows_opened"] == 0
    assert illinois["gate0_fingerprint"] == (
        "243f1796127d49477852fb3a177e57a9de599f8357f81412f9871b5e07d4481a"
    )

    soutpansberg = by_issue[335]
    assert soutpansberg["terminal_stage"] == "response_blind_zip_inventory"
    assert soutpansberg["gate1_run_id"] == 33596029399
    assert soutpansberg["member_payload_bytes_opened"] == 0
    assert soutpansberg["capture_payload_bytes_opened"] == 0
    assert soutpansberg["gate1_result_fingerprint"] == (
        "6894dc4b1c6a4d5ffb128b326ca4ec9c2b34e7c7c5ea945b29d6cf91782afddf"
    )

    loomis = by_issue[340]
    assert loomis["terminal_stage"] == "response_blind_physical_header_schema"
    assert loomis["stage1a_run_id"] == 33601669468
    assert loomis["deployment_rows_opened"] == 0
    assert loomis["detection_payload_bytes_opened"] == 0
    assert loomis["response_values_opened"] is False

    cassowary = by_issue[348]
    assert cassowary["terminal_stage"] == "metadata_identity_or_transport"
    assert cassowary["gate0_run_id"] == 33704514950
    assert cassowary["metadata_bytes_opened"] == 4999
    assert cassowary["file_payload_bytes_opened"] == 0
    assert cassowary["response_values_opened"] is False
    assert cassowary["gate0_artifact_digest"] == (
        "sha256:c7eaec624c68b0444124af7d4a3f10202bb6e246a6b80e422333d6817a4bdb55"
    )

    norway = by_issue[353]
    assert norway["terminal_stage"] == "metadata_identity_or_interface"
    assert norway["gate0_run_id"] == 33707931673
    assert norway["metadata_bytes_opened"] == 9861
    assert norway["archive_payload_bytes_opened"] == 0
    assert norway["member_payload_bytes_opened"] == 0
    assert norway["response_values_opened"] is False

    sebms = by_issue[358]
    assert sebms["terminal_stage"] == "source_transport_dns"
    assert sebms["gate0_metadata_passed"] is True
    assert sebms["gate1_run_id"] == 33900956377
    assert sebms["head_requests"] == 1
    assert sebms["head_body_bytes_opened"] == 0
    assert sebms["range_probe_requests"] == 1
    assert sebms["archive_metadata_range_requests"] == 1
    assert sebms["archive_metadata_range_bytes_opened"] == 0
    assert sebms["meta_xml_compressed_bytes_opened"] == 0
    assert sebms["event_member_payload_bytes_opened"] == 0
    assert sebms["emof_member_payload_bytes_opened"] == 0
    assert sebms["occurrence_member_header_bytes_opened"] == 0
    assert sebms["occurrence_member_payload_bytes_opened"] == 0
    assert sebms["response_rows_opened"] == 0
    assert sebms["response_values_opened"] is False
    assert sebms["model_fits"] == sebms["heldout_scores"] == 0
    assert sebms["gate1_fingerprint"] == (
        "5df113c4b257b3419f90a30be21c2d3955aa65380fd7714baea52e23072606f2"
    )
    assert sebms["gate1_artifact_digest"] == (
        "sha256:c148687e14df799ca0c8b8c2d21959b0b51837e4cd88c3ecc216cc120dde8c5a"
    )

    columbia = by_issue[370]
    assert columbia["terminal_stage"] == "response_blind_zip_presign_transport"
    assert columbia["gate0_metadata_passed"] is True
    assert columbia["gate1_run_id"] == 33939691964
    assert columbia["gate1_job_id"] == 101234603555
    assert columbia["presign_requests"] == 1
    assert columbia["presign_http_status"] == 403
    assert columbia["dryad_redirect_body_bytes_opened"] == 0
    assert columbia["s3_range_requests"] == 0
    assert columbia["archive_metadata_bytes_opened"] == 0
    assert columbia["archive_member_payload_bytes_opened"] == 0
    assert columbia["detection_history_payload_bytes_opened"] == 0
    assert columbia["camera_record_payload_bytes_opened"] == 0
    assert columbia["response_rows_opened"] == 0
    assert columbia["response_values_opened"] is False
    assert columbia["model_fits"] == columbia["heldout_scores"] == 0
    assert columbia["gate1_fingerprint"] == (
        "d07eaf7991ba9a65646315c8816332a4a559b878659bef6c1317a0dd327046be"
    )
    assert columbia["gate1_artifact_digest"] == (
        "sha256:795091a7fcc4be6361df6f48c2f631a32aa2babbbf2fda6c3d321a85b69c2320"
    )

    certificate = json.loads(COLUMBIA_GATE1_STOP.read_text(encoding="utf-8"))
    assert certificate["status"] == "stop_pre_response_zip_transport_or_inventory"
    assert certificate["counts_as_predictive_evidence"] is False
    assert certificate["transport_audit"]["first_presign_http_status"] == 403
    assert certificate["transport_audit"]["dryad_redirect_body_bytes_opened"] == 0
    assert certificate["transport_audit"]["s3_range_requests"] == 0
    assert certificate["transport_audit"]["response_values_opened"] is False
    assert certificate["protocol_boundary"]["retry_allowed"] is False
