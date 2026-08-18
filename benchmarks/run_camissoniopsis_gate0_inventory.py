#!/usr/bin/env python3
"""Inventory the frozen Camissoniopsis Zenodo archive without opening response rows.

The inventory reads archive metadata, full documentation/code, and one bounded physical
record from text-like data members.  It does not deserialize R objects, spreadsheets,
shapefiles, DBF tables, or any response-bearing data row.  The output identifies only
*plausible* response-free geometry routes for a later role-specific adjudication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import zipfile


EXPECTED_MD5 = "77f8047ce9fc908683824643a7ea7c0b"
MAX_HEADER_BYTES = 16_384

FULL_TEXT_CODE_EXTENSIONS = {".r", ".rmd", ".qmd", ".md"}
DOCUMENT_NAME_TERMS = ("readme", "metadata", "license", "codebook")
BOUNDED_TEXT_EXTENSIONS = {".csv", ".tsv", ".txt", ".tab", ".dat"}
BINARY_OR_SERIALIZED_EXTENSIONS = {
    ".rdata", ".rda", ".rds", ".xlsx", ".xls", ".sav", ".dta",
    ".shp", ".shx", ".dbf", ".prj", ".gpkg", ".gdb", ".feather", ".parquet",
}
SPATIAL_EXTENSIONS = {".shp", ".geojson", ".gpkg", ".kml", ".kmz"}

GEOMETRY_TERMS = (
    "latitude", "longitude", "lat", "lon", "coord", "easting", "northing",
    "utm", "x", "y", "gps", "point", "plot_id", "site_id", "plot", "site",
)
RESPONSE_TERMS = (
    "occup", "abundance", "count", "presence", "absence", "colon", "extinct",
    "response", "camissoniopsis", "cheiranthifolia", "population", "plant_n",
)
ROLE_SEARCH_TERMS = (
    "latitude", "longitude", "coordinates", "coordinate", "gps", "utm", "easting",
    "northing", "st_read", "read_sf", "read.csv", "read_csv", "plot id", "site id",
    "2019", "2022", "colon", "occup", "abundance", "suitable habitat",
)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_member_name(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe archive member path: {name!r}")
    return str(path)


def first_physical_record(stream, limit: int = MAX_HEADER_BYTES) -> tuple[bytes, str, int]:
    buffer = bytearray()
    while len(buffer) < limit:
        value = stream.read(1)
        if value == b"":
            raise ValueError("physical record terminator not found before EOF")
        if value == b"\r":
            return bytes(buffer), "CR", len(buffer) + 1
        if value == b"\n":
            return bytes(buffer), "LF", len(buffer) + 1
        buffer.extend(value)
    raise ValueError(f"first physical record exceeds {limit} bytes")


def decode_text(data: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("unable to decode text member")


def member_class(name: str) -> str:
    path = PurePosixPath(name)
    lower_name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix in FULL_TEXT_CODE_EXTENSIONS:
        return "full_code_or_markdown"
    if any(term in lower_name for term in DOCUMENT_NAME_TERMS):
        return "full_named_documentation"
    if suffix in BOUNDED_TEXT_EXTENSIONS:
        return "bounded_header_only"
    if suffix in BINARY_OR_SERIALIZED_EXTENSIONS:
        return "binary_inventory_only"
    if suffix in SPATIAL_EXTENSIONS:
        return "spatial_inventory_only"
    return "inventory_only"


def normalized_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def header_geometry_score(name: str, header: str) -> dict[str, Any]:
    combined = f"{PurePosixPath(name).name} {header}".lower()
    tokens = normalized_tokens(combined)
    geometry_hits = sorted(
        term for term in GEOMETRY_TERMS
        if term in tokens or (len(term) > 3 and term in combined)
    )
    response_hits = sorted(term for term in RESPONSE_TERMS if term in combined)
    plausible = bool(geometry_hits) and not response_hits
    return {
        "geometry_hits": geometry_hits,
        "response_hits": response_hits,
        "plausible_response_free_geometry": plausible,
    }


def line_snippets(text: str, terms: tuple[str, ...], max_rows: int = 120) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        lower = line.lower()
        hits = sorted({term for term in terms if term in lower})
        if not hits:
            continue
        rows.append({
            "line": line_number,
            "terms": hits,
            "text": line[:500],
        })
        if len(rows) >= max_rows:
            break
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    archive_md5 = digest_file(args.archive, "md5")
    archive_sha256 = digest_file(args.archive, "sha256")
    if archive_md5 != EXPECTED_MD5:
        raise SystemExit(f"archive MD5 mismatch: {archive_md5}")

    manifest: list[dict[str, Any]] = []
    bounded_headers: list[dict[str, Any]] = []
    documentation_index: list[dict[str, Any]] = []
    plausible_geometry: list[dict[str, Any]] = []
    full_text_files: list[str] = []
    binary_inventory: list[str] = []

    docs_root = args.output_dir / "documentation"
    docs_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.archive) as archive:
        for info in archive.infolist():
            safe_name = safe_member_name(info.filename)
            classification = member_class(safe_name)
            row = {
                "name": safe_name,
                "basename": PurePosixPath(safe_name).name,
                "suffix": PurePosixPath(safe_name).suffix.lower(),
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "crc32": f"{info.CRC:08x}",
                "is_dir": info.is_dir(),
                "inspection_class": classification,
            }
            manifest.append(row)
            if info.is_dir():
                continue

            suffix = PurePosixPath(safe_name).suffix.lower()
            if classification in {"full_code_or_markdown", "full_named_documentation"}:
                data = archive.read(info)
                try:
                    text, encoding = decode_text(data)
                except ValueError:
                    binary_inventory.append(safe_name)
                    continue
                full_text_files.append(safe_name)
                target_name = hashlib.sha256(safe_name.encode("utf-8")).hexdigest()[:12]
                target = docs_root / f"{target_name}_{PurePosixPath(safe_name).name}"
                target.write_text(text, encoding="utf-8")
                documentation_index.append({
                    "name": safe_name,
                    "encoding": encoding,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "role_snippets": line_snippets(text, ROLE_SEARCH_TERMS),
                })
            elif classification == "bounded_header_only":
                try:
                    with archive.open(info, "r") as stream:
                        header_bytes, terminator, bytes_consumed = first_physical_record(stream)
                    header, encoding = decode_text(header_bytes)
                    scoring = header_geometry_score(safe_name, header)
                    header_row = {
                        "name": safe_name,
                        "encoding": encoding,
                        "terminator": terminator,
                        "bytes_consumed": bytes_consumed,
                        "header": header,
                        **scoring,
                    }
                    bounded_headers.append(header_row)
                    if scoring["plausible_response_free_geometry"]:
                        plausible_geometry.append({
                            "name": safe_name,
                            "route": "bounded_text_header_candidate",
                            "geometry_hits": scoring["geometry_hits"],
                            "role_requires_adjudication": True,
                        })
                except Exception as error:
                    bounded_headers.append({
                        "name": safe_name,
                        "status": "bounded_header_error",
                        "error": repr(error),
                    })
            else:
                binary_inventory.append(safe_name)
                if suffix in SPATIAL_EXTENSIONS:
                    plausible_geometry.append({
                        "name": safe_name,
                        "route": "spatial_binary_candidate",
                        "role_requires_adjudication": True,
                    })
                elif any(term in PurePosixPath(safe_name).name.lower() for term in ("coord", "gps", "point", "plot", "site", "location")):
                    plausible_geometry.append({
                        "name": safe_name,
                        "route": "name_only_binary_candidate",
                        "role_requires_adjudication": True,
                    })

    manifest = sorted(manifest, key=lambda row: row["name"])
    bounded_headers = sorted(bounded_headers, key=lambda row: row["name"])
    documentation_index = sorted(documentation_index, key=lambda row: row["name"])
    plausible_geometry = sorted(plausible_geometry, key=lambda row: row["name"])

    status = (
        "gate0_inventory_pass_pending_geometry_role_adjudication"
        if plausible_geometry
        else "gate0_stop_no_plausible_response_free_geometry_route"
    )

    result = {
        "status": status,
        "archive": {
            "name": args.archive.name,
            "size": args.archive.stat().st_size,
            "md5": archive_md5,
            "sha256": archive_sha256,
            "member_count": len(manifest),
            "file_count": sum(not row["is_dir"] for row in manifest),
        },
        "response_rows_opened": False,
        "response_values_parsed": False,
        "serialized_objects_deserialized": False,
        "spatial_attribute_tables_opened": False,
        "full_text_code_or_documentation": full_text_files,
        "bounded_header_member_count": len(bounded_headers),
        "binary_inventory_member_count": len(binary_inventory),
        "plausible_geometry_candidates": plausible_geometry,
        "next_gate": (
            "adjudicate candidate roles from documentation/code and then whitelist one response-free geometry object"
            if plausible_geometry
            else "stop candidate pre-response"
        ),
    }
    result["fingerprint"] = canonical_sha256(result)

    (args.output_dir / "archive_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "bounded_headers.json").write_text(
        json.dumps(bounded_headers, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "documentation_index.json").write_text(
        json.dumps(documentation_index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "gate0_inventory_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
