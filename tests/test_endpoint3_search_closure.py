import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "validation" / "paper_ready_replication" / "endpoint3_search_closure.json"
LEDGER = ROOT / "validation" / "paper_ready_replication" / "candidate_flow_ledger.json"


def test_endpoint3_search_closure_freezes_evidence_denominator_and_unresolved_state():
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    evidence = closure["evidence_at_closure"]
    summary = ledger["current_denominator_summary"]

    assert closure["schema"] == "eog.paper_ready_replication.endpoint3_search_closure.v1"
    assert closure["scientific_status"] == "replicated_candidate_general_predictive_complement"
    assert evidence["fresh_predictive_endpoints_with_scores"] == 2
    assert evidence["fresh_candidate_protocol_stops"] == 25
    assert evidence["administrative_exclusions"] == 2
    assert evidence["third_predictive_endpoint_scored"] is False
    assert evidence["third_predictive_endpoint_status"] == "unresolved_not_obtained"
    assert evidence["stop_rows_count_as_predictive_evidence"] is False
    assert evidence["frozen_shortlist_issues"] == [327, 348, 353]
    assert evidence["frozen_shortlist_exhausted"] is True
    assert len(ledger["fresh_predictive_results"]) == 2
    assert len(ledger["fresh_candidate_stops"]) == 25
    assert summary["third_fresh_predictive_endpoint_still_required"] is False
    assert summary["third_predictive_endpoint_state"] == "unresolved_not_obtained"


def test_closure_forbids_dataset_hunting_and_does_not_turn_stops_into_nulls():
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    search = closure["search_closure"]
    claim = closure["claim_boundary"]

    assert search["candidate_search_closed"] is True
    assert search["new_fresh_candidates_allowed_for_this_manuscript"] is False
    assert search["third_endpoint_absence_is_null_result"] is False
    assert search["third_endpoint_absence_is_adverse_result"] is False
    assert search["protocol_stops_are_layer_b_failures"] is False
    assert search["stopped_attempt_repair_allowed"] is False
    assert search["prestige_driven_dataset_hunting_allowed"] is False
    assert search["new_connectivity_operator_authorized"] is False
    assert claim["keep_current_status"] is True
    assert claim["universal_predictive_superiority_claim_allowed"] is False
    assert claim["causal_identification_claim_allowed"] is False
    assert claim["exact_world_truth_claim_allowed"] is False


def test_publication_route_closes_nature_trigger_and_moves_to_mee():
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    publication = closure["publication_route"]
    transition = closure["paper_transition"]

    assert publication["nature_ecology_and_evolution_trigger_open"] is False
    assert publication["primary_target"] == "Methods in Ecology and Evolution"
    assert publication["conditional_fallback"] == "Ecography"
    assert publication["journal_choice_may_reopen_science"] is False
    assert transition["scientific_development_complete"] is True
    assert transition["next_phase"] == "manuscript_and_submission_package_assembly"
    assert transition["endpoint3_placebo_may_upgrade_claim"] is False
    assert transition["endpoint3_excluded_world_analysis_may_upgrade_claim"] is False
    assert transition["azores_louisiana_posthoc_robustness_may_upgrade_claim"] is False
