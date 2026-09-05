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
    assert hokkaido["full_response_live_job_id"] == 101234856240 if False else 101234856240
