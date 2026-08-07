"""Pre-outcome species screening for an A-Islands EOG benchmark.

This module does not inspect EOG performance. It only summarizes species occupancy
across comprehensively surveyed islands and applies fixed distributional eligibility
criteria before any topology comparison is run.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _require_columns(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    if not rows:
        raise ValueError(f"{label} is empty")
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def summarize_species(
    island_rows: list[dict[str, str]],
    species_rows: list[dict[str, str]],
    *,
    min_present_islands: int = 10,
    min_absent_islands: int = 10,
    min_prevalence: float = 0.10,
    max_prevalence: float = 0.90,
) -> list[dict[str, object]]:
    """Return deterministic occupancy summaries without using any EOG outcome."""
    _require_columns(island_rows, {"list_ID", "island_ID"}, "island_data")
    _require_columns(species_rows, {"List_ID", "Species_update"}, "species_data")
    if min_present_islands < 1 or min_absent_islands < 1:
        raise ValueError("minimum present and absent island counts must be positive")
    if not 0 <= min_prevalence < max_prevalence <= 1:
        raise ValueError("prevalence bounds must satisfy 0 <= min < max <= 1")

    list_to_island: dict[str, str] = {}
    for row in island_rows:
        list_id = row["list_ID"].strip()
        island_id = row["island_ID"].strip()
        if not list_id or not island_id:
            raise ValueError("island_data contains blank list_ID or island_ID")
        previous = list_to_island.get(list_id)
        if previous is not None and previous != island_id:
            raise ValueError(f"list_ID maps to multiple islands: {list_id}")
        list_to_island[list_id] = island_id

    surveyed_islands = sorted(set(list_to_island.values()))
    total_islands = len(surveyed_islands)
    if total_islands < 2:
        raise ValueError("at least two surveyed islands are required")

    species_islands: dict[str, set[str]] = {}
    native_values: dict[str, list[str]] = {}
    naturalised_values: dict[str, list[str]] = {}
    for row in species_rows:
        species = row["Species_update"].strip()
        list_id = row["List_ID"].strip()
        if not species:
            continue
        if list_id not in list_to_island:
            raise ValueError(f"species_data List_ID not found in island_data: {list_id}")
        species_islands.setdefault(species, set()).add(list_to_island[list_id])
        if "Native" in row and row["Native"].strip():
            native_values.setdefault(species, []).append(row["Native"].strip())
        if "Naturalised" in row and row["Naturalised"].strip():
            naturalised_values.setdefault(species, []).append(row["Naturalised"].strip())

    output: list[dict[str, object]] = []
    for species in sorted(species_islands):
        n_present = len(species_islands[species])
        n_absent = total_islands - n_present
        prevalence = n_present / total_islands
        distribution_eligible = (
            n_present >= min_present_islands
            and n_absent >= min_absent_islands
            and min_prevalence <= prevalence <= max_prevalence
        )
        native = native_values.get(species, [])
        naturalised = naturalised_values.get(species, [])
        output.append(
            {
                "species": species,
                "n_surveyed_islands": total_islands,
                "n_present_islands": n_present,
                "n_absent_islands": n_absent,
                "prevalence": round(prevalence, 8),
                "distribution_eligible": int(distribution_eligible),
                "native_status_values": "|".join(sorted(set(native))),
                "naturalised_status_values": "|".join(sorted(set(naturalised))),
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-present-islands", type=int, default=10)
    parser.add_argument("--min-absent-islands", type=int, default=10)
    parser.add_argument("--min-prevalence", type=float, default=0.10)
    parser.add_argument("--max-prevalence", type=float, default=0.90)
    args = parser.parse_args()

    rows = summarize_species(
        _read_csv(args.island_data),
        _read_csv(args.species_data),
        min_present_islands=args.min_present_islands,
        min_absent_islands=args.min_absent_islands,
        min_prevalence=args.min_prevalence,
        max_prevalence=args.max_prevalence,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else [
        "species", "n_surveyed_islands", "n_present_islands", "n_absent_islands",
        "prevalence", "distribution_eligible", "native_status_values",
        "naturalised_status_values",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
