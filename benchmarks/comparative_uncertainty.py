"""Frozen benchmark for comparative EOG effect sizes and uncertainty."""
from __future__ import annotations

import argparse
import csv
import json

import numpy as np

from eog import compare_geometry, fit_robust_reference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="comparative_uncertainty_results.csv")
    parser.add_argument("--decision", default="comparative_uncertainty_decision.json")
    args = parser.parse_args()

    rows = []
    for n in (60, 120, 240):
        for repeat in range(20):
            rng = np.random.default_rng(1000 + n * 10 + repeat)
            reference_values = rng.normal(size=(300, 2))
            reference = fit_robust_reference(reference_values, provenance="external frozen benchmark")
            compact = rng.normal(size=(n, 2))
            dilated = 2.0 * rng.normal(size=(max(40, n // 2), 2))
            extent = compare_geometry(
                compact,
                dilated,
                reference,
                n_resamples=100,
                resample_fraction=0.8,
                random_state=repeat,
            )
            null_a = rng.normal(size=(n, 2))
            null_b = rng.normal(size=(max(40, n // 2), 2))
            null = compare_geometry(
                null_a,
                null_b,
                reference,
                n_resamples=100,
                resample_fraction=0.8,
                random_state=repeat + 100,
            )
            rows.append({
                "n": n,
                "repeat": repeat,
                "extent_log_ratio": extent.estimate,
                "extent_low": extent.interval_low,
                "extent_high": extent.interval_high,
                "extent_direction_stability": extent.direction_stability,
                "extent_ambiguous": extent.ambiguous,
                "null_direction_stability": null.direction_stability,
                "null_ambiguous": null.ambiguous,
            })

    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    known = float(np.log(2.0))
    extent_errors = [abs(float(row["extent_log_ratio"]) - known) for row in rows]
    extent_cover = [float(row["extent_low"]) <= known <= float(row["extent_high"]) for row in rows]
    null_certainty = [float(row["null_direction_stability"]) >= 0.90 and not bool(row["null_ambiguous"]) for row in rows]
    decision = {
        "median_absolute_log_ratio_error": float(np.median(extent_errors)),
        "known_ratio_interval_coverage": float(np.mean(extent_cover)),
        "null_false_directional_certainty": float(np.mean(null_certainty)),
    }
    decision["passes_gate"] = bool(
        decision["median_absolute_log_ratio_error"] <= 0.20
        and decision["known_ratio_interval_coverage"] >= 0.70
        and decision["null_false_directional_certainty"] <= 0.10
    )
    with open(args.decision, "w", encoding="utf-8") as handle:
        json.dump(decision, handle, indent=2, sort_keys=True)
    if not decision["passes_gate"]:
        raise SystemExit(f"comparative uncertainty gate failed: {decision}")


if __name__ == "__main__":
    main()
