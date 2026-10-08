"""End-to-end guarantees for the unapproved, result-neutral author review archive."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "manuscript" / "inferential_openness" / "build_review_bundle_v1.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("inferential_review_builder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_author_review_bundle_is_complete_gated_and_deterministic(tmp_path):
    builder = load_builder()
    zip1, receipt1 = builder.build_review_bundle(tmp_path / "a")
    zip2, receipt2 = builder.build_review_bundle(tmp_path / "b")
    assert hashlib.sha256(zip1.read_bytes()).hexdigest() == hashlib.sha256(zip2.read_bytes()).hexdigest()
    assert receipt1.read_bytes() == receipt2.read_bytes()
    manifest = json.loads(receipt1.read_text(encoding="utf-8"))
    assert manifest["source_commit"] == "local-review"
    assert manifest["submission_ready"] is False
    assert manifest["all_author_approved"] is False
    assert manifest["archival_doi"] is None
    assert manifest["ecological_results_reestimated"] is False
    assert manifest["denominator"] == {
        "scientific_attempts": 34,
        "stops": 31,
        "scored_endpoints": 3,
        "administrative_exclusions": 3,
    }
    assert manifest["stop_label_count"] == 21

    with zipfile.ZipFile(zip1) as archive:
        names = set(archive.namelist())
        assert len(names) == len(manifest["files_sha256"]) + 1
        assert "BUNDLE_MANIFEST.json" in names
        for name, digest in manifest["files_sha256"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        assert json.loads(archive.read("BUNDLE_MANIFEST.json")) == manifest
        assert "manuscript/MANUSCRIPT_DRAFT_V2.md" in names
        assert "manuscript/FIGURE_LEGENDS_V1.md" in names
        assert "manuscript/TITLE_PAGE_TEMPLATE_V1.md" in names
        assert "manuscript/AI_ASSISTANCE_DECLARATION_AUTHOR_REVIEW.template.md" in names
        assert "provenance/CROSS_PROJECT_EVIDENCE_LEDGER_V2.json" in names
        assert "provenance/candidate_flow_table.csv" in names
        assert "supplementary/supplementary_table_S1_terminal_stops.csv" in names
        assert "supplementary/supplementary_figure_S1_terminal_taxonomy.svg" in names
        assert "figures/graphical_abstract_inferential_openness.svg" in names
        assert len([name for name in names if name.startswith("figures/figure") and name.endswith(".svg")]) == 4
        assert b"NOT an approved journal submission" in archive.read(
            "README_AUTHOR_REVIEW_NOT_SUBMISSION_READY.md"
        )
        assert "[Author 1]" in archive.read("manuscript/TITLE_PAGE_TEMPLATE_V1.md").decode()
        assert "no DOI is assigned here" in archive.read("manuscript/MANUSCRIPT_DRAFT_V2.md").decode()
        dates = {file.date_time for file in archive.infolist()}
        assert dates == {(1980, 1, 1, 0, 0, 0)}


def test_frozen_blob_sha_is_git_compatible_and_source_pins_match():
    builder = load_builder()
    assert builder.git_blob_sha(b"test content\n") == hashlib.sha1(b"blob 13\0test content\n").hexdigest()
    ledger, stops = builder.inspect_frozen_inputs()
    assert len(stops) == 31
    assert ledger["sources"]["284b"]["calibration_audit"]["blob_sha"]
    assert ledger["sources"]["eog"]["candidate_flow_table"]["blob_sha"]
