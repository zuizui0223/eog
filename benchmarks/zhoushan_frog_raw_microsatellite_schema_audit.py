"""Audit the Zhoushan raw microsatellite workbook after the Stage-2 freeze.

This script is deliberately limited to provenance, workbook structure, headers, string
labels and missing-code/schema inspection. It does not calculate pairwise FST, allele
frequencies, heterozygosity, clustering or migration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import xlrd

EXPECTED_MD5 = "0f9d9b36bb0c481f41170ad2d6cc6344"
EXPECTED_IDS = (
    "Guoju", "Xiepu", "Yuanhua", "Meishan", "Fodu", "Liuheng", "Huni", "Xiashi",
    "Mayi", "Taohua", "Dengbu", "Zhujiajian", "Putuoshan", "Zhoushan", "Damao",
    "Cezi", "Jintang", "Dapengshan", "Changbai", "Xiushan", "Dayushan", "Daishan",
    "Dongji", "Qushan", "Sijiao", "Shengshan", "Huaniao",
)
ALIASES = {
    "Xiashi": ("xiashi", "xiazhi"),
    "Dapengshan": ("dapengshan", "depengshan"),
}
MISSING_STRING_TOKENS = {"na", "n/a", "nan", ".", "-", "missing", "null"}


def _digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def audit(path: str | Path) -> dict[str, object]:
    source = Path(path)
    if source.suffix.lower() != ".xls":
        raise ValueError("Zhoushan raw microsatellite fallback must be the released .xls workbook")
    md5 = _digest(source, "md5")
    if md5 != EXPECTED_MD5:
        raise ValueError(f"Zhoushan raw microsatellite MD5 mismatch: {md5}")

    book = xlrd.open_workbook(str(source), on_demand=True)
    sheets = []
    all_strings: list[tuple[str, int, int, str]] = []
    total_nonempty_rows = 0
    total_numeric_cells = 0
    total_blank_cells = 0
    explicit_missing_tokens: set[str] = set()
    nonpositive_numeric_cells = 0

    for sheet in book.sheets():
        sheet_strings = []
        numeric_cells = 0
        blank_cells = 0
        nonempty_rows = 0
        first_rows_schema = []
        for row_index in range(sheet.nrows):
            row_nonempty = False
            row_schema = []
            for column_index in range(sheet.ncols):
                cell = sheet.cell(row_index, column_index)
                if cell.ctype in {xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK}:
                    blank_cells += 1
                    row_schema.append("EMPTY")
                    continue
                row_nonempty = True
                if cell.ctype == xlrd.XL_CELL_TEXT:
                    text = str(cell.value).strip()
                    normalized = _normalize(text)
                    all_strings.append((sheet.name, row_index + 1, column_index + 1, text))
                    sheet_strings.append({"row": row_index + 1, "column": column_index + 1, "text": text})
                    if normalized in MISSING_STRING_TOKENS:
                        explicit_missing_tokens.add(text)
                    row_schema.append("TEXT")
                elif cell.ctype == xlrd.XL_CELL_NUMBER:
                    numeric_cells += 1
                    if float(cell.value) <= 0.0:
                        nonpositive_numeric_cells += 1
                    row_schema.append("NUMBER")
                elif cell.ctype == xlrd.XL_CELL_DATE:
                    row_schema.append("DATE")
                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                    row_schema.append("BOOLEAN")
                elif cell.ctype == xlrd.XL_CELL_ERROR:
                    row_schema.append("ERROR")
                else:
                    row_schema.append(f"TYPE_{cell.ctype}")
            if row_nonempty:
                nonempty_rows += 1
            if row_index < 20:
                first_rows_schema.append(row_schema)
        total_nonempty_rows += nonempty_rows
        total_numeric_cells += numeric_cells
        total_blank_cells += blank_cells
        sheets.append(
            {
                "name": sheet.name,
                "n_rows": sheet.nrows,
                "n_columns": sheet.ncols,
                "n_nonempty_rows": nonempty_rows,
                "n_numeric_cells": numeric_cells,
                "n_blank_cells": blank_cells,
                "first_20_row_cell_types": first_rows_schema,
                "string_cells": sheet_strings,
            }
        )

    found = {}
    for node in EXPECTED_IDS:
        aliases = ALIASES.get(node, (node.lower(),))
        matches = []
        for sheet_name, row, column, text in all_strings:
            normalized = _normalize(text)
            if any(normalized == alias or re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases):
                matches.append({"sheet": sheet_name, "row": row, "column": column, "text": text})
        if matches:
            found[node] = matches

    header_candidates = []
    for sheet in sheets:
        for record in sheet["string_cells"]:
            if int(record["row"]) > 20:
                continue
            text = str(record["text"])
            normalized = _normalize(text)
            if any(
                token in normalized
                for token in (
                    "pop", "population", "site", "island", "sample", "individual", "id",
                    "locus", "allele", "microsat", "structure",
                )
            ):
                header_candidates.append({"sheet": sheet["name"], **record})

    result = {
        "status": "zhoushan-frog-raw-microsatellite-post-freeze-schema-audit",
        "source_file": source.name,
        "raw_md5": md5,
        "raw_sha256": _digest(source, "sha256"),
        "sheet_count": len(sheets),
        "sheets": sheets,
        "total_nonempty_rows": total_nonempty_rows,
        "total_numeric_cells": total_numeric_cells,
        "total_blank_cells": total_blank_cells,
        "nonpositive_numeric_cells": nonpositive_numeric_cells,
        "explicit_string_missing_tokens": sorted(explicit_missing_tokens),
        "header_candidates": header_candidates,
        "n_expected_population_labels": len(EXPECTED_IDS),
        "n_expected_population_labels_found_as_strings": len(found),
        "population_label_matches": found,
        "missing_population_labels": [node for node in EXPECTED_IDS if node not in found],
        "published_individual_count_integrity_target": 810,
        "published_locus_count_integrity_target": 9,
        "pairwise_fst_computed": False,
        "allele_frequencies_computed": False,
        "heterozygosity_computed": False,
        "clustering_computed": False,
        "migration_computed": False,
        "stage2_predictors_frozen_before_access": True,
    }
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
