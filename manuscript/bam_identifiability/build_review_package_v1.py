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
POSIX_LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9])/(?:home|Users|mnt/data)/[^\s'\"<>]*")
WINDOWS_LOCAL_PATH_RE = re.compile(r"\b[A-Za-z]:\\(?:Users|Documents and Settings)\\[^\s'\"<>]*", re.I)
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".csv", ".py", ".toml", ".yml", ".yaml"
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan_text(
    *,
    arcname: str,
    data: bytes,
    forbidden_tokens: tuple[str, ...],
) -> list[str]:
    if Path(arcname).suffix.lower() not in TEXT_SUFFIXES:
        return []
    text = data.decode("utf-8", errors="replace")
    lowered = text.lower()
    findings: list[str] = []
    if EMAIL_RE.search(text):
        findings.append("email_address")
    if ORCID_RE.search(text):
        findings.append("orcid_identifier")
    if POSIX_LOCAL_PATH_RE.search(text) or WINDOWS_LOCAL_PATH_RE.search(text):
        findings.append("absolute_local_filesystem_path")
    for token in forbidden_tokens:
        if token and token.lower() in lowered:
            findings.append(f"forbidden_text_token:{token}")
    return findings


def generated_pyproject() -> str:
    return """[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bam-inverse-identifiability-review"
version = "0.0.0"
description = "Anonymous review reproduction package for BAM inverse-identifiability"
requires-python = ">=3.10"
dependencies = ["numpy>=1.24"]

[project.optional-dependencies]
review = ["pytest>=8", "matplotlib>=3.8"]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["."]
"""


def generated_readme(focused_tests: list[str]) -> str:
    test_command = " ".join(focused_tests)
    return f"""# Anonymous review reproduction package

This archive contains only the files needed to inspect and reproduce the
BAM inverse-identifiability manuscript's frozen theory, simulations,
quantitative figures and focused tests.

No author/title-page metadata or public repository owner identifier is included.

## Install

    python -m pip install -e ".[review]"

## Focused tests

    python -m pytest {test_command} -q

## Rebuild Figures 1-6

    python manuscript/bam_identifiability/figures/build_quantitative_figures_v2.py

Figures are written to:

    build/bam_identifiability_figures/

## Canonical evidence

Frozen protocols and result summaries are under validation/.
Figure-source data and their source-fingerprint manifest are under:

    manuscript/bam_identifiability/figure_data/

The review manuscript is:

    manuscript/bam_identifiability/MANUSCRIPT_DRAFT_V4_JBI.md

All conclusions remain conditional on the declared finite world/evidence universes.
"""


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

    # Rebuild figures from frozen source data immediately before packaging.
    subprocess.run(
        ["python", str(FIGURE_BUILDER)],
        cwd=ROOT,
        check=True,
    )
    built_fig_dir = ROOT / "build/bam_identifiability_figures"

    excluded_tokens = tuple(
        str(token).lower() for token in manifest["excluded_patterns"]
    )
    forbidden_text_tokens = tuple(
        str(token) for token in manifest.get("forbidden_text_tokens", [])
    )

    entries: dict[str, bytes] = {}
    missing: list[str] = []
    privacy_findings: list[dict[str, object]] = []

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
        data = path.read_bytes()
        for finding in scan_text(
            arcname=rel,
            data=data,
            forbidden_tokens=forbidden_text_tokens,
        ):
            privacy_findings.append({"path": rel, "finding": finding})
        entries[rel] = data

    for generated in manifest["generated_files"]:
        name = Path(generated).name
        path = built_fig_dir / name
        if not path.is_file():
            missing.append(f"generated:{generated}")
            continue
        entries[generated] = path.read_bytes()

    support = {
        "pyproject.toml": generated_pyproject().encode("utf-8"),
        "README_REPRODUCTION.md": generated_readme(
            list(manifest["focused_tests"])
        ).encode("utf-8"),
    }
    for arcname, data in support.items():
        for finding in scan_text(
            arcname=arcname,
            data=data,
            forbidden_tokens=forbidden_text_tokens,
        ):
            privacy_findings.append({"path": arcname, "finding": finding})
        entries[arcname] = data

    expected_support = set(manifest.get("generated_support_files", []))
    if expected_support != set(support):
        raise RuntimeError(
            "generated support-file contract mismatch: "
            f"expected={sorted(expected_support)}, actual={sorted(support)}"
        )

    if missing:
        raise RuntimeError(f"review package is missing required files: {missing}")
    if privacy_findings:
        raise RuntimeError(
            "anonymous review package privacy checks failed: "
            + json.dumps(privacy_findings, sort_keys=True)
        )

    zip_path = output_dir / manifest["output"]["zip_name"]
    receipt_path = output_dir / manifest["output"]["receipt_name"]

    # Use deterministic archive timestamps/permissions so identical content yields
    # an identical zip hash across runners.
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for arcname in sorted(entries):
            info = zipfile.ZipInfo(arcname)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, entries[arcname])

    head_sha = "unknown"
    try:
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        pass

    file_rows = [
        {
            "path": arcname,
            "sha256": sha256_bytes(entries[arcname]),
            "bytes": len(entries[arcname]),
        }
        for arcname in sorted(entries)
    ]

    receipt = {
        "schema": "eog.bam_inverse_identifiability.review_package_receipt.v2",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "source_head_sha": head_sha,
        "anonymous_review": True,
        "reproducible_bundle": True,
        "file_count": len(entries),
        "files": file_rows,
        "privacy_findings": [],
        "focused_tests": list(manifest["focused_tests"]),
        "zip_name": zip_path.name,
        "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
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
