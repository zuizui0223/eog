"""CLI for the response-free SW Finland strict-source bundle freeze."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    root = str(Path(__file__).resolve().parents[1])
    if root not in sys.path:
        sys.path.insert(0, root)

from benchmarks.finland_strict_source_prepare import evaluate_strict_admission, prepare_strict_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    admission = evaluate_strict_admission(args.input)
    args.admission.parent.mkdir(parents=True, exist_ok=True)
    args.admission.write_text(
        json.dumps(admission, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    if not admission["admitted"]:
        raise SystemExit("Finland strict-source response-free admission failed")
    manifest = prepare_strict_bundle(args.input, args.bundle, args.manifest)
    print(json.dumps({
        "status": admission["status"],
        "admitted": admission["admitted"],
        "outcome_values_accessed": False,
        "n_species_strict": admission["n_species_strict"],
        "n_species_analysis_response_free": manifest["n_species_analysis_response_free"],
        "feature_bundle_fingerprint": manifest["feature_bundle_fingerprint"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
