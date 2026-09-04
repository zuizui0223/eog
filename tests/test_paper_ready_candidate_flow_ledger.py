import json
from pathlib import Path


LEDGER = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "paper_ready_replication"
    / "candidate_flow_ledger.json"
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
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 26
    assert summary["administrative_exclusions"] == len(exclusions) == 2
    assert summary["third_fresh_predictive_endpoint_still_required"] is False
    assert summary["third_predictive_endpoint_state"] == "unresolved_not_obtained"
    assert summary["endpoint3_search_closed_without_score"] is True
    assert summary["paper_development_closed_to_new_candidates"] is True
    assert summary["search_closure_issue"] == 357
    assert ledger["reporting_rules"]["no_new_candidates_after_search_closure"] is True
    assert ledger["reporting_rules"]["third_endpoint_unresolved_is_not_null_or_adverse"] is True
    assert len({row["issue"] for row in stops}) == len(stops)
    assert all(row["counts_as_predictive_evidence"] is False for row in stops)


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
