"""Outcome-free polygon-area audit for the frozen A-Islands v1.0 shapefile.

This script is a gate for the island-isolation adequacy extension.  It derives island
area only from the exact A-Islands polygon geometry already acquired by the frozen
source workflow.  It never reads species identities, occurrence outcomes, SDM/EOG
scores, or held-out performance.

Areas are computed on a sphere with a local Lambert azimuthal equal-area projection
centred on the frozen DBF centroid for each island.  Polygon parts are accumulated as
signed rings so correctly oriented interior rings subtract from exterior rings.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

import shapefile


EARTH_RADIUS_KM = 6371.0088
POLYGON_SHAPE_TYPES = {
    shapefile.POLYGON: "POLYGON",
    shapefile.POLYGONM: "POLYGONM",
    shapefile.POLYGONZ: "POLYGONZ",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_id(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if math.isfinite(number) and number.is_integer():
        return str(int(number))
    return text


def _read_audit(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("island audit table is empty")
    required = {"island_id", "x", "y", "coordinate_evaluable"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"island audit missing required columns: {sorted(missing)}")
    return rows


def _wrap_radians(delta: float) -> float:
    return (delta + math.pi) % (2.0 * math.pi) - math.pi


def _laea_xy_km(
    longitude_deg: float,
    latitude_deg: float,
    center_longitude_deg: float,
    center_latitude_deg: float,
) -> tuple[float, float]:
    """Project one lon/lat point using spherical Lambert azimuthal equal area."""
    lon = math.radians(longitude_deg)
    lat = math.radians(latitude_deg)
    lon0 = math.radians(center_longitude_deg)
    lat0 = math.radians(center_latitude_deg)
    dlon = _wrap_radians(lon - lon0)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lat0 = math.sin(lat0)
    cos_lat0 = math.cos(lat0)
    denominator = 1.0 + sin_lat0 * sin_lat + cos_lat0 * cos_lat * math.cos(dlon)
    if denominator <= 1e-15:
        raise ValueError("polygon vertex is at or numerically near the projection antipode")
    k = math.sqrt(2.0 / denominator)
    x = EARTH_RADIUS_KM * k * cos_lat * math.sin(dlon)
    y = EARTH_RADIUS_KM * k * (
        cos_lat0 * sin_lat - sin_lat0 * cos_lat * math.cos(dlon)
    )
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("non-finite equal-area projected coordinate")
    return x, y


def _signed_ring_area_km2(
    ring: Sequence[Sequence[float]],
    *,
    center_longitude_deg: float,
    center_latitude_deg: float,
) -> float:
    if len(ring) < 3:
        raise ValueError("polygon ring has fewer than three points")
    projected = [
        _laea_xy_km(float(point[0]), float(point[1]), center_longitude_deg, center_latitude_deg)
        for point in ring
    ]
    if projected[0] != projected[-1]:
        projected.append(projected[0])
    twice_area = 0.0
    for (x0, y0), (x1, y1) in zip(projected[:-1], projected[1:]):
        twice_area += x0 * y1 - x1 * y0
    return 0.5 * twice_area


def _shape_rings(shape: shapefile.Shape) -> list[list[Sequence[float]]]:
    points = list(shape.points)
    starts = list(shape.parts) + [len(points)]
    rings: list[list[Sequence[float]]] = []
    for start, end in zip(starts[:-1], starts[1:]):
        ring = points[int(start):int(end)]
        if ring:
            rings.append(ring)
    return rings


def spherical_polygon_area_km2(
    shape: shapefile.Shape,
    *,
    center_longitude_deg: float,
    center_latitude_deg: float,
) -> tuple[float, list[float]]:
    """Return total polygon area and signed part areas in square kilometres."""
    if shape.shapeType not in POLYGON_SHAPE_TYPES:
        raise ValueError(
            f"shape type {shape.shapeTypeName!r} is not one of {sorted(POLYGON_SHAPE_TYPES.values())}"
        )
    rings = _shape_rings(shape)
    if not rings:
        raise ValueError("polygon contains no rings")
    signed = [
        _signed_ring_area_km2(
            ring,
            center_longitude_deg=center_longitude_deg,
            center_latitude_deg=center_latitude_deg,
        )
        for ring in rings
    ]
    total = abs(float(sum(signed)))
    if not math.isfinite(total) or total <= 0:
        raise ValueError("derived polygon area is not finite and positive")
    return total, signed


def _record_field(fields: Sequence[str], wanted: str) -> str:
    matches = [field for field in fields if field.casefold() == wanted.casefold()]
    if len(matches) != 1:
        raise ValueError(f"expected one shapefile field {wanted!r}; available={list(fields)}")
    return matches[0]


def audit_polygon_areas(
    audit_csv: Path,
    shapefile_path: Path,
    *,
    projection_path: Path | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    audit_rows = _read_audit(audit_csv)
    surveyed = {_canonical_id(row["island_id"]): row for row in audit_rows}
    if len(surveyed) != len(audit_rows):
        raise ValueError("island audit contains duplicate/blank canonical island IDs")

    for island_id, row in surveyed.items():
        if row["coordinate_evaluable"].strip() != "1":
            raise ValueError(f"island {island_id} lacks a frozen evaluable centroid")
        lon = float(row["x"])
        lat = float(row["y"])
        if not (math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"island {island_id} has invalid frozen centroid")

    reader = shapefile.Reader(str(shapefile_path), encoding="cp1252")
    shape_type_name = POLYGON_SHAPE_TYPES.get(reader.shapeType, reader.shapeTypeName)
    fields = [field[0] for field in reader.fields[1:]]
    island_field = _record_field(fields, "island_ID")

    shapes: dict[str, shapefile.Shape] = {}
    duplicate_shape_ids: list[str] = []
    for shape_record in reader.iterShapeRecords():
        record = shape_record.record.as_dict()
        island_id = _canonical_id(record.get(island_field))
        if not island_id:
            continue
        if island_id in shapes:
            duplicate_shape_ids.append(island_id)
            continue
        shapes[island_id] = shape_record.shape

    rows: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for island_id in sorted(surveyed, key=int):
        audit_row = surveyed[island_id]
        shape = shapes.get(island_id)
        if shape is None:
            failures.append({"island_id": island_id, "reason": "missing polygon geometry"})
            rows.append({
                "island_id": island_id,
                "area_km2": "",
                "part_count": 0,
                "point_count": 0,
                "signed_positive_rings": 0,
                "signed_negative_rings": 0,
                "finite_positive": 0,
                "failure": "missing polygon geometry",
            })
            continue
        try:
            area, signed = spherical_polygon_area_km2(
                shape,
                center_longitude_deg=float(audit_row["x"]),
                center_latitude_deg=float(audit_row["y"]),
            )
            rows.append({
                "island_id": island_id,
                "area_km2": area,
                "part_count": len(_shape_rings(shape)),
                "point_count": len(shape.points),
                "signed_positive_rings": sum(value > 0 for value in signed),
                "signed_negative_rings": sum(value < 0 for value in signed),
                "finite_positive": 1,
                "failure": "",
            })
        except ValueError as exc:
            failures.append({"island_id": island_id, "reason": str(exc)})
            rows.append({
                "island_id": island_id,
                "area_km2": "",
                "part_count": len(_shape_rings(shape)),
                "point_count": len(shape.points),
                "signed_positive_rings": 0,
                "signed_negative_rings": 0,
                "finite_positive": 0,
                "failure": str(exc),
            })

    finite_areas = [float(row["area_km2"]) for row in rows if row["finite_positive"] == 1]
    sorted_areas = sorted(finite_areas)

    def quantile(p: float) -> float | None:
        if not sorted_areas:
            return None
        position = (len(sorted_areas) - 1) * p
        lower = int(math.floor(position))
        upper = int(math.ceil(position))
        if lower == upper:
            return sorted_areas[lower]
        weight = position - lower
        return sorted_areas[lower] * (1.0 - weight) + sorted_areas[upper] * weight

    projection_text = ""
    if projection_path and projection_path.exists():
        projection_text = projection_path.read_text(encoding="utf-8", errors="replace").strip()

    summary: dict[str, object] = {
        "status": "outcome_free_aislands_polygon_area_audit",
        "shapefile_type": shape_type_name,
        "shapefile_type_code": int(reader.shapeType),
        "shapefile_record_count": len(reader),
        "surveyed_islands": len(surveyed),
        "surveyed_shape_matches": sum(island_id in shapes for island_id in surveyed),
        "duplicate_shape_island_ids": sorted(set(duplicate_shape_ids), key=int),
        "finite_positive_area_islands": len(finite_areas),
        "failed_islands": failures,
        "derived_area_km2": {
            "min": min(finite_areas) if finite_areas else None,
            "q25": quantile(0.25),
            "median": quantile(0.5),
            "q75": quantile(0.75),
            "max": max(finite_areas) if finite_areas else None,
        },
        "area_method": "spherical Lambert azimuthal equal-area per island; signed polygon rings; Earth radius 6371.0088 km",
        "projection_text": projection_text,
        "input_sha256": {
            "island_audit_csv": _sha256(audit_csv),
            "shp": _sha256(shapefile_path),
            "shx": _sha256(shapefile_path.with_suffix(".shx")) if shapefile_path.with_suffix(".shx").exists() else None,
            "dbf": _sha256(shapefile_path.with_suffix(".dbf")) if shapefile_path.with_suffix(".dbf").exists() else None,
            "prj": _sha256(projection_path) if projection_path and projection_path.exists() else None,
        },
        "gate_passes": (
            shape_type_name in POLYGON_SHAPE_TYPES.values()
            and len(surveyed) == 842
            and len(finite_areas) == 842
            and not failures
            and not duplicate_shape_ids
        ),
        "species_outcomes_used": False,
        "sdm_outputs_used": False,
        "eog_outputs_used": False,
        "scientific_boundary": "same-source geometry audit only; no occurrence outcome is read or used",
    }
    return rows, summary


def _write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError("cannot write empty polygon-area audit")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--shapefile", type=Path, required=True)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = audit_polygon_areas(
        args.audit_csv,
        args.shapefile,
        projection_path=args.projection,
    )
    _write_csv(args.output_csv, rows)
    summary["output_area_table_sha256"] = _sha256(args.output_csv)
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not summary["gate_passes"]:
        raise SystemExit("A-Islands polygon-area gate failed; outcome extension is forbidden")


if __name__ == "__main__":
    main()
