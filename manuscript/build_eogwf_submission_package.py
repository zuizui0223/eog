#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from build_eogwf_author_admin import validate_admin_receipt

ROOT = Path(__file__).resolve().parents[1]
BLOCKERS = ROOT / "manuscript/EOG_WF_SUBMISSION_BLOCKERS_V1.json"
MANUSCRIPT_SOURCE = ROOT / "manuscript/EOG_WF_MANUSCRIPT_V1.md"
FINAL_MANUSCRIPT = ROOT / "manuscript/EOG_WF_MANUSCRIPT_FINAL.md"
FINAL_TITLE_PAGE = ROOT / "manuscript/EOG_WF_TITLE_PAGE.md"
TITLE_TEMPLATE = ROOT / "manuscript/EOG_WF_TITLE_PAGE_TEMPLATE.md"
AI_DISCLOSURE = ROOT / "manuscript/EOG_WF_AI_LLM_DISCLOSURE.md"
ADMIN_RECEIPT = ROOT / "manuscript/EOG_WF_AUTHOR_ADMIN_APPROVAL_RECEIPT.json"
AUTHOR_ADMIN_BLOCKER_IDS = {
    "title_page_author_confirmation",
    "ai_llm_disclosure_author_confirmation",
}

STATIC_FILES = [
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "docs/development_mainline.md",
    "manuscript/EOG_WF_MANUSCRIPT_V1.md",
    "manuscript/EOG_WF_KNOWN_TRUTH_BENCHMARK_V1.md",
    "manuscript/MEE_DESK_FIT_AUDIT_V2.md",
    "manuscript/EOG_WF_SUBMISSION_BLOCKERS_V1.json",
    "manuscript/EOG_WF_AUTHOR_ADMIN_CONFIRMATION.template.json",
    "manuscript/AUTHOR_ADMIN_CONFIRMATION_PACKET.md",
    "manuscript/build_eogwf_author_admin.py",
    "manuscript/check_eogwf_mee_readiness.py",
    "manuscript/build_paper_ready_eogwf.py",
]
TREE_ROOTS = [
    "manuscript/paper_ready",
    "src/eog",
    "tests",
]
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unavailable"


def is_package_source(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def selected_files(mode: str, admin_receipt_valid: bool) -> list[Path]:
    paths: list[Path] = []
    for rel in STATIC_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"required submission-package file missing: {rel}")
        paths.append(path)

    if mode == "final":
        if not admin_receipt_valid:
            raise RuntimeError(
                "final submission package requires a valid author-admin approval receipt"
            )
        for path in (
            FINAL_TITLE_PAGE,
            FINAL_MANUSCRIPT,
            AI_DISCLOSURE,
            ADMIN_RECEIPT,
        ):
            if not path.is_file():
                raise FileNotFoundError(
                    f"required author-admin finalization file missing: "
                    f"{path.relative_to(ROOT)}"
                )
            paths.append(path)
    else:
        title = FINAL_TITLE_PAGE if FINAL_TITLE_PAGE.is_file() else TITLE_TEMPLATE
        if not title.is_file():
            raise FileNotFoundError(
                "neither final nor template EOG-WF title page exists"
            )
        paths.append(title)

    for rel in TREE_ROOTS:
        root = ROOT / rel
        if not root.is_dir():
            raise FileNotFoundError(f"required submission-package tree missing: {rel}")
        paths.extend(p for p in root.rglob("*") if is_package_source(p))

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
    canonical_blocker_ids = [item["id"] for item in remaining]
    admin_receipt_valid = validate_admin_receipt(
        ADMIN_RECEIPT,
        title_path=FINAL_TITLE_PAGE,
        ai_path=AI_DISCLOSURE,
        manuscript_path=FINAL_MANUSCRIPT,
    )
    effective_blocker_ids = [
        blocker_id
        for blocker_id in canonical_blocker_ids
        if not (
            admin_receipt_valid
            and blocker_id in AUTHOR_ADMIN_BLOCKER_IDS
        )
    ]

    if mode == "final" and effective_blocker_ids:
        raise RuntimeError(
            "final submission package forbidden while blockers remain: "
            + ", ".join(effective_blocker_ids)
        )
    if mode == "final" and not admin_receipt_valid:
        raise RuntimeError(
            "final submission package requires a valid author-admin approval receipt"
        )
    manuscript_for_submission = (
        FINAL_MANUSCRIPT if admin_receipt_valid else MANUSCRIPT_SOURCE
    )
    if (
        mode == "final"
        and "[FINAL ARCHIVE/DOI TO ADD]"
        in manuscript_for_submission.read_text(encoding="utf-8")
    ):
        raise RuntimeError(
            "final submission package forbidden while archive/DOI placeholder remains"
        )

    if output_dir.exists():
        shutil.rmtree(output_dir)
    package_root = output_dir / "package"
    package_root.mkdir(parents=True)

    hashes: dict[str, str] = {}
    for src in selected_files(mode, admin_receipt_valid):
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
        "canonical_submission_blocker_ids": canonical_blocker_ids,
        "remaining_submission_blocker_ids": effective_blocker_ids,
        "remaining_submission_blocker_count": len(effective_blocker_ids),
        "author_admin_approval_receipt_valid": admin_receipt_valid,
        "final_title_page_present": FINAL_TITLE_PAGE.is_file(),
        "final_manuscript_present": FINAL_MANUSCRIPT.is_file(),
        "ai_llm_disclosure_present": AI_DISCLOSURE.is_file(),
        "archive_doi_placeholder_present": (
            "[FINAL ARCHIVE/DOI TO ADD]"
            in manuscript_for_submission.read_text(encoding="utf-8")
        ),
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
        "canonical_submission_blocker_ids": canonical_blocker_ids,
        "remaining_submission_blocker_ids": effective_blocker_ids,
        "remaining_submission_blocker_count": len(effective_blocker_ids),
        "author_admin_approval_receipt_valid": admin_receipt_valid,
        "scientific_desk_fit_ready": manifest["scientific_desk_fit_ready"],
        "submission_ready": mode == "final" and not effective_blocker_ids,
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
