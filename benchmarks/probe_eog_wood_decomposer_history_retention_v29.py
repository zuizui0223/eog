#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
from pathlib import Path
import re
import urllib.error
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


def _request(url: str) -> tuple[bytes, dict[str, str], str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/140 Safari/537.36 "
                "EOG-v29-schema-probe/1.0"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        final_url = response.geturl()
    return payload, headers, final_url


def _extract_stream_urls(landing: str, landing_url: str) -> dict[str, str]:
    normalized = html.unescape(landing)
    normalized = normalized.replace("\\/", "/").replace("\\u002F", "/")
    result: dict[str, str] = {}
    for filename in EXPECTED_FILES:
        positions = [m.start() for m in re.finditer(re.escape(filename), normalized)]
        candidates: list[tuple[int, str]] = []
        for position in positions:
            start = max(0, position - 2500)
            end = min(len(normalized), position + 2500)
            window = normalized[start:end]
            for match in re.finditer(
                r"(?:https?://datadryad\.org)?(?:/stash)?/downloads/file_stream/\d+",
                window,
            ):
                url = match.group(0)
                if url.startswith("/"):
                    url = "https://datadryad.org" + url
                distance = abs((start + match.start()) - position)
                candidates.append((distance, url))
        if candidates:
            result[filename] = min(candidates, key=lambda item: item[0])[1]
    return result


def _download_files() -> tuple[dict[str, bytes], dict]:
    # First try the documented package API. Dryad currently may require auth for this
    # route, so a 401/403 is a transport condition rather than a dataset failure.
    try:
        archive, headers, final_url = _request(DOWNLOAD_URL)
        content_type = headers.get("content-type", "")
        if archive and ("zip" in content_type.lower() or archive.startswith(b"PK")):
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                members = [
                    name
                    for name in zf.namelist()
                    if not name.endswith("/") and Path(name).name in EXPECTED_FILES
                ]
                by_basename = {}
                for member in members:
                    basename = Path(member).name
                    if basename in by_basename:
                        raise RuntimeError(
                            f"duplicate Dryad file basename {basename}"
                        )
                    by_basename[basename] = zf.read(member)
            if EXPECTED_FILES <= set(by_basename):
                return by_basename, {
                    "mode": "api_dataset_zip",
                    "download_url": DOWNLOAD_URL,
                    "final_url": final_url,
                    "archive_bytes": len(archive),
                    "archive_sha256": _sha256(archive),
                }
    except urllib.error.HTTPError as error:
        if error.code not in {401, 403, 404}:
            raise

    landing_urls = (
        "https://datadryad.org/dataset/doi%3A10.5061/dryad.7p2cv",
        "https://datadryad.org/stash/dataset/doi:10.5061/dryad.7p2cv",
    )
    failures = []
    for landing_url in landing_urls:
        try:
            landing_bytes, _, final_landing = _request(landing_url)
            landing = landing_bytes.decode("utf-8", errors="replace")
            streams = _extract_stream_urls(landing, final_landing)
            if set(streams) != EXPECTED_FILES:
                failures.append(
                    {
                        "landing_url": landing_url,
                        "stream_files_found": sorted(streams),
                        "landing_bytes": len(landing_bytes),
                    }
                )
                continue
            files = {}
            stream_meta = {}
            for filename, stream_url in sorted(streams.items()):
                payload, headers, final_url = _request(stream_url)
                if not payload:
                    raise RuntimeError(f"empty Dryad stream for {filename}")
                files[filename] = payload
                file_id_match = re.search(r"/file_stream/(\\d+)", stream_url)
                file_id = int(file_id_match.group(1)) if file_id_match else None
                file_metadata = (
                    _public_file_metadata(file_id)
                    if file_id is not None
                    else None
                )
                stream_meta[filename] = {
                    "stream_url": stream_url,
                    "file_id": file_id,
                    "file_metadata": file_metadata,
                    "final_url": final_url,
                    "bytes": len(payload),
                    "sha256": _sha256(payload),
                    "content_type": headers.get("content-type", ""),
                }
            return files, {
                "mode": "landing_page_file_streams",
                "landing_url": landing_url,
                "final_landing_url": final_landing,
                "streams": stream_meta,
            }
        except urllib.error.HTTPError as error:
            failures.append(
                {"landing_url": landing_url, "http_error": int(error.code)}
            )

    raise RuntimeError(
        "unable to materialize Dryad files through package API or public file streams: "
        + json.dumps(failures, sort_keys=True)
    )


def _public_file_metadata(file_id: int) -> dict:
    url = f"https://datadryad.org/api/v2/files/{file_id}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "EOG-v29-schema-probe/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


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
    prefix = payload[:512].lstrip().lower()
    if prefix.startswith(b"<!doctype html") or b"<html" in prefix:
        raise RuntimeError(
            f"{name} resolved to HTML rather than CSV; Dryad anti-bot interstitial"
        )
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
    by_basename, transport = _download_files()

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
            "transport": transport,
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
    try:
        result = run()
    except RuntimeError as error:
        result = {
            "schema": "eog.wood_decomposer_history_retention.transport_audit.v29",
            "status": "transport_blocked_before_v29_scoring_protocol",
            "source": {
                "doi": DOI,
                "package_api": "HTTP 401 without OAuth",
                "public_stream_ids": {
                    "sample.data.csv": 52325,
                    "species.prevalence.csv": 52326,
                    "collembola.csv": 52327,
                },
                "public_stream_behavior": "Anubis HTML interstitial instead of CSV",
            },
            "error": str(error),
            "response_values_exposed": False,
            "scoring_performed": False,
            "biological_evidence": False,
        }
        payload = json.dumps(
            result, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        result["fingerprint"] = _sha256(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
