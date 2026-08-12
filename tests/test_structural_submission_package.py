from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "manuscript" / "build_structural_submission_package.py"
SUBMISSION_MANIFEST = ROOT / "manuscript" / "submission" / "submission_manifest.json"
MANUSCRIPT = ROOT / "manuscript" / "structural_reachability_manuscript.md"
HIGHLIGHTS = ROOT / "manuscript" / "structural_highlights.txt"
AIS_STRONG_FP = "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"
TANZANIA_FP = "6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4"


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
    assert manifest["schema_version"] == "eog_structural_submission_package_v2"
    assert manifest["offline_build"] is True
    assert manifest["network_required"] is False
    assert manifest["scientific_assets_verified_against_committed_outputs"] is True
    assert manifest["aislands"]["declared_taxa"] == 886
    assert manifest["aislands"]["estimable_taxa"] == 845
    assert abs(manifest["aislands"]["conditional_concordance"] - 0.6177465917820878) < 1e-15
    strong = manifest["aislands_strong_reference"]
    assert strong["taxa"] == 886
    assert strong["evaluable_folds"] == 4231
    assert strong["heldout_predictions"] == 712515
    assert abs(strong["c_minus_r3_log_loss_difference"] - 0.003485181598265469) < 1e-15
    assert strong["species_favourable"] == 341
    assert strong["species_adverse"] == 545
    assert strong["result_fingerprint"] == AIS_STRONG_FP
    assert strong["workflow_run_id"] == 31564146592
    assert strong["rerun_allowed"] is False
    assert manifest["tanzania"]["species"] == 60
    assert manifest["tanzania"]["result_fingerprint"] == TANZANIA_FP
    assert abs(manifest["tanzania"]["primary_loso_log_loss_difference"] - 0.032113119) < 1e-12
    assert len(manifest["files"]) >= 42
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
        "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json",
        "validation/aislands_isolation_adequacy_20260812/authoritative_execution_provenance.json",
        "validation/aislands_isolation_adequacy_20260812/authoritative_outcome_qa.json",
    ):
        assert (output / relative).is_file(), relative
    generated_manifest = json.loads((output / "submission_package_manifest.json").read_text(encoding="utf-8"))
    assert generated_manifest == manifest
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", generated_manifest["source_commit"])


def test_submission_package_is_repeatable_within_one_environment(tmp_path: Path) -> None:
    module = builder()
    output = tmp_path / "submission"
    first = module.build(output)
    second = module.build(output)
    assert first["source_commit"] == second["source_commit"]
    assert first["files"] == second["files"]
    assert first["aislands_strong_reference"] == second["aislands_strong_reference"]


def test_complete_manuscript_submission_metadata_is_frozen_under_working_limits() -> None:
    manifest = json.loads(SUBMISSION_MANIFEST.read_text(encoding="utf-8"))
    text = MANUSCRIPT.read_text(encoding="utf-8")
    lines = text.splitlines()
    heading = lines[0].removeprefix("# ").strip()
    subtitle = next(line for line in lines[1:5] if line.startswith("**") and line.endswith("**")).strip("*")
    assert f"{heading} {subtitle}" == manifest["title"]
    assert manifest["target_journal"] == "Ecological Informatics"
    assert manifest["article_type"] == "Original Research Paper"
    match = re.search(r"^## Abstract\s*$\n(.*?)(?=^\*\*Keywords:\*\*)", text, flags=re.MULTILINE | re.DOTALL)
    assert match is not None
    abstract_words = re.findall(r"\b[\w’'-]+\b", match.group(1), flags=re.UNICODE)
    assert 150 <= len(abstract_words) <= 250
    keyword_match = re.search(r"^\*\*Keywords:\*\*\s*(.+)$", text, flags=re.MULTILINE)
    assert keyword_match is not None
    keywords = [item.strip() for item in keyword_match.group(1).split(";")]
    assert 5 <= len(keywords) <= 10
    highlights = [line.strip() for line in HIGHLIGHTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert 3 <= len(highlights) <= 5
    assert all(len(line) <= 85 for line in highlights)


def test_submission_facing_files_preserve_all_reference_boundaries() -> None:
    manifest = json.loads(SUBMISSION_MANIFEST.read_text(encoding="utf-8"))
    frozen = manifest["frozen_evidence"]
    assert frozen["aislands_original_direction"].startswith("positive")
    assert frozen["aislands_strong_reference_direction"].startswith("adverse")
    assert frozen["aislands_strong_reference_result_fingerprint"] == AIS_STRONG_FP
    assert frozen["tanzania_primary_direction"].startswith("adverse")
    assert frozen["tanzania_spatial_block_direction"].startswith("uncertain")
    cover = (ROOT / manifest["cover_letter"]).read_text(encoding="utf-8")
    assert "0.618" in cover and "0.609–0.627" in cover
    assert "increased held-out log loss by 0.00349" in cover
    assert "341 species" in cover and "545 were adverse" in cover
    assert "increased primary leave-one-fragment-out log loss by 0.032" in cover
    assert "spatial-block sensitivity was smaller and uncertain" in cover
    for prohibited in (
        "EOG outperforms SDM",
        "connected frequency estimates colonisation probability",
        "Tanzania shows current flow is better in general",
        "R3 causally explains the original A-Islands",
    ):
        assert prohibited not in cover


def test_release_and_author_placeholders_remain_explicit_blockers_without_sha_self_reference() -> None:
    availability = (ROOT / "manuscript/submission/data_code_availability.md").read_text(encoding="utf-8")
    declarations = (ROOT / "manuscript/submission/declarations.md").read_text(encoding="utf-8")
    cover = (ROOT / "manuscript/submission/cover_letter.md").read_text(encoding="utf-8")
    for token in ("<RELEASE_TAG>", "<ARCHIVE_DOI>"):
        assert token in availability
    assert "<RELEASE_COMMIT>" not in availability
    assert "submission_package_manifest.json" in availability
    assert "exact source Git commit" in availability
    assert "AUTHOR CONFIRMATION REQUIRED" in declarations
    assert "<CORRESPONDING_AUTHOR_NAME>" in cover
    assert "<AFFILIATION>" in cover
    assert "<EMAIL>" in cover


def test_package_builder_has_no_source_acquisition_or_http_client() -> None:
    source = BUILDER.read_text(encoding="utf-8")
    for token in ("requests.", "urllib.request", "httpx.", "aiohttp", "fetch_aislands", "fetch_tanzania"):
        assert token not in source
    assert "network_required\": False" in source
    assert "AIS_STRONG_FINGERPRINT" in source
