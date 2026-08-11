from __future__ import annotations

import importlib.util
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "figures/build_figure_1_roles.py"
CONTRACT = ROOT / "figures/figure_1_roles.json"
MANIFEST = ROOT / "figures/figure_manifest.json"


def load_builder():
    spec = importlib.util.spec_from_file_location("eog_figure1", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_matches_competitor_matrix_and_panel_order():
    module = load_builder()
    contract, competitor_path = module.validate_contract(CONTRACT)
    assert [panel["id"] for panel in contract["panels"]] == ["A", "B", "C", "D", "E"]
    assert module.git_blob_sha1(competitor_path) == contract["competitor_matrix_git_blob_sha1"]
    assert contract["design_constraints"] == {
        "movement_arrows": False,
        "shared_effect_axis": False,
        "empirical_effect_sizes": False,
        "causal_ordering": False,
    }


def test_svg_is_conceptual_and_contains_no_arrow_markers():
    module = load_builder()
    contract, _ = module.validate_contract(CONTRACT)
    svg = module.render_svg(contract)
    assert "marker-end" not in svg
    assert "marker-start" not in svg
    for panel in contract["panels"]:
        assert panel["title"] in svg
        for wrapped_line in module.wrap(panel["question"], 45):
            assert wrapped_line in svg
    assert "No panel is a movement, dispersal, or colonisation probability." in svg
    assert "0.617" not in svg
    assert "+0.022" not in svg


def test_build_writes_parseable_reproducible_outputs(tmp_path: Path):
    module = load_builder()
    out_dir = tmp_path / "output"
    caption = tmp_path / "caption.md"
    accessibility = tmp_path / "accessibility.md"
    metadata = module.build(CONTRACT, out_dir, caption, accessibility)

    svg_path = out_dir / "figure_1_roles.svg"
    metadata_path = out_dir / "figure_1_metadata.json"
    ET.parse(svg_path)
    on_disk = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert on_disk == metadata
    assert metadata["conceptual_only"] is True
    assert metadata["movement_arrows"] is False
    assert metadata["empirical_effect_sizes"] is False
    assert metadata["svg_sha256"] == module.sha256(svg_path)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["figure_1_roles"]
    assert manifest["conceptual_only"] is True
    assert manifest["required_panel_ids"] == metadata["panel_ids"]
    assert manifest["expected"]["contract_sha256"] == metadata["contract_sha256"]
    assert manifest["expected"]["competitor_matrix_git_blob_sha1"] == metadata["competitor_matrix_git_blob_sha1"]
    assert manifest["expected"]["svg_sha256"] == metadata["svg_sha256"]
    assert manifest["expected"]["movement_arrows"] is False
    assert manifest["expected"]["empirical_effect_sizes"] is False

    assert "deliberately non-sequential" in caption.read_text(encoding="utf-8")
    assert "no arrows are used to imply movement" in accessibility.read_text(encoding="utf-8")


def test_competitor_matrix_fingerprint_is_a_hard_gate(tmp_path: Path):
    module = load_builder()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["competitor_matrix_git_blob_sha1"] = "0" * 40
    altered = tmp_path / "figure_1_roles.json"
    altered.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(module.FigureContractError, match="fingerprint changed"):
        module.validate_contract(altered)


def test_prohibited_probability_claim_is_rejected(tmp_path: Path):
    module = load_builder()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["panels"][4]["role"] += " It is a movement probability."
    altered = tmp_path / "figure_1_roles.json"
    altered.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(module.FigureContractError, match="prohibited implication"):
        module.validate_contract(altered)
