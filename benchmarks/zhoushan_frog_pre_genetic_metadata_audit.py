"""Audit the Zhoushan pond-frog transect workbook before any genetic access.

This program accepts only the response-free `Raw transects .xlsx` workbook.  It never
opens or references the microsatellite workbook and is deliberately able to finish with
`geography_admitted = false`: a clean negative metadata audit is preferable to inferring
coordinates from genetic outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

DECLARED_MAINLAND = ("Guoju", "Xiepu", "Yuanhua")
DECLARED_ISLANDS = (
    "Meishan", "Fodu", "Liuheng", "Huni", "Xiashi", "Mayi", "Taohua", "Dengbu",
    "Zhujiajian", "Putuoshan", "Zhoushan", "Damao", "Cezi", "Jintang", "Dapengshan",
    "Changbai", "Xiushan", "Dayushan", "Daishan", "Dongji", "Qushan", "Sijiao",
    "Shengshan", "Huaniao",
)
DECLARED_NODES = DECLARED_MAINLAND + DECLARED_ISLANDS
EXPECTED_MD5 = "3fcd9bc56c414d6ca6518303d87c4736"

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

_COORDINATE_TOKENS = (
    "lat", "latitude", "lon", "lng", "long", "longitude", "easting", "northing",
    "xcoord", "ycoord", "gps", "coordinate",
)


def _digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _column_number(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference.upper())
    if not match:
        raise ValueError(f"invalid spreadsheet cell reference: {reference}")
    value = 0
    for character in match.group(1):
        value = value * 26 + (ord(character) - ord("A") + 1)
    return value - 1


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in archive.namelist():
        return []
    root = ET.fromstring(archive.read(name))
    result: list[str] = []
    for item in root.findall(f"{{{NS_MAIN}}}si"):
        text = "".join(node.text or "" for node in item.iter(f"{{{NS_MAIN}}}t"))
        result.append(text)
    return result


def _sheet_paths(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in relationships.findall(f"{{{NS_PKG_REL}}}Relationship")
    }
    result = []
    for sheet in workbook.findall(f".//{{{NS_MAIN}}}sheet"):
        title = sheet.attrib.get("name", "")
        rel_id = sheet.attrib.get(f"{{{NS_REL}}}id")
        if not rel_id or rel_id not in targets:
            continue
        target = targets[rel_id].lstrip("/")
        if target.startswith("xl/"):
            path = target
        else:
            path = "xl/" + target
        result.append((title, path))
    return result


def _read_sheet(archive: zipfile.ZipFile, path: str, shared: list[str]) -> list[list[str]]:
    root = ET.fromstring(archive.read(path))
    output: list[list[str]] = []
    for row in root.findall(f".//{{{NS_MAIN}}}row"):
        values: dict[int, str] = {}
        for cell in row.findall(f"{{{NS_MAIN}}}c"):
            reference = cell.attrib.get("r", "")
            column = _column_number(reference)
            cell_type = cell.attrib.get("t")
            if cell_type == "inlineStr":
                text = "".join(node.text or "" for node in cell.iter(f"{{{NS_MAIN}}}t"))
            else:
                value_node = cell.find(f"{{{NS_MAIN}}}v")
                raw = "" if value_node is None or value_node.text is None else value_node.text
                if cell_type == "s" and raw:
                    index = int(raw)
                    text = shared[index] if 0 <= index < len(shared) else raw
                elif cell_type == "b":
                    text = "TRUE" if raw == "1" else "FALSE"
                else:
                    text = raw
            values[column] = text.strip()
        if values:
            width = max(values) + 1
            output.append([values.get(index, "") for index in range(width)])
    return output


def _header_row(rows: list[list[str]]) -> tuple[int | None, list[str]]:
    for index, row in enumerate(rows[:25]):
        nonempty = [value.strip() for value in row if value.strip()]
        alphabetic = [value for value in nonempty if re.search(r"[A-Za-z]", value)]
        if len(nonempty) >= 2 and len(alphabetic) >= 1:
            return index, row
    return None, []


def _node_hits(rows: list[list[str]]) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {node: [] for node in DECLARED_NODES}
    normalized = {node.lower(): node for node in DECLARED_NODES}
    for row_index, row in enumerate(rows, start=1):
        for column_index, value in enumerate(row, start=1):
            token = re.sub(r"\s+", " ", value.strip()).lower()
            for key, canonical in normalized.items():
                if token == key or re.search(rf"\b{re.escape(key)}\b", token):
                    result[canonical].append({"row": row_index, "column": column_index, "value": value})
    return {key: value for key, value in result.items() if value}


def audit(path: str | Path) -> dict[str, object]:
    source = Path(path)
    if source.suffix.lower() != ".xlsx":
        raise ValueError("Zhoushan pre-genetic audit accepts only the response-free .xlsx transect workbook")
    md5 = _digest(source, "md5")
    if md5 != EXPECTED_MD5:
        raise ValueError(f"Zhoushan Raw transects workbook MD5 mismatch: {md5}")

    sheets: list[dict[str, object]] = []
    all_hits: dict[str, list[dict[str, object]]] = {}
    coordinate_candidates: list[dict[str, object]] = []
    with zipfile.ZipFile(source) as archive:
        shared = _shared_strings(archive)
        for title, sheet_path in _sheet_paths(archive):
            rows = _read_sheet(archive, sheet_path, shared)
            header_index, header = _header_row(rows)
            headers = [value.strip() for value in header]
            hits = _node_hits(rows)
            for node, values in hits.items():
                all_hits.setdefault(node, []).extend(
                    {"sheet": title, **record} for record in values
                )
            for column_index, value in enumerate(headers, start=1):
                normalized = re.sub(r"[^a-z]", "", value.lower())
                if any(token in normalized for token in _COORDINATE_TOKENS):
                    coordinate_candidates.append(
                        {"sheet": title, "column": column_index, "header": value}
                    )
            sheets.append(
                {
                    "name": title,
                    "n_nonempty_rows": len(rows),
                    "max_columns": max((len(row) for row in rows), default=0),
                    "header_row": None if header_index is None else header_index + 1,
                    "headers": headers,
                    "declared_node_hits": hits,
                }
            )

    node_coverage = sorted(all_hits, key=lambda value: DECLARED_NODES.index(value))
    explicit_coordinate_headers_found = bool(coordinate_candidates)
    # A header name alone never admits geography: complete per-node coordinate extraction
    # must be implemented and audited in a later response-free commit.
    result: dict[str, object] = {
        "status": "zhoushan-frog-response-free-transect-metadata-audit",
        "source_file": source.name,
        "raw_md5": md5,
        "raw_sha256": _digest(source, "sha256"),
        "n_declared_nodes": len(DECLARED_NODES),
        "declared_nodes": list(DECLARED_NODES),
        "n_declared_nodes_seen": len(node_coverage),
        "declared_nodes_seen": node_coverage,
        "missing_declared_nodes": [node for node in DECLARED_NODES if node not in all_hits],
        "coordinate_header_candidates": coordinate_candidates,
        "explicit_coordinate_headers_found": explicit_coordinate_headers_found,
        "sheets": sheets,
        "genetic_response_accessed": False,
        "microsatellite_file_accessed": False,
        "geography_admitted": False,
        "next_gate": (
            "extract_and_freeze_complete_response_free_coordinates"
            if explicit_coordinate_headers_found
            else "resolve_declared_node_geography_from_external_response_free_source"
        ),
    }
    fingerprint_payload = dict(result)
    result["response_free_metadata_fingerprint"] = _canonical_sha256(fingerprint_payload)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
