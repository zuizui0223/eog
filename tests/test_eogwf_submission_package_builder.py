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
