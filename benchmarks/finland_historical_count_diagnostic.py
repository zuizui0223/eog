"""Diagnose the SW Finland response-free historical-count admission mismatch.

This script never reads the released ``outcome`` field.  It compares the pre-outcome
reconstructed historical-source count (complement of potential-target islands) with the
released standardized ``Historical_total_log`` value and records structural consistency
patterns without changing the frozen admission threshold or source rule.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    root = str(Path(__file__).resolve().parents[1])
    if root not in sys.path:
        sys.path.insert(0, root)

from benchmarks.finland_csv_format_adapter import detect_csv_format, fixed_dict_reader_delimiter
from benchmarks.finland_colonization_preoutcome_admission import (
    _best_affine_transform_r2,
    _load_response_free_projection,
)


def diagnose(path: str | Path) -> dict[str, object]:
    source = Path(path)
    fmt = detect_csv_format(source)
    with fixed_dict_reader_delimiter(str(fmt["delimiter"])):
        projection = _load_response_free_projection(source)

    island_ids: tuple[str, ...] = projection["island_ids"]
    species_ids: tuple[str, ...] = projection["species_ids"]
    universe = set(island_ids)
    rows: list[dict[str, object]] = []
    for species in species_ids:
        source_count = len(universe - projection["species_targets"][species])
        values = projection["species_history_values"].get(species, [])
        if not values:
            continue
        unique = sorted({float(value) for value in values})
        if len(unique) != 1:
            raise ValueError(f"Historical_total_log varies within species {species}")
        rows.append(
            {
                "species": species,
                "reconstructed_source_count": int(source_count),
                "released_historical_total_scaled": float(unique[0]),
            }
        )

    x = np.asarray([row["reconstructed_source_count"] for row in rows], dtype=float)
    y = np.asarray([row["released_historical_total_scaled"] for row in rows], dtype=float)
    fit = _best_affine_transform_r2(x, y)
    transform = str(fit["transform"])
    if transform not in {"log10p1", "lnp1"}:
        raise RuntimeError(f"best released historical-count transform is unexpectedly {transform!r}")
    if transform == "lnp1":
        z = np.log1p(x)
        inverse = lambda value: math.exp(value) - 1.0
    else:
        z = np.log10(x + 1.0)
        inverse = lambda value: (10.0 ** value) - 1.0
    intercept = float(fit["intercept"])
    slope = float(fit["slope"])
    fitted = intercept + slope * z

    # Search the discrete island-count domain for the integer count most compatible with
    # each released standardized value under the global response-free affine transform.
    candidate_counts = np.arange(0, len(island_ids) + 1, dtype=float)
    candidate_z = np.log1p(candidate_counts) if transform == "lnp1" else np.log10(candidate_counts + 1.0)
    candidate_y = intercept + slope * candidate_z

    for index, row in enumerate(rows):
        released = float(row["released_historical_total_scaled"])
        residual = released - float(fitted[index])
        best_index = int(np.argmin(np.abs(candidate_y - released)))
        implied_continuous = inverse((released - intercept) / slope)
        row.update(
            {
                "fitted_released_value": float(fitted[index]),
                "residual": float(residual),
                "absolute_residual": float(abs(residual)),
                "best_integer_count_under_global_transform": best_index,
                "best_integer_count_delta": int(best_index - int(row["reconstructed_source_count"])),
                "implied_continuous_count": float(implied_continuous),
            }
        )

    by_reconstructed: dict[int, set[float]] = defaultdict(set)
    by_released: dict[float, set[int]] = defaultdict(set)
    for row in rows:
        by_reconstructed[int(row["reconstructed_source_count"])].add(
            float(row["released_historical_total_scaled"])
        )
        by_released[float(row["released_historical_total_scaled"])].add(
            int(row["reconstructed_source_count"])
        )

    conflicting_reconstructed_counts = [
        {
            "reconstructed_source_count": count,
            "n_distinct_released_values": len(values),
            "released_values": sorted(values),
        }
        for count, values in sorted(by_reconstructed.items())
        if len(values) > 1
    ]
    conflicting_released_values = [
        {
            "released_value": released,
            "n_distinct_reconstructed_counts": len(counts),
            "reconstructed_counts": sorted(counts),
        }
        for released, counts in sorted(by_released.items())
        if len(counts) > 1
    ]

    ranked = sorted(rows, key=lambda row: (-float(row["absolute_residual"]), str(row["species"])))
    nonzero_integer_delta = [row for row in rows if int(row["best_integer_count_delta"]) != 0]
    delta_histogram: dict[str, int] = defaultdict(int)
    for row in nonzero_integer_delta:
        delta_histogram[str(int(row["best_integer_count_delta"]))] += 1

    return {
        "status": "finland-response-free-historical-count-diagnostic",
        "outcome_values_accessed": False,
        "n_islands": len(island_ids),
        "n_species_with_released_historical_total": len(rows),
        "best_affine_transform": fit,
        "max_absolute_residual": float(max(float(row["absolute_residual"]) for row in rows)),
        "median_absolute_residual": float(np.median([float(row["absolute_residual"]) for row in rows])),
        "n_reconstructed_count_levels_with_multiple_released_values": len(conflicting_reconstructed_counts),
        "n_released_levels_with_multiple_reconstructed_counts": len(conflicting_released_values),
        "n_species_best_integer_count_differs": len(nonzero_integer_delta),
        "best_integer_count_delta_histogram": dict(sorted(delta_histogram.items(), key=lambda item: int(item[0]))),
        "top_50_absolute_residual_species": ranked[:50],
        "conflicting_reconstructed_count_levels": conflicting_reconstructed_counts,
        "conflicting_released_value_levels": conflicting_released_values,
        "claim_boundary": (
            "Response-free diagnostic only. No outcome value was accessed; the frozen 0.999999 admission "
            "threshold and complement-source rule are unchanged."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "outcome_values_accessed": False,
        "r2": result["best_affine_transform"]["r2"],
        "n_species_best_integer_count_differs": result["n_species_best_integer_count_differs"],
        "max_absolute_residual": result["max_absolute_residual"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
