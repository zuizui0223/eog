#!/usr/bin/env python3
"""ONE-SHOT public Dryad marked-movement data qualification, metadata only.

Freeze DOI/file names and source/target gates BEFORE transport. Retrieves only
the official public version + version-file metadata and a tightly capped
version ZIP. Saves filenames, SHA256/digests, CSV headers and total row counts;
never models biological movement, never exports raw event/individual rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any

PROTOCOL = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
UA = "EOG-IndependentMovement-SourceQualification/1.0 (public DOI source verification)"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
    result["receipt_sha256_without_self_hash"] = _sha((output + "\n").encode())
    path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")


def _approved(host: str, *, payload: bool) -> bool:
    if host in ("datadryad.org", "www.datadryad.org"):
        return True
    return payload and (host.endswith(".amazonaws.com") or host.endswith(".cloudfront.net"))


def _get(url: str, *, byte_cap: int, timeout: int, is_payload: bool) -> tuple[bytes, str]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ("datadryad.org", "www.datadryad.org"):
        raise ValueError("STOP_UNDECLARED_SOURCE_ENDPOINT")
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json" if not is_payload else "application/zip, */*",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        target = urllib.parse.urlsplit(response.geturl())
        if target.scheme != "https" or not _approved(target.hostname or "", payload=is_payload):
            raise ValueError("STOP_UNEXPECTED_SOURCE_REDIRECT")
        content = response.read(byte_cap + 1)
        if len(content) > byte_cap:
            raise ValueError("STOP_SOURCE_BYTE_BUDGET")
        return content, target.hostname or ""


def _json_get(url: str, limits: dict[str, Any]) -> tuple[dict[str, Any], str]:
    raw, _ = _get(
        url, byte_cap=limits["max_metadata_bytes"],
        timeout=limits["request_timeout_seconds"], is_payload=False
    )
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("STOP_API_EXPECTED_JSON_OBJECT")
    return value, _sha(raw)


def _version_id(metadata: dict[str, Any]) -> str:
    links = metadata.get("_links") or metadata.get("links") or {}
    candidates = [links.get(k) for k in ("stash:version", "latestVersion", "version")]
    for c in candidates:
        href = c.get("href") if isinstance(c, dict) else c
        if isinstance(href, str):
            m = re.search(r"/versions/(\d+)(?:[/?]|$)", href)
            if m:
                return m.group(1)
    for k in ("versionId", "version_id"):
        if str(metadata.get(k, "")).isdigit():
            return str(metadata[k])
    raise ValueError("STOP_VERSION_ID_NOT_IN_OFFICIAL_METADATA")


def _metadata_files(response: dict[str, Any], max_files: int) -> list[dict[str, Any]]:
    embedded = response.get("_embedded") or response.get("embedded") or {}
    entries = embedded.get("stash:files") or embedded.get("files") or response.get("files") or []
    if isinstance(entries, dict):
        entries = entries.get("files") or entries.get("entries") or []
    if not isinstance(entries, list) or len(entries) > max_files:
        raise ValueError("STOP_VERSION_FILE_METADATA_SCHEMA_OR_BUDGET")
    rows = []
    for f in entries:
        if not isinstance(f, dict):
            raise ValueError("STOP_FILE_METADATA_NOT_OBJECT")
        name = str(f.get("path") or f.get("filename") or f.get("name") or "")
        if not name or PurePosixPath(name).name != name or ".." in name.split("/"):
            raise ValueError("STOP_FILE_METADATA_UNSAFE_NAME")
        digest = str(f.get("digest") or f.get("checksum") or "")
        dtype = str(f.get("digestType") or f.get("digest_type") or "")
        if ":" in digest and not dtype:
            dtype, digest = digest.split(":", 1)
        rows.append({
            "name": name,
            "size_bytes": int(f.get("size") or f.get("sizeBytes") or 0),
            "publisher_digest_type": dtype.lower() or None,
            "publisher_digest": digest.lower() or None,
        })
    return sorted(rows, key=lambda x: x["name"])


def _read_zip(raw: bytes, source: dict[str, Any], limits: dict[str, Any],
              metadata_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("STOP_VERSION_DOWNLOAD_NOT_ZIP")
    expected = set(source["publisher_landing_file_names"])
    listed = {x["name"]: x for x in metadata_files}
    if set(listed) != expected:
        raise ValueError("STOP_PUBLISHER_FILELIST_MISMATCH")
    parsed = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = [x for x in archive.infolist() if not x.is_dir()]
        if len(infos) > limits["archive_members_max"]:
            raise ValueError("STOP_ZIP_MEMBER_BUDGET")
        if sum(x.file_size for x in infos) > limits["max_uncompressed_bytes"]:
            raise ValueError("STOP_UNCOMPRESSED_BUDGET")
        by_name: dict[str, zipfile.ZipInfo] = {}
        for item in infos:
            path = item.filename.replace("\\", "/")
            parts = path.split("/")
            if path.startswith("/") or ".." in parts:
                raise ValueError("STOP_ZIP_UNSAFE_PATH")
            basename = parts[-1]
            if basename in by_name:
                raise ValueError("STOP_DUPLICATE_MEMBER_BASENAME")
            by_name[basename] = item
        if set(by_name) != expected:
            raise ValueError("STOP_VERSION_ZIP_FILES_MISMATCH")
        for name in sorted(expected):
            item = by_name[name]
            data = archive.read(item)
            if len(data) > limits["max_uncompressed_bytes"]:
                raise ValueError("STOP_MEMBER_BYTES")
            row = listed[name]
            if row["size_bytes"] > 0 and row["size_bytes"] != len(data):
                raise ValueError("STOP_MEMBER_SIZE_MISMATCH")
            digest_type = row["publisher_digest_type"]
            digest = row["publisher_digest"]
            if digest_type and digest and digest_type in ("md5", "sha256"):
                computed = hashlib.new(digest_type, data).hexdigest()
                if computed.lower() != digest.lower():
                    raise ValueError("STOP_MEMBER_PUBLISHER_CHECKSUM_MISMATCH")
            result: dict[str, Any] = {
                "name": name, "size_bytes": len(data), "sha256": _sha(data),
                "publisher_digest_type": digest_type,
                "publisher_digest_verified": bool(digest and digest_type in ("md5","sha256")),
            }
            if name.lower().endswith(".csv"):
                txt = io.StringIO(data.decode("utf-8-sig", errors="replace"), newline="")
                reader = csv.reader(txt)
                header = next(reader, [])
                if not header or len(header) > limits["max_header_columns"]:
                    raise ValueError("STOP_CSV_HEADER_MISSING_OR_TOO_WIDE")
                # Read a row only for counting; do not examine/serialize any field values.
                n = 0
                for _ in reader:
                    n += 1
                    if n > limits["max_csv_rows"]:
                        raise ValueError("STOP_CSV_ROW_BUDGET")
                result["csv_header"] = [col.strip()[:110] for col in header]
                result["data_row_count"] = n
            elif name.lower().endswith((".txt",".md")):
                result["header_preview"] = data[:200].decode("utf-8-sig", errors="replace").splitlines()[0][:130] if data else ""
            elif name.lower().endswith(".rtf"):
                result["format"] = "rtf"
                result["header_preview"] = "OMITTED_RTF_CONTENT_METADATA_ONLY"
            parsed.append(result)
    return parsed


def _qualify_one(source: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    lim = protocol["resource_limits"]
    doi = source["doi"]
    encoded = urllib.parse.quote("doi:" + doi, safe="")
    prefix = "https://datadryad.org/api/v2"
    result: dict[str, Any] = {
        "source_id": source["id"], "doi": doi,
        "priority": source["priority"],
        "status": "STOP_UNSTARTED",
        "models_fit": 0, "biological_outcome_values_analyzed": 0,
        "new_eog_wf_endpoints": 0,
    }
    try:
        meta, meta_sha = _json_get(f"{prefix}/datasets/{encoded}", lim)
        result["dataset_metadata_sha256"] = meta_sha
        publisher_doi = str(meta.get("identifier") or meta.get("doi") or "").lower()
        if doi.lower() not in publisher_doi:
            raise ValueError("STOP_SOURCE_DOI_IDENTITY_MISMATCH")
        result["publisher_title"] = str(meta.get("title") or "")[:240]
        version_id = _version_id(meta)
        result["publisher_version_id"] = version_id
        version, version_sha = _json_get(f"{prefix}/versions/{version_id}", lim)
        result["version_metadata_sha256"] = version_sha
        files, files_sha = _json_get(f"{prefix}/versions/{version_id}/files?per_page=100", lim)
        result["files_metadata_sha256"] = files_sha
        listing = _metadata_files(files, lim["max_version_files"])
        result["publisher_file_list"] = listing
        if {x["name"] for x in listing} != set(source["publisher_landing_file_names"]):
            raise ValueError("STOP_PUBLISHER_FILELIST_MISMATCH")
        result["version_number"] = version.get("versionNumber")
        result["publisher_publication_date"] = str(
            version.get("publicationDate") or meta.get("publicationDate") or ""
        )[:30] or None
        pub_year = result["publisher_publication_date"]
        if pub_year and not pub_year.startswith(str(source["expected_publication_year"])):
            raise ValueError("STOP_VERSION_PUBLICATION_YEAR_MISMATCH")
        archive, final_host = _get(
            f"{prefix}/versions/{version_id}/download",
            byte_cap=lim["max_archive_bytes"],
            timeout=lim["request_timeout_seconds"], is_payload=True
        )
        result["download_host"] = final_host
        result["archive_size_bytes"] = len(archive)
        result["archive_sha256"] = _sha(archive)
        result["file_checks"] = _read_zip(archive,source,lim,listing)
        result["geographic_origin_destination_observable"] = "SCHEMA_NEEDS_SEMANTIC_REVIEW"
        result["full_three_axis_minrelax_qualified"] = False
        result["status"] = "SOURCE_SCHEMA_ONLY_QUALIFIED_BIOLOGICAL_OUTCOME_NOT_SCORED"
    except urllib.error.HTTPError as err:
        result["status"] = "STOP_TRANSPORT_HTTP_" + str(err.code)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
        result["status"] = "STOP_TRANSPORT_NETWORK"
        result["error_type"] = type(err).__name__
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError, zipfile.BadZipFile) as err:
        result["status"] = str(err) if str(err).startswith("STOP_") else "STOP_SOURCE_SCHEMA"
        result["error_type"] = type(err).__name__
    return result


def run(protocol: dict[str, Any]) -> dict[str, Any]:
    if protocol.get("status") != "PRE_TRANSPORT_SOURCE_ONLY_FROZEN":
        raise ValueError("source protocol must be frozen before execution")
    responses = [_qualify_one(source, protocol) for source in protocol["source_references"]]
    result = {
        "schema": "eog.independent_movement_source_qualification_v1.result",
        "status": ("SOURCE_SCHEMA_GATES_ALL_PASS" if all(x["status"].startswith("SOURCE_SCHEMA_ONLY_QUALIFIED")
                  for x in responses) else "SOURCE_SCHEMA_HAS_SCIENTIFIC_STOP"),
        "source_results": responses,
        "biological_event_rows_exported": 0,
        "biological_outcomes_analyzed": 0,
        "ecological_models_fit": 0,
        "new_eog_wf_endpoints": 0,
        "source_eligibility_for_external_validation": "NOT_AUTHORIZED_PENDING_SEMANTIC_REVIEW_AND_NEW_PRE_SCORE_PROTOCOL",
    }
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--protocol", type=Path, default=PROTOCOL)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(json.loads(args.protocol.read_text(encoding="utf-8")))
    _write(args.output, result)
    print(json.dumps({
        "status": result["status"],
        "source_statuses": {x["source_id"]:x["status"] for x in result["source_results"]},
        "biological_outcomes_analyzed": result["biological_outcomes_analyzed"],
        "new_eog_wf_endpoints": result["new_eog_wf_endpoints"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
