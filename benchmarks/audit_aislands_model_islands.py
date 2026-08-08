"""Audit geospatial/model-unit completeness for the frozen A-Islands benchmark.

This stage is outcome-free: it inspects only island/list metadata, the existence of
species rows, and the frozen A-Islands shapefile. It does not fit any support model,
calculate EOG structure, or inspect species-specific held-out performance.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
from pathlib import Path

import shapefile


def _read(path: Path) -> tuple[list[dict[str, str]], str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return list(csv.DictReader(io.StringIO(text))), encoding
    raise ValueError(f"unable to decode CSV: {path}")


def _column(rows: list[dict[str, str]], *names: str) -> str:
    if not rows:
        raise ValueError("source table is empty")
    wanted = {_normalise(name) for name in names}
    matches = [key for key in rows[0] if _normalise(key) in wanted]
    if len(matches) != 1:
        raise ValueError(f"missing or ambiguous column among {names}; available={list(rows[0])}")
    return matches[0]


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _shape_field(fields: list[str], *aliases: str, required: bool = False) -> str | None:
    wanted = {_normalise(alias) for alias in aliases}
    matches = [field for field in fields if _normalise(field) in wanted]
    if len(matches) == 1:
        return matches[0]
    if required:
        raise ValueError(
            f"missing or ambiguous shapefile field among {aliases}; available={fields}"
        )
    return None


def _finite(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _clean(value: object) -> str:
    return str(value or "").strip()


def _bbox_center(shape: shapefile.Shape) -> tuple[float | None, float | None]:
    bbox = getattr(shape, "bbox", None)
    if not bbox or len(bbox) < 4:
        return None, None
    xmin, ymin, xmax, ymax = (_finite(value) for value in bbox[:4])
    if None in (xmin, ymin, xmax, ymax):
        return None, None
    return (float(xmin) + float(xmax)) / 2.0, (float(ymin) + float(ymax)) / 2.0


def audit(
    island_data: Path,
    species_data: Path,
    shapefile_path: Path,
    projection_path: Path | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    islands, island_encoding = _read(island_data)
    species, species_encoding = _read(species_data)

    list_col = _column(islands, "List_ID", "list_ID")
    island_col = _column(islands, "Island_ID", "island_ID")
    species_list_col = _column(species, "List_ID", "list_ID")

    list_to_island: dict[str, str] = {}
    for row in islands:
        list_id = row[list_col].strip()
        island_id = row[island_col].strip()
        if not list_id or not island_id:
            raise ValueError("blank list_ID or island_ID in island_data")
        previous = list_to_island.get(list_id)
        if previous is not None and previous != island_id:
            raise ValueError(f"list_ID maps to multiple islands: {list_id}")
        list_to_island[list_id] = island_id

    species_list_ids: set[str] = set()
    for row in species:
        list_id = row[species_list_col].strip()
        if not list_id:
            raise ValueError("blank list_ID in species_data")
        if list_id not in list_to_island:
            raise ValueError(f"species_data list_ID missing from island_data: {list_id}")
        species_list_ids.add(list_id)
    surveyed_islands = sorted({list_to_island[list_id] for list_id in species_list_ids})

    reader = shapefile.Reader(str(shapefile_path), encoding="cp1252")
    fields = [field[0] for field in reader.fields[1:]]
    island_id_field = _shape_field(fields, "Island_ID", "island_ID", required=True)
    name_field = _shape_field(fields, "Island_name", "Island_Name", "Name")
    x_field = _shape_field(fields, "X", "Longitude", "Lon")
    y_field = _shape_field(fields, "Y", "Latitude", "Lat")
    area_field = _shape_field(fields, "Area", "Area_km2", "Area_km_2")
    arch1_field = _shape_field(fields, "Arch_lvl_1", "Arch_level_1", "Arch1")
    arch2_field = _shape_field(fields, "Arch_lvl_2", "Arch_level_2", "Arch2")

    shape_by_island: dict[str, tuple[dict[str, object], shapefile.Shape]] = {}
    duplicate_shape_islands: list[str] = []
    blank_shape_island_ids = 0
    for shape_record in reader.iterShapeRecords():
        record = shape_record.record.as_dict()
        island_id = _clean(record.get(island_id_field))
        if not island_id:
            blank_shape_island_ids += 1
            continue
        if island_id in shape_by_island:
            duplicate_shape_islands.append(island_id)
            continue
        shape_by_island[island_id] = (record, shape_record.shape)

    projection_text = ""
    if projection_path and projection_path.exists():
        projection_text = projection_path.read_text(encoding="utf-8", errors="replace").strip()

    output: list[dict[str, object]] = []
    missing_geometry_ids: list[str] = []
    invalid_coordinate_ids: list[str] = []
    missing_area_ids: list[str] = []
    nonpositive_area_ids: list[str] = []
    missing_arch1_ids: list[str] = []
    missing_arch2_ids: list[str] = []

    for island_id in surveyed_islands:
        payload = shape_by_island.get(island_id)
        if payload is None:
            missing_geometry_ids.append(island_id)
            output.append({
                "island_id": island_id,
                "shape_present": 0,
                "island_name": "",
                "x": "",
                "y": "",
                "coordinate_source": "",
                "area_km2": "",
                "arch_lvl_1": "",
                "arch_lvl_2": "",
                "coordinate_evaluable": 0,
                "area_evaluable": 0,
                "arch1_available": 0,
                "arch2_available": 0,
            })
            continue

        record, shape = payload
        x = _finite(record.get(x_field)) if x_field else None
        y = _finite(record.get(y_field)) if y_field else None
        coordinate_source = "dbf_XY" if x is not None and y is not None else ""
        if x is None or y is None:
            bbox_x, bbox_y = _bbox_center(shape)
            if bbox_x is not None and bbox_y is not None:
                x, y = bbox_x, bbox_y
                coordinate_source = "shape_bbox_center"

        coordinate_valid = (
            x is not None
            and y is not None
            and -180 <= x <= 180
            and -90 <= y <= 90
        )
        if not coordinate_valid:
            invalid_coordinate_ids.append(island_id)

        area = _finite(record.get(area_field)) if area_field else None
        if area is None:
            missing_area_ids.append(island_id)
        elif area <= 0:
            nonpositive_area_ids.append(island_id)

        arch1 = _clean(record.get(arch1_field)) if arch1_field else ""
        arch2 = _clean(record.get(arch2_field)) if arch2_field else ""
        if not arch1:
            missing_arch1_ids.append(island_id)
        if not arch2:
            missing_arch2_ids.append(island_id)

        output.append({
            "island_id": island_id,
            "shape_present": 1,
            "island_name": _clean(record.get(name_field)) if name_field else "",
            "x": x if x is not None else "",
            "y": y if y is not None else "",
            "coordinate_source": coordinate_source,
            "area_km2": area if area is not None else "",
            "arch_lvl_1": arch1,
            "arch_lvl_2": arch2,
            "coordinate_evaluable": int(coordinate_valid),
            "area_evaluable": int(area is not None and area > 0),
            "arch1_available": int(bool(arch1)),
            "arch2_available": int(bool(arch2)),
        })

    summary = {
        "island_data_encoding": island_encoding,
        "species_data_encoding": species_encoding,
        "surveyed_islands_with_species_rows": len(surveyed_islands),
        "shapefile_record_count": len(reader),
        "shapefile_fields": fields,
        "shapefile_field_mapping": {
            "island_id": island_id_field,
            "island_name": name_field,
            "x": x_field,
            "y": y_field,
            "area": area_field,
            "arch_lvl_1": arch1_field,
            "arch_lvl_2": arch2_field,
        },
        "projection_text": projection_text,
        "blank_shape_island_ids": blank_shape_island_ids,
        "duplicate_shape_island_ids": sorted(set(duplicate_shape_islands)),
        "shape_present_surveyed_islands": sum(int(row["shape_present"]) for row in output),
        "coordinate_evaluable_islands": sum(int(row["coordinate_evaluable"]) for row in output),
        "area_evaluable_islands": sum(int(row["area_evaluable"]) for row in output),
        "arch1_available_islands": sum(int(row["arch1_available"]) for row in output),
        "arch2_available_islands": sum(int(row["arch2_available"]) for row in output),
        "missing_geometry_island_ids": missing_geometry_ids,
        "invalid_coordinate_island_ids": invalid_coordinate_ids,
        "missing_area_island_ids": missing_area_ids,
        "nonpositive_area_island_ids": nonpositive_area_ids,
        "missing_arch1_island_ids": missing_arch1_ids,
        "missing_arch2_island_ids": missing_arch2_ids,
        "scientific_boundary": (
            "pre-model island metadata and geometry audit only; no SDM, EOG topology, reachability, or held-out performance inspected"
        ),
    }
    return output, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--shapefile", type=Path, required=True)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = audit(
        args.island_data,
        args.species_data,
        args.shapefile,
        args.projection,
    )
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
