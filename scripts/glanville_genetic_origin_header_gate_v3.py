#!/usr/bin/env python3
"""SHA-pinned Dryad genetic-origin source headers: no biological row access.

The source-only contract was frozen BEFORE the 3 declared file downloads.
Only the README's term presence and two CSV's first header line are inspected;
a structurally possible source/destination/year join remains UNVALIDATED.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError


class SourceStop(Exception):
    pass


def _safe_url(url: str, download: bool=False) -> str:
    if url.startswith("/api/v2/"):
        url="https://datadryad.org"+url
    u=urlparse(url)
    allowed=r"/api/v2/files/[1-9]\d*/download" if download else r"/api/v2/versions/181375/files"
    if (u.scheme!="https" or u.hostname!="datadryad.org" or
        not re.fullmatch(allowed,u.path) or u.username or u.password):
        raise SourceStop("STOP_INVALID_DRYAD_FILE_API_LINK")
    return url


def _get_json(url: str,cap: int) -> tuple[dict,str]:
    req=Request(_safe_url(url),headers={"Accept":"application/json","User-Agent":"EOG-pinned-header-audit/1.0"})
    try:
        with urlopen(req,timeout=35) as response:
            if urlparse(response.geturl()).hostname!="datadryad.org":
                raise SourceStop("STOP_REDIRECTED_METADATA")
            raw=response.read(cap+1)
            if len(raw)>cap:
                raise SourceStop("STOP_METADATA_OVER_LIMIT")
            obj=json.loads(raw.decode("utf-8-sig"))
            if not isinstance(obj,dict):
                raise SourceStop("STOP_MANIFEST_NOT_OBJECT")
            return obj,hashlib.sha256(raw).hexdigest()
    except HTTPError as exc:
        raise SourceStop(f"STOP_HTTP_SOURCE_{exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise SourceStop("STOP_TRANSPORT_"+type(exc).__name__) from exc
    except (ValueError,UnicodeError) as exc:
        raise SourceStop("STOP_JSON_DECODE_"+type(exc).__name__) from exc


def _get_bytes(url: str,cap: int) -> bytes:
    request=Request(_safe_url(url,True),headers={"Accept":"*/*","User-Agent":"EOG-pinned-header-audit/1.0"})
    try:
        with urlopen(request,timeout=35) as response:
            # Dryad may redirect to a controlled object store. Verify HTTPS and
            # exact publisher digest before any inspection; never report URL.
            if urlparse(response.geturl()).scheme!="https":
                raise SourceStop("STOP_INSECURE_PUBLISHER_DOWNLOAD")
            payload=response.read(cap+1)
            if len(payload)>cap:
                raise SourceStop("STOP_FILE_OVER_BYTES_LIMIT")
            return payload
    except HTTPError as exc:
        raise SourceStop(f"STOP_HTTP_SOURCE_{exc.code}") from exc
    except (URLError,TimeoutError,OSError) as exc:
        raise SourceStop("STOP_TRANSPORT_"+type(exc).__name__) from exc


def _csv_header(data: bytes) -> list[str]:
    # At most the first two header lines; no individual event records parsed.
    buf=io.BytesIO(data)
    first=buf.readline(8192)
    if not first or len(first)==8192 and not first.endswith(b"\n"):
        raise SourceStop("STOP_CSV_SCHEMA_LONG_OR_MISSING_HEADER")
    if first.strip().lower().startswith(b"sep="):
        delim=first.strip()[4:].decode("ascii",errors="strict") or ","
        first=buf.readline(8192)
    else:
        delim=","
    if len(delim)!=1:
        raise SourceStop("STOP_CSV_SCHEMA_INVALID_SEPARATOR")
    try:
        line=first.decode("utf-8-sig")
        columns=next(csv.reader([line],delimiter=delim))
    except (UnicodeError, csv.Error, StopIteration,ValueError) as exc:
        raise SourceStop("STOP_CSV_SCHEMA_PARSE") from exc
    if not columns or len(columns)>300:
        raise SourceStop("STOP_CSV_SCHEMA_EMPTY_OR_TOO_WIDE")
    return [str(x).strip() for x in columns]


def _candidate_signals(columns: list[str]) -> dict:
    names=[re.sub("[^a-z0-9]","",x.lower()) for x in columns]
    source=any(any(tok in x for tok in ("source","origin","natal","birthpatch")) for x in names)
    destination=any(any(tok in x for tok in ("dest","settlement","arrival","samplepatch","observedpatch","collectedpatch")) for x in names)
    year=any(any(tok in x for tok in ("year","collectiondate","samplingdate")) for x in names)
    assignment=any(any(tok in x for tok in ("assign","geneclass","posterior","score","confidence")) for x in names)
    return {"possible_source_column":source,"possible_destination_column":destination,
            "possible_year_column":year,"possible_assignment_quality_column":assignment,
            "all_three_source_destination_year_column_cues":bool(source and destination and year)}


def run(protocol: dict) -> dict:
    output={
        "schema_version":1,"status":"STOP_NOT_STARTED",
        "dryad_version_id":protocol["target_version_id"],
        "parent_manifest_fingerprint":protocol["lineage"]["manifest_fingerprint"],
        "expected_publisher_sha256":{x["name"]:x["sha256"] for x in protocol["files"]},
        "files":[],
        "biological_event_rows_read":0,
        "genetic_events_scored":0,
        "models_fit":0,"new_EOG_WF_endpoints":0,
        "source_patch_join_verified":False,
        "true_movement_direction_identified":False,
    }
    try:
        if protocol.get("status")!="pre_download_exact_header_only_frozen":
            raise SourceStop("STOP_PROTOCOL_NOT_FROZEN")
        if protocol.get("target_version_id")!=181375 or protocol.get("file_downloads_max")!=3:
            raise SourceStop("STOP_VERSION_OR_SCOPE_CHANGED")
        manifest,manifest_sha=_get_json(protocol["file_metadata_api"],protocol["api_metadata_byte_cap"])
        output["source_manifest_sha256"]=manifest_sha
        entries=(manifest.get("_embedded") or {}).get("stash:files")
        if not isinstance(entries,list):
            raise SourceStop("STOP_MANIFEST_SCHEMA_FILES")
        by_path={}
        for row in entries:
            if not isinstance(row,dict):
                raise SourceStop("STOP_MANIFEST_SCHEMA_ROW")
            name=row.get("path")
            if name in by_path:
                raise SourceStop("STOP_MANIFEST_DUPLICATE_NAME")
            by_path[name]=row
        for item in protocol["files"]:
            name=item["name"]
            row=by_path.get(name)
            if row is None or row.get("size")!=item["size_bytes"] or row.get("digest")!=item["sha256"] or str(row.get("digestType","")).lower()!="sha-256":
                raise SourceStop("STOP_FILE_METADATA_MISMATCH_"+name)
            vlink=((row.get("_links") or {}).get("stash:version") or {}).get("href")
            if vlink and vlink!=f"/api/v2/versions/{protocol['target_version_id']}":
                raise SourceStop("STOP_MANIFEST_VERSION_CHANGED")
            href=((row.get("_links") or {}).get("stash:download") or {}).get("href")
            if not href:
                raise SourceStop("STOP_UNAVAILABLE_DRYAD_FILE_"+name)
            url=_safe_url(href,download=True)
            content=_get_bytes(url,protocol["data_transfer_byte_cap_each"])
            if len(content)!=item["size_bytes"]:
                raise SourceStop("STOP_FILE_BYTES_MISMATCH_"+name)
            digest=hashlib.sha256(content).hexdigest()
            if digest!=item["sha256"]:
                raise SourceStop("STOP_FILE_CHECKSUM_MISMATCH_"+name)
            if item["role"].startswith("first header"):
                headers=_csv_header(content)
                rowout={"name":name,"size_bytes":len(content),"sha256":digest,
                        "type":"csv_header_only","header_columns":headers,
                        "header_column_count":len(headers),
                        "column_name_signals":_candidate_signals(headers)}
            else:
                readme=content.decode("utf-8-sig",errors="replace").lower()
                words=("source","origin","destination","dispersal","year","patch",
                       "family","kinship","assignment","natal","genetic")
                rowout={"name":name,"size_bytes":len(content),"sha256":digest,
                        "type":"README_metadata_term_presence_only",
                        "term_presence":{word:word in readme for word in words}}
            output["files"].append(rowout)
        output["status"]="SOURCE_HEADERS_VERIFIED_EVENT_JOIN_NOT_VALIDATED"
    except (SourceStop,KeyError,TypeError,UnicodeError) as exc:
        output["status"]=str(exc) if isinstance(exc,SourceStop) else "STOP_SOURCE_SCHEMA_OR_RUNTIME"
        output["error_type"]=type(exc).__name__
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=Path("validation/glanville_genetic_origin_header_gate_v3/protocol_v3.json"))
    parser.add_argument("--output",type=Path,default=Path("results/glanville_genetic_origin_header_gate_v3/receipt.json"))
    args=parser.parse_args()
    proto=json.loads(args.protocol.read_text(encoding="utf-8"))
    out=run(proto)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    encoded=json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    out["fingerprint_without_self_hash"]=hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({"science_status":out["status"],"verified_files":len(out["files"]),
                      "receipt":str(args.output)},sort_keys=True))


if __name__=="__main__":
    main()
