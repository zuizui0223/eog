from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "manuscript" / "build_structural_submission_package.py"
SUBMISSION_MANIFEST = ROOT / "manuscript" / "submission" / "submission_manifest.json"


def builder():
    spec = importlib.util.spec_from_file_location("structural_submission_package", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_submission_package_rebuilds_and_verifies_frozen_assets(tmp_path: Path) -> None:
    module = builder()
    output = tmp_path / "submission"
    manifest = module.build(output)
    assert manifest["offline_build"] is True
    assert manifest["network_required"] is False
    assert manifest["scientific_assets_verified_against_committed_outputs"] is True
    assert manifest["aislands"]["declared_taxa"] == 886
    assert manifest["aislands"]["estimable_taxa"] == 845
    assert abs(manifest["aislands"]["conditional_concordance"] - 0.6177465917820878) < 1e-15
    assert manifest["tanzania"]["species"] == 60
    assert manifest["tanzania"]["result_fingerprint"] == "6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4"
    assert abs(manifest["tanzania"]["primary_loso_log_loss_difference"] - 0.032113119) < 1e-12
    assert len(manifest["files"]) >= 35
    for relative in (
        "figures/output/figure_1_roles.svg",
        "figures/output/figure_2_aislands.svg",
        "figures/output/figure_3_tanzania.svg",
        "figures/output/figure_4_boundary.svg",
        "figures/output/figure_5_audit.svg",
        "manuscript/result_tables/table_3_main_sensitivity_results.csv",
        "manuscript/result_tables/table_s1_applicability_accounting.csv",
        "manuscript/structural_reachability_manuscript.md",
        "manuscript/submission/cover_letter.md",
    ):
        assert (output / relative).is_file(), relative
    generated_manifest = json.loads((output / "submission_package_manifest.json").read_text(encoding="utf-8"))
    assert generated_manifest == manifest


def test_submission_package_is_repeatable_within_one_environment(tmp_path: Path) -> None:
    module = builder()
    output = tmp_path / "submission"
    first = module.build(output)
    second = module.build(output)
    assert first["source_commit"] == second["source_commit"]
    assert first["files"] == second["files"]


def test_submission_facing_files_preserve_positive_and_negative_boundary() -> None:
    manifest = json.loads(SUBMISSION_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["frozen_evidence"]["aislands_direction"].startswith("positive")
    assert manifest["frozen_evidence"]["tanzania_primary_direction"].startswith("adverse")
    assert manifest["frozen_evidence"]["tanzania_spatial_block_direction"].startswith("uncertain")
    cover = (ROOT / manifest["cover_letter"]).read_text(encoding="utf-8")
    assert "0.618" in cover and "0.609–0.627" in cover
    assert "increased leave-one-fragment-out log loss by 0.032" in cover
    assert "spatial-block sensitivity was smaller and uncertain" in cover
    assert "universal-superiority" in cover
    for prohibited in (
        "EOG outperforms SDM",
        "connected frequency estimates colonisation probability",
        "Tanzania shows current flow is better in general",
    ):
        assert prohibited not in cover


def test_release_and_author_placeholders_remain_explicit_blockers() -> None:
    availability = (ROOT / "manuscript/submission/data_code_availability.md").read_text(encoding="utf-8")
    declarations = (ROOT / "manuscript/submission/declarations.md").read_text(encoding="utf-8")
    cover = (ROOT / "manuscript/submission/cover_letter.md").read_text(encoding="utf-8")
    for token in ("<RELEASE_TAG>", "<ARCHIVE_DOI>", "<RELEASE_COMMIT>"):
        assert token in availability
    assert "AUTHOR CONFIRMATION REQUIRED" in declarations
    assert "<CORRESPONDING_AUTHOR_NAME>" in cover
    assert "<AFFILIATION>" in cover
    assert "<EMAIL>" in cover


def test_package_builder_has_no_source_acquisition_or_http_client() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    for token in ("requests.", "urllib.request", "httpx.", "aiohttp", "fetch_aislands", "fetch_tanzania"):
        assert token not in source
    assert "network_required\": False" in source
