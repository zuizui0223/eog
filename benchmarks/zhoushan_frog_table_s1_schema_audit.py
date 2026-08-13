"""Audit Wiley Table S1 workbook structure after Zhoushan predictors are frozen.

The exact response file is now permitted to be downloaded because the Stage-2 predictor
artifact is already byte-frozen.  This schema audit records workbook provenance and
string labels only. Numeric FST cell values are neither emitted nor summarized here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

EXPECTED_IDS = (
    "Guoju", "Xiepu", "Yuanhua", "Meishan", "Fodu", "Liuheng", "Huni", "Xiashi",
    "Mayi", "Taohua", "Dengbu", "Zhujiajian", "Putuoshan", "Zhoushan", "Damao",
    "Cezi", "Jintang", "Dapengshan", "Changbai", "Xiushan", "Dayushan", "Daishan",
    "Dongji", "Qushan", "Sijiao", "Shengshan", "Huaniao",
)
ALIASES = {
    "Xiashi": ("Xiashi", "Xiazhi"),
    "Dapengshan": ("Dapengshan", "Depengshan"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.iter(f"{{{NS_MAIN}}}t"))
        for item in root.findall(f"{{{NS_MAIN}}}si")
    ]


def _sheet_paths(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in relationships.findall(f"{{{NS_PKG_REL}}}Relationship")
    }
    output = []
    for sheet in workbook.findall(f".//{{{NS_MAIN}}}sheet"):
        title = sheet.attrib.get("name", "")
        rel_id = sheet.attrib.get(f"{{{NS_REL}}}id")
        if not rel_id or rel_id not in targets:
            continue
        target = targets[rel_id].lstrip("/")
        output.append((title, target if target.startswith("xl/") else "xl/" + target))
    return output


def _string_cells(archive: zipfile.ZipFile, path: str, shared: list[str]) -> tuple[list[dict[str, str]], int, str | None]:
    root = ET.fromstring(archive.read(path))
    dimension = root.find(f"{{{NS_MAIN}}}dimension")
    dimension_ref = None if dimension is None else dimension.attrib.get("ref")
    strings: list[dict[str, str]] = []
    numeric_count = 0
    for cell in root.findall(f".//{{{NS_MAIN}}}c"):
        reference = cell.attrib.get("r", "")
        cell_type = cell.attrib.get("t")
        if cell_type == "inlineStr":
            text = "".join(node.text or "" for node in cell.iter(f"{{{NS_MAIN}}}t"))
            if text.strip():
                strings.append({"cell": reference, "text": text.strip()})
            continue
        value = cell.find(f"{{{NS_MAIN}}}v")
        raw = "" if value is None or value.text is None else value.text
        if cell_type == "s" and raw:
            index = int(raw)
            text = shared[index] if 0 <= index < len(shared) else raw
            if text.strip():
                strings.append({"cell": reference, "text": text.strip()})
        elif raw:
            numeric_count += 1
    return strings, numeric_count, dimension_ref


def audit(path: str | Path) -> dict[str, object]:
    source = Path(path)
    if source.suffix.lower() != ".xlsx":
        raise ValueError("Zhoushan Table S1 must be an xlsx workbook")
    sheets = []
    all_strings: list[str] = []
    with zipfile.ZipFile(source) as archive:
        shared = _shared_strings(archive)
        for title, sheet_path in _sheet_paths(archive):
            string_cells, numeric_count, dimension = _string_cells(archive, sheet_path, shared)
            all_strings.extend(record["text"] for record in string_cells)
            sheets.append(
                {
                    "name": title,
                    "dimension": dimension,
                    "n_string_cells": len(string_cells),
                    "n_numeric_cells": numeric_count,
                    "string_cells": string_cells,
                }
            )

    normalized_strings = [re.sub(r"\s+", " ", value.strip()).lower() for value in all_strings]
    found = {}
    for node in EXPECTED_IDS:
        aliases = ALIASES.get(node, (node,))
        matches = []
        for alias in aliases:
            alias_lower = alias.lower()
            for value in all_strings:
                normalized = re.sub(r"\s+", " ", value.strip()).lower()
                if normalized == alias_lower or re.search(rf"\b{re.escape(alias_lower)}\b", normalized):
                    matches.append(value)
        if matches:
            found[node] = sorted(set(matches))

    return {
        "status": "zhoushan-frog-table-s1-post-freeze-schema-audit",
        "source_file": source.name,
        "raw_sha256": _sha256(source),
        "sheet_count": len(sheets),
        "sheets": sheets,
        "n_expected_population_labels": len(EXPECTED_IDS),
        "n_expected_population_labels_found_as_strings": len(found),
        "population_label_matches": found,
        "missing_population_labels": [node for node in EXPECTED_IDS if node not in found],
        "numeric_fst_values_emitted": False,
        "numeric_fst_values_summarized": False,
        "predictor_freeze_completed_before_access": True,
    }


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
