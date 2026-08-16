#!/usr/bin/env python3
"""Run the frozen SIVFLORA climate freeze with a pre-downloaded WorldClim archive.

This is an acquisition adapter only. The scientific sampling and missing-data rules stay
in ``freeze_sivflora_climate.py``. A workflow can acquire the exact pre-outcome-frozen
WorldClim v2.1 2.5-minute mirror asset, then this adapter supplies those bytes to the
frozen climate implementation and records mirror provenance in the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import freeze_sivflora_climate as base  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    nodes: Path,
    worldclim_archive: Path,
    output_csv: Path,
    output_manifest: Path,
    *,
    acquisition_url: str,
    acquisition_repository: str,
    release_id: int,
    asset_id: int,
    expected_asset_bytes: int,
) -> dict[str, object]:
    if not worldclim_archive.is_file() or worldclim_archive.stat().st_size == 0:
        raise ValueError("pre-downloaded WorldClim archive is missing or empty")
    if worldclim_archive.stat().st_size != expected_asset_bytes:
        raise ValueError(
            f"WorldClim mirror asset byte-size mismatch: expected {expected_asset_bytes}, "
            f"got {worldclim_archive.stat().st_size}"
        )
    archive_sha256 = _sha256(worldclim_archive)

    def _copy_frozen_archive(url: str, destination: Path) -> dict[str, object]:
        if url != base.WORLDCLIM_ARCHIVE_URL:
            raise ValueError("climate implementation requested an undeclared WorldClim logical source")
        shutil.copyfile(worldclim_archive, destination)
        return {
            "resolved_url": url,
            "download_method": "preoutcome_frozen_github_release_mirror_exact_byte_copy",
            "content_length": str(worldclim_archive.stat().st_size),
            "etag": None,
            "last_modified": None,
        }

    base._download = _copy_frozen_archive
    result = base.freeze_climate(nodes, output_csv, output_manifest)

    manifest = json.loads(output_manifest.read_text(encoding="utf-8"))
    manifest["worldclim"]["acquisition_mirror"] = {
        "repository": acquisition_repository,
        "release_id": int(release_id),
        "asset_id": int(asset_id),
        "browser_download_url": acquisition_url,
        "asset_bytes": int(worldclim_archive.stat().st_size),
        "archive_sha256": archive_sha256,
        "role": "transport mirror for frozen WorldClim v2.1 current bioclim 2.5-minute representation",
    }
    output_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = dict(result)
    result["worldclim_acquisition_mirror"] = manifest["worldclim"]["acquisition_mirror"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--worldclim-archive", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    parser.add_argument("--acquisition-url", required=True)
    parser.add_argument("--acquisition-repository", required=True)
    parser.add_argument("--release-id", type=int, required=True)
    parser.add_argument("--asset-id", type=int, required=True)
    parser.add_argument("--expected-asset-bytes", type=int, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.nodes,
                args.worldclim_archive,
                args.output_csv,
                args.output_manifest,
                acquisition_url=args.acquisition_url,
                acquisition_repository=args.acquisition_repository,
                release_id=args.release_id,
                asset_id=args.asset_id,
                expected_asset_bytes=args.expected_asset_bytes,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
