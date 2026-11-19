#!/usr/bin/env python3
"""One-shot structural qualification of DiLeo 2022 genetic assignment evidence.

Publisher-linked Zenodo software and Dryad metadata ONLY; NO genetic event
rows, no historical movement claims, no occupancy fit and no EOG-WF endpoint.
A source that is not accessible is a source ACCESS STOP, not biological failure.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile


def _request(url: str, *, byte_cap: int) -> tuple[bytes, int]:
    if not url.startswith("https://"):
        raise ValueError("STOP_NON_HTTPS_SOURCE")
    original = urllib.parse.urlparse(url)
    if original.hostname not in ("zenodo.org", "datadryad.org"):
        raise ValueError("STOP_UNDECLARED_SOURCE_HOST")
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json, */*", "User-Agent": "EOG-source-only-publication-audit/1.0"},
    )
    with urllib.request.urlopen(req, timeout=35) as response:
        final = urllib.parse.urlparse(response.geturl())
        if final.hostname not in ("zenodo.org", "datadryad.org"):
            raise ValueError("STOP_REDIRECT_SOURCE_HOST_NOT_ALLOWED")
        content = response.read(byte_cap + 1)
        if len(content) > byte_cap:
            raise ValueError("STOP_SOURCE_SIZE_BUDGET")
        return content, int(getattr(response, "status", 200))


def _normalize_files(record: dict) -> list[dict]:
    files = record.get("files", [])
    if isinstance(files, dict):
        files = files.get("entries", files)
        if isinstance(files, dict):
            files = [dict(row, key=key) for key, row in files.items()]
    if not isinstance(files, list):
        raise ValueError("STOP_API_SCHEMA_FILES_NOT_LIST")
    normalized = []
    for row in files:
        name = str(row.get("key") or row.get("filename") or "").strip()
        if not name:
            continue
        size = int(row.get("size") or 0)
        checks = str(row.get("checksum") or "")
        links = row.get("links") or {}
        candidate = links.get("self") or links.get("content") or links.get("download") or ""
        if not candidate and row.get("download"):
            candidate = row["download"]
        normalized.append({"filename": name, "size":size, "checksum":checks, "_url":str(candidate)})
    return sorted(normalized,key=lambda x:x["filename"].lower())


def _candidate(files: list[dict], contract: dict) -> dict | None:
    maxsize = contract["max_candidate_bytes"]
    text_ext=(".csv",".tsv",".txt",".md")
    archive_ext=(".zip",".tar.gz")
    eligible=[f for f in files if 0<f["size"]<=maxsize and f["_url"]
              and f["filename"].lower().endswith(text_ext+archive_ext)]
    direct=[f for f in eligible if f["filename"].lower().endswith(text_ext)
            and any(t in f["filename"].lower() for t in ("source","dest","origin","dispers","data"))]
    if direct:
        return sorted(direct,key=lambda x:x["filename"].lower())[0]
    archives=[f for f in eligible if f["filename"].lower().endswith(archive_ext)]
    if archives:
        return sorted(archives,key=lambda x:(x["size"],x["filename"].lower()))[0]
    return None


def _verify_checksum(contents: bytes, expected: str) -> bool | None:
    if not expected:
        return None
    if ":" not in expected:
        return None
    algorithm, digest = expected.split(":", 1)
    if algorithm.lower() not in ("md5","sha256"):
        return None
    return hashlib.new(algorithm.lower(),contents).hexdigest().lower()==digest.lower()


def _safe_name(name: str) -> bool:
    path=name.replace("\\","/")
    return bool(path and not path.startswith("/") and ".." not in path.split("/"))


def _manifest(data: bytes, name: str, contract: dict) -> dict:
    hlim = contract["max_header_preview_bytes"]
    if name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members=[m for m in archive.infolist() if not m.is_dir()]
            if len(members)>contract["max_members"] or sum(m.file_size for m in members)>contract["max_uncompressed_archive_bytes"]:
                raise ValueError("STOP_ARCHIVE_BUDGET")
            if any(not _safe_name(m.filename) for m in members):
                raise ValueError("STOP_UNSAFE_ARCHIVE_MEMBERS")
            names=sorted(m.filename for m in members)
            return {"kind":"zip","member_count":len(names),"first_60_member_paths":names[:60]}
    if name.lower().endswith(".tar.gz"):
        with tarfile.open(fileobj=io.BytesIO(data),mode="r:gz") as archive:
            members=[m for m in archive.getmembers() if m.isfile()]
            if len(members)>contract["max_members"] or sum(m.size for m in members)>contract["max_uncompressed_archive_bytes"]:
                raise ValueError("STOP_ARCHIVE_BUDGET")
            if any(not _safe_name(m.name) for m in members):
                raise ValueError("STOP_UNSAFE_ARCHIVE_MEMBERS")
            names=sorted(m.name for m in members)
            return {"kind":"tar.gz","member_count":len(names),"first_60_member_paths":names[:60]}
    if name.lower().endswith((".csv",".tsv",".txt",".md")):
        # Header only. Never expose individual records from the source.
        first = data[:hlim].decode("utf-8-sig",errors="replace").splitlines()
        return {"kind":"text","first_line_header":first[0][:300] if first else ""}
    return {"kind":"unreadable_declared_source"}


def run(protocol: dict) -> dict:
    contract=protocol["source_contract"]
    result={
        "schema_version":1,
        "status":"STOP_UNSTARTED",
        "scientific_claim":"source metadata and file-grain qualification only; no event-level genetic validation",
        "zenodo_record_id":contract["record_id"],
        "dryad_doi":"10.5061/dryad.7h44j0zws",
        "source_results_opened":0,
        "biological_event_rows_read":0,
        "new_EOG_WF_endpoints":0,
        "models_fit":0,
        "zenodo":{"status":"NOT_CHECKED"},
        "dryad":{"status":"NOT_CHECKED"},
    }
    if protocol.get("status")!="pre_transport_metadata_only_frozen":
        result["status"]="STOP_PROTOCOL_NOT_FROZEN"
        return result
    for tag,url,limit in (
        ("zenodo",contract["zenodo_api"],contract["zenodo_max_metadata_bytes"]),
        ("dryad",contract["dryad_api"],contract["dryad_max_metadata_bytes"]),
    ):
        try:
            raw,status=_request(url,byte_cap=limit)
            source=json.loads(raw.decode("utf-8-sig"))
            if not isinstance(source,dict):
                raise ValueError("STOP_API_SCHEMA_NOT_OBJECT")
            result[tag]={"status":"METADATA_OK","http_status":status,
                         "metadata_sha256":hashlib.sha256(raw).hexdigest(),
                         "title":str(source.get("metadata",{}).get("title") or source.get("title") or "")[:160]}
            if tag=="zenodo":
                files=_normalize_files(source)
                if len(files)>contract["files_max"]:
                    raise ValueError("STOP_TOO_MANY_METADATA_FILES")
                result[tag]["files"]=[
                    {k:v for k,v in f.items() if not k.startswith("_")} for f in files
                ]
                chosen=_candidate(files,contract)
                result[tag]["candidate_file_name"]=chosen["filename"] if chosen else None
                if chosen:
                    try:
                        data,_=_request(chosen["_url"],byte_cap=contract["max_candidate_bytes"])
                        valid=_verify_checksum(data,chosen["checksum"])
                        result[tag]["candidate_checksum_matches_publisher"]=valid
                        result[tag]["candidate_sha256"]=hashlib.sha256(data).hexdigest()
                        if valid is False:
                            raise ValueError("STOP_SOURCE_CHECKSUM_MISMATCH")
                        result[tag]["candidate_structure"]=_manifest(data,chosen["filename"],contract)
                        result[tag]["status"]="METADATA_AND_ONE_FILE_MANIFEST_OK"
                    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,zipfile.BadZipFile,tarfile.TarError) as error:
                        result[tag]["file_gate_status"]=(
                            f"STOP_HTTP_{error.code}" if isinstance(error,urllib.error.HTTPError)
                            else str(error) if isinstance(error,ValueError) else f"STOP_{type(error).__name__}"
                        )
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,ValueError,KeyError,json.JSONDecodeError) as error:
            result[tag]={
                "status":f"STOP_HTTP_{error.code}" if isinstance(error,urllib.error.HTTPError)
                else str(error) if isinstance(error,ValueError) else f"STOP_{type(error).__name__}"
            }
    result["has_explicit_genetic_event_source_destination_year"]=False
    result["join_to_Glanville_patch_table_verified"]=False
    result["status"]=(
        "SOURCE_METADATA_PREFLIGHT_COMPLETED_EVENT_JOIN_NOT_VERIFIED"
        if result["zenodo"]["status"].startswith("METADATA")
        else "STOP_SOURCE_METADATA_UNAVAILABLE"
    )
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=Path("validation/glanville_genetic_origin_source_preflight_v1/protocol_v1.json"))
    p.add_argument("--output",type=Path,default=Path("results/glanville_genetic_origin_source_preflight_v1/receipt.json"))
    args=p.parse_args()
    proto=json.loads(args.protocol.read_text(encoding="utf-8"))
    result=run(proto)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    result["fingerprint_without_self_hash"]=hashlib.sha256(text.encode()).hexdigest()
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "zenodo_status":result["zenodo"]["status"],
        "dryad_status":result["dryad"]["status"],
        "receipt":str(args.output),
    },sort_keys=True))


if __name__=="__main__":
    main()
