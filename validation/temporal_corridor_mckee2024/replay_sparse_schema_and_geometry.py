#!/usr/bin/env python3
"""Reproduce verified McKee 2024 12h shapefile schema and CRS diagnostics.

No 2h input, animal IDs, dates, coordinate tables or individual tracks are
produced. The CLI requires a prior frozen stage protocol and an original
publisher-SHA-matching ZIP. Use --stage schema before --stage geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import stat
import struct
import zipfile

HERE = Path(__file__).resolve().parent
ZIP_SHA256 = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"
ZIP_SIZE = 1539661
EXPECTED_MEMBERS = {f"GPS12hrs_Locs.{ext}" for ext in ("dbf", "prj", "shp", "shx")}
EXPECTED_FIELDS = (
    "State", "Herd", "SpcsCmm", "SpcsScn", "AID",
    "SeasnYr", "Season", "Year", "Timstmp", "UTM_E", "UTM_N",
)
REGION = (-114.5, -102.0, 39.0, 47.0)
CANDIDATES = ("EPSG:3742", "EPSG:5070", "ESRI:102003", "EPSG:3857")


def verify_source(path: Path) -> zipfile.ZipFile:
    if path.name != "GPS12hrs_Locs.zip" or path.stat().st_size != ZIP_SIZE:
        raise ValueError("Only exact 12h source filename/size accepted")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(part)
    if digest.hexdigest() != ZIP_SHA256:
        raise ValueError("Source SHA-256 not equal to frozen Dryad identity")
    archive = zipfile.ZipFile(path)
    infos = archive.infolist()
    if {i.filename for i in infos} != EXPECTED_MEMBERS or len(infos) != 4:
        archive.close()
        raise ValueError("Not the frozen single-layer 12h ZIP")
    for i in infos:
        p = PurePosixPath(i.filename)
        if (
            p.is_absolute() or ".." in p.parts or "\\" in i.filename
            or i.is_dir() or i.flag_bits & 1
            or stat.S_IFMT((i.external_attr >> 16) & 0xFFFF) == stat.S_IFLNK
            or i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
            or i.file_size > 120_000_000
            or i.file_size / max(1, i.compress_size) >= 200
        ):
            archive.close()
            raise ValueError("Unsafe shapefile archive member")
    return archive


def dbf_schema(archive: zipfile.ZipFile):
    with archive.open("GPS12hrs_Locs.dbf") as fp:
        header = fp.read(32)
        n = struct.unpack("<I", header[4:8])[0]
        length = struct.unpack("<H", header[8:10])[0]
        row_length = struct.unpack("<H", header[10:12])[0]
        if n != 28953 or not 33 <= length <= 16384:
            raise ValueError("DBF count/header length mismatch")
        d = fp.read(length - 32)
        if len(d) != length - 32 or d[-1] != 13:
            raise ValueError("Malformed field descriptor terminator")
    fields = {}
    cursor = 1
    for offset in range(0, len(d) - 1, 32):
        desc = d[offset:offset + 32]
        field = desc[:11].split(b"\x00")[0].decode("ascii")
        width = desc[16]
        fields[field] = (cursor, cursor + width)
        cursor += width
    if tuple(fields) != EXPECTED_FIELDS or cursor != row_length:
        raise ValueError("Physical DBF names or widths changed")
    return n, length, row_length, fields


def read_header(archive, extension):
    filename = "GPS12hrs_Locs." + extension
    with archive.open(filename) as fp:
        head = fp.read(100)
    if len(head) != 100 or struct.unpack(">I", head[:4])[0] != 9994:
        raise ValueError("Not a valid shape header")
    if struct.unpack("<I", head[28:32])[0] != 1000:
        raise ValueError("Unexpected shape version")
    if struct.unpack("<I", head[32:36])[0] != 1:
        raise ValueError("Expected Point feature type only")
    if struct.unpack(">I", head[24:28])[0] * 2 != archive.getinfo(filename).file_size:
        raise ValueError("Declared shape bytes differ from archive")
    return head


def run(archive, stage):
    count, header_len, row_len, fields = dbf_schema(archive)
    read_header(archive, "shp")
    read_header(archive, "shx")
    if (archive.getinfo("GPS12hrs_Locs.shx").file_size - 100) // 8 != count:
        raise ValueError("SHP index count mismatches DBF")
    receipt = {
        "schema": "eog.mckee2024.sparse12h.source_replay.v1",
        "stage": stage,
        "source_sha256_verified": True,
        "file_bytes": ZIP_SIZE,
        "dbf_and_index_count": count,
        "dense_2h_holdout_opened": False,
        "animal_ID_or_coordinates_exported": False,
        "ecological_scores_computed": False,
    }
    if stage == "schema":
        with archive.open("GPS12hrs_Locs.prj") as fp:
            text = fp.read(65537)
        if len(text) > 65536:
            raise ValueError("Projection text too large")
        from pyproj import CRS
        receipt["physical_field_names"] = list(fields)
        receipt["declared_prj_epsg"] = CRS.from_wkt(text.decode("utf-8-sig")).to_epsg()
        receipt["shape_type"] = 1
        receipt["status"] = "SCHEMA_ONLY__NO_ROW_ACCESS"
        return receipt
    if stage != "geometry":
        raise ValueError("Only schema or geometry stage accepted")
    from pyproj import Transformer
    transforms = {c: Transformer.from_crs(c, "EPSG:4326", always_xy=True)
                  for c in CANDIDATES}
    region_counts = {c: 0 for c in CANDIDATES}
    same = 0
    with archive.open("GPS12hrs_Locs.shp") as shp, archive.open("GPS12hrs_Locs.dbf") as dbf:
        shp.read(100)
        dbf.read(header_len)
        for index in range(count):
            shape_record_header = shp.read(8)
            row = dbf.read(row_len)
            if len(shape_record_header) != 8 or len(row) != row_len or row[0] != 32:
                raise ValueError("Truncated shape or deleted DBF record")
            number, words = struct.unpack(">II", shape_record_header)
            shape_record = shp.read(words * 2)
            if number != index + 1 or words != 10 or len(shape_record) != 20:
                raise ValueError("Unexpected point record shape")
            if struct.unpack("<I", shape_record[:4])[0] != 1:
                raise ValueError("Not a Point record")
            x, y = struct.unpack("<dd", shape_record[4:20])
            ax, bx = fields["UTM_E"]
            ay, by = fields["UTM_N"]
            dx = float(row[ax:bx].decode("ascii").strip())
            dy = float(row[ay:by].decode("ascii").strip())
            if max(abs(dx - x), abs(dy - y)) <= 1e-6:
                same += 1
            for crs, transformer in transforms.items():
                lon, lat = transformer.transform(x, y)
                if (math.isfinite(lon) and math.isfinite(lat)
                        and REGION[0] <= lon <= REGION[1]
                        and REGION[2] <= lat <= REGION[3]):
                    region_counts[crs] += 1
    receipt.update({
        "point_vs_DBF_xy_matches": same,
        "candidate_region_counts": region_counts,
        "predeclared_broad_WY_ID_lonlat_bounds": REGION,
        "publisher_PRJ_EPSG": 3742,
        "candidate_CRS_accepted_as_truth": False,
        "status": "CRS_CONFLICT_DIAGNOSTIC_ONLY__NO_AUTOMATIC_CORRECTION",
    })
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--stage", choices=("schema", "geometry"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    protocol = ("gate1_sparse_zip_schema_protocol_v1.json" if args.stage == "schema"
                else "post_stop_crs_geometry_protocol_v1.json")
    if not (HERE / protocol).is_file():
        raise SystemExit("Required frozen stage protocol missing")
    with verify_source(args.zip) as archive:
        receipt = run(archive, args.stage)
    output = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
