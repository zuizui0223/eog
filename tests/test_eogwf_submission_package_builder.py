from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "manuscript/build_eogwf_submission_package.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("eogwf_submission_builder", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_prep_package_is_deterministic_and_tracks_current_blockers(tmp_path: Path) -> None:
    builder = load_builder()
    out1 = tmp_path / "one"
    out2 = tmp_path / "two"

    receipt1 = builder.build(out1, "review-prep")
    receipt2 = builder.build(out2, "review-prep")

    blockers = json.loads(
        (ROOT / "manuscript/EOG_WF_SUBMISSION_BLOCKERS_V1.json").read_text(encoding="utf-8")
    )
    expected_ids = [item["id"] for item in blockers["remaining_submission_blockers"]]

    assert receipt1["scientific_desk_fit_ready"] is True
    assert receipt1["submission_ready"] is False
    assert receipt1["remaining_submission_blocker_ids"] == expected_ids
    assert receipt1["remaining_submission_blocker_count"] == len(expected_ids)
    assert receipt1["archive_sha256"] == receipt2["archive_sha256"]
    assert receipt1["manifest_sha256"] == receipt2["manifest_sha256"]

    archive = out1 / "eogwf_submission_package.zip"
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        assert "LICENSE" in names
        assert "manuscript/EOG_WF_MANUSCRIPT_V1.md" in names
        assert "manuscript/paper_ready/submission_boundary.json" in names
        assert "submission_package_manifest.json" in names
        assert not any("__pycache__" in name for name in names)
        assert not any(name.endswith((".pyc", ".pyo")) for name in names)


def test_final_package_refuses_to_build_while_submission_blockers_remain(tmp_path: Path) -> None:
    builder = load_builder()
    blockers = json.loads(
        (ROOT / "manuscript/EOG_WF_SUBMISSION_BLOCKERS_V1.json").read_text(encoding="utf-8")
    )
    assert blockers["remaining_submission_blockers"]

    with pytest.raises(RuntimeError, match="final submission package forbidden while blockers remain"):
        builder.build(tmp_path / "final", "final")



def _configure_synthetic_final_repo(builder, tmp_path, monkeypatch, blockers):
    root = tmp_path / "repo"
    root.mkdir()
    blocker_path = root / "blockers.json"
    blocker_path.write_text(
        json.dumps(
            {
                "scientific_desk_fit_ready": True,
                "remaining_submission_blockers": [
                    {"id": blocker_id} for blocker_id in blockers
                ],
            }
        ),
        encoding="utf-8",
    )
    source = root / "source.md"
    final = root / "final.md"
    title = root / "title.md"
    ai = root / "ai.md"
    receipt = root / "admin_receipt.json"
    payload = root / "payload.txt"
    source.write_text("source\n", encoding="utf-8")
    final.write_text("final manuscript\n", encoding="utf-8")
    title.write_text("title\n", encoding="utf-8")
    ai.write_text("ai\n", encoding="utf-8")
    receipt.write_text("{}\n", encoding="utf-8")
    payload.write_text("payload\n", encoding="utf-8")

    monkeypatch.setattr(builder, "ROOT", root)
    monkeypatch.setattr(builder, "BLOCKERS", blocker_path)
    monkeypatch.setattr(builder, "MANUSCRIPT_SOURCE", source)
    monkeypatch.setattr(builder, "FINAL_MANUSCRIPT", final)
    monkeypatch.setattr(builder, "FINAL_TITLE_PAGE", title)
    monkeypatch.setattr(builder, "AI_DISCLOSURE", ai)
    monkeypatch.setattr(builder, "ADMIN_RECEIPT", receipt)
    monkeypatch.setattr(builder, "validate_admin_receipt", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        builder,
        "selected_files",
        lambda mode, admin_receipt_valid: [payload, final, title, ai, receipt],
    )
    return root


def test_valid_admin_receipt_resolves_only_the_two_author_blockers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    author_blockers = [
        "title_page_author_confirmation",
        "ai_llm_disclosure_author_confirmation",
    ]
    root = _configure_synthetic_final_repo(
        builder,
        tmp_path,
        monkeypatch,
        author_blockers,
    )

    receipt = builder.build(root / "build", "final")
    assert receipt["canonical_submission_blocker_ids"] == author_blockers
    assert receipt["remaining_submission_blocker_ids"] == []
    assert receipt["remaining_submission_blocker_count"] == 0
    assert receipt["author_admin_approval_receipt_valid"] is True
    assert receipt["submission_ready"] is True


def test_valid_admin_receipt_does_not_resolve_unrelated_blocker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    builder = load_builder()
    blockers = [
        "title_page_author_confirmation",
        "ai_llm_disclosure_author_confirmation",
        "unrelated_release_blocker",
    ]
    root = _configure_synthetic_final_repo(
        builder,
        tmp_path,
        monkeypatch,
        blockers,
    )

    with pytest.raises(RuntimeError, match="unrelated_release_blocker"):
        builder.build(root / "build", "final")
