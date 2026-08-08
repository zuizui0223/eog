"""Freeze outcome-independent A-Islands geographic holdout folds.

The folds are evaluation partitions only. They do not represent dispersal barriers and
must not be interpreted as an ecological connectivity model.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _block_id(lon: float, lat: float, block_size_degrees: float) -> str:
    lon_bin = math.floor((lon + 180.0) / block_size_degrees)
    lat_bin = math.floor((lat + 90.0) / block_size_degrees)
    return f"{lon_bin}_{lat_bin}"


def freeze(
    audit_csv: Path,
    *,
    block_size_degrees: float = 5.0,
    n_folds: int = 5,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if block_size_degrees <= 0:
        raise ValueError("block_size_degrees must be positive")
    if n_folds < 2:
        raise ValueError("n_folds must be at least two")

    with audit_csv.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("model-island audit is empty")
    required = {"island_id", "x", "y", "coordinate_evaluable"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"model-island audit missing columns: {', '.join(sorted(missing))}")

    units: list[dict[str, object]] = []
    for row in rows:
        if int(row["coordinate_evaluable"]) != 1:
            continue
        lon = float(row["x"])
        lat = float(row["y"])
        units.append({
            "island_id": row["island_id"],
            "x": lon,
            "y": lat,
            "spatial_block": _block_id(lon, lat, block_size_degrees),
        })
    if not units:
        raise ValueError("no coordinate-evaluable islands")

    block_counts = Counter(str(row["spatial_block"]) for row in units)
    ordered_blocks = sorted(block_counts, key=lambda block: (-block_counts[block], block))
    fold_sizes = [0] * n_folds
    block_to_fold: dict[str, int] = {}
    for block in ordered_blocks:
        fold_index = min(range(n_folds), key=lambda index: (fold_sizes[index], index))
        block_to_fold[block] = fold_index + 1
        fold_sizes[fold_index] += block_counts[block]

    output = [
        {
            **row,
            "fold": block_to_fold[str(row["spatial_block"])],
        }
        for row in sorted(units, key=lambda item: int(str(item["island_id"])))
    ]
    fold_counts = Counter(int(row["fold"]) for row in output)
    summary = {
        "n_coordinate_evaluable_islands": len(output),
        "block_size_degrees": block_size_degrees,
        "n_spatial_blocks": len(block_counts),
        "n_folds": n_folds,
        "fold_island_counts": {str(fold): fold_counts[fold] for fold in range(1, n_folds + 1)},
        "largest_block_islands": max(block_counts.values()),
        "smallest_block_islands": min(block_counts.values()),
        "block_assignment_rule": (
            "5-degree lon/lat grid from global origin; blocks sorted by descending island count then block ID; each block assigned greedily to the currently smallest fold, ties to the lower fold ID"
        ),
        "ecological_interpretation": (
            "evaluation partition only; spatial blocks are not dispersal barriers, connectivity estimates, or colonisation units"
        ),
        "species_outcomes_used": False,
        "sdm_outputs_used": False,
        "eog_outputs_used": False,
    }
    return output, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--output-folds", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--block-size-degrees", type=float, default=5.0)
    parser.add_argument("--n-folds", type=int, default=5)
    args = parser.parse_args()

    rows, summary = freeze(
        args.audit_csv,
        block_size_degrees=args.block_size_degrees,
        n_folds=args.n_folds,
    )
    args.output_folds.parent.mkdir(parents=True, exist_ok=True)
    with args.output_folds.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary["fold_assignment_sha256"] = _sha256(args.output_folds)
    args.output_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
