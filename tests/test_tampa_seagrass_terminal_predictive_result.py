import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation/paper_ready_replication/candidate_flow_ledger.json"
CERT = ROOT / "validation/tampa_seagrass_endpoint3/terminal_predictive_result_certificate.json"
SYNTH = ROOT / "validation/paper_ready_replication/observed_endpoint3_synthesis.json"
FROZEN_SYNTH = ROOT / "validation/paper_ready_replication/cross_ecosystem_synthesis_contract.json"
FINAL_WORKFLOW = ROOT / ".github/workflows/tampa-seagrass-final.yml"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_tampa_is_valid_adverse_third_predictive_endpoint_and_hard_stops_hunting():
    c = load(CERT)
    assert c["terminal_class"] == "predictive_result"
    assert c["terminal_status"] == "adverse_complementary_added_value"
    assert c["counts_as_predictive_evidence"] is True
    assert c["candidate_hunting_hard_stop"] is True
    assert c["provenance"]["once_only_run_id"] == 34028447227
    assert c["provenance"]["live_job_id"] == 101477018912
    assert c["provenance"]["artifact_id"] == 9988383179
    assert c["provenance"]["result_fingerprint"] == "7fae3383aae989dae1abac9051f138043a70ea0e37c71105362634c82449cfbc"
    assert c["primary"]["baseline_macro_log_loss"] == 0.33773536863857834
    assert c["primary"]["augmented_macro_log_loss"] == 0.43876404318128526
    assert c["primary"]["augmented_minus_baseline"] == 0.10102867454270692
    assert c["primary"]["baseline_better_folds"] == 4
    assert c["primary"]["augmented_better_folds"] == 1
    assert c["response_access"]["occurrence_full_gets"] == 1
    assert c["response_access"]["occurrence_bytes_opened"] == 12508487
    assert c["response_access"]["emof_full_gets"] == 0
    assert c["response_access"]["emof_full_bytes_opened"] == 0
    assert c["response_access"]["retry_allowed"] is False


def test_candidate_ledger_closes_the_third_endpoint_denominator():
    ledger = load(LEDGER)
    summary = ledger["current_denominator_summary"]
    results = {row["issue"]: row for row in ledger["fresh_predictive_results"]}
    assert summary["fresh_predictive_endpoints_with_scores"] == len(results) == 3
    assert summary["fresh_candidate_stops_listed"] == len(ledger["fresh_candidate_stops"]) == 31
    assert summary["administrative_exclusions"] == len(ledger["administrative_exclusions"]) == 3
    assert summary["third_fresh_predictive_endpoint_still_required"] is False
    assert summary["candidate_hunting_hard_stop"] is True
    assert summary["product_boundary"] == "structural_diagnostic_plus_context_dependent_predictive_complement"
    assert results[388]["terminal_status"] == "adverse_complementary_added_value"
    assert results[388]["candidate_hunting_hard_stop"] is True


def test_observed_synthesis_applies_but_does_not_mutate_frozen_decision_mapping():
    observed = load(SYNTH)
    frozen = load(FROZEN_SYNTH)
    assert observed["prospective_contract_must_remain_unchanged"] is True
    assert observed["observed_endpoint3_status"] == "adverse_complementary_added_value"
    assert observed["predeclared_product_boundary_applied"] == frozen["endpoint_3_decision_mapping"]["adverse_complementary_added_value"]["paper_boundary"]
    assert observed["candidate_hunting_hard_stop"] is True
    assert observed["fourth_fresh_endpoint_allowed"] is False
    assert observed["primary_submission_route"] == "Methods in Ecology and Evolution"
    assert observed["nature_ecology_evolution_trigger_open"] is False


def test_consumed_tampa_final_workflow_is_removed():
    assert not FINAL_WORKFLOW.exists()
