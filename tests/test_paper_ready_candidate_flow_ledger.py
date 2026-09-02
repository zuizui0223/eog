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
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 22
    assert summary["administrative_exclusions"] == len(exclusions) == 2
    assert summary["third_fresh_predictive_endpoint_still_required"] is True
    assert len({row["issue"] for row in stops}) == len(stops)
    assert all(row["counts_as_predictive_evidence"] is False for row in stops)


def test_latest_gate0_stops_remain_response_unconsumed_and_non_scientific():
    ledger = _load_ledger()
    by_issue = {row["issue"]: row for row in ledger["fresh_candidate_stops"]}

    portal = by_issue[314]
    assert portal["terminal_stage"] == "response_independent_calendar_value"
    assert portal["gate0_run_id"] == 32954719035
    assert portal["response_payload_requests"] == 0
    assert portal["response_payload_bytes_opened"] == 0
    assert portal["model_fits"] == 0
    assert portal["heldout_scores"] == 0

    andrews = by_issue[315]
    assert andrews["terminal_stage"] == "source_transport"
    assert andrews["gate0_run_id"] == 33140901154
    assert andrews["forbidden_response_head_requests"] == 0
    assert andrews["response_payload_requests"] == 0
    assert andrews["response_payload_bytes_opened"] == 0
    assert andrews["model_fits"] == 0
    assert andrews["heldout_scores"] == 0
    assert andrews["gate0_fingerprint"] == (
        "2642d550130817740bef9343a2386f29e9429f6701f36b36876efb0bce97c358"
    )

    mica = by_issue[327]
    assert mica["terminal_stage"] == "source_transport"
    assert mica["gate0_run_id"] == 33484335166
    assert mica["head_body_bytes_opened"] == 0
    assert mica["archive_metadata_range_requests"] == 0
    assert mica["archive_metadata_bytes_opened"] == 0
    assert mica["deployment_payload_bytes_opened"] == 0
    assert mica["observation_header_bytes_opened"] == 0
    assert mica["observation_payload_bytes_opened"] == 0
    assert mica["model_fits"] == 0
    assert mica["heldout_scores"] == 0
    assert mica["gate0_artifact_digest"] == (
        "sha256:0658b3adad8a240b6008469dced18d3c1e7aebce99ee7bc2436632321c6978e3"
    )

    illinois = by_issue[331]
    assert illinois["terminal_stage"] == "metadata_identity_or_transport"
    assert illinois["gate0_run_id"] == 33581329294
    assert illinois["metadata_only"] is True
    assert illinois["file_payload_requests"] == 0
    assert illinois["file_payload_bytes_opened"] == 0
    assert illinois["response_header_bytes_opened"] == 0
    assert illinois["response_rows_opened"] == 0
    assert illinois["response_values_opened"] == 0
    assert illinois["model_fits"] == 0
    assert illinois["heldout_scores"] == 0
    assert illinois["gate0_fingerprint"] == (
        "243f1796127d49477852fb3a177e57a9de599f8357f81412f9871b5e07d4481a"
    )
    assert illinois["gate0_artifact_digest"] == (
        "sha256:42e54f11b0db49de7404942cef760cadcd099f30288a06d96dfd5e6da3cd6349"
    )

    soutpansberg = by_issue[335]
    assert soutpansberg["terminal_stage"] == "response_blind_zip_inventory"
    assert soutpansberg["gate1_run_id"] == 33596029399
    assert soutpansberg["archive_metadata_range_requests"] == 492
    assert soutpansberg["archive_metadata_bytes_opened"] == 48050
    assert soutpansberg["member_payload_bytes_opened"] == 0
    assert soutpansberg["deployment_payload_bytes_opened"] == 0
    assert soutpansberg["capture_header_bytes_opened"] == 0
    assert soutpansberg["capture_payload_bytes_opened"] == 0
    assert soutpansberg["response_rows_opened"] == 0
    assert soutpansberg["response_values_opened"] == 0
    assert soutpansberg["model_fits"] == 0
    assert soutpansberg["heldout_scores"] == 0
    assert soutpansberg["gate1_result_fingerprint"] == (
        "6894dc4b1c6a4d5ffb128b326ca4ec9c2b34e7c7c5ea945b29d6cf91782afddf"
    )
    assert soutpansberg["gate1_artifact_digest"] == (
        "sha256:1e2b2e162ffb34c59d235396761794ee823971ea2a80953201118f11bc231f53"
    )
