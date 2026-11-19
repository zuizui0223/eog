#!/usr/bin/env python3
"""Read-only, bounded, checksum-pinned Zenodo source-only gate.

One attempt per frozen source; stop after any transport/checksum failure.
Never scores biological records, fits a model, or exports raw ZIP/TAR bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile


class SourceStop(Exception):
    """A scientific source gate STOP, distinct from ecological model failure."""


def _safe_member(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return bool(normalized and not normalized.startswith("/") and
                ".." not in normalized.split("/") and
                not normalized.startswith("~"))


def _header(raw: bytes) -> list[str] | None:
    first = raw.decode("utf-8-sig", errors="replace").splitlines()
    if not first:
        return None
    return [x.strip() for x in first[0].split(",")][:300]


def _manifest(path: Path, item: dict, max_header_files: int, header_bytes: int) -> dict:
    if item["type"] == "zip":
        try:
            with zipfile.ZipFile(path) as z:
                info = [x for x in z.infolist() if not x.is_dir()]
                members = [(x.filename, x.file_size, x) for x in info]
                def header_read(x):
                    with z.open(x) as f:
                        return f.read(header_bytes)
                return _members_result(members, item, max_header_files, header_read)
        except (zipfile.BadZipFile, RuntimeError) as e:
            raise SourceStop("STOP_ZIP_FORMAT_" + type(e).__name__) from e
    if item["type"] == "tar.gz":
        try:
            with tarfile.open(path, mode="r:gz") as t:
                info = [x for x in t.getmembers() if x.isfile()]
                members = [(x.name, x.size, x) for x in info]
                def header_read(x):
                    f = t.extractfile(x)
                    if f is None:
                        return b""
                    with f:
                        return f.read(header_bytes)
                return _members_result(members, item, max_header_files, header_read)
        except (tarfile.TarError, RuntimeError, EOFError) as e:
            raise SourceStop("STOP_TAR_FORMAT_" + type(e).__name__) from e
    raise SourceStop("STOP_UNKNOWN_ARCHIVE_TYPE")


def _members_result(members, item: dict, max_headers: int, read_header) -> dict:
    if len(members) > item["max_members"]:
        raise SourceStop("STOP_TOO_MANY_ARCHIVE_MEMBERS")
    if any(not _safe_member(name) for name, _, _ in members):
        raise SourceStop("STOP_UNSAFE_ARCHIVE_PATH")
    total = sum(n for _, n, _ in members)
    if total > item["max_uncompressed_bytes"]:
        raise SourceStop("STOP_ARCHIVE_DECOMPRESSION_BUDGET")
    path_samples = sorted((n for n, _, _ in members))[:50]
    candidates = sorted(
        (name, size, handle)
        for name, size, handle in members
        if name.lower().endswith((".csv", ".tsv", ".txt", ".r", ".rmd", ".md"))
    )
    previews = []
    for name, size, handle in candidates:
        if len(previews) >= max_headers:
            break
        if name.lower().endswith((".csv", ".tsv", ".txt")) and size <= 50000000:
            firstline = read_header(handle)
            preview = _header(firstline)
            previews.append({
                "member_path": name,
                "member_bytes": size,
                "first_line_fields": preview,
                "first_line_truncated": b"\n" not in firstline,
            })
    return {
        "member_count": len(members),
        "total_uncompressed_bytes": total,
        "sorted_member_path_samples": path_samples,
        "candidate_text_table_count": len(candidates),
        "candidate_text_table_paths": [name for name, _, _ in candidates[:100]],
        "header_previews": previews,
    }


def run_gate(protocol: dict, output: Path) -> dict:
    result = {
        "schema_version": 1,
        "gate": "zenodo_two_archive_transport_and_manifest_only",
        "status": "STOP_UNSTARTED",
        "source_results": [],
        "models_fit": 0,
        "response_values_opened": 0,
        "new_eogwf_endpoints": 0,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="eog_zenodo_source_gate_") as directory:
            for item in protocol["sources"]:
                row = {
                    "tag": item["tag"], "source_doi": item["doi"],
                    "record_id": item["record_id"], "file_name": item["filename"],
                    "declared_md5": item["expected_md5"],
                }
                result["source_results"].append(row)
                sha256, md5 = hashlib.sha256(), hashlib.md5()
                size = 0
                path = Path(directory) / item["filename"]
                request = urllib.request.Request(item["url"], headers={
                    "User-Agent": "EOG-public-source-qualification/1.0",
                    "Accept": "*/*",
                })
                try:
                    with urllib.request.urlopen(request, timeout=40) as response:
                        row["transport_status"] = response.status
                        row["transport_final_url"] = response.geturl()
                        with path.open("wb") as sink:
                            for chunk in iter(lambda: response.read(1048576), b""):
                                size += len(chunk)
                                if size > item["max_bytes"]:
                                    raise SourceStop("STOP_SOURCE_COMPRESSED_SIZE_LIMIT")
                                sha256.update(chunk)
                                md5.update(chunk)
                                sink.write(chunk)
                except urllib.error.HTTPError as exc:
                    raise SourceStop(f"STOP_{item['tag']}_HTTP_{exc.code}") from exc
                except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                    raise SourceStop(f"STOP_{item['tag']}_NETWORK_{type(exc).__name__}") from exc
                row.update({
                    "downloaded_bytes": size,
                    "sha256": sha256.hexdigest(),
                    "actual_md5": md5.hexdigest(),
                    "md5_matches_publisher": md5.hexdigest() == item["expected_md5"],
                })
                if not row["md5_matches_publisher"]:
                    raise SourceStop("STOP_" + item["tag"] + "_MD5_MISMATCH")
                row["archive_manifest"] = _manifest(
                    path, item, protocol["max_header_files"], protocol["max_header_preview_bytes"]
                )
                row["status"] = "CHECKSUM_VERIFIED_ARCHIVE_MANIFEST_ONLY"
            result["status"] = "BOTH_ARCHIVES_CHECKSUM_VERIFIED_JOINABILITY_UNASSESSED"
    except SourceStop as exc:
        result["status"] = str(exc)
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    result["receipt_sha256_without_self_hash"] = hashlib.sha256(text.encode()).hexdigest()
    output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "gate_status": result["status"],
        "verified_archives": sum(x.get("md5_matches_publisher", False) for x in result["source_results"]),
        "receipt_path": str(output),
    }, sort_keys=True))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("validation/glanville_zenodo_dual_source_gate_v1/protocol_v1.json"))
    parser.add_argument("--output", type=Path, default=Path("results/glanville_zenodo_dual_source_gate_v1/receipt.json"))
    args = parser.parse_args()
    proto = json.loads(args.protocol.read_text(encoding="utf-8"))
    run_gate(proto, args.output)


if __name__ == "__main__":
    main()
