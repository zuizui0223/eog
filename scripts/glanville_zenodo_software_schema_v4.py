#!/usr/bin/env python3
"""Publisher-MD5-pinned Zenodo R script static schema hints, no data or R execution.

A separate source-only route after Dryad file API returned 401. Only
filename-like string literals and identifier tokens are exported, no raw R
code, study records, inferred movement, or historical source claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError


class SourceStop(Exception):
    pass


def _safe_source(url: str) -> str:
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!="zenodo.org" or not (
        parsed.path.startswith("/api/") or parsed.path.startswith("/records/")
    ):
        raise SourceStop("STOP_UNAPPROVED_ZENODO_FILE_LINK")
    return url


def _get(url: str, *, limit: int) -> bytes:
    target=_safe_source(url)
    req=Request(target,headers={"Accept":"*/*","User-Agent":"EOG-static-software-source-audit/1.0"})
    try:
        with urlopen(req,timeout=35) as r:
            if urlparse(r.geturl()).scheme!="https":
                raise SourceStop("STOP_INSECURE_SOURCE_REDIRECT")
            payload=r.read(limit+1)
            if len(payload)>limit:
                raise SourceStop("STOP_SOURCE_SIZE_BUDGET")
            return payload
    except HTTPError as exc:
        raise SourceStop(f"STOP_SOURCE_HTTP_{exc.code}") from exc
    except (URLError,TimeoutError,OSError) as exc:
        raise SourceStop("STOP_SOURCE_TRANSPORT_"+type(exc).__name__) from exc


def _files(record: dict) -> list[dict]:
    files=record.get("files")
    if isinstance(files,dict):
        entries=files.get("entries")
        if not isinstance(entries,dict):
            raise SourceStop("STOP_ZENODO_FILES_SCHEMA")
        files=[dict({"key":name},**val) for name,val in entries.items()]
    if not isinstance(files,list):
        raise SourceStop("STOP_ZENODO_FILES_SCHEMA")
    return files


def _extract_static_symbols(script: str, policy: dict) -> dict:
    # Do not preserve raw code or literals containing personal home directories.
    quoted=re.findall(
        r"(?<![A-Za-z0-9_])[\x22\x27]([^\x22\x27\r\n]+\.(?:csv|tsv|rds|rdata|txt|xlsx))[\x22\x27]",
        script,re.IGNORECASE
    )
    filenames=sorted(set(
        x.replace("\\","/").split("/")[-1].strip()
        for x in quoted
        if 0<len(x)<=260
    ))
    candidates=sorted(set(
        x for x in re.findall(r"\b[A-Za-z][A-Za-z0-9._]*\b",script)
        if any(k in x.lower() for k in policy["identifier_tokens"])
        and len(x)<=100
    ))
    return {
        "script_line_count":len(script.splitlines()),
        "distinct_input_filename_like_literals":filenames[:policy["out_max_input_names"]],
        "distinct_identifier_hints":candidates[:policy["out_max_identifiers"]],
        "identifier_total_matches_before_cap":len(candidates),
        "input_filename_total_matches_before_cap":len(filenames),
        "source_destination_year_symbol_cues":{
            "source_or_origin":any(any(k in x.lower() for k in ("source","origin","natal","birth")) for x in candidates),
            "destination_or_sample":any(any(k in x.lower() for k in ("dest","arrival","settle","sample")) for x in candidates),
            "year":any("year" in x.lower() for x in candidates),
            "assignment":any(any(k in x.lower() for k in ("assign","geneclass")) for x in candidates),
        }
    }


def run(proto: dict) -> dict:
    result={
        "schema_version":1,
        "status":"STOP_UNSTARTED",
        "record_id":proto["zenodo_record_id"],
        "expected_publisher_md5":proto["source_md5"],
        "dryad_file_access_stop":proto["dryad_source_stop"],
        "script_executed":False,
        "genetic_event_data_rows_read":0,
        "source_destination_year_events_verified":False,
        "ecological_models_fit":0,
        "new_EOG_WF_endpoints":0,
    }
    try:
        if proto["status"]!="pre_fetch_single_publisher_software_frozen":
            raise SourceStop("STOP_PROTOCOL_NOT_FROZEN")
        meta=_get(proto["zenodo_api"],limit=proto["network"]["api_max_bytes"])
        obj=json.loads(meta.decode("utf-8-sig"))
        if not isinstance(obj,dict):
            raise SourceStop("STOP_ZENODO_METADATA_SCHEMA")
        result["metadata_sha256"]=hashlib.sha256(meta).hexdigest()
        matching=[x for x in _files(obj) if (x.get("key") or x.get("filename"))==proto["source_filename"]]
        if len(matching)!=1:
            raise SourceStop("STOP_ZENODO_FILE_MISSING_OR_AMBIGUOUS")
        file=matching[0]
        if file.get("size")!=proto["source_file_bytes"] or str(file.get("checksum") or "")!="md5:"+proto["source_md5"]:
            raise SourceStop("STOP_ZENODO_FILE_METADATA_CHANGED")
        links=file.get("links") or {}
        url=links.get("self") or links.get("content") or links.get("download")
        if not url:
            raise SourceStop("STOP_ZENODO_FILE_LINK_MISSING")
        payload=_get(str(url),limit=proto["network"]["source_max_bytes"])
        if len(payload)!=proto["source_file_bytes"] or hashlib.md5(payload).hexdigest()!=proto["source_md5"]:
            raise SourceStop("STOP_ZENODO_SCRIPT_MD5_MISMATCH")
        result["script_sha256"]=hashlib.sha256(payload).hexdigest()
        text=payload.decode("utf-8-sig")
        result["static_token_metadata"]=_extract_static_symbols(text,proto["static_only"])
        result["status"]="SOFTWARE_STATIC_IDENTIFIERS_QUALIFIED_EVENT_DATA_UNVERIFIED"
    except (SourceStop,KeyError,ValueError,UnicodeError,TypeError) as exc:
        result["status"]=str(exc) if isinstance(exc,SourceStop) else "STOP_SOURCE_SCHEMA_OR_RUNTIME"
        result["error_type"]=type(exc).__name__
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=Path("validation/glanville_zenodo_software_schema_v4/protocol_v4.json"))
    p.add_argument("--output",type=Path,default=Path("results/glanville_zenodo_software_schema_v4/receipt.json"))
    args=p.parse_args()
    policy=json.loads(args.protocol.read_text(encoding="utf-8"))
    receipt=run(policy)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n"
    receipt["fingerprint_without_self_hash"]=hashlib.sha256(raw.encode()).hexdigest()
    args.output.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({"status":receipt["status"],
                      "input_filename_hints":len(receipt.get("static_token_metadata",{}).get("distinct_input_filename_like_literals",[])),
                      "receipt":str(args.output)},sort_keys=True))


if __name__=="__main__":
    main()
