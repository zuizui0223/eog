"""Audit geospatial/model-unit completeness for the frozen A-Islands benchmark.

This stage is outcome-free: it inspects only island/list metadata and the existence of
species rows. It does not fit any support model, calculate EOG structure, or inspect
species-specific held-out performance.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from collections import defaultdict
from pathlib import Path


def _read(path: Path) -> tuple[list[dict[str, str]], str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return list(csv.DictReader(io.StringIO(text))), encoding
    raise ValueError(f"unable to decode CSV: {path}")


def _column(rows: list[dict[str, str]], *names: str, required: bool = True) -> str | None:
    if not rows:
        raise ValueError("source table is empty")
    wanted = {name.casefold() for name in names}
    matches = [key for key in rows[0] if key.casefold() in wanted]
    if len(matches) == 1:
        return matches[0]
    if required:
        raise ValueError(f"missing or ambiguous column among {names}; available={list(rows[0])}")
    return None


def _finite(value: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _values(rows: list[dict[str, str]], column: str | None) -> list[str]:
    if column is None:
        return []
    return sorted({row[column].strip() for row in rows if row[column].strip()})


def audit(island_data: Path, species_data: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    islands, island_encoding = _read(island_data)
    species, species_encoding = _read(species_data)

    list_col = _column(islands, "List_ID", "list_ID")
    island_col = _column(islands, "Island_ID", "island_ID")
    species_list_col = _column(species, "List_ID", "list_ID")
    x_col = _column(islands, "X")
    y_col = _column(islands, "Y")
    area_col = _column(islands, "Area")
    arch1_col = _column(islands, "Arch_lvl_1", "Arch_level_1", required=False)
    arch2_col = _column(islands, "Arch_lvl_2", "Arch_level_2", required=False)
    name_col = _column(islands, "Island_name", "Island_Name", required=False)

    list_to_island: dict[str, str] = {}
    island_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in islands:
        list_id = row[list_col].strip()
        island_id = row[island_col].strip()
        if not list_id or not island_id:
            raise ValueError("blank list_ID or island_ID in island_data")
        previous = list_to_island.get(list_id)
        if previous is not None and previous != island_id:
            raise ValueError(f"list_ID maps to multiple islands: {list_id}")
        list_to_island[list_id] = island_id
        island_rows[island_id].append(row)

    species_list_ids: set[str] = set()
    for row in species:
        list_id = row[species_list_col].strip()
        if not list_id:
            raise ValueError("blank list_ID in species_data")
        if list_id not in list_to_island:
            raise ValueError(f"species_data list_ID missing from island_data: {list_id}")
        species_list_ids.add(list_id)

    surveyed_islands = sorted({list_to_island[list_id] for list_id in species_list_ids})
    output: list[dict[str, object]] = []
    missing_coordinate_ids: list[str] = []
    invalid_coordinate_ids: list[str] = []
    missing_area_ids: list[str] = []
    nonpositive_area_ids: list[str] = []
    missing_arch1_ids: list[str] = []
    missing_arch2_ids: list[str] = []
    inconsistent_islands: dict[str, list[str]] = {}

    for island_id in surveyed_islands:
        rows = island_rows[island_id]
        x_values = _values(rows, x_col)
        y_values = _values(rows, y_col)
        area_values = _values(rows, area_col)
        arch1_values = _values(rows, arch1_col)
        arch2_values = _values(rows, arch2_col)
        name_values = _values(rows, name_col)

        inconsistencies = []
        for label, values in (
            ("X", x_values),
            ("Y", y_values),
            ("Area", area_values),
            ("Arch_lvl_1", arch1_values),
            ("Arch_lvl_2", arch2_values),
        ):
            if len(values) > 1:
                inconsistencies.append(label)
        if inconsistencies:
            inconsistent_islands[island_id] = inconsistencies

        x = _finite(x_values[0]) if len(x_values) == 1 else None
        y = _finite(y_values[0]) if len(y_values) == 1 else None
        area = _finite(area_values[0]) if len(area_values) == 1 else None
        coord_missing = not x_values or not y_values
        coord_invalid = (
            not coord_missing
            and (x is None or y is None or not (-180 <= x <= 180) or not (-90 <= y <= 90))
        )
        area_missing = not area_values
        area_nonpositive = not area_missing and (area is None or area <= 0)
        arch1_missing = not arch1_values
        arch2_missing = not arch2_values

        if coord_missing:
            missing_coordinate_ids.append(island_id)
        if coord_invalid:
            invalid_coordinate_ids.append(island_id)
        if area_missing:
            missing_area_ids.append(island_id)
        if area_nonpositive:
            nonpositive_area_ids.append(island_id)
        if arch1_missing:
            missing_arch1_ids.append(island_id)
        if arch2_missing:
            missing_arch2_ids.append(island_id)

        coordinate_evaluable = not coord_missing and not coord_invalid and not inconsistencies
        output.append({
            "island_id": island_id,
            "n_list_rows": len(rows),
            "island_name_values": "|".join(name_values),
            "x": x if x is not None else "",
            "y": y if y is not None else "",
            "area_km2": area if area is not None else "",
            "arch_lvl_1_values": "|".join(arch1_values),
            "arch_lvl_2_values": "|".join(arch2_values),
            "coordinate_evaluable": int(coordinate_evaluable),
            "area_evaluable": int(not area_missing and not area_nonpositive and "Area" not in inconsistencies),
            "arch1_available": int(not arch1_missing and "Arch_lvl_1" not in inconsistencies),
            "arch2_available": int(not arch2_missing and "Arch_lvl_2" not in inconsistencies),
            "metadata_inconsistencies": "|".join(inconsistencies),
        })

    summary = {
        "island_data_encoding": island_encoding,
        "species_data_encoding": species_encoding,
        "surveyed_islands_with_species_rows": len(surveyed_islands),
        "coordinate_evaluable_islands": sum(int(row["coordinate_evaluable"]) for row in output),
        "area_evaluable_islands": sum(int(row["area_evaluable"]) for row in output),
        "arch1_available_islands": sum(int(row["arch1_available"]) for row in output),
        "arch2_available_islands": sum(int(row["arch2_available"]) for row in output),
        "missing_coordinate_island_ids": missing_coordinate_ids,
        "invalid_coordinate_island_ids": invalid_coordinate_ids,
        "missing_area_island_ids": missing_area_ids,
        "nonpositive_area_island_ids": nonpositive_area_ids,
        "missing_arch1_island_ids": missing_arch1_ids,
        "missing_arch2_island_ids": missing_arch2_ids,
        "inconsistent_island_metadata": inconsistent_islands,
        "scientific_boundary": (
            "pre-model island metadata audit only; no SDM, EOG topology, reachability, or held-out performance inspected"
        ),
    }
    return output, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = audit(args.island_data, args.species_data)
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
