#!/usr/bin/env python3
"""Freeze and audit Hydrilla Gate 0 through Dryad's public dataset bundle route.

The first candidate-specific workflow showed that Dryad's per-file API download link
returns HTTP 401 in GitHub Actions.  This replacement tries the one official dataset
bundle route documented by Dryad.  It always writes an auditable result, including a
transport STOP, without opening response rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
import zipfile

import numpy as np

from eog.v2.response_firewall import read_bounded_first_record_text


DOI = "10.5061/dryad.jsxksn0fn"
DATASET_API = f"https://datadryad.org/api/v2/datasets/doi%3A{quote(DOI, safe='')}"
VERSIONS_API = DATASET_API + "/versions"
BUNDLE_API = DATASET_API + "/download"
EXPECTED_FILES = {
    "All_Data.csv",
    "All_dist.csv",
    "Days_since_occupancy.csv",
    "FiveYearAverages.csv",
    "near_neigh_dist.csv",
    "Post_Hoc_Dataset.csv",
    "README.md",
}
AMBIGUOUS_OR_RESPONSE = {
    "All_Data.csv",
    "Days_since_occupancy.csv",
    "FiveYearAverages.csv",
    "Post_Hoc_Dataset.csv",
}
GEOMETRY_CANDIDATES = {"All_dist.csv", "near_neigh_dist.csv"}
EXPECTED_NODE_COUNT = 506
EXPECTED_PAIR_COUNT = EXPECTED_NODE_COUNT * (EXPECTED_NODE_COUNT - 1) // 2
MAX_HEADER_BYTES = 16_384
USER_AGENT = "EOG-Hydrilla-Gate0/2.0 (+https://github.com/zuizui0223/eog)"
RESPONSE_TERMS = (
    "hydrilla",
    "occup",
    "presence",
    "absence",
    "detect",
    "colon",
    "extinct",
    "persist",
    "abund",
    "response",
    "status",
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


def digest_bytes(data: bytes, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    digest.update(data)
    return digest.hexdigest()


def digest_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def request_bytes(url: str, *, accept: str) -> tuple[bytes | None, dict[str, Any]]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
        },
    )
    try:
        with urlopen(request, timeout=90) as response:
            data = response.read()
            return data, {
                "url": url,
                "status": int(getattr(response, "status", 200)),
                "content_type": response.headers.get("Content-Type"),
                "content_length_header": response.headers.get("Content-Length"),
                "downloaded_size": len(data),
                "sha256": digest_bytes(data, "sha256"),
                "zip_signature": data.startswith(b"PK\x03\x04"),
            }
    except HTTPError as error:
        body = error.read()
        return None, {
            "url": url,
            "status": int(error.code),
            "reason": str(error.reason),
            "content_type": error.headers.get("Content-Type") if error.headers else None,
            "body_size": len(body),
            "body_sha256": digest_bytes(body, "sha256"),
            "body_preview": body[:240].decode("utf-8", errors="replace"),
        }
    except URLError as error:
        return None, {
            "url": url,
            "status": "transport_error",
            "reason": str(error.reason),
        }


def get_json(url: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    data, diagnostic = request_bytes(url, accept="application/json")
    if data is None:
        return None, diagnostic
    try:
        return json.loads(data.decode("utf-8")), diagnostic
    except Exception as error:
        diagnostic = {**diagnostic, "json_decode_error": repr(error)}
        return None, diagnostic


def nested_lists(value: Any) -> Iterable[list[Any]]:
    if isinstance(value, list):
        yield value
        for item in value:
            yield from nested_lists(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from nested_lists(item)


def choose_version(payload: dict[str, Any]) -> dict[str, Any]:
    records: dict[str, dict[str, Any]] = {}
    for values in nested_lists(payload):
        if not values or not all(isinstance(item, dict) for item in values):
            continue
        for item in values:
            identifier = item.get("id", item.get("versionId"))
            if identifier is not None:
                records[str(identifier)] = item
    if not records:
        raise ValueError("no version records in Dryad versions response")

    def sort_key(item: dict[str, Any]) -> tuple[int, int, int]:
        status = str(item.get("status", "")).lower()
        published = 1 if status in {"published", "submitted"} else 0
        try:
            version_number = int(item.get("versionNumber", item.get("version", 0)))
        except Exception:
            version_number = 0
        try:
            identifier = int(item.get("id", item.get("versionId", 0)))
        except Exception:
            identifier = 0
        return published, version_number, identifier

    return max(records.values(), key=sort_key)


def resolve_version_id(version: dict[str, Any]) -> int:
    for key in ("id", "versionId"):
        if version.get(key) is not None:
            return int(version[key])
    raise ValueError("Dryad version record has no numeric ID")


def file_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for values in nested_lists(payload):
        if not values or not all(isinstance(item, dict) for item in values):
            continue
        for item in values:
            name = item.get("path", item.get("filename", item.get("name")))
            if name:
                records[PurePosixPath(str(name)).name] = item
    return [records[name] for name in sorted(records)]


def api_file_summary(record: dict[str, Any]) -> dict[str, Any]:
    name = PurePosixPath(
        str(record.get("path", record.get("filename", record.get("name", ""))))
    ).name
    links = record.get("_links") if isinstance(record.get("_links"), dict) else {}
    link_summary: dict[str, str] = {}
    for key, value in links.items():
        href = value.get("href") if isinstance(value, dict) else value
        if href:
            link_summary[str(key)] = str(href)
    return {
        "name": name,
        "id": record.get("id", record.get("fileId")),
        "size": record.get("size", record.get("sizeBytes", record.get("bytes"))),
        "digest": record.get("digest", record.get("checksum", record.get("md5"))),
        "mime_type": record.get("mimeType", record.get("mime_type")),
        "links": link_summary,
    }


def safe_extract_bundle(bundle: bytes, root: Path) -> list[Path]:
    bundle_path = root / "dryad_bundle.zip"
    bundle_path.write_bytes(bundle)
    extracted: list[Path] = []
    with zipfile.ZipFile(bundle_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            basename = PurePosixPath(info.filename).name
            if basename not in EXPECTED_FILES:
                continue
            target = root / basename
            target.write_bytes(archive.read(info))
            extracted.append(target)
    return sorted(extracted)


def delimiter_from_header(text: str) -> str:
    try:
        return csv.Sniffer().sniff(text, delimiters=",\t;").delimiter
    except csv.Error:
        return ","


def bounded_header(path: Path) -> tuple[tuple[str, ...], str]:
    text, record = read_bounded_first_record_text(path, max_record_bytes=MAX_HEADER_BYTES)
    delimiter = delimiter_from_header(text)
    columns = tuple(str(value).strip() for value in next(csv.reader([text], delimiter=delimiter)))
    if not columns:
        raise ValueError(f"empty header in {path.name}")
    return columns, record.terminator


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def find_column(columns: tuple[str, ...], candidates: tuple[str, ...]) -> str | None:
    exact = {normalized(column): column for column in columns}
    for candidate in candidates:
        if normalized(candidate) in exact:
            return exact[normalized(candidate)]
    for column in columns:
        token = normalized(column)
        if any(normalized(candidate) in token for candidate in candidates):
            return column
    return None


def finite_float(value: str) -> float:
    result = float(str(value).strip())
    if not math.isfinite(result):
        raise ValueError("non-finite geometry value")
    return result


def inspect_square_matrix(path: Path, delimiter: str) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))
    if len(rows) != EXPECTED_NODE_COUNT + 1:
        return None
    if len(rows[0]) != EXPECTED_NODE_COUNT + 1:
        return None
    columns = tuple(str(value).strip() for value in rows[0][1:])
    row_ids = tuple(str(row[0]).strip() for row in rows[1:])
    if columns != row_ids or len(set(row_ids)) != EXPECTED_NODE_COUNT:
        return None
    matrix = np.asarray([[finite_float(value) for value in row[1:]] for row in rows[1:]])
    if not np.allclose(matrix, matrix.T, atol=1e-9, rtol=1e-9):
        raise ValueError("distance matrix is not symmetric")
    if not np.allclose(np.diag(matrix), 0.0, atol=1e-9, rtol=0.0):
        raise ValueError("distance matrix diagonal is not zero")
    if np.any(matrix < -1e-12):
        raise ValueError("negative pairwise distance")
    values = matrix[np.triu_indices(EXPECTED_NODE_COUNT, 1)]
    return {
        "geometry_type": "square_distance_matrix",
        "node_count": EXPECTED_NODE_COUNT,
        "pair_count": int(values.size),
        "node_ids_fingerprint": canonical_sha256(list(row_ids)),
        "matrix_fingerprint": canonical_sha256(matrix.tolist()),
        "distance_min_positive": float(np.min(values[values > 0.0])),
        "distance_median": float(np.median(values)),
        "distance_max": float(np.max(values)),
    }


def inspect_tabular_geometry(path: Path, delimiter: str) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = tuple(reader.fieldnames or ())
        rows = list(reader)
    id_col = find_column(columns, ("pool_id", "pond_id", "site_id", "pool", "pond", "site", "id"))
    x_col = find_column(columns, ("x", "easting", "longitude", "lon"))
    y_col = find_column(columns, ("y", "northing", "latitude", "lat"))
    if id_col and x_col and y_col:
        ids = tuple(str(row[id_col]).strip() for row in rows)
        coords = np.asarray([[finite_float(row[x_col]), finite_float(row[y_col])] for row in rows])
        if len(ids) == EXPECTED_NODE_COUNT and len(set(ids)) == EXPECTED_NODE_COUNT:
            return {
                "geometry_type": "coordinate_table",
                "node_count": EXPECTED_NODE_COUNT,
                "node_ids_fingerprint": canonical_sha256(list(ids)),
                "coordinate_columns": [x_col, y_col],
                "coordinates_fingerprint": canonical_sha256(coords.tolist()),
                "coordinate_range": {
                    "x_min": float(np.min(coords[:, 0])),
                    "x_max": float(np.max(coords[:, 0])),
                    "y_min": float(np.min(coords[:, 1])),
                    "y_max": float(np.max(coords[:, 1])),
                },
            }

    source_col = find_column(columns, ("source", "from", "pool1", "pond1", "site1", "id1"))
    target_col = find_column(columns, ("target", "to", "pool2", "pond2", "site2", "id2"))
    distance_col = find_column(columns, ("distance", "dist", "euclidean"))
    if source_col and target_col and distance_col:
        pairs: dict[tuple[str, str], float] = {}
        ids: set[str] = set()
        for row in rows:
            source = str(row[source_col]).strip()
            target = str(row[target_col]).strip()
            if not source or not target or source == target:
                continue
            distance = finite_float(row[distance_col])
            if distance < 0.0:
                raise ValueError("negative pairwise distance")
            key = tuple(sorted((source, target)))
            if key in pairs and not math.isclose(pairs[key], distance, abs_tol=1e-9, rel_tol=1e-9):
                raise ValueError("inconsistent duplicate pairwise distance")
            pairs[key] = distance
            ids.update(key)
        if len(ids) == EXPECTED_NODE_COUNT and len(pairs) == EXPECTED_PAIR_COUNT:
            ordered = [[a, b, pairs[(a, b)]] for a, b in sorted(pairs)]
            values = np.asarray([row[2] for row in ordered], dtype=float)
            return {
                "geometry_type": "complete_pairwise_long_table",
                "node_count": EXPECTED_NODE_COUNT,
                "pair_count": len(pairs),
                "node_ids_fingerprint": canonical_sha256(sorted(ids)),
                "pairwise_fingerprint": canonical_sha256(ordered),
                "distance_columns": [source_col, target_col, distance_col],
                "distance_min_positive": float(np.min(values[values > 0.0])),
                "distance_median": float(np.median(values)),
                "distance_max": float(np.max(values)),
            }
    return None


def inspect_geometry(path: Path) -> dict[str, Any]:
    columns, terminator = bounded_header(path)
    if any(term in " ".join(columns).lower() for term in RESPONSE_TERMS):
        return {
            "file": path.name,
            "header": list(columns),
            "terminator": terminator,
            "status": "rejected_response_term_in_header",
        }
    text, _ = read_bounded_first_record_text(path, max_record_bytes=MAX_HEADER_BYTES)
    delimiter = delimiter_from_header(text)
    geometry = inspect_square_matrix(path, delimiter)
    if geometry is None:
        geometry = inspect_tabular_geometry(path, delimiter)
    return {
        "file": path.name,
        "header": list(columns),
        "terminator": terminator,
        "row_count": sum(1 for _ in path.open("r", encoding="utf-8-sig")) - 1,
        "status": "complete_geometry" if geometry else "not_complete_geometry",
        "geometry": geometry,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dataset, dataset_diag = get_json(DATASET_API)
    versions, versions_diag = get_json(VERSIONS_API)
    metadata_diagnostics: dict[str, Any] = {
        "dataset": dataset_diag,
        "versions": versions_diag,
    }
    if dataset is None or versions is None:
        result = {
            "status": "gate0_stop_source_metadata_transport_blocked",
            "response_rows_opened": False,
            "response_data_rows_parsed": False,
            "transport_diagnostics": metadata_diagnostics,
            "next_gate": "stop candidate pre-response",
        }
        result["fingerprint"] = canonical_sha256(result)
        (args.output_dir / "gate0_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    version = choose_version(versions)
    version_id = resolve_version_id(version)
    files_api = f"https://datadryad.org/api/v2/versions/{version_id}/files"
    files, files_diag = get_json(files_api)
    metadata_diagnostics["files"] = files_diag
    if files is None:
        result = {
            "status": "gate0_stop_source_metadata_transport_blocked",
            "response_rows_opened": False,
            "response_data_rows_parsed": False,
            "transport_diagnostics": metadata_diagnostics,
            "next_gate": "stop candidate pre-response",
        }
        result["fingerprint"] = canonical_sha256(result)
        (args.output_dir / "gate0_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    records = file_records(files)
    api_manifest = [api_file_summary(record) for record in records]
    actual_api_names = {row["name"] for row in api_manifest}
    (args.output_dir / "dryad_dataset_metadata.json").write_text(
        json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "dryad_versions_metadata.json").write_text(
        json.dumps(versions, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "dryad_files_metadata.json").write_text(
        json.dumps(files, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    bundle, bundle_diag = request_bytes(
        BUNDLE_API,
        accept="application/zip,application/octet-stream,*/*",
    )
    transport_attempts = {
        "first_file_route_run": {
            "workflow_run_id": 32093871518,
            "status": 401,
            "response_rows_opened": False,
        },
        "official_dataset_bundle_route": bundle_diag,
    }

    if bundle is None or not bundle.startswith(b"PK\x03\x04"):
        result = {
            "status": "gate0_stop_source_transport_blocked",
            "response_rows_opened": False,
            "response_data_rows_parsed": False,
            "resolved_version_id": version_id,
            "expected_file_names": sorted(EXPECTED_FILES),
            "actual_api_file_names": sorted(actual_api_names),
            "api_file_manifest": api_manifest,
            "transport_attempts": transport_attempts,
            "next_gate": "stop candidate pre-response; do not attempt browser-challenge workarounds",
        }
        result["fingerprint"] = canonical_sha256(result)
        (args.output_dir / "gate0_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    with tempfile.TemporaryDirectory(prefix="hydrilla_bundle_") as temp_dir:
        root = Path(temp_dir)
        extracted = safe_extract_bundle(bundle, root)
        extracted_by_name = {path.name: path for path in extracted}
        extracted_names = set(extracted_by_name)
        file_manifest = [
            {
                "name": path.name,
                "size": path.stat().st_size,
                "md5": digest_file(path, "md5"),
                "sha256": digest_file(path, "sha256"),
            }
            for path in extracted
        ]
        headers: dict[str, dict[str, Any]] = {}
        geometry_audit: list[dict[str, Any]] = []
        for name, path in sorted(extracted_by_name.items()):
            if name == "README.md":
                (args.output_dir / "README_frozen.md").write_bytes(path.read_bytes())
                continue
            if path.suffix.lower() != ".csv":
                continue
            columns, terminator = bounded_header(path)
            headers[name] = {
                "columns": list(columns),
                "terminator": terminator,
            }
            if name in GEOMETRY_CANDIDATES:
                geometry_audit.append(inspect_geometry(path))

    complete_geometry = [row for row in geometry_audit if row["status"] == "complete_geometry"]
    all_data_header = headers.get("All_Data.csv", {}).get("columns", [])
    all_data_text = " ".join(str(value).lower() for value in all_data_header)
    survey_schema_pass = (
        any(term in all_data_text for term in ("date", "year", "survey"))
        and any(term in all_data_text for term in ("hydrilla", "occup", "detect", "presence"))
    )

    if extracted_names != EXPECTED_FILES or actual_api_names != EXPECTED_FILES:
        status = "gate0_stop_source_manifest_mismatch"
    elif not complete_geometry:
        status = "gate0_stop_no_complete_response_free_geometry"
    elif not survey_schema_pass:
        status = "gate0_stop_response_semantics_not_auditable_from_schema"
    else:
        status = "gate0_pass_source_geometry_schema"

    result = {
        "status": status,
        "response_rows_opened": False,
        "response_data_rows_parsed": False,
        "resolved_version_id": version_id,
        "expected_file_names": sorted(EXPECTED_FILES),
        "actual_api_file_names": sorted(actual_api_names),
        "actual_bundle_file_names": sorted(extracted_names),
        "api_file_manifest": api_manifest,
        "extracted_file_manifest": file_manifest,
        "bundle_sha256": digest_bytes(bundle, "sha256"),
        "transport_attempts": transport_attempts,
        "bounded_headers": headers,
        "geometry_audit": geometry_audit,
        "complete_geometry_files": [row["file"] for row in complete_geometry],
        "event_count_feasibility": {
            "published_colonization_events": 133,
            "published_extinction_events": 55,
            "published_persistence_events": 147,
            "status": "pass_from_public_aggregate_metadata",
        },
        "next_gate": (
            "freeze canonical geometry and run unchanged response-blind structural ladder"
            if status == "gate0_pass_source_geometry_schema"
            else "stop candidate pre-response"
        ),
    }
    result["fingerprint"] = canonical_sha256(result)
    (args.output_dir / "gate0_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "bounded_headers.json").write_text(
        json.dumps(headers, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "geometry_audit.json").write_text(
        json.dumps(geometry_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
