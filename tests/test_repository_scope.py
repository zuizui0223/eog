"""Regression tests: EOG must not re-adopt migrated biological manuscripts.

This checks repository ownership, not ecological outcomes or numeric scores.
No network access, dataset fetching, or re-scoring is performed.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "REPOSITORY_SCOPE_POLICY_V1.json"


def _policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def test_migrated_experiment_source_directories_stay_absent():
    p = _policy()
    for prefix in p["disallowed_prefixes"]:
        assert not (ROOT / prefix).exists(), f"biological source ownership reverted: {prefix}"


def test_archived_biological_scripts_and_workflows_stay_outside_eog():
    patterns = [re.compile(pattern) for pattern in _policy()["disallowed_biological_script_regexes"]]
    for base in ("benchmarks", "tests", "scripts", ".github/workflows"):
        directory = ROOT / base
        if not directory.is_dir():
            continue
        for file in directory.rglob("*"):
            if not file.is_file():
                continue
            rel = file.relative_to(ROOT).as_posix()
            assert not any(pattern.fullmatch(rel) for pattern in patterns), rel


def test_manuscript_lanes_are_explicitly_declared():
    allowed = set(_policy()["allowed_manuscript_subdirectories"])
    found = {f.name for f in (ROOT / "manuscript").iterdir() if f.is_dir() and not f.name.startswith("__") and not f.name.startswith(".")}
    assert found <= allowed, f"new manuscript lane lacks a repository owner: {sorted(found - allowed)}"


def test_neon_paper_filenames_are_link_only_and_not_an_active_manuscript():
    for prefix, owner in _policy()["legacy_redirect_only"].items():
        folder = ROOT / prefix
        assert folder.is_dir(), f"legacy entry point unexpectedly removed: {prefix}"
        for path in folder.iterdir():
            assert path.is_file() and path.suffix == ".md", (
                f"active biology-only asset in EOG: {path.relative_to(ROOT)}"
            )
            data = path.read_text(encoding="utf-8")
            assert owner in data and "SUBMISSION HOLD" in data
            assert "archive/eog_legacy_neon_20261122/" in data
            assert len(data.encode("utf-8")) < 2048, (
                f"historical biology paper restored in place: {path.relative_to(ROOT)}"
            )


def test_knk_biology_documents_are_redirects_only():
    p = _policy()
    seen = 0
    for glob in p["knk_doc_stub_globs"]:
        for path in ROOT.glob(glob):
            seen += 1
            data = path.read_text(encoding="utf-8")
            assert "https://github.com/zuizui0223/knk" in data
            assert len(data.encode("utf-8")) < 2048, path.relative_to(ROOT)
    assert seen >= 20, "KNK historical doc pointers unexpectedly disappeared"


def test_method_cores_and_evidence_denominator_are_retained():
    p = _policy()
    for path in p["method_cores"]:
        assert (ROOT / path).is_file(), f"reusable methods implementation missing: {path}"
    result = (ROOT / "docs/result_inventory/EMPIRICAL_RESULTS.md").read_text(encoding="utf-8")
    assert "3 scored" in result
    assert "31 scientific" in result
    assert "3 administrative" in result
    assert "2 favorable" in result and "1 adverse" in result
    assert (ROOT / "docs/REPOSITORY_BOUNDARY.md").is_file()
