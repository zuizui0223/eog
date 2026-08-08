"""Audit A-Islands table structure before model or EOG outcomes."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _col(rows: list[dict[str, str]], name: str) -> str:
    if not rows:
        raise ValueError("table is empty")
    matches = [column for column in rows[0] if column.casefold() == name.casefold()]
    if len(matches) != 1:
        raise ValueError(f"missing or ambiguous column: {name}")
    return matches[0]


def audit(island_data: Path, species_data: Path) -> dict[str, object]:
    islands = _read(island_data)
    species = _read(species_data)
    island_list_col = _col(islands, "List_ID")
    island_id_col = _col(islands, "Island_ID")
    species_list_col = _col(species, "List_ID")
    species_name_col = _col(species, "Species_update")

    island_list_ids = [row[island_list_col].strip() for row in islands]
    island_ids = [row[island_id_col].strip() for row in islands]
    species_list_ids = [row[species_list_col].strip() for row in species]
    species_names = [row[species_name_col].strip() for row in species if row[species_name_col].strip()]

    list_to_islands: dict[str, set[str]] = {}
    for list_id, island_id in zip(island_list_ids, island_ids):
        list_to_islands.setdefault(list_id, set()).add(island_id)
    ambiguous_lists = {
        list_id: sorted(values)
        for list_id, values in list_to_islands.items()
        if len(values) > 1
    }
    island_list_set = set(island_list_ids)
    species_list_set = set(species_list_ids)
    repeated_island_ids = Counter(island_ids)

    return {
        "island_data_rows": len(islands),
        "unique_list_ids_island_data": len(island_list_set),
        "unique_island_ids": len(set(island_ids)),
        "islands_with_multiple_lists": sum(count > 1 for count in repeated_island_ids.values()),
        "maximum_lists_per_island": max(repeated_island_ids.values()),
        "species_data_rows": len(species),
        "unique_list_ids_species_data": len(species_list_set),
        "unique_standardized_species": len(set(species_names)),
        "species_list_ids_missing_from_island_data": sorted(species_list_set - island_list_set),
        "island_list_ids_without_species_rows": sorted(island_list_set - species_list_set),
        "list_ids_mapping_to_multiple_islands": ambiguous_lists,
        "blank_list_ids_island_data": sum(not value for value in island_list_ids),
        "blank_island_ids": sum(not value for value in island_ids),
        "blank_list_ids_species_data": sum(not value for value in species_list_ids),
        "scientific_boundary": (
            "source-structure audit only; no SDM, EOG, topology, bridge, or held-out performance inspected"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.island_data, args.species_data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
