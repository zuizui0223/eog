"""Audit taxonomic/status fields for distribution-eligible A-Islands taxa.

This stage is deliberately outcome-free. It summarizes source metadata needed to freeze
status-cleaning rules before any SDM, EOG topology, bridge, or held-out evaluation.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _column(rows: list[dict[str, str]], name: str, *, required: bool = True) -> str | None:
    if not rows:
        raise ValueError("source table is empty")
    matches = [key for key in rows[0] if key.casefold() == name.casefold()]
    if len(matches) == 1:
        return matches[0]
    if required:
        raise ValueError(f"missing or ambiguous column: {name}")
    return None


def _clean(value: str) -> str:
    value = value.strip()
    return value if value else "<blank>"


def audit(species_data: Path, species_screen: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    source = _read_csv(species_data)
    screen = _read_csv(species_screen)
    eligible = {
        row["species"].strip()
        for row in screen
        if int(row["distribution_eligible"]) == 1
    }
    if not eligible:
        raise ValueError("distribution screen contains no eligible species")

    species_col = _column(source, "Species_update")
    native_col = _column(source, "Native", required=False)
    naturalised_col = _column(source, "Naturalised", required=False)
    endemic_col = _column(source, "Endemic", required=False)
    apc_col = _column(source, "Status_APC", required=False)
    family_col = _column(source, "Family", required=False)

    fields = {
        "native": native_col,
        "naturalised": naturalised_col,
        "endemic": endemic_col,
        "status_apc": apc_col,
        "family": family_col,
    }
    values: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    records = Counter()
    raw_counts = {name: Counter() for name in fields}

    for row in source:
        species = row[species_col].strip()
        if species not in eligible:
            continue
        records[species] += 1
        for name, column in fields.items():
            if column is None:
                continue
            value = _clean(row[column])
            values[species][name].add(value)
            raw_counts[name][value] += 1

    missing_species = sorted(eligible - set(records))
    if missing_species:
        raise ValueError(f"eligible species missing from species_data: {missing_species[:10]}")

    rows: list[dict[str, object]] = []
    pattern_counts = {name: Counter() for name in fields}
    for species in sorted(eligible):
        row: dict[str, object] = {
            "species": species,
            "source_record_count": records[species],
        }
        for name in fields:
            pattern = "|".join(sorted(values[species].get(name, {"<column_absent>"})))
            row[f"{name}_values"] = pattern
            pattern_counts[name][pattern] += 1
        rows.append(row)

    summary = {
        "n_distribution_eligible": len(eligible),
        "source_columns": {name: column for name, column in fields.items()},
        "eligible_species_value_patterns": {
            name: dict(sorted(counter.items())) for name, counter in pattern_counts.items()
        },
        "eligible_record_value_counts": {
            name: dict(sorted(counter.items())) for name, counter in raw_counts.items()
        },
        "scientific_boundary": (
            "pre-outcome status audit only; no species retained or excluded using SDM, EOG, topology, bridge, or held-out performance"
        ),
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--species-screen", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = audit(args.species_data, args.species_screen)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    args.output_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
