#!/usr/bin/env python3
"""Inventory the India tiger occupancy workbook without opening response rows.

The workbook is treated as an OPC/ZIP package rather than loaded through pandas or
openpyxl.  Gate 0 may inspect workbook, relationship, table and style metadata; it may
also read exactly the first logical worksheet row.  No later worksheet row, occupancy
value, detection/sign value or cached formula result is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


EXPECTED_MD5 = "ac4fd29ab1f7ea1045ac279885c72a11"
MAX_PREFIX_BYTES = 2_000_000
MAX_HEADER_STRINGS = 512

SS_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

ID_TERMS = {
    "gridid", "grid_id", "cellid", "cell_id", "siteid", "site_id", "id",
    "gridcode", "grid_code", "cellcode", "cell_code",
}
GEOMETRY_TERMS = {
    "x", "y", "lat", "latitude", "lon", "long", "longitude",
    "easting", "northing", "centroidx", "centroidy", "xcoord", "ycoord",
    "gridrow", "gridcol", "row", "column", "col", "utm_x", "utm_y",
}
RESPONSE_TERMS = {
    "tiger", "presence", "absence", "occupancy", "occupied", "detect",
    "detection", "sign", "response", "colonization", "colonisation",
    "extinction", "abundance", "count", "psi", "zstate", "state",
}
EFFORT_TERMS = {
    "effort", "surveyed", "survey", "replicate", "occasion", "transect",
    "distancewalked", "walked", "missing", "naflag", "availability",
}
CYCLE_TERMS = {"2006", "2010", "2014", "2018", "year", "cycle", "period"}


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def normalized_tokens(columns: list[str] | tuple[str, ...]) -> set[str]:
    return {normalized(value) for value in columns if str(value).strip()}


def has_term(tokens: set[str], terms: set[str]) -> bool:
    normalized_terms = {normalized(value) for value in terms}
    for token in tokens:
        if token in normalized_terms:
            return True
        if any(term and (token.startswith(term) or token.endswith(term)) for term in normalized_terms):
            return True
    return False


def archive_manifest(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for info in archive.infolist():
        rows.append(
            {
                "name": info.filename,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "crc32": f"{info.CRC:08x}",
                "is_dir": info.is_dir(),
            }
        )
    return rows


def relationship_map(data: bytes) -> dict[str, dict[str, str]]:
    root = ET.fromstring(data)
    result: dict[str, dict[str, str]] = {}
    for relation in root.findall(f"{{{PKG_REL_NS}}}Relationship"):
        identifier = str(relation.attrib.get("Id", ""))
        if not identifier:
            continue
        result[identifier] = {
            "target": str(relation.attrib.get("Target", "")),
            "type": str(relation.attrib.get("Type", "")),
            "target_mode": str(relation.attrib.get("TargetMode", "")),
        }
    return result


def resolve_opc_target(base_member: str, target: str) -> str:
    target = str(target).replace("\\", "/")
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_member), target))


def workbook_sheets(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    workbook_member = "xl/workbook.xml"
    rel_member = "xl/_rels/workbook.xml.rels"
    if workbook_member not in archive.namelist() or rel_member not in archive.namelist():
        raise ValueError("XLSX is missing workbook.xml or workbook relationships")
    root = ET.fromstring(archive.read(workbook_member))
    rels = relationship_map(archive.read(rel_member))
    rows: list[dict[str, Any]] = []
    for sheet in root.findall(f".//{{{SS_NS}}}sheet"):
        rid = str(sheet.attrib.get(f"{{{REL_NS}}}id", ""))
        relation = rels.get(rid, {})
        target = relation.get("target", "")
        member = resolve_opc_target(workbook_member, target) if target else ""
        rows.append(
            {
                "name": str(sheet.attrib.get("name", "")),
                "sheet_id": str(sheet.attrib.get("sheetId", "")),
                "state": str(sheet.attrib.get("state", "visible")),
                "relationship_id": rid,
                "relationship_type": relation.get("type"),
                "member": member,
            }
        )
    return rows


def read_exact_first_row(archive: zipfile.ZipFile, member: str) -> tuple[bytes | None, bytes, str | None]:
    """Read through the exact closing byte of the first worksheet row only."""

    if member not in archive.namelist():
        return None, b"", None
    prefix = bytearray()
    row_start = -1
    with archive.open(member) as handle:
        while len(prefix) < MAX_PREFIX_BYTES:
            value = handle.read(1)
            if value == b"":
                break
            prefix.extend(value)
            if row_start < 0:
                row_start = prefix.find(b"<row")
            if row_start >= 0:
                close = prefix.find(b"</row>", row_start)
                if close >= 0:
                    end = close + len(b"</row>")
                    dimension_match = re.search(br"<dimension\b[^>]*\bref=\"([^\"]+)\"", bytes(prefix[:row_start]))
                    dimension = dimension_match.group(1).decode("utf-8", errors="replace") if dimension_match else None
                    return bytes(prefix[row_start:end]), bytes(prefix[:end]), dimension
                open_end = prefix.find(b">", row_start)
                if open_end >= 0 and prefix[max(row_start, open_end - 1):open_end + 1] == b"/>":
                    dimension_match = re.search(br"<dimension\b[^>]*\bref=\"([^\"]+)\"", bytes(prefix[:row_start]))
                    dimension = dimension_match.group(1).decode("utf-8", errors="replace") if dimension_match else None
                    return bytes(prefix[row_start:open_end + 1]), bytes(prefix[:open_end + 1]), dimension
    dimension_match = re.search(br"<dimension\b[^>]*\bref=\"([^\"]+)\"", bytes(prefix))
    dimension = dimension_match.group(1).decode("utf-8", errors="replace") if dimension_match else None
    return None, bytes(prefix), dimension


def parse_row_cells(row_bytes: bytes | None) -> list[dict[str, Any]]:
    if not row_bytes:
        return []
    wrapper = f'<root xmlns="{SS_NS}">'.encode() + row_bytes + b"</root>"
    root = ET.fromstring(wrapper)
    row = root.find(f"{{{SS_NS}}}row")
    if row is None:
        return []
    cells: list[dict[str, Any]] = []
    for cell in row.findall(f"{{{SS_NS}}}c"):
        cell_type = str(cell.attrib.get("t", "n"))
        ref = str(cell.attrib.get("r", ""))
        value_node = cell.find(f"{{{SS_NS}}}v")
        inline_text = "".join(node.text or "" for node in cell.findall(f".//{{{SS_NS}}}t"))
        value = value_node.text if value_node is not None else None
        cells.append(
            {
                "reference": ref,
                "type": cell_type,
                "value": value,
                "inline_text": inline_text or None,
                "style": cell.attrib.get("s"),
            }
        )
    return cells


def extract_si_text(si_bytes: bytes) -> str:
    wrapper = f'<root xmlns="{SS_NS}">'.encode() + si_bytes + b"</root>"
    root = ET.fromstring(wrapper)
    return "".join(node.text or "" for node in root.findall(f".//{{{SS_NS}}}t"))


def read_shared_strings_prefix(archive: zipfile.ZipFile, maximum_index: int) -> list[str]:
    """Read shared-string records only through maximum_index, never beyond it."""

    member = "xl/sharedStrings.xml"
    if maximum_index < 0:
        return []
    if maximum_index >= MAX_HEADER_STRINGS:
        raise ValueError("header shared-string index exceeds the bounded Gate 0 limit")
    if member not in archive.namelist():
        raise ValueError("shared-string header reference exists but sharedStrings.xml is absent")

    values: list[str] = []
    buffer = bytearray()
    current_start = -1
    with archive.open(member) as handle:
        while len(values) <= maximum_index:
            value = handle.read(1)
            if value == b"":
                raise ValueError("sharedStrings.xml ended before required header records")
            buffer.extend(value)
            if current_start < 0:
                current_start = buffer.find(b"<si")
            if current_start >= 0:
                close = buffer.find(b"</si>", current_start)
                if close >= 0:
                    end = close + len(b"</si>")
                    values.append(extract_si_text(bytes(buffer[current_start:end])))
                    del buffer[:end]
                    current_start = -1
    return values


def decode_header_cells(archive: zipfile.ZipFile, cells: list[dict[str, Any]]) -> dict[str, Any]:
    shared_indices: list[int] = []
    for cell in cells:
        if cell["type"] == "s" and cell["value"] is not None:
            shared_indices.append(int(cell["value"]))

    shared_values: list[str] = []
    shared_status = "not_used"
    if shared_indices:
        maximum = max(shared_indices)
        unique = sorted(set(shared_indices))
        if unique != list(range(maximum + 1)):
            return {
                "status": "unresolved_noncontiguous_shared_string_header_indices",
                "columns": [],
                "shared_string_indices": shared_indices,
                "cell_count": len(cells),
            }
        shared_values = read_shared_strings_prefix(archive, maximum)
        shared_status = "bounded_prefix_resolved"

    columns: list[str] = []
    unresolved: list[str] = []
    for cell in cells:
        cell_type = cell["type"]
        value = cell["value"]
        if cell_type == "s" and value is not None:
            columns.append(shared_values[int(value)])
        elif cell_type == "inlineStr":
            columns.append(str(cell.get("inline_text") or ""))
        elif cell_type in {"str", "e"}:
            columns.append(str(value or cell.get("inline_text") or ""))
        elif cell_type == "b":
            columns.append(str(value or ""))
            unresolved.append(str(cell.get("reference") or ""))
        else:
            columns.append(str(value or ""))
            unresolved.append(str(cell.get("reference") or ""))

    return {
        "status": "resolved" if not unresolved else "partially_resolved_nontext_header_cells",
        "columns": columns,
        "shared_string_status": shared_status,
        "shared_string_indices": shared_indices,
        "unresolved_cell_references": unresolved,
        "cell_count": len(cells),
    }


def sheet_relationships(archive: zipfile.ZipFile, sheet_member: str) -> dict[str, dict[str, str]]:
    member_path = PurePosixPath(sheet_member)
    rel_member = str(member_path.parent / "_rels" / f"{member_path.name}.rels")
    if rel_member not in archive.namelist():
        return {}
    return relationship_map(archive.read(rel_member))


def table_inventory(archive: zipfile.ZipFile) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in sorted(archive.namelist()):
        if not name.startswith("xl/tables/") or not name.endswith(".xml"):
            continue
        root = ET.fromstring(archive.read(name))
        columns = [
            str(column.attrib.get("name", ""))
            for column in root.findall(f".//{{{SS_NS}}}tableColumn")
        ]
        result[name] = {
            "name": str(root.attrib.get("name", "")),
            "display_name": str(root.attrib.get("displayName", "")),
            "ref": str(root.attrib.get("ref", "")),
            "header_row_count": str(root.attrib.get("headerRowCount", "1")),
            "columns": columns,
        }
    return result


def map_tables_to_sheets(
    archive: zipfile.ZipFile,
    sheets: list[dict[str, Any]],
    tables: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    mapped: dict[str, list[dict[str, Any]]] = {sheet["name"]: [] for sheet in sheets}
    for sheet in sheets:
        member = str(sheet.get("member") or "")
        for relation in sheet_relationships(archive, member).values():
            if "table" not in str(relation.get("type", "")).lower():
                continue
            target = resolve_opc_target(member, relation.get("target", ""))
            if target in tables:
                mapped[sheet["name"]].append({"member": target, **tables[target]})
    return mapped


def classify_columns(columns: list[str]) -> dict[str, Any]:
    tokens = normalized_tokens(columns)
    has_id = has_term(tokens, ID_TERMS)
    has_geometry = has_term(tokens, GEOMETRY_TERMS)
    has_response = has_term(tokens, RESPONSE_TERMS)
    has_effort = has_term(tokens, EFFORT_TERMS)
    has_cycle = has_term(tokens, CYCLE_TERMS)
    if has_id and has_geometry and not has_response:
        role = "plausible_response_free_geometry_registry"
    elif has_geometry and has_response:
        role = "geometry_response_colocated"
    elif has_response:
        role = "response_bearing_or_result_table"
    elif has_effort and has_id:
        role = "plausible_effort_or_availability_table"
    else:
        role = "unresolved_or_nongeometry_table"
    return {
        "normalized_tokens": sorted(tokens),
        "has_stable_id_term": has_id,
        "has_geometry_term": has_geometry,
        "has_response_term": has_response,
        "has_effort_term": has_effort,
        "has_cycle_term": has_cycle,
        "provisional_role": role,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    observed_md5 = digest_file(args.workbook, "md5")
    if observed_md5 != EXPECTED_MD5:
        raise SystemExit(f"workbook MD5 mismatch: {observed_md5}")

    with zipfile.ZipFile(args.workbook) as archive:
        manifest = archive_manifest(archive)
        sheets = workbook_sheets(archive)
        tables = table_inventory(archive)
        mapped_tables = map_tables_to_sheets(archive, sheets, tables)

        sheet_rows: list[dict[str, Any]] = []
        for sheet in sheets:
            member = str(sheet.get("member") or "")
            row_bytes, prefix, dimension = read_exact_first_row(archive, member)
            cells = parse_row_cells(row_bytes)
            header = decode_header_cells(archive, cells) if cells else {
                "status": "no_first_logical_row",
                "columns": [],
                "cell_count": 0,
            }
            table_defs = mapped_tables.get(sheet["name"], [])
            table_columns: list[str] = []
            for table in table_defs:
                if table.get("columns"):
                    table_columns = list(table["columns"])
                    break
            effective_columns = table_columns or list(header.get("columns", []))
            classification = classify_columns(effective_columns)
            sheet_rows.append(
                {
                    **sheet,
                    "dimension": dimension,
                    "bytes_consumed_through_first_row": len(prefix),
                    "first_row": header,
                    "table_definitions": table_defs,
                    "effective_columns": effective_columns,
                    "classification": classification,
                }
            )

    geometry_candidates = [
        row for row in sheet_rows
        if row["classification"]["provisional_role"] == "plausible_response_free_geometry_registry"
    ]
    colocated = [
        row for row in sheet_rows
        if row["classification"]["provisional_role"] == "geometry_response_colocated"
    ]
    effort_candidates = [
        row for row in sheet_rows
        if row["classification"]["provisional_role"] == "plausible_effort_or_availability_table"
    ]
    unresolved_headers = [
        row for row in sheet_rows
        if str(row["first_row"].get("status", "")).startswith("unresolved")
    ]

    if geometry_candidates:
        status = "gate0_inventory_pass_pending_sheet_role_adjudication"
        next_gate = "adjudicate candidate geometry and effort worksheet roles before opening later rows"
    elif colocated:
        status = "gate0_stop_response_inseparable_geometry"
        next_gate = "stop candidate pre-response"
    elif unresolved_headers:
        status = "gate0_stop_unresolved_workbook_headers"
        next_gate = "stop candidate pre-response; do not read farther to rescue headers"
    else:
        status = "gate0_stop_no_plausible_response_free_grid_geometry"
        next_gate = "stop candidate pre-response"

    result = {
        "status": status,
        "response_rows_opened": False,
        "response_values_parsed": False,
        "rows_after_first_logical_row_opened": False,
        "general_workbook_library_used": False,
        "workbook": {
            "name": args.workbook.name,
            "size": args.workbook.stat().st_size,
            "md5": observed_md5,
            "sha256": digest_file(args.workbook, "sha256"),
            "member_count": len(manifest),
        },
        "sheet_count": len(sheet_rows),
        "table_definition_count": len(tables),
        "geometry_candidate_sheet_names": [row["name"] for row in geometry_candidates],
        "geometry_response_colocated_sheet_names": [row["name"] for row in colocated],
        "effort_candidate_sheet_names": [row["name"] for row in effort_candidates],
        "unresolved_header_sheet_names": [row["name"] for row in unresolved_headers],
        "sheet_inventory": sheet_rows,
        "next_gate": next_gate,
    }
    result["fingerprint"] = canonical_sha256(result)

    (args.output_dir / "archive_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "table_inventory.json").write_text(
        json.dumps(tables, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "sheet_inventory.json").write_text(
        json.dumps(sheet_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "gate0_inventory_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
