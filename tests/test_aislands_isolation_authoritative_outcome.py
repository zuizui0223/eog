from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json"
PROVENANCE = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_execution_provenance.json"
QA = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome_qa.json"
AUTHORIZATION = ROOT / "validation/aislands_isolation_adequacy_20260812/outcome_execution_authorization.json"
ONE_TIME_WORKFLOW = ROOT / ".github/workflows/aislands-isolation-outcome-once.yml"


def test_authoritative_island_outcome_is_frozen_exactly() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["schema_version"] == "eog_aislands_isolation_adequacy_outcome_v1"
    assert result["status"] == "first_and_only_authoritative_island_isolation_adequacy_execution"
    assert result["contract_schema"] == "eog_aislands_isolation_adequacy_v1_3"
    assert result["taxa_declared"] == 886
    assert result["taxa_estimable"] == 886
    assert result["taxa_non_estimable"] == 0
    assert result["folds_declared"] == 4430
    assert result["folds_evaluable"] == 4231
    assert result["heldout_predictions"] == 712515
    assert result["failure_counts"] == {"insufficient_training_class_count_5_5": 199}
    assert result["result_fingerprint"] == "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"


def test_primary_is_adverse_against_the_frozen_r3_reference() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    primary = result["primary"]
    assert primary["contrast"] == "C_minus_R3_matched_heldout_log_loss"
    assert primary["favourable_direction"] == "negative"
    assert primary["species_macro_mean"] == 0.003485181598265469
    assert primary["bootstrap_95_ci"] == [
        0.0024664225728659645,
        0.004508216483355693,
    ]
    assert primary["sign_flip_two_sided_p"] == 9.99990000099999e-06
    assert primary["species_favourable_negative"] == 341
    assert primary["species_zero"] == 0
    assert primary["species_adverse_positive"] == 545


def test_secondary_brier_result_is_also_adverse() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    secondary = result["secondary"]
    assert secondary["contrast"] == "C_minus_R3_matched_heldout_brier"
    assert secondary["species_macro_mean"] == 0.0002682455326733689
    assert secondary["bootstrap_95_ci"] == [
        7.890886470882312e-05,
        0.0004570031232482133,
    ]
    assert secondary["sign_flip_two_sided_p"] == 0.005619943800561995


def test_execution_provenance_proves_one_run_and_no_rerun_path() -> None:
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    assert provenance["git_commit"] == "a9329d929933c919fe6c1c03934f0314c40f5c50"
    assert provenance["workflow_run_id"] == 31564146592
    assert provenance["workflow_run_attempt"] == 1
    assert provenance["authoritative_execution_count_declared"] == 1
    assert provenance["rerun_allowed"] is False
    assert provenance["result_fingerprint"] == "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"
    assert provenance["artifact_id"] == 9128998976
    assert provenance["artifact_digest"] == "sha256:59363bc82924e74445ad10a1d9732511e9bd5bcd056bef17ac89166f45b8355e"
    assert authorization["species_outcome_executions_before_this_commit"] == 0
    assert authorization["preoutcome_smoke_gate"]["c_minus_r3_inspected"] is False
    assert authorization["preoutcome_smoke_gate"]["models_fitted"] == 0
    assert not ONE_TIME_WORKFLOW.exists(), "completed one-time workflow must stay removed to prevent reruns"


def test_independent_qa_matches_authoritative_result_and_preserves_claim_boundary() -> None:
    qa = json.loads(QA.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert qa["source_result_fingerprint"] == result["result_fingerprint"]
    checks = qa["independent_consistency_checks"]
    assert checks["taxa_recalculated"] == 886
    assert checks["evaluable_folds_recalculated"] == 4231
    assert checks["non_evaluable_folds_recalculated"] == 199
    assert checks["heldout_prediction_rows_recalculated"] == 712515
    assert abs(checks["primary_species_macro_mean_recalculated"] - result["primary"]["species_macro_mean"]) < 1e-15
    assert checks["primary_species_favourable_negative_recalculated"] == 341
    assert checks["primary_species_adverse_positive_recalculated"] == 545
    assert checks["constant_predictor_drops_in_evaluable_folds"] == 0
    assert "cannot replace the frozen C-minus-R3 primary endpoint" in qa["interpretation_guard"]["explanatory_ladder_status"]
