"""Run the frozen Finland source-identifiability audit with the robust count-grid decoder.

The underlying source-identifiability logic is unchanged; only the response-free integer
count decoder is replaced with the exact-consensus implementation frozen in
``finland_historical_count_grid.py`` before any colonization outcome access.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import benchmarks.finland_source_identity_identifiability as base
from benchmarks.finland_historical_count_grid import decode_integer_historical_counts


def audit(path: str | Path) -> dict[str, object]:
    original = base.decode_integer_historical_counts
    base.decode_integer_historical_counts = decode_integer_historical_counts
    try:
        result = base.audit(path)
    finally:
        base.decode_integer_historical_counts = original
    result = dict(result)
    result["count_decoder"] = "finland_historical_count_grid.decode_integer_historical_counts"
    result["count_decoder_response_free"] = True
    result["outcome_values_accessed"] = False
    result["fingerprint"] = base._canonical_sha256({key: value for key, value in result.items() if key != "fingerprint"})
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "outcome_values_accessed": False,
        "n_uniquely_recoverable_species": result["n_uniquely_recoverable_species"],
        "minimum_species_gate_passed": result["minimum_species_gate_passed"],
        "source_identity_status_counts": result["source_identity_status_counts"],
        "historical_count_grid": result["historical_count_grid"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
