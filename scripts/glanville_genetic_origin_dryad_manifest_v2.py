#!/usr/bin/env python3
"""Version-pinned Dryad API file manifest qualification; no biological record access.

A second, separately frozen source-only gate after a successful DOI metadata
preflight. Reads only public version and file-list API JSON, never downloads
individual research file bytes or infers genetically reconstructed movement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class SourceStop(Exception):
    pass


def _api_url(href: str) -> str:
    if not isinstance(href, str) or not href.strip():
        raise SourceStop("STOP_FILE_MANIFEST_SCHEMA_BAD_LINK")
    url = ("https://datadryad.org" + href) if href.startswith("/api/v2/") else href
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname != "datadryad.org"
            or not parsed.path.startswith("/api/v2/")
            or parsed.username is not None or parsed.password is not None):
        raise SourceStop("STOP_UNAPPROVED_API_LINK")
    return url


def _get_json(url: str, byte_cap: int) -> tuple[dict, str]:
    safe = _api_url(url)
    request = Request(safe, headers={"Accept":"application/json",
                                    "User-Agent":"EOG-Dryad-public-manifest/1.0"})
    try:
        with urlopen(request, timeout=35) as response:
            final_url = _api_url(response.geturl())
            if urlparse(final_url).hostname != "datadryad.org":
                raise SourceStop("STOP_UNAPPROVED_API_REDIRECT")
            raw = response.read(byte_cap+1)
            if len(raw)>byte_cap:
                raise SourceStop("STOP_API_RESPONSE_OVER_BUDGET")
            obj = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(obj,dict):
                raise SourceStop("STOP_API_SCHEMA_NOT_OBJECT")
            return obj,hashlib.sha256(raw).hexdigest()
    except HTTPError as exc:
        raise SourceStop(f"STOP_HTTP_{exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise SourceStop("STOP_TRANSPORT_"+type(exc).__name__) from exc
    except (ValueError, UnicodeError) as exc:
        raise SourceStop("STOP_API_SCHEMA_PARSE_"+type(exc).__name__) from exc


def _version_candidates(result: dict) -> list[dict]:
    versions = (result.get("_embedded") or {}).get("stash:versions",[])
    if not isinstance(versions,list):
        raise SourceStop("STOP_VERSION_DATA_SCHEMA_NOT_LIST")
    result=[]
    for row in versions:
        if not isinstance(row,dict):
            raise SourceStop("STOP_VERSION_DATA_SCHEMA_NOT_OBJECT")
        links=row.get("_links") or {}
        href=(links.get("self") or {}).get("href","")
        match=re.fullmatch(r"/api/v2/versions/([1-9]\d*)",href)
        if not match:
            raise SourceStop("STOP_VERSION_DATA_SCHEMA_BAD_LINK")
        date=str(row.get("publicationDate") or row.get("publication_date") or "")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date):
            raise SourceStop("STOP_VERSION_DATA_SCHEMA_NO_PUBLISHED_DATE")
        number=row.get("versionNumber",0)
        if isinstance(number,bool) or not isinstance(number,int):
            raise SourceStop("STOP_VERSION_DATA_SCHEMA_BAD_NUMBER")
        result.append({
            "id":int(match.group(1)), "version_number":number,
            "published_date":date,
            "version_url":href,
            "files_href":((links.get("stash:files") or {}).get("href") or ""),
        })
    return result


def _manifest_page(result: dict, version_id: int) -> list[dict]:
    items=(result.get("_embedded") or {}).get("stash:files",[])
    if not isinstance(items,list):
        raise SourceStop("STOP_FILE_MANIFEST_SCHEMA_NOT_LIST")
    out=[]
    for item in items:
        if not isinstance(item,dict):
            raise SourceStop("STOP_FILE_MANIFEST_SCHEMA_BAD_OBJECT")
        path=str(item.get("path") or "")
        if not path or ".." in path.replace("\\","/").split("/") or path.startswith("/"):
            raise SourceStop("STOP_FILE_MANIFEST_SCHEMA_BAD_PATH")
        link=((item.get("_links") or {}).get("stash:version") or {}).get("href")
        if link and link != f"/api/v2/versions/{version_id}":
            raise SourceStop("STOP_VERSION_MISMATCH_IN_FILE_LINK")
        size=item.get("size",None)
        if isinstance(size,bool) or not isinstance(size,int) or size<0:
            raise SourceStop("STOP_FILE_MANIFEST_SCHEMA_BAD_SIZE")
        digest=str(item.get("digest") or "")
        alg=str(item.get("digestType") or "")
        out.append({"file_path":path,"size_bytes":size,
                    "digest":digest or None,
                    "digest_algorithm":alg or None,
                    "file_mime_type":str(item.get("mimeType") or "") or None})
    return out


def run(protocol: dict) -> dict:
    receipt={
        "schema_version":1, "status":"STOP_NOT_STARTED",
        "doi":protocol["base_doi"],
        "parent_source_preflight_fingerprint":protocol["parent_source_result_sha256_without_self_hash"],
        "version_id":None,"files":[],
        "biological_event_rows_read":0,
        "file_bytes_opened":0,"models_fit":0,"new_EOG_WF_endpoints":0,
        "genetically_inferred_source_direction_verified":False,
        "patch_year_join_verified":False,
    }
    try:
        if protocol["status"]!="frozen_before_dryad_version_file_listing":
            raise SourceStop("STOP_PROTOCOL_NOT_FROZEN")
        versions,sha=_get_json(protocol["version_list_url"],protocol["max_api_response_bytes"])
        receipt["versions_list_sha256"]=sha
        version_list=_version_candidates(versions)
        if not version_list:
            raise SourceStop("STOP_NO_PUBLIC_VERSIONS")
        if len(version_list) > 100 or protocol["max_version_list_pages"] != 1:
            raise SourceStop("STOP_VERSION_LIST_TOO_LONG_OR_POLICY_CHANGED")
        latest=max(version_list,key=lambda row:(row["published_date"],row["version_number"],row["id"]))
        version_id=latest["id"]
        receipt["version_id"]=version_id
        receipt["version_number"]=latest["version_number"]
        receipt["version_publication_date"]=latest["published_date"]
        href=latest["files_href"]
        if href!=f"/api/v2/versions/{version_id}/files":
            raise SourceStop("STOP_VERSION_FILES_LINK_NOT_PINNABLE")
        data=[]
        pages=[]
        url=_api_url(href)
        for page in range(1,protocol["max_file_manifest_pages"]+1):
            response,fingerprint=_get_json(url,protocol["max_api_response_bytes"])
            pages.append(fingerprint)
            data.extend(_manifest_page(response,version_id))
            if len(data)>protocol["max_file_entries"]:
                raise SourceStop("STOP_TOO_MANY_FILES")
            nex=((response.get("_links") or {}).get("next") or {}).get("href")
            if not nex:
                break
            next_url=_api_url(nex)
            if f"/versions/{version_id}/files" not in next_url:
                raise SourceStop("STOP_FILE_PAGINATION_VERSION_MISMATCH")
            if page==protocol["max_file_manifest_pages"]:
                raise SourceStop("STOP_FILE_MANIFEST_TRUNCATED")
            url=next_url
        if not data:
            raise SourceStop("STOP_NO_FILES")
        paths=[row["file_path"] for row in data]
        if len(paths)!=len(set(paths)):
            raise SourceStop("STOP_DUPLICATE_FILE_METADATA")
        receipt["files"]=sorted(data,key=lambda x:x["file_path"])
        receipt["file_count"]=len(data)
        receipt["file_listing_sha256_by_page"]=pages
        receipt["manifest_total_bytes"]=sum(item["size_bytes"] for item in data)
        keywords=("source","origin","assign","dispers","distance","move","family","dataset","data")
        receipt["filename_only_possible_event_table_names"]=[
            x for x in paths if x.lower().endswith((".csv",".tsv",".txt",".xlsx",".rdata",".rds",".zip"))
            and any(k in x.lower() for k in keywords)
        ]
        receipt["status"]="DRYAD_VERSION_PINNED_FILE_METADATA_ONLY_EVENT_JOIN_NOT_VERIFIED"
    except (SourceStop, KeyError, TypeError) as exc:
        receipt["status"]=str(exc) if isinstance(exc,SourceStop) else "STOP_VERSION_DATA_SCHEMA"
        receipt["stop_error_type"]=type(exc).__name__
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=Path("validation/glanville_genetic_origin_dryad_manifest_v2/protocol_v2.json"))
    parser.add_argument("--output",type=Path,default=Path("results/glanville_genetic_origin_dryad_manifest_v2/receipt.json"))
    args=parser.parse_args()
    p=json.loads(args.protocol.read_text(encoding="utf-8"))
    r=run(p)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    encoded=json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n"
    r["fingerprint_without_self_hash"]=hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":r["status"],"version_id":r.get("version_id"),
                      "files":r.get("file_count",0),"receipt":str(args.output)},sort_keys=True))


if __name__=="__main__":
    main()
