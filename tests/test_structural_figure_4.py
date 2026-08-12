from __future__ import annotations

import csv
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "figures/build_figure_4_boundary.py"
STRONG = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json"


def builder():
    spec = importlib.util.spec_from_file_location("figure4", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tmp(tmp_path: Path):
    b = builder()
    data = tmp_path / "data.csv"
    caption = tmp_path / "caption.md"
    alt = tmp_path / "alt.md"
    outputs = b.build(
        panel_data_path=data,
        output_dir=tmp_path / "out",
        caption_path=caption,
        accessibility_path=alt,
        build_timestamp="2026-08-12T08:40:00Z",
    )
    return b, outputs, data, caption, alt


def test_frozen_values_and_three_separate_axes(tmp_path: Path) -> None:
    b, outputs, data, caption, alt = run_tmp(tmp_path)
    rows = list(csv.DictReader(data.open(newline="", encoding="utf-8")))
    assert [r["benchmark_id"] for r in rows] == ["A_ISLANDS_ORIGINAL", "A_ISLANDS_STRONG", "TANZANIA"]
    a = json.loads((ROOT / "benchmarks/aislands_authoritative_expected.json").read_text())
    strong = json.loads(STRONG.read_text())
    t = json.loads((ROOT / "benchmarks/tanzania_heldout_expected.json").read_text())
    tprimary = t["expected_projection"]["contrasts"]["primary::primary_loso"]
    assert float(rows[0]["effect"]) == pytest.approx(a["overall_conditional_concordance"])
    assert float(rows[1]["effect"]) == pytest.approx(strong["primary"]["species_macro_mean"])
    assert rows[1]["source_fingerprint"] == strong["result_fingerprint"]
    assert float(rows[2]["effect"]) == pytest.approx(tprimary["macro_mean_species_log_loss_difference"])
    assert rows[2]["source_fingerprint"] == t["expected_projection"]["result_fingerprint"]
    svg = outputs["svg"].read_text()
    ET.fromstring(svg)
    assert "own metric scale" in svg
    assert "No predictive increment beyond R3" in svg
    assert "No incremental benefit beyond current flow" in svg
    assert all(term not in svg.lower() for term in b.PROHIBITED_TERMS)
    metadata = json.loads(outputs["metadata"].read_text())
    assert metadata["metrics_share_axis"] is False
    assert metadata["row_count"] == 3
    assert metadata["sources"]["aislands_original"]["workflow_run_id"] == 31251171516
    assert metadata["sources"]["aislands_strong_reference"]["result_fingerprint"] == b.AIS_STRONG_FP
    assert "Each row uses its own endpoint" in caption.read_text()
    assert "separate scales" in alt.read_text().lower()


def test_committed_outputs_reproduce(tmp_path: Path) -> None:
    _, outputs, data, caption, alt = run_tmp(tmp_path)
    assert data.read_bytes() == (ROOT / "manuscript/figure_data/structural_cross_system_evidence.csv").read_bytes()
    assert outputs["svg"].read_bytes() == (ROOT / "figures/output/figure_4_boundary.svg").read_bytes()
    assert caption.read_bytes() == (ROOT / "manuscript/figure_4_caption.md").read_bytes()
    assert alt.read_bytes() == (ROOT / "manuscript/figure_4_accessibility.md").read_bytes()


def test_aislands_sha_gate_rejects_tampering(tmp_path: Path) -> None:
    b = builder()
    source = json.loads((ROOT / "benchmarks/aislands_authoritative_expected.json").read_text())
    source["overall_conditional_concordance"] += 0.001
    tampered = tmp_path / "a.json"
    tampered.write_text(json.dumps(source))
    with pytest.raises(b.FigureContractError, match="SHA"):
        b.build(
            aislands_path=tampered,
            panel_data_path=tmp_path / "d.csv",
            output_dir=tmp_path / "o",
            caption_path=tmp_path / "c.md",
            accessibility_path=tmp_path / "a.md",
        )


def test_plot_code_has_no_frozen_effect_literals() -> None:
    source = SCRIPT.read_text()
    for literal in ("0.617746592", "0.003485182", "0.032113119", "0.608680609", "0.004508216"):
        assert literal not in source
