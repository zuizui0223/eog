#!/usr/bin/env python3
"""Read only publication/archive file headers from the exact McKee 12h ZIP.

This never opens a DBF row, SHP point, raw track, animal ID or the dense
2h GPS. DOS ZIP timestamps and DBF last-update are mutable metadata,
not verified authorship, creation time, clock offset or R version.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import stat
import struct
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_archived_zip_dbf_header_protocol_v1.json"
ZIP_SHA256 = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"
ZIP_SIZE = 1539661
MEMBERS = (
    "GPS12hrs_Locs.dbf", "GPS12hrs_Locs.prj",
    "GPS12hrs_Locs.shp", "GPS12hrs_Locs.shx",
)


def _guard() -> dict:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    s = p["source"]
    if (
        p["schema"] != "eog.mckee2024.prepublication_original_archive_header_provenance.v1"
        or p["status"] != "FROZEN_BEFORE_NEW_DBF_HEADER_AND_LOCAL_ZIP_METADATA_INSPECTION"
        or s["sha256"] != ZIP_SHA256 or s["size_bytes"] != ZIP_SIZE
        or tuple(s["members"]) != MEMBERS or s["no_dense_2h_access"] is not True
    ):
        raise ValueError("Original archive metadata protocol changed")
    return p


def read_headers(source_zip: Path) -> dict:
    _guard()
    if source_zip.name != "GPS12hrs_Locs.zip" or source_zip.stat().st_size != ZIP_SIZE:
        raise ValueError("Wrong source archive name or file size")
    h = hashlib.sha256()
    with source_zip.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    if h.hexdigest() != ZIP_SHA256:
        raise ValueError("Original 12h source archive SHA-256 mismatch")

    with ZipFile(source_zip) as z:
        files = z.infolist()
        if len(files) != 4 or set(m.filename for m in files) != set(MEMBERS):
            raise ValueError("Expected exactly 4 publisher named members")
        entries = {}
        for m in files:
            mode = (m.external_attr >> 16) & 0xFFFF
            if (
                m.is_dir() or (m.flag_bits & 1)
                or stat.S_IFMT(mode) == stat.S_IFLNK
                or m.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                or m.file_size > 30_000_000
                or m.file_size > 200 * max(1, m.compress_size)
            ):
                raise ValueError("Unsafe ZIP member")
            entries[m.filename] = {
                "DOS_time_local_no_timezone": "%04d-%02d-%02dT%02d:%02d:%02d" % m.date_time,
                "uncompressed_bytes": m.file_size,
                "compressed_bytes": m.compress_size,
                "zip_crc32_hex": f"{m.CRC:08x}",
                "zip_compression_method": m.compress_type,
                "zip_creator_system_code": m.create_system,
            }
        with z.open("GPS12hrs_Locs.dbf") as stream:
            h = stream.read(32)
            if len(h) != 32 or h[0] != 3:
                raise ValueError("Unexpected dBASE file header")
            yy, mm, dd = h[1], h[2], h[3]
            if not (1 <= mm <= 12 and 1 <= dd <= 31):
                raise ValueError("Invalid DBF last update fields")
            last_date = datetime(1900 + yy, mm, dd).date().isoformat()
            n = struct.unpack("<I", h[4:8])[0]
            header_length = struct.unpack("<H", h[8:10])[0]
            row_length = struct.unpack("<H", h[10:12])[0]
            if n != 28953 or header_length != 385 or row_length != 769:
                raise ValueError("Original DBF structure drifted")
            desc = stream.read(header_length - 32)
            if len(desc) != header_length - 32 or desc[-1] != 13:
                raise ValueError("DBF field descriptors malformed")
            fields = []
            for i in range(0, len(desc)-1, 32):
                d = desc[i:i+32]
                fields.append({
                    "name": d[:11].split(b"\0")[0].decode("ascii"),
                    "type": chr(d[11]),
                    "width": int(d[16]),
                    "decimal_places": int(d[17]),
                })
            names = [f["name"] for f in fields]
            if names != ["State","Herd","SpcsCmm","SpcsScn","AID",
                         "SeasnYr","Season","Year","Timstmp","UTM_E","UTM_N"]:
                raise ValueError("DBF field roster drifted")
            stamp = fields[8]
            if stamp != {"name":"Timstmp","type":"C","width":80,"decimal_places":0}:
                raise ValueError("Timestamp field schema differs from original")
        shape_headers = {}
        for filename in ("GPS12hrs_Locs.shp","GPS12hrs_Locs.shx"):
            with z.open(filename) as stream:
                header=stream.read(100)
            length = struct.unpack(">I", header[24:28])[0] * 2
            if (len(header)!=100 or struct.unpack(">I",header[:4])[0]!=9994
                or struct.unpack("<I",header[28:32])[0]!=1000
                or struct.unpack("<I",header[32:36])[0]!=1
                or length!=entries[filename]["uncompressed_bytes"]):
                raise ValueError("SHP/SHX header structure drifted")
            shape_headers[filename] = {
                "file_length_bytes": length,
                "shape_type": 1,
                "file_code": 9994,
                "version": 1000,
            }
        with z.open("GPS12hrs_Locs.prj") as stream:
            prj=stream.read(1500).decode("ascii")
        if not prj.startswith('PROJCS["NAD_1983_HARN_UTM_Zone_12N"'):
            raise ValueError("Declared EPSG3742-family WKT changed")
    dates = {v["DOS_time_local_no_timezone"] for v in entries.values()}
    return {
        "schema": "eog.mckee2024.original_zip_dbf_header_receipt.v1",
        "status": "CONSISTENT_PREPUBLICATION_HEADER_DATES_NOT_AUTHOR_CREATION_PROOF",
        "source_sha256": ZIP_SHA256,
        "source_sha256_verified": True,
        "source_size_bytes": ZIP_SIZE,
        "members": {name: entries[name] for name in MEMBERS},
        "identical_member_DOS_timestamps": len(dates)==1,
        "common_DOS_timestamp": next(iter(dates)) if len(dates)==1 else None,
        "dbf_header": {
            "version_hex":"0x03",
            "last_updated_YY_MM_DD_raw":[yy,mm,dd],
            "last_updated_parsed_date":last_date,
            "record_count":n,
            "header_length_bytes":header_length,
            "record_length_bytes":row_length,
            "language_driver_id_hex":f"0x{h[29]:02x}",
            "field_descriptors":fields,
            "Timstmp_field_can_fit_full_19_character_string":stamp["width"]>=19,
        },
        "shape_headers":shape_headers,
        "source_prj_projected_wkt_name":"NAD_1983_HARN_UTM_Zone_12N",
        "DBF_update_date_matches_ZIP_member_date": (
            len(dates)==1 and next(iter(dates))[:10]==last_date
        ),
        "July_18_2024_Dryad_release_source":"https://datadryad.org/dataset/doi:10.5061/dryad.15dv41p51",
        "DOS_time_author_creation_proof":False,
        "DBF_last_update_author_or_original_R_version_proof":False,
        "date_only_is_exact_midnight_proven":False,
        "CRS_author_intent_proven":False,
        "original_source_time_and_CRS_STOP_preserved":True,
        "dense_2h_GPS_opened":False,
        "DBF_record_rows_or_SHP_geometry_read":False,
        "raw_animal_IDs_dates_or_coordinates_exported":False,
        "ecological_or_EOG_prediction_scored":False,
        "original_EOG_WF_scored_endpoints":3,
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    receipt=read_headers(args.source_zip)
    content=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
    if args.output is None:
        print(content)
    else:
        args.output.write_text(content,encoding="utf-8")


if __name__=="__main__":
    main()
