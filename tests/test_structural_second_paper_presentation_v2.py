from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_committed_assets_match(assets: dict[str, str]) -> None:
    for relative, text in assets.items():
        path = ROOT / relative
        assert path.is_file(), f"generated presentation asset is not committed: {relative}"
        assert path.read_text(encoding="utf-8") == text, f"committed presentation asset drift: {relative}"


def test_second_paper_boundary_is_separate_from_eog_wf():
    boundary = json.loads((ROOT / "manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json").read_text())
    assert boundary["status"] == "scientific_content_closed_presentation_release_active"
    non_overlap = boundary["non_overlap_with_eog_wf_paper"]
    assert non_overlap["structural_paper_empirical_denominator_is_separate"] is True
    assert non_overlap["structural_paper_does_not_use_eog_wf_three_endpoint_denominator"] is True
    assert non_overlap["ncrn_post_closure_programme_excluded"] is True


def test_reference_conditioned_figure1_is_deterministic_and_bounded():
    module = load_module("figures/build_figure_1_reference_conditioned.py", "fig1_ref_v2")
    a = module.build_assets()
    b = module.build_assets()
    assert a == b
    assert_committed_assets_match(a)
    svg = a["figures/output/figure_1_reference_conditioned.svg"]
    meta = json.loads(a["figures/output/figure_1_reference_conditioned_metadata.json"])
    assert "Declare the reference R" in svg
    assert "Score C relative to R" in svg
    assert "EARNED" in svg and "ADVERSE" in svg and "INDETERMINATE" in svg
    assert meta["conceptual_only"] is True
    assert meta["movement_probability"] is False
    assert meta["separate_from_eog_wf_empirical_denominator"] is True


def test_aislands_dual_endpoint_figure_keeps_metrics_separate():
    module = load_module("figures/build_figure_2_aislands_reference_conditioned.py", "fig2_ref_v2")
    a = module.build_assets()
    b = module.build_assets()
    assert a == b
    assert_committed_assets_match(a)
    svg = a["figures/output/figure_2_aislands_reference_conditioned.svg"]
    meta = json.loads(a["figures/output/figure_2_aislands_reference_conditioned_metadata.json"])
    assert "Restricted reference: conditional ordering" in svg
    assert "Rich R3 reference: incremental predictive value" in svg
    assert "Primary extension contrast: C − R3 only" in svg
    assert meta["metrics_share_axis"] is False
    assert meta["common_effect_claim"] is False
    assert meta["movement_probability"] is False
    assert meta["strong_result_fingerprint"] == "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"
    assert meta["original_direction_counts"] == {"above": 672, "equal": 42, "below": 131, "not_estimable": 41}


def test_structural_package_v2_uses_new_canonical_figures(tmp_path):
    module = load_module("manuscript/build_structural_submission_package_v2.py", "structural_package_v2")
    receipt = module.build(tmp_path / "pkg")
    assert receipt["schema"] == "eog.structural_submission_package.v3"
    assert receipt["scientific_evidence_rebuilt_by_v1_builder"] is True
    assert receipt["presentation_only_v2_figures"] == ["figure_1", "figure_2"]
    assert receipt["metrics_share_axis_in_aislands_figure"] is False
    assert receipt["eog_wf_empirical_denominator_included"] is False
    assert receipt["canonical_submission_figures"]["figure_1"].endswith("figure_1_reference_conditioned.svg")
    assert receipt["canonical_submission_figures"]["figure_2"].endswith("figure_2_aislands_reference_conditioned.svg")
