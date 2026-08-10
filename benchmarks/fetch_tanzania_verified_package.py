"""Acquire and integrity-verify the frozen Tanzania Dryad source package."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eog.tanzania_source_acquisition import (
    SourceContractError,
    SourceIntegrityError,
    acquire_tanzania_source,
)


def _write_failure(output_dir: Path, status: str, exc: Exception) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "acquisition_report.json").write_text(
        json.dumps(
            {
                "status": status,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "species_outcomes_inspected": False,
                "verified_source_dir": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--live-manifest", type=Path)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--require-success",
        action="store_true",
        help="return nonzero unless every official Dryad byte is verified",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    try:
        result = acquire_tanzania_source(
            contract_path=args.contract,
            output_dir=args.output_dir,
            live_manifest_path=args.live_manifest,
            timeout=args.timeout,
        )
    except SourceIntegrityError as exc:
        _write_failure(args.output_dir, "official_source_integrity_failure", exc)
        print(json.dumps({"status": "official_source_integrity_failure", "error": str(exc)}, indent=2))
        return 2
    except SourceContractError as exc:
        _write_failure(args.output_dir, "source_contract_or_authentication_failure", exc)
        print(
            json.dumps(
                {"status": "source_contract_or_authentication_failure", "error": str(exc)},
                indent=2,
            )
        )
        return 2

    payload = result.__dict__
    print(json.dumps(payload, indent=2))
    if args.require_success and result.status != "verified_official_dryad_bytes":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
