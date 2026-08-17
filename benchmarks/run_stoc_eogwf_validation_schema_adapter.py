#!/usr/bin/env python3
"""Schema-only adapter for the frozen STOC EOG-WF validation runner.

The first once-only attempt verified the exact frozen source bytes and then stopped
before modeling because the real CSV uses lowercase ``x_wgs84`` / ``y_wgs84`` while
the public documentation and frozen runner used uppercase ``X_WGS84`` / ``Y_WGS84``.
This adapter changes only those two in-memory column labels.  It does not change any
source bytes, response values, world definitions, thresholds, anchors, models,
metrics, or decision rules.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path


RUNNER_PATH = Path(__file__).with_name("run_stoc_eogwf_validation.py")


def _load_runner():
    spec = importlib.util.spec_from_file_location("_stoc_frozen_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen STOC runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    runner = _load_runner()
    original_read_csv = runner.pd.read_csv

    def read_csv_with_coordinate_case_adapter(*read_args, **read_kwargs):
        frame = original_read_csv(*read_args, **read_kwargs)
        return frame.rename(columns={"x_wgs84": "X_WGS84", "y_wgs84": "Y_WGS84"})

    runner.pd.read_csv = read_csv_with_coordinate_case_adapter
    args.output.mkdir(parents=True, exist_ok=True)
    result = runner.run(args.source)
    result["schema_adapter"] = {
        "status": "coordinate_header_case_only",
        "mapping": {"x_wgs84": "X_WGS84", "y_wgs84": "Y_WGS84"},
        "first_failed_run": 31985198572,
    }
    # Recompute the result fingerprint after adding the transparent adapter record.
    result.pop("result_fingerprint", None)
    result["result_fingerprint"] = runner.canonical_sha256(result)

    result_path = args.output / "stoc_eogwf_result.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    runner.write_species_csv(result, args.output / "stoc_eogwf_species_summary.csv")
    print(json.dumps({"summary": result["summary"], "result_fingerprint": result["result_fingerprint"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
