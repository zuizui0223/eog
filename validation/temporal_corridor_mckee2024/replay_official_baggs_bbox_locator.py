#!/usr/bin/env python3
"""Exact-source 12h GPS / official WGFD Baggs EXTENT comparison.

Only aggregate locator counts are emitted. The official rectangular bounding
extent is NOT a biological corridor polygon, and cannot prove individual
movement or recover the authors' intended CRS. Original GPS stays local.
Requires pyproj and exact source ZIP; 2h data is never referenced.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import stat
import struct
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_official_baggs_locator_protocol_v1.json"
SHA = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"
FILES = {"GPS12hrs_Locs.dbf", "GPS12hrs_Locs.prj",
         "GPS12hrs_Locs.shp", "GPS12hrs_Locs.shx"}
CODES = ("EPSG:3742", "EPSG:5070", "EPSG:5071", "ESRI:102003", "EPSG:3857")
BBOX = (-12021622.7691, 5012625.0685, -11916202.5626, 5110144.4915)
BUFFER = 5000


def _source(path: Path):
    if path.name != "GPS12hrs_Locs.zip" or path.stat().st_size != 1539661:
        raise ValueError("Only exact-size 12h ZIP input is permitted")
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != SHA:
        raise ValueError("Source ZIP does not match frozen Dryad SHA-256")
    archive = ZipFile(path)
    members = archive.infolist()
    if len(members) != 4 or {i.filename for i in members} != FILES:
        archive.close()
        raise ValueError("Unexpected source ZIP components")
    for info in members:
        if (info.is_dir() or info.flag_bits & 1
            or stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK
            or info.compress_type not in (ZIP_DEFLATED, ZIP_STORED)
            or info.file_size > 120000000
            or info.file_size / max(1, info.compress_size) >= 200):
            archive.close()
            raise ValueError("Unsafe source ZIP component")
    return archive


def _validate_protocol():
    data = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if data["schema"] != "eog.mckee2024.post_stop_official_baggs_extent_crs_locator.v1":
        raise ValueError("Unknown protocol")
    if data["status"] != "FROZEN_BEFORE_CROSS_SOURCE_SPATIAL_COMPARISON":
        raise ValueError("Protocol not frozen")
    if data["source"]["sha256"] != SHA or data["source"]["original_file_id"] != 3334125:
        raise ValueError("Frozen source differs")
    ref = data["independent_geographic_reference"]
    bounds = tuple(ref[f"public_full_extent_web_mercator_{x}"]
                   for x in ("xmin", "ymin", "xmax", "ymax"))
    if bounds != BBOX or data["predeclared_buffer_meters"] != BUFFER:
        raise ValueError("Frozen WGFD extent/buffer differs")
    if tuple(x["crs"] for x in data["hypotheses"]) != CODES:
        raise ValueError("Frozen competing CRS hypotheses differ")
    if data["dense_2h_access"] is not False:
        raise ValueError("Dense holdout must remain sealed")


def _columns(dbf):
    head = dbf.read(32)
    if len(head) != 32:
        raise ValueError("Truncated DBF")
    count, header_len, record_len = (
        struct.unpack("<I", head[4:8])[0],
        struct.unpack("<H", head[8:10])[0],
        struct.unpack("<H", head[10:12])[0],
    )
    if count != 28953 or not 33 <= header_len <= 16384:
        raise ValueError("Unfrozen DBF count/header")
    desc = dbf.read(header_len - 32)
    if len(desc) != header_len - 32 or desc[-1] != 13:
        raise ValueError("Invalid DBF fields")
    start, cols = 1, {}
    for k in range(0, len(desc) - 1, 32):
        raw = desc[k:k + 32]
        name = raw[:11].split(b"\x00")[0].decode("ascii")
        width = raw[16]
        cols[name] = (start, start + width)
        start += width
    if start != record_len or "Herd" not in cols:
        raise ValueError("Unrecognized DBF record layout")
    return count, record_len, cols


def run(path: Path):
    _validate_protocol()
    from pyproj import Transformer
    tr = {c: Transformer.from_crs(c, "EPSG:3857", always_xy=True) for c in CODES}
    finite = Counter()
    inside = Counter()
    buffered = Counter()
    all_records = selected = 0
    with _source(path) as archive:
        with archive.open("GPS12hrs_Locs.shp") as shp, archive.open("GPS12hrs_Locs.dbf") as dbf:
            header = shp.read(100)
            if len(header) != 100 or struct.unpack("<I", header[32:36])[0] != 1:
                raise ValueError("Expected Point shapefile")
            n, record_len, cols = _columns(dbf)
            a, b = cols["Herd"]
            for i in range(n):
                record_head = shp.read(8)
                row = dbf.read(record_len)
                if len(record_head) != 8 or len(row) != record_len or row[0] != 32:
                    raise ValueError("Truncated or deleted source record")
                index, words = struct.unpack(">II", record_head)
                geom = shp.read(words * 2)
                if index != i + 1 or words != 10 or len(geom) != 20:
                    raise ValueError("Unexpected Point geometry")
                if struct.unpack("<I", geom[:4])[0] != 1:
                    raise ValueError("Not a Point")
                x, y = struct.unpack("<dd", geom[4:20])
                all_records += 1
                if row[a:b].decode("latin-1").strip() != "AtlanticRim":
                    continue
                selected += 1
                for crs, fn in tr.items():
                    xx, yy = fn.transform(x, y)
                    if not (math.isfinite(xx) and math.isfinite(yy)):
                        continue
                    finite[crs] += 1
                    if BBOX[0] <= xx <= BBOX[2] and BBOX[1] <= yy <= BBOX[3]:
                        inside[crs] += 1
                    if (BBOX[0] - BUFFER <= xx <= BBOX[2] + BUFFER
                        and BBOX[1] - BUFFER <= yy <= BBOX[3] + BUFFER):
                        buffered[crs] += 1
            if all_records != 28953 or selected != 17248:
                raise ValueError("Frozen public herd/record count differs")
    return {
        "schema": "eog.mckee2024.post_stop_official_baggs_locator_result.v1",
        "source_sha256": SHA, "all_12h_records": all_records,
        "AtlanticRim_records": selected, "wgfd_extent_epsg3857": list(BBOX),
        "predeclared_extension_meters": BUFFER,
        "crs_diagnostics": [
            {
                "input_crs": code,
                "finite_transform_count": finite[code],
                "inside_public_full_bbox_count": inside[code],
                "inside_full_bbox_plus_5km_count": buffered[code],
                "bbox_fraction": inside[code] / selected,
                "bbox_5km_fraction": buffered[code] / selected,
            }
            for code in CODES
        ],
        "crs_author_intent_confirmed": False,
        "two_hour_holdout_opened": False,
        "raw_coordinates_or_animal_ids_exported": False,
        "ecological_prediction_scored": False,
        "EOG_WF_scored_endpoints_unchanged": 3,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run(args.source_zip)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(serialized)
    else:
        args.output.write_text(serialized, encoding="utf-8")


if __name__ == "__main__":
    main()
