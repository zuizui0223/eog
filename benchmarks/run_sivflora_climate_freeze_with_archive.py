#!/usr/bin/env python3
"""Run the frozen SIVFLORA climate freeze with a pre-downloaded WorldClim archive.

This is an acquisition adapter only. The scientific sampling and missing-data rules stay
in ``freeze_sivflora_climate.py``. A workflow can use curl retry/resume to obtain the
large official archive, then this adapter supplies those exact bytes to the frozen
climate implementation instead of opening a second network connection.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import freeze_sivflora_climate as base  # noqa: E402


def run(nodes: Path, worldclim_archive: Path, output_csv: Path, output_manifest: Path) -> dict[str, object]:
    if not worldclim_archive.is_file() or worldclim_archive.stat().st_size == 0:
        raise ValueError("pre-downloaded WorldClim archive is missing or empty")

    def _copy_frozen_archive(url: str, destination: Path) -> dict[str, object]:
        if url != base.WORLDCLIM_ARCHIVE_URL:
            raise ValueError("climate implementation requested an undeclared WorldClim URL")
        shutil.copyfile(worldclim_archive, destination)
        return {
            "resolved_url": url,
            "download_method": "workflow_curl_retry_resume_then_exact_byte_copy",
            "content_length": str(worldclim_archive.stat().st_size),
            "etag": None,
            "last_modified": None,
        }

    base._download = _copy_frozen_archive
    return base.freeze_climate(nodes, output_csv, output_manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--worldclim-archive", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.nodes, args.worldclim_archive, args.output_csv, args.output_manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
