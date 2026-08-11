from __future__ import annotations

import csv
import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "figures/build_figure_3_tanzania.py"


def builder():
    spec = importlib.util.spec_from_file_location("figure3", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tmp(tmp_path: Path):
    b = builder()
    out = tmp_path / "out"
    data = tmp_path / "data"
    caption = tmp_path / "caption.md"
    alt = tmp_path / "alt.md"
    outputs = b.build(
        output_dir=out,
        data_dir=data,
        caption_path=caption,
        accessibility_path=alt,
        build_timestamp="2026-08-11T02:30:00Z",
    )
    return b, outputs, data, caption, alt


def test_all_species_and_frozen_contrasts_are_retained(tmp_path: Path) -> None:
    _, outputs, data, caption, alt = run_tmp(tmp_path)
    species = list(csv.DictReader((data / "tanzania_species_loso_effects.csv").open(newline="", encoding="utf-8")))
    contrasts = list(csv.DictReader((data / "tanzania_aggregate_contrasts.csv").open(newline="", encoding="utf-8")))
    applicability = list(csv.DictReader((data / "tanzania_applicability.csv").open(newline="", encoding="utf-8")))
    assert len(species) == 60
    assert sum(r["direction"] == "favourable" for r in species) == 17
    assert sum(r["direction"] == "adverse" for r in species) == 43
    assert len(contrasts) == 4
    assert [r["interval_class"] for r in contrasts] == ["adverse", "adverse", "uncertain", "uncertain"]
    assert [int(r["matched_rows_per_weighting"]) for r in applicability] == [826, 718]
    assert [int(r["invalid_rows_per_weighting"]) for r in applicability] == [14, 122]
    root = ET.fromstring(outputs["svg"].read_text())
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert len(root.findall('.//svg:circle[@class="species-point"]', ns)) == 60
    assert len(root.findall('.//svg:circle[@class="aggregate-point"]', ns)) == 4
    assert "negative values favour EOG" in caption.read_text()
    assert "both spatial-block intervals cross zero" in alt.read_text().lower()


def test_committed_outputs_reproduce_exactly(tmp_path: Path) -> None:
    _, outputs, data, caption, alt = run_tmp(tmp_path)
    pairs = [
        (outputs["svg"], ROOT / "figures/output/figure_3_tanzania.svg"),
        (caption, ROOT / "manuscript/figure_3_caption.md"),
        (alt, ROOT / "manuscript/figure_3_accessibility.md"),
        (data / "tanzania_species_loso_effects.csv", ROOT / "manuscript/figure_data/tanzania_species_loso_effects.csv"),
        (data / "tanzania_aggregate_contrasts.csv", ROOT / "manuscript/figure_data/tanzania_aggregate_contrasts.csv"),
        (data / "tanzania_applicability.csv", ROOT / "manuscript/figure_data/tanzania_applicability.csv"),
    ]
    for regenerated, committed in pairs:
        assert regenerated.read_bytes() == committed.read_bytes()


def test_species_source_sha_gate_rejects_tampering(tmp_path: Path) -> None:
    b = builder()
    source = ROOT / "benchmarks/tanzania_heldout_species_expected.csv"
    tampered = tmp_path / "species.csv"
    text = source.read_text()
    tampered.write_text(text + "\n")
    with pytest.raises(b.FigureContractError, match="species table SHA"):
        b.build(
            species_source_path=tampered,
            output_dir=tmp_path / "out",
            data_dir=tmp_path / "data",
            caption_path=tmp_path / "caption.md",
            accessibility_path=tmp_path / "alt.md",
        )


def test_plotting_code_has_no_frozen_effect_literals() -> None:
    source = SCRIPT.read_text()
    for literal in ("0.032113119", "0.030629623", "0.010953824", "0.005701619"):
        assert literal not in source


def test_metadata_preserves_verified_fingerprint(tmp_path: Path) -> None:
    _, outputs, *_ = run_tmp(tmp_path)
    metadata = json.loads(outputs["metadata"].read_text())
    frozen = json.loads((ROOT / "benchmarks/tanzania_heldout_expected.json").read_text())
    assert metadata["source"]["result_fingerprint"] == frozen["expected_projection"]["result_fingerprint"]
    assert metadata["derived"] == {
        "aggregate_contrasts": 4,
        "species_adverse": 43,
        "species_displayed": 60,
        "species_equal": 0,
        "species_favourable": 17,
    }
