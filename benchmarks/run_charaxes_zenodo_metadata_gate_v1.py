#!/usr/bin/env python3
"""Single-shot Zenodo public-record metadata gate; no ecology-file downloads.

A transport or schema failure produces a terminal STOP receipt, not an
adverse ecological result or permission to change the source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"validation/charaxes_zenodo_metadata_v1/protocol_v1.json"
PROTOCOL_COMMIT="81f360249b48d9ebff539367911dae0331b27225"


def digest(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def fetch_json_once(url):
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!="zenodo.org":
        raise ValueError("SOURCE_STOP_UNAUTHORIZED_HOST")
    req=Request(url,headers={"Accept":"application/json",
                              "User-Agent":"EOG-BAM-ZenodoMetadata/1"})
    with urlopen(req,timeout=35) as response:
        final=urlparse(response.geturl())
        if final.scheme!="https" or final.hostname!="zenodo.org":
            raise ValueError("SOURCE_STOP_REDIRECT_OUTSIDE_HOST")
        if response.status!=200:
            raise ValueError(f"SOURCE_STOP_HTTP_{response.status}")
        raw=response.read(1048577)
    if len(raw)>1048576:
        raise ValueError("SOURCE_STOP_METADATA_TOO_LARGE")
    try: result=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise ValueError("SOURCE_STOP_INVALID_JSON") from exc
    if not isinstance(result,dict):
        raise ValueError("SOURCE_STOP_JSON_NOT_OBJECT")
    return result


def parse_metadata(raw,protocol):
    if not isinstance(raw,dict) or raw.get("id")!=protocol["record_id"]:
        raise ValueError("SOURCE_STOP_RECORD_ID_MISMATCH")
    doi=raw.get("doi")
    if not doi and isinstance(raw.get("pids"),dict):
        doi=(raw["pids"].get("doi") or {}).get("identifier")
    if str(doi).lower()!=protocol["doi"]:
        raise ValueError("SOURCE_STOP_DOI_MISMATCH")
    files=raw.get("files")
    if isinstance(files,dict):
        entries=files.get("entries")
        if not isinstance(entries,dict):
            raise ValueError("SOURCE_STOP_NO_FILE_ENTRIES")
        items=list(entries.items())
    elif isinstance(files,list):
        items=[(str(x.get("key","")),x) for x in files]
    else:
        raise ValueError("SOURCE_STOP_UNSUPPORTED_FILE_SCHEMA")
    seen={}
    for key,entry in items:
        if not isinstance(entry,dict):
            raise ValueError("SOURCE_STOP_INVALID_FILE_METADATA")
        actual=str(entry.get("key") or key)
        if actual in seen:
            raise ValueError("SOURCE_STOP_DUPLICATE_FILE")
        size=entry.get("size")
        if isinstance(size,bool) or not isinstance(size,int):
            raise ValueError("SOURCE_STOP_INVALID_SIZE")
        seen[actual]={
            "name":actual,
            "size":size,
            "checksum":str(entry.get("checksum") or "").lower(),
            "links":entry.get("links",{}),
        }
    expected={r["name"]:r for r in protocol["public_metadata_context"]["expected_files"]}
    if set(seen)!=set(expected):
        raise ValueError("SOURCE_STOP_UNEXPECTED_FILE_ROSTER")
    recorded=[]
    for name in sorted(expected):
        row=seen[name]
        e=expected[name]
        lo,hi=e["size_range"]
        if not lo <= row["size"] <= hi:
            raise ValueError("SOURCE_STOP_FILE_SIZE_RANGE")
        if row["checksum"] not in ("md5:"+e["md5"],e["md5"]):
            raise ValueError("SOURCE_STOP_CHECKSUM_MISMATCH")
        links=row["links"]
        if not isinstance(links,dict):
            raise ValueError("SOURCE_STOP_FILE_LINKS_SCHEMA")
        links_out={}
        for key in ("self","content","download"):
            url=links.get(key)
            if url is not None:
                parsed=urlparse(str(url))
                if parsed.scheme!="https" or parsed.hostname!="zenodo.org":
                    raise ValueError("SOURCE_STOP_FILE_LINK_OUTSIDE_HOST")
                links_out[key]=str(url)
        recorded.append({
            "name":name,"size":row["size"],
            "checksum_md5":e["md5"],"validated_links":links_out
        })
    return {
        "record_id":raw["id"],
        "doi":protocol["doi"],
        "published":str((raw.get("metadata") or {}).get("publication_date") or ""),
        "files":recorded,
        "file_count":len(recorded)
    }


def evaluate(protocol, fetch=fetch_json_once):
    receipt={
        "schema":"eog.charaxes_zenodo_metadata_receipt.v1",
        "protocol_commit":PROTOCOL_COMMIT,
        "record_id":protocol["record_id"],
        "doi":protocol["doi"],
        "request_count":0,"data_files_opened":0,
        "biological_response_rows_opened":0,"ecological_scores":0,
        "file_metadata":None,
        "status":"NOT_RUN"
    }
    try:
        receipt["request_count"]=1
        metadata=fetch(protocol["official_url"])
        receipt["file_metadata"]=parse_metadata(metadata,protocol)
        receipt["status"]="SOURCE_METADATA_QUALIFIED_NO_RESPONSE_ROWS"
    except HTTPError as ex:
        receipt["status"]=f"SOURCE_STOP_HTTP_{ex.code}"
    except URLError:
        receipt["status"]="SOURCE_STOP_NETWORK_TRANSPORT"
    except (OSError,ValueError,TypeError,KeyError) as ex:
        receipt["status"]=(
            str(ex) if str(ex).startswith("SOURCE_STOP_")
            else "SOURCE_STOP_UNKNOWN_METADATA_ERROR"
        )
        receipt["error_type"]=type(ex).__name__
    receipt["fingerprint"]=digest(receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    raw=PROTOCOL.read_bytes()
    p=json.loads(raw)
    if p.get("schema")!="eog.charaxes_zenodo_metadata_gate.v1":
        raise ValueError("unexpected protocol version")
    r=evaluate(p)
    r["protocol_sha256"]=hashlib.sha256(raw).hexdigest()
    r["fingerprint"]=digest({k:v for k,v in r.items() if k!="fingerprint"})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("CHARAXES_SOURCE_GATE="+json.dumps({
        "status":r["status"],"files_verified":len((r["file_metadata"] or {}).get("files",[])),
        "request_count":r["request_count"],
        "response_rows_opened":r["biological_response_rows_opened"],
        "fingerprint":r["fingerprint"]
    },sort_keys=True))


if __name__=="__main__":
    main()
