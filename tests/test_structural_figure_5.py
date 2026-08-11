from __future__ import annotations

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "figures/build_figure_5_audit.py"
CONTRACT = ROOT / "figures/figure_5_audit_contract.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("eog_figure5", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_and_audit_rows_are_frozen():
    module = load_builder()
    contract, figure_manifest, result_manifest, result_metadata = module.validate_contract(CONTRACT)
    records = module.build_records(contract, figure_manifest, result_manifest, result_metadata)
    assert [record["id"] for record in records] == ["F1", "F2", "F3", "F4", "T3"]
    assert all(len(record["result_sha256"]) == 64 for record in records)
    assert result_metadata["tanzania_result_fingerprint"] == figure_manifest["figure_3_tanzania"]["expected"]["result_fingerprint"]
    assert result_metadata["aislands_species_output_sha256"] == figure_manifest["figure_2_aislands"]["expected"]["primary_species_table_sha256"]


def test_svg_contains_no_movement_or_causal_arrow_markers():
    module = load_builder()
    contract, figure_manifest, result_manifest, result_metadata = module.validate_contract(CONTRACT)
    records = module.build_records(contract, figure_manifest, result_manifest, result_metadata)
    svg = module.render_svg(contract, records)
    assert "marker-end" not in svg
    assert "marker-start" not in svg
    assert "No new model fit, effect size, hypothesis test, movement route, or causal ordering" in svg
    assert "0.617" not in svg
    assert "0.032" not in svg


def test_build_writes_parseable_svg_and_fingerprinted_metadata(tmp_path: Path):
    module = load_builder()
    out = tmp_path / "output"
    caption = tmp_path / "caption.md"
    alt = tmp_path / "accessibility.md"
    metadata = module.build(CONTRACT, out, caption, alt)
    svg = out / "figure_5_audit.svg"
    ET.parse(svg)
    assert metadata["svg_sha256"] == module.sha256(svg)
    assert metadata["new_effect_sizes"] is False
    assert metadata["new_hypothesis_tests"] is False
    assert metadata["movement_arrows"] is False
    assert metadata["causal_arrows"] is False
    assert len(metadata["rows"]) == 5
    assert "provenance and rebuildability only" in caption.read_text(encoding="utf-8")
    assert "no movement or causal arrows" in alt.read_text(encoding="utf-8")


def test_table_fingerprint_mismatch_is_rejected(tmp_path: Path):
    module = load_builder()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fake = tmp_path / "fake_table.csv"
    fake.write_text("changed\n", encoding="utf-8")
    contract["rows"][4]["result_path"] = str(fake.relative_to(ROOT)) if ROOT in fake.parents else "missing/fake_table.csv"
    altered = tmp_path / "contract.json"
    altered.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(module.AuditContractError):
        c, fm, rm, md = module.validate_contract(altered)
        module.build_records(c, fm, rm, md)


def test_figure1_svg_is_pinned_by_shared_manifest():
    module = load_builder()
    contract, figure_manifest, result_manifest, result_metadata = module.validate_contract(CONTRACT)
    records = module.build_records(contract, figure_manifest, result_manifest, result_metadata)
    f1 = next(record for record in records if record["id"] == "F1")
    assert f1["result_sha256"] == figure_manifest["figure_1_roles"]["expected"]["svg_sha256"]
