from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "manuscript/build_paper_ready_eogwf.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_paper_ready_builder_freezes_observed_three_endpoint_boundary(tmp_path: Path) -> None:
    output = tmp_path / "paper"
    subprocess.run(
        [sys.executable, str(BUILDER), "--output-dir", str(output)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    expected = {
        "README.md",
        "candidate_flow_table.csv",
        "candidate_funnel_summary.csv",
        "figure_1_two_layer_architecture.svg",
        "figure_2_candidate_funnel.svg",
        "figure_3_endpoint_performance.svg",
        "figure_4_louisiana_decoupling.svg",
        "fresh_endpoint_results.csv",
        "generation_manifest.json",
        "methods_results_core.md",
        "submission_boundary.json",
    }
    assert {path.name for path in output.iterdir()} == expected

    boundary = json.loads((output / "submission_boundary.json").read_text())
    assert boundary["fresh_predictive_endpoints_with_scores"] == 3
    assert boundary["favorable_endpoints"] == 2
    assert boundary["adverse_endpoints"] == 1
    assert boundary["scientific_protocol_stops"] == 31
    assert boundary["administrative_exclusions"] == 3
    assert boundary["candidate_hunting_hard_stop"] is True
    assert boundary["fourth_fresh_endpoint_allowed"] is False
    assert boundary["product_boundary"] == "structural_diagnostic_plus_context_dependent_predictive_complement"
    assert boundary["primary_submission_route"] == "Methods in Ecology and Evolution"
    assert boundary["nature_ecology_evolution_trigger_open"] is False


def test_endpoint_table_preserves_favorable_favorable_adverse_pattern(tmp_path: Path) -> None:
    output = tmp_path / "paper"
    subprocess.run([sys.executable, str(BUILDER), "--output-dir", str(output)], cwd=ROOT, check=True)
    with (output / "fresh_endpoint_results.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["issue"]) for row in rows] == [289, 292, 388]
    assert [row["terminal_status"] for row in rows] == [
        "favorable_complementary_added_value",
        "favorable_complementary_added_value",
        "adverse_complementary_added_value",
    ]
    assert float(rows[0]["augmented_minus_baseline"]) < 0
    assert float(rows[1]["augmented_minus_baseline"]) < 0
    assert float(rows[2]["augmented_minus_baseline"]) > 0


def test_candidate_flow_keeps_stops_and_admin_outside_predictive_denominator(tmp_path: Path) -> None:
    output = tmp_path / "paper"
    subprocess.run([sys.executable, str(BUILDER), "--output-dir", str(output)], cwd=ROOT, check=True)
    with (output / "candidate_flow_table.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    classes = [row["classification"] for row in rows]
    assert classes.count("predictive_result") == 3
    assert classes.count("scientific_protocol_stop") == 31
    assert classes.count("administrative_exclusion") == 3
    assert len(rows) == 37
    assert sum(row["counts_as_predictive_evidence"] == "True" for row in rows) == 3

    with (output / "candidate_funnel_summary.csv").open(newline="", encoding="utf-8") as handle:
        stage_rows = list(csv.DictReader(handle))
    assert sum(int(row["scientific_stop_count"]) for row in stage_rows) == 31


def test_manuscript_core_reports_tampa_placebo_without_rescuing_primary_result(tmp_path: Path) -> None:
    output = tmp_path / "paper"
    subprocess.run([sys.executable, str(BUILDER), "--output-dir", str(output)], cwd=ROOT, check=True)
    text = (output / "methods_results_core.md").read_text(encoding="utf-8")
    assert "Azores yellow eel telemetry" in text
    assert "Southwest Louisiana King Rail" in text
    assert "Tampa Bay seagrass monitoring" in text
    assert "31 scientific/protocol STOPs" in text
    assert "0% of placebo replicates" in text
    assert "does not rescue" in text
    assert "structural_diagnostic_plus_context_dependent_predictive_complement" in text
    assert "does not support universal predictive superiority" in text


def test_figures_and_manifest_are_deterministic_and_audited(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        subprocess.run([sys.executable, str(BUILDER), "--output-dir", str(output)], cwd=ROOT, check=True)

    figure_names = [
        "figure_1_two_layer_architecture.svg",
        "figure_2_candidate_funnel.svg",
        "figure_3_endpoint_performance.svg",
        "figure_4_louisiana_decoupling.svg",
    ]
    for name in figure_names:
        assert (first / name).read_bytes() == (second / name).read_bytes()
        text = (first / name).read_text(encoding="utf-8")
        assert text.startswith("<svg")
        assert "font-family" in text

    manifest = json.loads((first / "generation_manifest.json").read_text())
    assert set(manifest["inputs"]) == {
        "validation/paper_ready_replication/candidate_flow_ledger.json",
        "validation/paper_ready_replication/observed_endpoint3_synthesis.json",
        "validation/tampa_seagrass_endpoint3/terminal_predictive_result_certificate.json",
    }
    for name, digest in manifest["outputs"].items():
        assert digest == _sha256(first / name)
