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
    assert summary["fresh_candidate_stops_listed"] == len(stops) == 20
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
