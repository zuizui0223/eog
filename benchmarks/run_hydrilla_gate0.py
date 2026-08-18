#!/usr/bin/env python3
"""Run Hydrilla two-layer EOG-WF Gate 0 without opening response rows.

The runner freezes the published Dryad version and exact bytes, reads the full README,
reads only bounded first physical records from ambiguous/response-bearing CSV files,
and inspects complete rows only for tables whose headers and declared roles are
response-free geometry.  It determines whether the 506-pool universe has complete
coordinates or complete pairwise distances.  A scientific Gate-0 STOP is emitted as a
normal result rather than converted into a CI error.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterable
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

import numpy as np

from eog.v2.response_firewall import read_bounded_first_record_text


DOI = "10.5061/dryad.jsxksn0fn"
DATASET_API = f"https://datadryad.org/api/v2/datasets/doi%3A{quote(DOI, safe='')}"
VERSIONS_API = DATASET_API + "/versions"
EXPECTED_FILES = {
    "All_Data.csv",
    "All_dist.csv",
    "Days_since_occupancy.csv",
    "FiveYearAverages.csv",
    "near_neigh_dist.csv",
    "Post_Hoc_Dataset.csv",
    "README.md",
}
EXPECTED_NODE_COUNT = 506
PAIR_COUNT = EXPECTED_NODE_COUNT * (EXPECTED_NODE_COUNT - 1) // 2
MAX_HEADER_BYTES = 16_384
USER_AGENT = "EOG-Hydrilla-Gate0/1.0 (+https://github.com/zuizui0223/eog)"

RESPONSE_OR_AMBIGUOUS_FILES = {
    "All_Data.csv",
    "Days_since_occupancy.csv",
    "FiveYearAverages.csv",
    "Post_Hoc_Dataset.csv",
}
GEOMETRY_CANDIDATES = {"All_dist.csv", "near_neigh_dist.csv"}

RESPONSE_HEADER_TERMS = {
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
    "invad",
    "status",
}


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def get_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
    with urlopen(request, timeout=60) as response:
        return response.read()


def get_json(url: str) -> dict[str, Any]:
    return json.loads(get_bytes(url).decode("utf-8"))


def nested_lists(value: Any) -> Iterable[list[Any]]:
    if isinstance(value, list):
        yield value
        for item in value:
            yield from nested_lists(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from nested_lists(item)


def choose_version(payload: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for values in nested_lists(payload):
        if values and all(isinstance(item, dict) for item in values):
            for item in values:
                if any(key in item for key in ("versionNumber", "version", "id", "versionId")):
                    candidates.append(item)
    if not candidates:
        raise ValueError("Dryad versions API returned no recognizable version records")

    def key(item: dict[str, Any]) -> tuple[int, int]:
        version = item.get("versionNumber", item.get("version", 0))
        identifier = item.get("id", item.get("versionId", 0))
        try:
            version_i = int(version)
        except Exception:
            version_i = 0
        try:
            id_i = int(identifier)
        except Exception:
            id_i = 0
        published = str(item.get("status", "")).lower() in {"published", "submitted"}
        return (1 if published else 0, version_i * 1_000_000_000 + id_i)

    return max(candidates, key=key)


def version_id(version: dict[str, Any]) -> int:
    for key in ("id", "versionId"):
        if key in version:
            return int(version[key])
    links = version.get("_links", {})
    for entry in links.values() if isinstance(links, dict) else ():
        href = entry.get("href") if isinstance(entry, dict) else None
        if href:
            match = re.search(r"/versions/(\d+)", str(href))
            if match:
                return int(match.group(1))
    raise ValueError("unable to resolve Dryad version ID")


def extract_file_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for values in nested_lists(payload):
        if values and all(isinstance(item, dict) for item in values):
            if any(
                any(key in item for key in ("path", "filename", "name"))
                for item in values
            ):
                candidates.extend(values)
    records: dict[str, dict[str, Any]] = {}
    for item in candidates:
        name = str(item.get("path", item.get("filename", item.get("name", "")))).strip()
        name = Path(name).name
        if name:
            records[name] = item
    if not records:
        raise ValueError("Dryad files API returned no recognizable file records")
    return [records[name] for name in sorted(records)]


def file_name(record: dict[str, Any]) -> str:
    return Path(str(record.get("path", record.get("filename", record.get("name", ""))))).name


def file_size(record: dict[str, Any]) -> int | None:
    for key in ("size", "sizeBytes", "bytes"):
        value = record.get(key)
        if value is not None:
            try:
                return int(value)
            except Exception:
                pass
    return None


def declared_digest(record: dict[str, Any]) -> str | None:
    for key in ("digest", "checksum", "md5", "sha256"):
        value = record.get(key)
        if value:
            if isinstance(value, dict):
                for nested in value.values():
                    if nested:
                        return str(nested)
            return str(value)
    return None


def download_href(record: dict[str, Any]) -> str:
    links = record.get("_links", {})
    if isinstance(links, dict):
        preferred = (
            "stash:download",
            "download",
            "self",
        )
        for key in preferred:
            entry = links.get(key)
            href = entry.get("href") if isinstance(entry, dict) else entry
            if href and (key != "self" or "/files/" in str(href)):
                return urljoin("https://datadryad.org", str(href))
        for entry in links.values():
            href = entry.get("href") if isinstance(entry, dict) else entry
            if href and "download" in str(href).lower():
                return urljoin("https://datadryad.org", str(href))
    for key in ("downloadUrl", "download_url", "url"):
        if record.get(key):
            return urljoin("https://datadryad.org", str(record[key]))
    identifier = record.get("id", record.get("fileId"))
    if identifier is not None:
        return f"https://datadryad.org/api/v2/files/{int(identifier)}/download"
    raise ValueError(f"unable to resolve download URL for {file_name(record)!r}")


def download_record(record: dict[str, Any], destination: Path) -> dict[str, Any]:
    data = get_bytes(download_href(record))
    destination.write_bytes(data)
    expected_size = file_size(record)
    if expected_size is not None and expected_size != len(data):
        raise ValueError(
            f"size mismatch for {destination.name}: API={expected_size}, downloaded={len(data)}"
        )
    return {
        "name": destination.name,
        "api_size": expected_size,
        "downloaded_size": len(data),
        "api_digest": declared_digest(record),
        "md5": md5_file(destination),
        "sha256": sha256_file(destination),
    }


def sniff_delimiter(header: str) -> str:
    try:
        return csv.Sniffer().sniff(header, delimiters=",\t;").delimiter
    except csv.Error:
        return ","


def header_columns(path: Path) -> tuple[str, ...]:
    text, record = read_bounded_first_record_text(path, max_record_bytes=MAX_HEADER_BYTES)
    delimiter = sniff_delimiter(text)
    columns = tuple(next(csv.reader([text], delimiter=delimiter)))
    if not columns:
        raise ValueError(f"empty header in {path.name}")
    return tuple(str(value).strip() for value in columns)


def header_has_response_terms(columns: tuple[str, ...]) -> bool:
    lowered = " ".join(columns).lower()
    return any(term in lowered for term in RESPONSE_HEADER_TERMS)


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def find_column(columns: tuple[str, ...], candidates: tuple[str, ...]) -> str | None:
    normalized = {normalize_name(column): column for column in columns}
    for candidate in candidates:
        if normalize_name(candidate) in normalized:
            return normalized[normalize_name(candidate)]
    for column in columns:
        token = normalize_name(column)
        if any(normalize_name(candidate) in token for candidate in candidates):
            return column
    return None


def parse_float(value: str) -> float:
    number = float(str(value).strip())
    if not math.isfinite(number):
        raise ValueError("distance/coordinate values must be finite")
    return number


def inspect_square_matrix(path: Path, delimiter: str) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))
    if len(rows) != EXPECTED_NODE_COUNT + 1:
        return None
    header = tuple(str(value).strip() for value in rows[0])
    if len(header) != EXPECTED_NODE_COUNT + 1:
        return None
    column_ids = header[1:]
    row_ids = tuple(str(row[0]).strip() for row in rows[1:])
    if row_ids != column_ids or len(set(row_ids)) != EXPECTED_NODE_COUNT:
        return None
    matrix = np.asarray([[parse_float(value) for value in row[1:]] for row in rows[1:]])
    if matrix.shape != (EXPECTED_NODE_COUNT, EXPECTED_NODE_COUNT):
        return None
    if not np.allclose(matrix, matrix.T, atol=1e-9, rtol=1e-9):
        raise ValueError("distance matrix is not symmetric")
    if not np.allclose(np.diag(matrix), 0.0, atol=1e-9, rtol=0.0):
        raise ValueError("distance matrix diagonal is not zero")
    if np.any(matrix < -1e-12):
        raise ValueError("distance matrix contains negative values")
    positive = matrix[np.triu_indices(EXPECTED_NODE_COUNT, 1)]
    return {
        "type": "square_distance_matrix",
        "node_count": EXPECTED_NODE_COUNT,
        "pair_count": int(positive.size),
        "node_ids_fingerprint": canonical_sha256(list(row_ids)),
        "distance_min_positive": float(np.min(positive)),
        "distance_median": float(np.median(positive)),
        "distance_max": float(np.max(positive)),
        "distance_matrix_fingerprint": canonical_sha256(matrix.tolist()),
    }


def inspect_long_or_coordinate_table(path: Path, delimiter: str) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        columns = tuple(reader.fieldnames or ())
        rows = list(reader)
    if not columns:
        return None

    id_column = find_column(columns, ("pool_id", "pond_id", "site_id", "pool", "pond", "site", "id"))
    x_column = find_column(columns, ("x", "easting", "longitude", "lon"))
    y_column = find_column(columns, ("y", "northing", "latitude", "lat"))
    if id_column and x_column and y_column:
        ids = tuple(str(row[id_column]).strip() for row in rows)
        coords = np.asarray([[parse_float(row[x_column]), parse_float(row[y_column])] for row in rows])
        if len(ids) == EXPECTED_NODE_COUNT and len(set(ids)) == EXPECTED_NODE_COUNT:
            if len({(float(x), float(y)) for x, y in coords}) != EXPECTED_NODE_COUNT:
                raise ValueError("coordinate table contains duplicate coordinates")
            return {
                "type": "coordinate_table",
                "node_count": EXPECTED_NODE_COUNT,
                "node_ids_fingerprint": canonical_sha256(list(ids)),
                "coordinate_columns": [x_column, y_column],
                "coordinate_range": {
                    "x_min": float(np.min(coords[:, 0])),
                    "x_max": float(np.max(coords[:, 0])),
                    "y_min": float(np.min(coords[:, 1])),
                    "y_max": float(np.max(coords[:, 1])),
                },
                "coordinates_fingerprint": canonical_sha256(coords.tolist()),
            }

    source_column = find_column(columns, ("source", "from", "pool1", "pond1", "site1", "id1", "origin"))
    target_column = find_column(columns, ("target", "to", "pool2", "pond2", "site2", "id2", "destination"))
    distance_column = find_column(columns, ("distance", "dist", "euclidean"))
    if source_column and target_column and distance_column:
        pairs: dict[tuple[str, str], float] = {}
        ids: set[str] = set()
        for row in rows:
            source = str(row[source_column]).strip()
            target = str(row[target_column]).strip()
            if not source or not target or source == target:
                continue
            distance = parse_float(row[distance_column])
            if distance < 0.0:
                raise ValueError("pairwise distance contains a negative value")
            key = tuple(sorted((source, target)))
            if key in pairs and not math.isclose(pairs[key], distance, rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError("duplicate pair has inconsistent distance")
            pairs[key] = distance
            ids.update(key)
        if len(ids) == EXPECTED_NODE_COUNT and len(pairs) == PAIR_COUNT:
            ordered_pairs = [[a, b, pairs[(a, b)]] for a, b in sorted(pairs)]
            values = np.asarray([row[2] for row in ordered_pairs], dtype=float)
            return {
                "type": "complete_pairwise_long_table",
                "node_count": EXPECTED_NODE_COUNT,
                "pair_count": len(pairs),
                "columns": {
                    "source": source_column,
                    "target": target_column,
                    "distance": distance_column,
                },
                "node_ids_fingerprint": canonical_sha256(sorted(ids)),
                "distance_min_positive": float(np.min(values[values > 0.0])),
                "distance_median": float(np.median(values)),
                "distance_max": float(np.max(values)),
                "pairwise_fingerprint": canonical_sha256(ordered_pairs),
            }
    return None


def inspect_geometry(path: Path) -> dict[str, Any]:
    columns = header_columns(path)
    if header_has_response_terms(columns):
        return {
            "file": path.name,
            "header": list(columns),
            "status": "rejected_response_terms_in_header",
        }
    text, _ = read_bounded_first_record_text(path, max_record_bytes=MAX_HEADER_BYTES)
    delimiter = sniff_delimiter(text)
    geometry = inspect_square_matrix(path, delimiter)
    if geometry is None:
        geometry = inspect_long_or_coordinate_table(path, delimiter)
    return {
        "file": path.name,
        "header": list(columns),
        "status": "complete_geometry" if geometry else "not_complete_geometry",
        "geometry": geometry,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dataset = get_json(DATASET_API)
    versions_payload = get_json(VERSIONS_API)
    version = choose_version(versions_payload)
    resolved_version_id = version_id(version)
    files_api = f"https://datadryad.org/api/v2/versions/{resolved_version_id}/files"
    files_payload = get_json(files_api)
    records = extract_file_records(files_payload)
    record_by_name = {file_name(record): record for record in records}
    actual_names = set(record_by_name)

    source_manifest: list[dict[str, Any]] = []
    headers: dict[str, list[str]] = {}
    geometry_results: list[dict[str, Any]] = []
    readme_sha256: str | None = None

    with tempfile.TemporaryDirectory(prefix="hydrilla_gate0_") as temporary:
        root = Path(temporary)
        for name in sorted(actual_names):
            destination = root / name
            source_manifest.append(download_record(record_by_name[name], destination))
            if name == "README.md":
                readme_text = destination.read_text(encoding="utf-8-sig")
                readme_sha256 = hashlib.sha256(readme_text.encode("utf-8")).hexdigest()
                (args.output_dir / "README_frozen.md").write_text(readme_text, encoding="utf-8")
            elif destination.suffix.lower() in {".csv", ".tsv", ".txt"}:
                columns = header_columns(destination)
                headers[name] = list(columns)
                if name in GEOMETRY_CANDIDATES:
                    geometry_results.append(inspect_geometry(destination))

    complete_geometry = [
        row for row in geometry_results if row.get("status") == "complete_geometry"
    ]
    expected_files_match = actual_names == EXPECTED_FILES
    node_geometry_pass = bool(complete_geometry)

    all_data_header = headers.get("All_Data.csv", [])
    lowered_all_data = " ".join(all_data_header).lower()
    survey_semantics_supported = bool(
        any(token in lowered_all_data for token in ("year", "date", "survey"))
        and any(token in lowered_all_data for token in ("hyd", "occup", "detect", "presence"))
    )

    source_metadata = {
        "dataset_api_sha256": canonical_sha256(dataset),
        "versions_api_sha256": canonical_sha256(versions_payload),
        "files_api_sha256": canonical_sha256(files_payload),
        "resolved_version_id": resolved_version_id,
        "version_record": version,
        "expected_files_match": expected_files_match,
        "expected_file_names": sorted(EXPECTED_FILES),
        "actual_file_names": sorted(actual_names),
        "file_manifest": source_manifest,
        "readme_sha256": readme_sha256,
    }
    (args.output_dir / "source_manifest.json").write_text(
        json.dumps(source_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "bounded_headers.json").write_text(
        json.dumps(headers, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "geometry_audit.json").write_text(
        json.dumps(geometry_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not expected_files_match:
        status = "gate0_stop_source_manifest_mismatch"
    elif not node_geometry_pass:
        status = "gate0_stop_no_complete_response_free_geometry"
    elif not survey_semantics_supported:
        status = "gate0_stop_response_semantics_not_auditable_from_schema"
    else:
        status = "gate0_pass_source_geometry_schema"

    result: dict[str, Any] = {
        "status": status,
        "response_rows_opened": False,
        "response_data_rows_parsed": False,
        "full_files_parsed": [
            "README.md",
            *[row["file"] for row in geometry_results],
        ],
        "ambiguous_or_response_files_header_only": sorted(RESPONSE_OR_AMBIGUOUS_FILES),
        "source_manifest": source_metadata,
        "bounded_headers": headers,
        "geometry_audit": geometry_results,
        "complete_geometry_files": [row["file"] for row in complete_geometry],
        "node_geometry_pass": node_geometry_pass,
        "survey_semantics_schema_pass": survey_semantics_supported,
        "event_count_feasibility": {
            "published_colonization_events": 133,
            "published_extinction_events": 55,
            "published_persistence_events": 147,
            "status": "pass_from_public_aggregate_metadata",
        },
        "process_source_boundary": {
            "internal_sources": "recorded occupied pools at the preceding eligible period",
            "external_river_source": "must remain explicit uncertainty unless a response-free distance-to-river input is identified before response access",
            "claim": "conditional recorded-colonization forecast, not unique historical route",
        },
        "next_gate": (
            "freeze canonical geometry and run unchanged response-blind structural ladder"
            if status == "gate0_pass_source_geometry_schema"
            else "stop candidate pre-response and preserve result"
        ),
    }
    result["fingerprint"] = canonical_sha256(result)
    (args.output_dir / "gate0_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
