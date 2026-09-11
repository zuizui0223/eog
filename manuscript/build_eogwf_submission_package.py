#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKERS = ROOT / "manuscript/EOG_WF_SUBMISSION_BLOCKERS_V1.json"
MANUSCRIPT = ROOT / "manuscript/EOG_WF_MANUSCRIPT_V1.md"
FINAL_TITLE_PAGE = ROOT / "manuscript/EOG_WF_TITLE_PAGE.md"
TITLE_TEMPLATE = ROOT / "manuscript/EOG_WF_TITLE_PAGE_TEMPLATE.md"

STATIC_FILES = [
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "docs/development_mainline.md",
    "manuscript/EOG_WF_MANUSCRIPT_V1.md",
    "manuscript/EOG_WF_KNOWN_TRUTH_BENCHMARK_V1.md",
    "manuscript/MEE_DESK_FIT_AUDIT_V2.md",
    "manuscript/EOG_WF_SUBMISSION_BLOCKERS_V1.json",
    "manuscript/check_eogwf_mee_readiness.py",
    "manuscript/build_paper_ready_eogwf.py",
]
TREE_ROOTS = [
    "manuscript/paper_ready",
    "src/eog",
    "tests",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unavailable"


def selected_files() -> list[Path]:
    paths: list[Path] = []
    for rel in STATIC_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"required submission-package file missing: {rel}")
        paths.append(path)

    title = FINAL_TITLE_PAGE if FINAL_TITLE_PAGE.is_file() else TITLE_TEMPLATE
    if not title.is_file():
        raise FileNotFoundError("neither final nor template EOG-WF title page exists")
    paths.append(title)

    for rel in TREE_ROOTS:
        root = ROOT / rel
        if not root.is_dir():
            raise FileNotFoundError(f"required submission-package tree missing: {rel}")
        paths.extend(p for p in root.rglob("*") if p.is_file())

    unique = {p.relative_to(ROOT).as_posix(): p for p in paths}
    return [unique[key] for key in sorted(unique)]


def write_deterministic_zip(package_root: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in package_root.rglob("*") if p.is_file()):
            rel = path.relative_to(package_root).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())


def build(output_dir: Path, mode: str) -> dict:
    blockers = json.loads(BLOCKERS.read_text(encoding="utf-8"))
    remaining = blockers.get("remaining_submission_blockers", [])
    blocker_ids = [item["id"] for item in remaining]

    if mode == "final" and remaining:
        raise RuntimeError(
            "final submission package forbidden while blockers remain: "
            + ", ".join(blocker_ids)
        )
    if mode == "final" and not FINAL_TITLE_PAGE.is_file():
        raise RuntimeError("final submission package requires manuscript/EOG_WF_TITLE_PAGE.md")
    if mode == "final" and "[FINAL ARCHIVE/DOI TO ADD]" in MANUSCRIPT.read_text(encoding="utf-8"):
        raise RuntimeError("final submission package forbidden while archive/DOI placeholder remains")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    package_root = output_dir / "package"
    package_root.mkdir(parents=True)

    hashes: dict[str, str] = {}
    for src in selected_files():
        rel = src.relative_to(ROOT)
        dst = package_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        dst.write_bytes(data)
        hashes[rel.as_posix()] = sha256_bytes(data)

    manifest = {
        "schema": "eog.eogwf_submission_package_manifest.v1",
        "mode": mode,
        "git_head": git_head(),
        "scientific_desk_fit_ready": blockers.get("scientific_desk_fit_ready") is True,
        "remaining_submission_blocker_ids": blocker_ids,
        "remaining_submission_blocker_count": len(blocker_ids),
        "final_title_page_present": FINAL_TITLE_PAGE.is_file(),
        "archive_doi_placeholder_present": "[FINAL ARCHIVE/DOI TO ADD]" in MANUSCRIPT.read_text(encoding="utf-8"),
        "included_files": hashes,
    }
    manifest_path = package_root / "submission_package_manifest.json"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_bytes)

    zip_path = output_dir / "eogwf_submission_package.zip"
    write_deterministic_zip(package_root, zip_path)
    receipt = {
        "schema": "eog.eogwf_submission_package_receipt.v1",
        "mode": mode,
        "git_head": manifest["git_head"],
        "archive": zip_path.name,
        "archive_sha256": sha256_bytes(zip_path.read_bytes()),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "remaining_submission_blocker_ids": blocker_ids,
        "remaining_submission_blocker_count": len(blocker_ids),
        "scientific_desk_fit_ready": manifest["scientific_desk_fit_ready"],
        "submission_ready": mode == "final" and not blocker_ids,
    }
    receipt_path = output_dir / "submission_package_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "build/eogwf_submission_package",
    )
    parser.add_argument("--mode", choices=("review-prep", "final"), default="review-prep")
    args = parser.parse_args()
    receipt = build(args.output_dir, args.mode)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
