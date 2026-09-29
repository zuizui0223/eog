#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "manuscript/bam_identifiability/REVIEW_PACKAGE_MANIFEST_V2.json"
FIGURE_BUILDER = (
    ROOT / "manuscript/bam_identifiability/figures/build_quantitative_figures_v2.py"
)


EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-[\dX]{4}\b", re.I)
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".csv", ".py", ".toml", ".yml", ".yaml"
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_text(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    if EMAIL_RE.search(text):
        findings.append("email_address")
    if ORCID_RE.search(text):
        findings.append("orcid_identifier")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "build/bam_review_package",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Rebuild figures from the frozen source data immediately before packaging.
    subprocess.run(
        ["python", str(FIGURE_BUILDER)],
        cwd=ROOT,
        check=True,
    )
    built_fig_dir = ROOT / "build/bam_identifiability_figures"

    package_entries: list[tuple[Path, str]] = []
    missing: list[str] = []
    privacy_findings: list[dict[str, object]] = []

    excluded_tokens = tuple(
        token.lower() for token in manifest["excluded_patterns"]
    )

    for rel in manifest["exact_files"]:
        path = ROOT / rel
        if not path.is_file():
            missing.append(rel)
            continue
        lowered = rel.lower()
        if any(token in lowered for token in excluded_tokens):
            privacy_findings.append(
                {"path": rel, "finding": "excluded_filename_pattern"}
            )
            continue
        for finding in scan_text(path):
            privacy_findings.append({"path": rel, "finding": finding})
        package_entries.append((path, rel))

    for generated in manifest["generated_files"]:
        name = Path(generated).name
        path = built_fig_dir / name
        if not path.is_file():
            missing.append(f"generated:{generated}")
            continue
        package_entries.append((path, generated))

    if missing:
        raise RuntimeError(f"review package is missing required files: {missing}")
    if privacy_findings:
        raise RuntimeError(
            "anonymous review package privacy checks failed: "
            + json.dumps(privacy_findings, sort_keys=True)
        )

    package_entries.sort(key=lambda row: row[1])
    zip_path = output_dir / manifest["output"]["zip_name"]
    receipt_path = output_dir / manifest["output"]["receipt_name"]

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path, arcname in package_entries:
            archive.write(path, arcname)

    head_sha = "unknown"
    try:
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        pass

    receipt = {
        "schema": "eog.bam_inverse_identifiability.review_package_receipt.v1",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "source_head_sha": head_sha,
        "anonymous_review": True,
        "file_count": len(package_entries),
        "files": [
            {
                "path": arcname,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path, arcname in package_entries
        ],
        "privacy_findings": [],
        "zip_name": zip_path.name,
        "zip_sha256": sha256_file(zip_path),
        "zip_bytes": zip_path.stat().st_size,
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
