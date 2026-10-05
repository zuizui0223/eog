#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile


DOI = "10.5061/dryad.7p2cv"
DOWNLOAD_URL = (
    "https://datadryad.org/api/v2/datasets/"
    "doi%3A10.5061%2Fdryad.7p2cv/download"
)
EXPECTED_FILES = {
    "sample.data.csv",
    "species.prevalence.csv",
    "collembola.csv",
}
DESIGN_RE = re.compile(
    r"(id|sample|microcosm|rep|nitrogen|fungiv|history|initial|arrival|harvest|month|treat)",
    re.IGNORECASE,
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _download() -> bytes:
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "EOG-v29-schema-probe/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
        content_type = response.headers.get("Content-Type", "")
    if not payload:
        raise RuntimeError("Dryad download returned empty payload")
    if "zip" not in content_type.lower() and not payload.startswith(b"PK"):
        raise RuntimeError(
            f"Dryad download is not a zip archive: content-type={content_type!r}"
        )
    return payload


def _read_csv(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise RuntimeError("CSV has no header")
    columns = [str(name) for name in reader.fieldnames]
    rows = [
        {str(key): ("" if value is None else str(value)) for key, value in row.items()}
        for row in reader
    ]
    return columns, rows


def _is_numeric(values: list[str]) -> bool:
    nonempty = [value.strip() for value in values if value.strip() != ""]
    if not nonempty:
        return False
    try:
        for value in nonempty:
            float(value)
        return True
    except ValueError:
        return False


def _schema_summary(name: str, payload: bytes) -> dict:
    columns, rows = _read_csv(payload)
    column_info = {}
    for column in columns:
        values = [row.get(column, "") for row in rows]
        missing = sum(value.strip() == "" for value in values)
        numeric = _is_numeric(values)
        unique = sorted({value.strip() for value in values if value.strip() != ""})
        info = {
            "numeric": bool(numeric),
            "missing_count": int(missing),
            "unique_count": int(len(unique)),
        }
        if DESIGN_RE.search(column) and len(unique) <= 100:
            info["design_levels"] = unique
        column_info[column] = info
    return {
        "filename": name,
        "bytes": len(payload),
        "sha256": _sha256(payload),
        "row_count": len(rows),
        "columns": columns,
        "column_info": column_info,
    }


def _join_candidates(summaries: dict[str, dict]) -> list[dict]:
    names = sorted(summaries)
    candidates = []
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            overlap = sorted(
                set(summaries[left]["columns"]) & set(summaries[right]["columns"])
            )
            if overlap:
                candidates.append(
                    {
                        "left": left,
                        "right": right,
                        "shared_columns": overlap,
                    }
                )
    return candidates


def run() -> dict:
    archive = _download()
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        members = [
            name for name in zf.namelist()
            if not name.endswith("/") and Path(name).name in EXPECTED_FILES
        ]
        by_basename = {}
        for member in members:
            basename = Path(member).name
            if basename in by_basename:
                raise RuntimeError(f"duplicate Dryad file basename {basename}")
            by_basename[basename] = zf.read(member)

    missing = sorted(EXPECTED_FILES - set(by_basename))
    if missing:
        raise RuntimeError(f"Dryad archive missing expected files: {missing}")

    summaries = {
        name: _schema_summary(name, by_basename[name])
        for name in sorted(EXPECTED_FILES)
    }
    result = {
        "schema": "eog.wood_decomposer_history_retention.schema_probe.v29",
        "status": "schema_materialized_before_v29_scoring_protocol",
        "source": {
            "doi": DOI,
            "download_url": DOWNLOAD_URL,
            "archive_bytes": len(archive),
            "archive_sha256": _sha256(archive),
        },
        "files": summaries,
        "join_candidates": _join_candidates(summaries),
        "response_values_exposed": False,
        "scoring_performed": False,
    }
    fingerprint_payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = _sha256(fingerprint_payload)
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
