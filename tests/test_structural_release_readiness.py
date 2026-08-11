from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
RELEASE = ROOT / "manuscript/submission/release_readiness.md"
AVAILABILITY = ROOT / "manuscript/submission/data_code_availability.md"
SUBMISSION_MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"
PACKAGE_BUILDER = ROOT / "manuscript/build_structural_submission_package.py"


def project_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', text, flags=re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_candidate_release_tag_matches_package_version() -> None:
    version = project_version()
    release = RELEASE.read_text(encoding="utf-8")
    assert version == "0.1.0"
    assert f"`v{version}`" in release
    assert "recommended first submission archive tag" in release


def test_release_sequence_reserves_doi_before_final_tag() -> None:
    release = RELEASE.read_text(encoding="utf-8")
    assert "Reserve a DOI" in release or "reserve a DOI" in release
    assert "Get a DOI now" in release
    assert "https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/" in release
    assert "Do **not** create the final `v0.1.0` tag" in release
    assert "Create tag and GitHub release" in release
    assert release.index("Create a Zenodo draft manually") < release.index("Create tag and GitHub release")


def test_exact_commit_is_machine_recorded_not_source_self_reference() -> None:
    availability = AVAILABILITY.read_text(encoding="utf-8")
    builder = PACKAGE_BUILDER.read_text(encoding="utf-8")
    assert "<RELEASE_COMMIT>" not in availability
    assert "submission_package_manifest.json" in availability
    assert "exact source Git commit" in availability
    assert '"source_commit": git_commit()' in builder


def test_release_and_figure_qa_are_part_of_submission_manifest() -> None:
    manifest = json.loads(SUBMISSION_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["release_readiness"] == "manuscript/submission/release_readiness.md"
    assert manifest["figure_qa"] == "manuscript/submission/figure_qa.md"
    blockers = "\n".join(manifest["required_pre_submission_resolutions"])
    assert "<RELEASE_TAG>" in blockers and "<ARCHIVE_DOI>" in blockers
    assert "<RELEASE_COMMIT>" not in blockers


def test_manual_external_release_boundary_is_explicit() -> None:
    release = RELEASE.read_text(encoding="utf-8")
    assert "does not expose a GitHub Release-creation action" in release
    assert "No Zenodo connector is installed" in release
    assert "must not be reported as completed until their public records exist" in release
