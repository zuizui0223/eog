"""Summarize a frozen pre-outcome A-Islands distribution screen."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def _values(text: str) -> list[str]:
    return [value for value in (part.strip() for part in text.split("|")) if value]


def summarize(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "species", "n_surveyed_islands", "n_present_islands", "n_absent_islands",
        "prevalence", "distribution_eligible", "native_status_values", "naturalised_status_values",
    }
    if not rows:
        raise ValueError("species screen is empty")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"species screen missing columns: {', '.join(sorted(missing))}")

    island_counts = {int(row["n_surveyed_islands"]) for row in rows}
    if len(island_counts) != 1:
        raise ValueError("screen contains inconsistent surveyed-island counts")

    eligible = [row for row in rows if int(row["distribution_eligible"]) == 1]
    native = Counter()
    naturalised = Counter()
    for row in eligible:
        native.update(_values(row["native_status_values"]))
        naturalised.update(_values(row["naturalised_status_values"]))

    present_counts = [int(row["n_present_islands"]) for row in eligible]
    summary = {
        "n_surveyed_islands": next(iter(island_counts)),
        "n_species_total": len(rows),
        "n_distribution_eligible": len(eligible),
        "eligible_present_islands_min": min(present_counts) if present_counts else None,
        "eligible_present_islands_max": max(present_counts) if present_counts else None,
        "eligible_native_status_values": dict(sorted(native.items())),
        "eligible_naturalised_status_values": dict(sorted(naturalised.items())),
        "screen_rule": {
            "min_present_islands": 10,
            "min_absent_islands": 10,
            "prevalence_filter": "none_primary_full_0_to_1",
        },
        "scientific_boundary": (
            "distributional data-sufficiency screen only; no EOG or SDM outcome used for taxon selection"
        ),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--screen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.screen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
