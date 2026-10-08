#!/usr/bin/env python3
"""Offline SHA256 byte-parity gate for two publicly published Helgeland files.

The whole upstream files are read as opaque bytes solely for hashing; no
biological rows are decoded, interpreted, exported, joined or scored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = (ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
          / "helgeland_2026_source_metadata_frozen_v1.json")
UPSTREAM_REPO = "torhanssonfrank/DensityRegulationHouseSparrows"
UPSTREAM_COMMIT = "a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"

# Predeclared GitHub-file -> Dryad v6 file mapping. No fuzzy name matching.
TARGETS = {
    "Data/presence_data_1994_2022.txt":
        "presence_data_1994_2022_ECY25-1341.txt",
    "Data/estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt":
        "estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy_ECY25-1341.txt",
}


def file_path(root: Path, name: str) -> Path:
    root = root.absolute()
    if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("Upstream checkout root missing or symlinked")
    here = root
    for token in name.split("/"):
        if token in ("", ".", ".."):
            raise ValueError("Unsafe mapped source path")
        here = here / token
        if here.is_symlink():
            raise ValueError("Source file/directory is a symlink")
    if not here.is_file() or not stat.S_ISREG(here.stat().st_mode):
        raise ValueError("Mapped source is not a regular file")
    return here


def sha256_opaque_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as raw:
        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(upstream_root: Path, frozen: dict) -> dict:
    if frozen.get("schema") != "eog.helgeland.dryad_2026.source_metadata_frozen_observed_v1":
        raise ValueError("Invalid Dryad 2026 source metadata contract")
    if (frozen.get("dryad_dataset_id") != 177360 or
            frozen.get("dryad_version_id") != 421942 or
            frozen.get("dryad_version_number") != 6):
        raise ValueError("Unfrozen Dryad dataset/version")
    pinned = {x["name"]: x for x in frozen["files"]}
    if len(pinned) != 18 or set(TARGETS.values()) - pinned.keys():
        raise ValueError("Required 2026 source files absent from frozen version")
    rows = []
    for gh_path, dryad_name in TARGETS.items():
        expected = pinned[dryad_name]
        source = file_path(upstream_root, gh_path)
        actual_size = source.stat().st_size
        actual_digest = sha256_opaque_bytes(source)
        size_match = actual_size == expected["size_bytes"]
        digest_match = actual_digest == expected["source_declared_sha256"]
        rows.append({
            "upstream_repo_path": gh_path,
            "dryad_file_name": dryad_name,
            "dryad_file_metadata_id": expected["file_metadata_id"],
            "dryad_version_id": frozen["dryad_version_id"],
            "upstream_byte_count": actual_size,
            "size_matches_dryad_registered_metadata": size_match,
            "upstream_sha256_matches_dryad_declared_digest": digest_match,
            "whole_upstream_file_bytes_read_opaquely_for_hash": True,
            "physical_headers_decoded": False,
            "biological_rows_decoded_or_scored": False,
        })
    all_match = all(x["size_matches_dryad_registered_metadata"] and
                    x["upstream_sha256_matches_dryad_declared_digest"] for x in rows)
    return {
        "schema": "eog.helgeland.2026.github_dryad_byte_parity.v1",
        "status": ("MATCHES_TWO_FROZEN_DRYAD_V6_FILES"
                   if all_match else "HOLD_UPSTREAM_DRYAD_BYTE_MISMATCH"),
        "dryad_doi": frozen["source_doi"],
        "dryad_version_id": frozen["dryad_version_id"],
        "upstream_repo": UPSTREAM_REPO,
        "upstream_commit": UPSTREAM_COMMIT,
        "files": rows,
        "no_other_dryad_github_file_equivalence_implied": True,
        "biological_rows_decoded_or_scored": False,
        "surveyed_zero_panel_verified": False,
        "as_of_t_processing_verified": False,
        "directional_movement_event_verified": False,
        "ecological_endpoint_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    verdict = audit(args.upstream_checkout, frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": verdict["status"], "files_checked": len(verdict["files"])}))


if __name__ == "__main__":
    main()
