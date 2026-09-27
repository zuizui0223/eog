from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
LANE = ROOT / "manuscript" / "neon_small_mammal_continuity"
OUT = LANE / "generated"
ZIP_PATH = OUT / "anonymous_review_data_code_v1.zip"

FILES = (
    "pyproject.toml",
    "src/eog/v2/metacommunity_connectivity.py",
    "src/eog/v2/adequacy_complete_ladder.py",
    "src/eog/v2/world_adequacy.py",
    "src/eog/v2/world_scale_ladder.py",
    "src/eog/v2/world_survival_regime.py",
    "src/eog/v2/world_survival_regime_v2.py",
    "tests/test_metacommunity_connectivity.py",
    "validation/neon_metacommunity_connectivity_v1/protocol_v1.json",
    "validation/neon_metacommunity_connectivity_v1/protocol_lock_v1.json",
    "validation/neon_metacommunity_connectivity_v1/fresh_roster_lock_v1.json",
    "validation/neon_metacommunity_connectivity_v1/analysis_implementation_v1.json",
    "validation/neon_metacommunity_connectivity_v1/response_protocol_v1.json",
    "validation/neon_metacommunity_connectivity_v1/response_lock_v1.json",
    "validation/neon_metacommunity_connectivity_v1/programme_closure_v1.json",
    "validation/neon_metacommunity_connectivity_v1/capture_fresh_roster.py",
    "validation/neon_metacommunity_connectivity_v1/run_response_once.py",
    "manuscript/neon_small_mammal_continuity/site_metrics_v1.csv",
    "manuscript/neon_small_mammal_continuity/best_species_frequency_v1.csv",
    "manuscript/neon_small_mammal_continuity/IDENTITY_REDUNDANCY_AUDIT_V1.json",
    "manuscript/neon_small_mammal_continuity/build_paper_assets.py",
)

FORBIDDEN_TEXT = (
    "github.com/",
    "orcid.org/",
    "mailto:",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_readme() -> str:
    return """# Anonymous peer-review reproducibility package

Study: small-mammal occupancy-continuity redundancy

Primary source data:
NSF National Ecological Observatory Network (NEON)
Small mammal box trapping, DP1.10072.001, RELEASE-2026
DOI: 10.48443/A83H-TB34

This bundle contains frozen protocols, metadata/response locks, analysis code, tests,
derived site-level data used in the manuscript, and the deterministic figure/table
builder. Raw NEON response files are not redistributed. The exact authenticated query
contract, source release, file counts, checksums/fingerprints, and once-only response
receipt are preserved in the included validation files.

To inspect the core ecological metric implementation:
  src/eog/v2/metacommunity_connectivity.py

To inspect the consumed response analysis:
  validation/neon_metacommunity_connectivity_v1/run_response_once.py

To verify the metric implementation:
  pytest tests/test_metacommunity_connectivity.py

To regenerate manuscript figures/tables from the frozen site-level closure:
  python manuscript/neon_small_mammal_continuity/build_paper_assets.py

No API token is included. Reviewers wishing to re-download the original public NEON
data can obtain access through NEON and reproduce the frozen query in
response_protocol_v1.json.

This package intentionally omits author identity and repository ownership metadata for
double-blind peer review.
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "schema": "eog.neon_small_mammal_continuity.anonymous_review_bundle.v1",
        "neon_product": "DP1.10072.001",
        "neon_release": "RELEASE-2026",
        "neon_doi": "10.48443/A83H-TB34",
        "files": {},
    }

    resolved: list[tuple[str, Path]] = []
    for relative in FILES:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        if path.suffix.lower() in {".md", ".py", ".json", ".csv", ".toml", ".txt"}:
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            for token in FORBIDDEN_TEXT:
                if token in lowered:
                    raise RuntimeError(
                        f"identity-bearing link token {token!r} found in {relative}"
                    )
        resolved.append((relative, path))
        manifest["files"][relative] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    readme = review_readme().encode("utf-8")
    manifest_raw = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README_REVIEW.md", readme)
        archive.writestr("BUNDLE_MANIFEST_V1.json", manifest_raw)
        for relative, path in resolved:
            archive.write(path, arcname=relative)

    receipt = {
        "schema": "eog.neon_small_mammal_continuity.anonymous_review_bundle_receipt.v1",
        "zip_name": ZIP_PATH.name,
        "zip_sha256": sha256(ZIP_PATH),
        "zip_bytes": ZIP_PATH.stat().st_size,
        "file_count": len(FILES) + 2,
        "double_blind_identity_scan": "passed",
        "contains_raw_neon_response_files": False,
        "contains_api_token": False,
    }
    (OUT / "anonymous_review_bundle_receipt_v1.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
