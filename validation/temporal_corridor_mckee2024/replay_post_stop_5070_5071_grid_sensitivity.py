#!/usr/bin/env python3
"""Offline, source-SHA-gated EPSG:5070/5071 positional/grid sensitivity.

Only the original 12-hour GPS .shp POINT records may be read. No .dbf
records, animal IDs, timestamps, 2h holdout, EOG scores or raw points
are exported. Best datum transformation availability must be reported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
import warnings
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

import numpy as np

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "post_stop_5070_5071_datum_grid_sensitivity_protocol_v1.json"
SOURCE_SHA256 = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"
SOURCE_SIZE = 1539661
N = 28953
SOURCE_MEMBERS = {"GPS12hrs_Locs.dbf", "GPS12hrs_Locs.prj",
                  "GPS12hrs_Locs.shp", "GPS12hrs_Locs.shx"}
CRS_CODES = ("EPSG:5070", "EPSG:5071")
GRID_SIZES = (100, 250, 500, 1000, 5000)
GRID_ORIGIN = (-12021622.7691, 5012625.0685)
QUANTILES = (0.0, 0.5, 0.95, 0.99, 1.0)


def _source_points(archive_path: Path) -> np.ndarray:
    if archive_path.name != "GPS12hrs_Locs.zip" or archive_path.stat().st_size != SOURCE_SIZE:
        raise ValueError("Only exact 12-hour source ZIP and byte size are accepted")
    digest = hashlib.sha256()
    with archive_path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != SOURCE_SHA256:
        raise ValueError("Source ZIP SHA-256 differs from frozen Dryad identity")
    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) != 4 or {x.filename for x in infos} != SOURCE_MEMBERS:
            raise ValueError("Unexpected frozen 12-hour ZIP member set")
        for entry in infos:
            mode = (entry.external_attr >> 16) & 0xFFFF
            if (
                entry.is_dir() or entry.flag_bits & 1
                or stat.S_IFMT(mode) == stat.S_IFLNK
                or entry.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                or entry.file_size > 120_000_000
                or entry.file_size / max(1, entry.compress_size) >= 200
            ):
                raise ValueError("Unsafe source ZIP member")
        locations = np.empty((N, 2), dtype=np.float64)
        with archive.open("GPS12hrs_Locs.shp") as shp:
            header = shp.read(100)
            if (
                len(header) != 100
                or struct.unpack(">I", header[:4])[0] != 9994
                or struct.unpack("<I", header[28:32])[0] != 1000
                or struct.unpack("<I", header[32:36])[0] != 1
            ):
                raise ValueError("Source must be verified Point Shapefile")
            if struct.unpack(">I", header[24:28])[0] * 2 != archive.getinfo("GPS12hrs_Locs.shp").file_size:
                raise ValueError("Declared SHP length drift")
            for index in range(N):
                record_header = shp.read(8)
                if len(record_header) != 8:
                    raise ValueError("Unexpected SHP record count")
                number, length_words = struct.unpack(">II", record_header)
                body = shp.read(length_words * 2)
                if (number != index + 1 or length_words != 10 or
                    len(body) != 20 or struct.unpack("<I", body[:4])[0] != 1):
                    raise ValueError("Unexpected source Point record")
                locations[index] = struct.unpack("<dd", body[4:20])
            if shp.read(1):
                raise ValueError("More source records than frozen count")
    if not np.isfinite(locations).all():
        raise ValueError("Nonfinite source coordinates")
    return locations


def _same_grid_counts(a: np.ndarray, b: np.ndarray) -> list[dict]:
    """Compare both coordinate hypotheses on one *fixed* EPSG3857 grid."""
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 2:
        raise ValueError("Expected two matching Nx2 coordinate arrays")
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("Grid coordinates must be finite")
    origin = np.asarray(GRID_ORIGIN)
    result = []
    for width in GRID_SIZES:
        cells_a = np.floor((a - origin) / width).astype(np.int64)
        cells_b = np.floor((b - origin) / width).astype(np.int64)
        same = np.all(cells_a == cells_b, axis=1)
        matches = int(np.sum(same))
        result.append({
            "grid_width_m": width,
            "same_cell_count": matches,
            "different_cell_count": int(len(a) - matches),
            "same_cell_fraction": matches / len(a),
        })
    return result


def _quantiles(values: np.ndarray) -> dict[str, float]:
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("Displacement vector must be finite and nonempty")
    keys = ("minimum", "median", "p95", "p99", "maximum")
    return {
        key: round(float(value), 6)
        for key, value in zip(keys, np.quantile(values, QUANTILES), strict=True)
    }


def _check_protocol() -> dict:
    p = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    if (p.get("schema") != "eog.mckee2024.albers_datum_grid_sensitivity.v1"
        or p.get("status") != "FROZEN_PRE_ORIGINAL_POINT_TRANSFORM"):
        raise ValueError("Precommitted sensitivity protocol is missing or mutated")
    v = p["input"]
    if (v["sha256"] != SOURCE_SHA256 or v["size_bytes"] != SOURCE_SIZE
        or (v["candidate_A"], v["candidate_B"]) != CRS_CODES
        or tuple(v["grid_origin_in_reference_meters"]) != GRID_ORIGIN):
        raise ValueError("Frozen source identity or CRS/grid origin changed")
    if (tuple(p["sensitivity"]["grid_size_m"]) != GRID_SIZES
        or tuple(p["transformation_policy"]["WGS84_geodesic_quantiles"]) != QUANTILES
        or tuple(p["transformation_policy"]["planar_position_difference_quantiles"]) != QUANTILES):
        raise ValueError("Frozen grid widths or quantiles changed")
    if p["transformation_policy"]["grid_downloads_allowed"] is not False:
        raise ValueError("Datum grid network downloads are not allowed")
    return p


def run(archive_path: Path) -> dict:
    p = _check_protocol()
    import pyproj
    from pyproj import Geod, Transformer
    from pyproj.transformer import TransformerGroup

    pyproj.network.set_network_enabled(False)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        group = TransformerGroup(*CRS_CODES, always_xy=True)
    missing_grids = list(dict.fromkeys(
        grid.short_name for op in group.unavailable_operations
        for grid in op.grids if not grid.available
    ))
    points = _source_points(archive_path)
    transformed = {}
    for crs in CRS_CODES:
        to3857 = Transformer.from_crs(crs, "EPSG:3857", always_xy=True)
        to4326 = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        x, y = to3857.transform(points[:, 0], points[:, 1])
        lon, lat = to4326.transform(points[:, 0], points[:, 1])
        transformed[crs] = {
            "xy": np.column_stack((x, y)),
            "lonlat": np.column_stack((lon, lat)),
            "operation_accuracy_m": to3857.accuracy,
        }
        if (not np.isfinite(transformed[crs]["xy"]).all()
            or not np.isfinite(transformed[crs]["lonlat"]).all()):
            raise ValueError("CRS transformation returned nonfinite coordinates")

    a, b = [transformed[crs] for crs in CRS_CODES]
    geographic = Geod(ellps="WGS84")
    _, _, distances = geographic.inv(
        a["lonlat"][:, 0], a["lonlat"][:, 1],
        b["lonlat"][:, 0], b["lonlat"][:, 1],
    )
    dxy = np.linalg.norm(a["xy"] - b["xy"], axis=1)
    return {
        "schema": "eog.mckee2024.albers_datum_grid_sensitivity_result.v1",
        "status": (
            "CONDITIONAL_OFFLINE_BALLPARK__BEST_DATUM_GRID_UNAVAILABLE"
            if not group.best_available else
            "OFFLINE_BEST_DATUM_TRANSFORMATION_AVAILABLE__AUTHOR_CRS_UNCONFIRMED"
        ),
        "source_sha256_verified": True,
        "source_sha256": SOURCE_SHA256,
        "source_file_size": SOURCE_SIZE,
        "sparse_points": len(points),
        "coordinate_hypotheses": list(CRS_CODES),
        "comparison_crs": "EPSG:3857",
        "comparison_grid_origin_m": list(GRID_ORIGIN),
        "PROJ_network_enabled": pyproj.network.is_network_enabled(),
        "pyproj_version": pyproj.__version__,
        "PROJ_version": pyproj.proj_version_str,
        "best_available_datum_operation": group.best_available,
        "available_operation_count": len(group.transformers),
        "unavailable_operation_count": len(group.unavailable_operations),
        "missing_grid_names_first_10": missing_grids[:10],
        "available_datum_operation_description": [
            {"description": tr.description, "accuracy_m": tr.accuracy}
            for tr in group.transformers[:2]
        ],
        "planar_3857_displacement_m": _quantiles(dxy),
        "WGS84_geodesic_displacement_m": _quantiles(np.abs(distances)),
        "fixed_grid_agreement": _same_grid_counts(a["xy"], b["xy"]),
        "all_raw_xy_pairwise_distances_identical_by_construction": True,
        "author_intended_CRS_verified": False,
        "source_CRS_STOP_unchanged": True,
        "dense_2hour_GPS_opened": False,
        "DBF_records_opened": False,
        "raw_points_or_individual_IDs_exported": False,
        "prediction_scored": False,
        "original_EOG_WF_scored_endpoints_unchanged": 3,
        "precommitted_protocol_status": p["status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source_zip)
    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
