from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "validation/paper_ready_replication/candidate_flow_ledger.json"
README = ROOT / "README.md"
LADDER = ROOT / "manuscript/submission/eog_wf_publication_decision_ladder.md"
CERT = ROOT / "validation/tampa_seagrass_endpoint3/terminal_predictive_result_certificate.json"
SYNTH = ROOT / "validation/paper_ready_replication/observed_endpoint3_synthesis.json"
FINAL_WORKFLOW = ROOT / ".github/workflows/tampa-seagrass-final.yml"
SELF = ROOT / "tools/_tampa_terminal_bookkeeping_once.py"
SELF_WORKFLOW = ROOT / ".github/workflows/tampa-terminal-bookkeeping-once.yml"

RUN_ID = 34028447227
LIVE_JOB_ID = 101477018912
EXECUTE_HEAD = "6ec7402751e8c17382558ed9332fc6ab9257d72d"
ARTIFACT_ID = 9988383179
ARTIFACT_DIGEST = "sha256:95aee0192537700f08ff07f7cffa8f64c2be73b13c76e5ec594bd3bdfb45044f"
RESULT_FINGERPRINT = "7fae3383aae989dae1abac9051f138043a70ea0e37c71105362634c82449cfbc"
PAIRED_FINGERPRINT = "e2472a918cfec2cbceb75de5c9c9614af7c0d7cbd2ce65d9ce592c1e945f371f"
PLACEBO_FINGERPRINT = "15aeca5ceae9357e7abdf3c2c90a30a94e0ae24765941a9662ec4d49c5c86b17"
PRODUCT_BOUNDARY = "structural_diagnostic_plus_context_dependent_predictive_complement"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_between(text: str, start: str, end: str, replacement: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError(f"section markers not unique: {start!r}, {end!r}")
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + replacement.rstrip() + "\n\n" + text[b:]


ledger = load_json(LEDGER)
summary = ledger["current_denominator_summary"]
assert summary["fresh_predictive_endpoints_with_scores"] == 2
assert summary["fresh_candidate_stops_listed"] == 31
assert summary["administrative_exclusions"] == 3
assert summary["third_fresh_predictive_endpoint_still_required"] is True
assert [row["issue"] for row in ledger["fresh_predictive_results"]] == [289, 292]
assert 388 not in {row["issue"] for row in ledger["fresh_candidate_stops"]}
assert 388 not in {row["issue"] for row in ledger["administrative_exclusions"]}

tampa_row = {
    "issue": 388,
    "system": "Tampa Bay seagrass transect monitoring",
    "endpoint": "eligible parent Transect visit x recorded Thalassia testudinum detection among linked child Point events",
    "observation_process": "long-term fixed-transect seagrass monitoring",
    "terminal_class": "predictive_result",
    "terminal_status": "adverse_complementary_added_value",
    "once_only_run_id": RUN_ID,
    "baseline_macro_log_loss": 0.33773536863857834,
    "augmented_macro_log_loss": 0.43876404318128526,
    "augmented_minus_baseline": 0.10102867454270692,
    "relative_log_loss_change": 0.2991356071173612,
    "augmented_heldout_wins": 1,
    "heldout_units": 5,
    "candidate_unit_count": 1497,
    "node_count": 71,
    "candidate_hunting_hard_stop": True,
}
ledger["fresh_predictive_results"].append(tampa_row)
summary["fresh_predictive_endpoints_with_scores"] = 3
summary["third_fresh_predictive_endpoint_still_required"] = False
summary["candidate_hunting_hard_stop"] = True
summary["observed_endpoint3_status"] = "adverse_complementary_added_value"
summary["product_boundary"] = PRODUCT_BOUNDARY
write_json(LEDGER, ledger)

certificate = {
    "schema": "eog.tampa_seagrass_endpoint3.terminal_predictive_result_certificate.v1",
    "attempt_id": "tampa_seagrass_endpoint3_v1",
    "issue": 388,
    "focal_taxon": "Thalassia testudinum",
    "provenance": {
        "once_only_run_id": RUN_ID,
        "live_job_id": LIVE_JOB_ID,
        "execute_head_sha": EXECUTE_HEAD,
        "artifact_id": ARTIFACT_ID,
        "artifact_name": "tampa-seagrass-final-endpoint",
        "artifact_digest": ARTIFACT_DIGEST,
        "result_fingerprint": RESULT_FINGERPRINT,
        "paired_result_fingerprint": PAIRED_FINGERPRINT,
    },
    "terminal_class": "predictive_result",
    "terminal_status": "adverse_complementary_added_value",
    "counts_as_predictive_evidence": True,
    "candidate_hunting_hard_stop": True,
    "primary": {
        "baseline_macro_log_loss": 0.33773536863857834,
        "augmented_macro_log_loss": 0.43876404318128526,
        "augmented_minus_baseline": 0.10102867454270692,
        "relative_log_loss_change": 0.2991356071173612,
        "baseline_better_folds": 4,
        "augmented_better_folds": 1,
        "tied_folds": 0,
        "heldout_folds_with_both_classes": 5,
        "fold_augmented_minus_baseline": [
            0.3475867430831058,
            0.05472414563925099,
            0.023266891514603927,
            -0.0012178452431740872,
            0.08078343771974805,
        ],
    },
    "endpoint_population": {
        "candidate_unit_count": 1497,
        "node_count": 71,
        "positive_candidate_units": 927,
        "negative_candidate_units": 570,
        "ever_positive_nodes": 54,
    },
    "response_access": {
        "occurrence_full_gets": 1,
        "occurrence_bytes_opened": 12508487,
        "safe_event_bytes_opened": 24654717,
        "emof_full_gets": 0,
        "emof_full_bytes_opened": 0,
        "primary_model_fits": 10,
        "placebo_model_fits": 100,
        "model_fits_total": 110,
        "heldout_scores": 10,
        "retry_allowed": False,
    },
    "secondary_placebo": {
        "secondary_only": True,
        "changes_primary_status": False,
        "replicates": 20,
        "feature_count": 10,
        "median_macro_log_loss": 0.33617575480692563,
        "q25_macro_log_loss": 0.33533628142421457,
        "q75_macro_log_loss": 0.3373586052296552,
        "real_augmented_minus_placebo_median": 0.10258828837435963,
        "fraction_placebo_replicates_beaten_by_real_augmented": 0.0,
        "fingerprint": PLACEBO_FINGERPRINT,
    },
    "predeclared_decision_application": {
        "source_contract": "validation/paper_ready_replication/cross_ecosystem_synthesis_contract.json",
        "observed_branch": "adverse_complementary_added_value",
        "product_boundary": PRODUCT_BOUNDARY,
        "allowed_claim": "Layer A remains a structural falsification framework; Layer B predictive value is not uniformly beneficial",
        "nature_ecology_evolution_trigger_open": False,
        "primary_submission_route": "Methods in Ecology and Evolution",
    },
}
write_json(CERT, certificate)

observed_synthesis = {
    "schema": "eog.paper_ready_replication.observed_endpoint3_synthesis.v1",
    "prospective_contract": "validation/paper_ready_replication/cross_ecosystem_synthesis_contract.json",
    "prospective_contract_must_remain_unchanged": True,
    "fresh_endpoint_unit": "ecosystem_endpoint",
    "endpoint_results": [
        {
            "issue": 289,
            "name": "azores_yellow_eel_receiver_week",
            "terminal_status": "favorable_complementary_added_value",
            "baseline_macro_log_loss": 0.14227269867445852,
            "augmented_macro_log_loss": 0.13228712656635494,
            "augmented_minus_baseline": -0.00998557210810358,
            "relative_log_loss_change": -0.07018614394144643,
            "augmented_heldout_wins": 5,
            "heldout_units": 5,
            "once_only_run_id": 32807155541,
        },
        {
            "issue": 292,
            "name": "southwest_louisiana_king_rail_site_occasion",
            "terminal_status": "favorable_complementary_added_value",
            "baseline_macro_log_loss": 0.2463173322,
            "augmented_macro_log_loss": 0.2453455299,
            "augmented_minus_baseline": -0.0009718023,
            "relative_log_loss_change": -0.003945326507559504,
            "augmented_heldout_wins": 7,
            "heldout_units": 8,
            "once_only_run_id": 32812052801,
        },
        tampa_row,
    ],
    "observed_endpoint3_status": "adverse_complementary_added_value",
    "predeclared_product_boundary_applied": PRODUCT_BOUNDARY,
    "allowed_claim": "Layer A remains a structural falsification framework; Layer B predictive value is not uniformly beneficial",
    "forbidden_interpretations": [
        "universal_predictive_superiority",
        "guaranteed_layer_b_improvement",
        "standalone_layer_b_prediction",
        "causal_identification",
        "truth_of_exact_layer_a_world",
    ],
    "aggregation": {
        "pool_row_level_predictions_across_ecosystems": False,
        "pooled_p_value_or_common_effect_claim": False,
        "report_endpoint_heterogeneity_explicitly": True,
    },
    "candidate_hunting_hard_stop": True,
    "fourth_fresh_endpoint_allowed": False,
    "primary_submission_route": "Methods in Ecology and Evolution",
    "nature_ecology_evolution_trigger_open": False,
    "next_phase": "manuscript figures, evidence table, methods/results text, and submission package",
}
write_json(SYNTH, observed_synthesis)

readme = README.read_text(encoding="utf-8")
old_empirical = "> **The two-layer EOG-WF has two favorable, genuinely fresh paired heldout endpoints under the unchanged `symmetric_world_support_summary_v1`: Azores yellow eel telemetry and Southwest Louisiana King Rail passive acoustics. The supported boundary is `replicated_candidate_general_predictive_complement`.**"
new_empirical = "> **The paper-ready fresh programme is closed with three valid paired predictive endpoints under the unchanged `symmetric_world_support_summary_v1`: Azores yellow eel and Southwest Louisiana King Rail are favorable, while Tampa Bay seagrass is adverse. The preregistered endpoint-3 mapping therefore fixes the supported boundary at `structural_diagnostic_plus_context_dependent_predictive_complement`.**"
old_product = "> **Exact world identity is retained as the latent sequential update/falsification state (Layer A), while the default predictive interface is the world-label-invariant surviving-support summary (Layer B). One valid third heterogeneous endpoint is still required before the paper-level synthesis is closed.**"
new_product = "> **Layer A remains the exact auditable world-compatibility / contraction / falsification state. Layer B remains the unchanged world-label-invariant support summary, but its added predictive value is explicitly context dependent rather than uniformly beneficial. Candidate hunting is hard-stopped after the valid Tampa endpoint.**"
assert old_empirical in readme and old_product in readme
readme = readme.replace(old_empirical, new_empirical, 1).replace(old_product, new_product, 1)

fresh_section = """## Current fresh two-layer evidence

- **Azores yellow eel telemetry** — favorable paired complementarity; baseline macro log loss `0.1422727`, augmented `0.1322871`, delta `-0.0099856`; augmented won 5/5 heldout blocks; run `32807155541`.
- **Southwest Louisiana King Rail passive acoustics** — favorable paired complementarity; baseline `0.2463173`, augmented `0.2453455`, delta `-0.0009718`; augmented won 7/8 heldout occasions; run `32812052801`.
- **Tampa Bay seagrass transect monitoring** — valid adverse endpoint 3; baseline `0.3377354`, augmented `0.4387640`, delta `+0.1010287` (~29.9% higher log loss); baseline won 4/5 folds; run `34028447227`. The 20-replicate ten-feature placebo median (`0.3361758`) also outperformed the real augmented arm.

The manuscript-facing denominator is now **3 scored predictive endpoints / 31 scientific-protocol STOPs / 3 administrative exclusions**. STOPs remain methods-integrity evidence rather than negative Layer-B results.

The preregistered adverse mapping fixes the product boundary at:

`structural_diagnostic_plus_context_dependent_predictive_complement`

This supports Layer A as a structural falsification framework and shows that Layer B can add predictive information in some systems but is not uniformly beneficial. It does not support universal superiority, a standalone Layer-B predictor, causal identification, or the truth of an exact Layer-A world.

Candidate hunting is closed. No fourth dataset may be added to improve the apparent result or journal rank.
"""
readme = replace_between(readme, "## Current fresh two-layer evidence", "## Historical evidence ledger", fresh_section)

development_section = """## Development rule

The paper-ready fresh replication programme is scientifically closed. A valid third predictive terminal was reached in Tampa Bay and was adverse under the frozen decision rule.

Therefore:

- do not search for a fourth or prestige-driven favorable dataset;
- do not repair or rerun any consumed fresh endpoint;
- do not add generic connectivity operators to rescue predictive performance;
- keep Layer A and `symmetric_world_support_summary_v1` unchanged for the manuscript evidence;
- complete the already-frozen cross-ecosystem synthesis, endpoint-wise performance figure, candidate-funnel evidence table, Methods/Results text, and submission package.

The observed product boundary is `structural_diagnostic_plus_context_dependent_predictive_complement`. The default strong submission route is **Methods in Ecology and Evolution**; the Nature Ecology & Evolution trigger is closed by the adverse third endpoint.

Public API/CLI/package-surface freeze follows manuscript scientific closure rather than reopening model development.
"""
readme = replace_between(readme, "## Development rule", "## Package architecture", development_section)
README.write_text(readme, encoding="utf-8")

ladder = LADDER.read_text(encoding="utf-8")
anchor = """## Current scientific anchor

The paper-ready EOG-WF fresh endpoint programme is closed at:

`structural_diagnostic_plus_context_dependent_predictive_complement`

Three genuinely fresh heterogeneous paired endpoints reached valid predictive terminals under the same two-layer architecture and unchanged `symmetric_world_support_summary_v1`:

1. Azores yellow eel telemetry — favorable;
2. Southwest Louisiana King Rail passive acoustics — favorable;
3. Tampa Bay seagrass transect monitoring — adverse.

Tampa's once-only endpoint produced baseline macro log loss `0.3377354` versus augmented `0.4387640` (delta `+0.1010287`), with the baseline arm winning 4/5 folds. The preregistered adverse branch is therefore applied without rescue tuning: Layer A remains a structural falsification framework, while Layer B predictive value is context dependent rather than uniformly beneficial.

The Nature Ecology & Evolution trigger is closed. **Methods in Ecology and Evolution is now the primary submission route**, with Ecography retained only as a framing-dependent fallback. Candidate hunting is hard-stopped; no fourth dataset may be collected to improve journal rank.
"""
ladder = replace_between(ladder, "## Current scientific anchor", "## Publication principle", anchor)
LADDER.write_text(ladder, encoding="utf-8")

changed_test_files = []
for path in sorted((ROOT / "tests").glob("test_*.py")):
    text = path.read_text(encoding="utf-8")
    if "current_denominator_summary" not in text:
        continue
    original = text
    text = text.replace(
        'summary["fresh_predictive_endpoints_with_scores"] == len(results) == 2',
        'summary["fresh_predictive_endpoints_with_scores"] == len(results) == 3',
    )
    text = text.replace(
        'summary["fresh_predictive_endpoints_with_scores"] == 2',
        'summary["fresh_predictive_endpoints_with_scores"] == 3',
    )
    text = text.replace(
        'summary["third_fresh_predictive_endpoint_still_required"] is True',
        'summary["third_fresh_predictive_endpoint_still_required"] is False',
    )
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed_test_files.append(path.name)

assert "test_paper_ready_candidate_flow_ledger.py" in changed_test_files
assert "test_leipzig_final_terminal_stop.py" in changed_test_files

new_test = ROOT / "tests/test_tampa_seagrass_terminal_predictive_result.py"
new_test.write_text(
    """import json
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
""",
    encoding="utf-8",
)

assert FINAL_WORKFLOW.exists()
FINAL_WORKFLOW.unlink()
SELF.unlink()
SELF_WORKFLOW.unlink()
