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


def _optional_col(rows: list[dict[str, str]], name: str) -> str | None:
    if not rows:
        return None
    matches = [column for column in rows[0] if column.casefold() == name.casefold()]
    return matches[0] if len(matches) == 1 else None


def audit(island_data: Path, species_data: Path, reference_data: Path | None = None) -> dict[str, object]:
    islands = _read(island_data)
    species = _read(species_data)
    references = _read(reference_data) if reference_data else []
    island_list_col = _col(islands, "List_ID")
    island_id_col = _col(islands, "Island_ID")
    species_list_col = _col(species, "List_ID")
    species_name_col = _col(species, "Species_update")
    ref_id_col = _optional_col(islands, "Ref_ID")

    reference_by_id: dict[str, dict[str, str]] = {}
    reference_id_col = _optional_col(references, "Ref_ID")
    if references and reference_id_col:
        reference_by_id = {row[reference_id_col].strip(): row for row in references}

    island_list_ids = [row[island_list_col].strip() for row in islands]
    island_ids = [row[island_id_col].strip() for row in islands]
    species_list_ids = [row[species_list_col].strip() for row in species]
    species_names = [row[species_name_col].strip() for row in species if row[species_name_col].strip()]

    list_to_islands: dict[str, set[str]] = {}
    list_to_row: dict[str, dict[str, str]] = {}
    for row, list_id, island_id in zip(islands, island_list_ids, island_ids):
        list_to_islands.setdefault(list_id, set()).add(island_id)
        list_to_row[list_id] = row
    ambiguous_lists = {
        list_id: sorted(values)
        for list_id, values in list_to_islands.items()
        if len(values) > 1
    }
    island_list_set = set(island_list_ids)
    species_list_set = set(species_list_ids)
    repeated_island_ids = Counter(island_ids)
    empty_list_ids = sorted(island_list_set - species_list_set)

    species_island_ids = {
        next(iter(list_to_islands[list_id]))
        for list_id in species_list_set
        if list_id in list_to_islands and len(list_to_islands[list_id]) == 1
    }
    all_island_ids = set(island_ids)
    empty_context = []
    for list_id in empty_list_ids:
        row = list_to_row[list_id]
        island_id = row[island_id_col].strip()
        ref_id = row[ref_id_col].strip() if ref_id_col else ""
        sibling_lists = sorted(
            other_list
            for other_list, values in list_to_islands.items()
            if island_id in values and other_list != list_id
        )
        reference_row = reference_by_id.get(ref_id, {})
        empty_context.append({
            "list_id": list_id,
            "island_id": island_id,
            "island_name": next((row[key].strip() for key in row if key.casefold() == "island_name"), ""),
            "survey_year": next((row[key].strip() for key in row if key.casefold() == "survey_year"), ""),
            "ref_id": ref_id,
            "lists_for_same_island": repeated_island_ids[island_id],
            "sibling_list_ids": sibling_lists,
            "sibling_lists_with_species_rows": [value for value in sibling_lists if value in species_list_set],
            "reference_full_ref": next((reference_row[key].strip() for key in reference_row if key.casefold() == "full_ref"), ""),
            "reference_native_indicated": next((reference_row[key].strip() for key in reference_row if key.casefold() == "native_indicated"), ""),
            "reference_naturalised_indicated": next((reference_row[key].strip() for key in reference_row if key.casefold() == "naturalised_indicated"), ""),
        })

    return {
        "island_data_rows": len(islands),
        "unique_list_ids_island_data": len(island_list_set),
        "unique_island_ids": len(all_island_ids),
        "unique_island_ids_with_species_rows": len(species_island_ids),
        "unique_island_ids_without_species_rows": sorted(all_island_ids - species_island_ids),
        "islands_with_multiple_lists": sum(count > 1 for count in repeated_island_ids.values()),
        "maximum_lists_per_island": max(repeated_island_ids.values()),
        "species_data_rows": len(species),
        "unique_list_ids_species_data": len(species_list_set),
        "unique_standardized_species": len(set(species_names)),
        "species_list_ids_missing_from_island_data": sorted(species_list_set - island_list_set),
        "island_list_ids_without_species_rows": empty_list_ids,
        "island_lists_without_species_rows_context": empty_context,
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
    parser.add_argument("--reference-data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.island_data, args.species_data, args.reference_data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
