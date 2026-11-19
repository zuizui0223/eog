"""Fetch source CSVs only when their bytes match frozen Dryad file metadata.

May inspect only headers in the output. No species counts or treatment outcomes are
summarized. Do not call this a completed study or an EOG-WF endpoint.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

DOI = "10.5061/dryad.8vs569h"
DATASET_API = "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.8vs569h"
ZENODO_API = "https://zenodo.org/api/records/5023851"
EXPECTED = {
    "composition-data.csv": ("5d9455e9ec281ca351db250340f3a1e5", 1510812),
    "env-param-Y0.csv": ("663fe1ce5ce18ffb27462e99c0e3d2a6", 47604),
}
MAX_BYTES = 3_000_000
ALLOWED_HOSTS = {"datadryad.org", "zenodo.org"}
UA = {"User-Agent": "EOG-original-source-byte-gate/1.0",
      "Accept": "application/octet-stream,application/json"}

def request_bytes(url: str, *, limit: int = MAX_BYTES) -> tuple[bytes | None, str]:
    """Strictly bounded public GET of fixed provider URLs; do not print response."""
    u = urlparse(url)
    if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
        return None, "STOP_BAD_URL_HOST"
    try:
        with urlopen(Request(url, headers=UA), timeout=25) as response:
            if response.geturl() and urlparse(response.geturl()).scheme != "https":
                return None, "STOP_INSECURE_REDIRECT"
            blob = response.read(limit+1)
            if len(blob) > limit:
                return None, "STOP_SIZE_LIMIT"
            return blob, "HTTP_200"
    except HTTPError as e:
        return None, "HTTP_" + str(e.code)
    except (URLError, TimeoutError, OSError, ValueError) as e:
        return None, "ACCESS_STOP_" + type(e).__name__

def get_json(url, request_fn=request_bytes):
    data, status = request_fn(url)
    if data is None:
        return None, status
    try:
        value = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError):
        return None, "STOP_NOT_JSON"
    return (value, status) if isinstance(value, dict) else (None, "STOP_JSON_NOT_OBJECT")

def dryad_files(request_fn=request_bytes):
    meta, status = get_json(DATASET_API, request_fn)
    events = [{"endpoint": "Dryad dataset metadata", "status": status}]
    if meta is None:
        return {}, events
    vers = meta.get("_links",{}).get("stash:version",{}).get("href","")
    if not isinstance(vers, str) or not re.fullmatch(r"/api/v2/versions/\d+", vers):
        return {}, events+[{"endpoint":"Dryad version","status":"STOP_UNEXPECTED_VERSION_LINK"}]
    listing, status = get_json(urljoin("https://datadryad.org", vers+"/files"),request_fn)
    events.append({"endpoint":"Dryad version file listing","status":status})
    if listing is None:
        return {}, events
    entries = listing.get("_embedded", {}).get("stash:files", [])
    if not isinstance(entries,list):
        return {}, events+[{"endpoint":"Dryad file entries","status":"STOP_NO_EMBEDDED_FILES"}]
    files={}
    for f in entries:
        if not isinstance(f, dict):
            continue
        name = f.get("path",f.get("filename"))
        fid = f.get("id")
        if name in EXPECTED and isinstance(fid,int) and fid > 0:
            files[name] = "https://datadryad.org/api/v2/files/"+str(fid)+"/download"
    return files, events

def zenodo_files(request_fn=request_bytes):
    meta,status=get_json(ZENODO_API,request_fn)
    events=[{"endpoint":"Zenodo candidate mirror metadata","status":status}]
    if meta is None:
        return {},events
    entries=meta.get("files",[])
    result={}
    for f in entries if isinstance(entries,list) else []:
        if not isinstance(f,dict):continue
        name=f.get("key", f.get("filename"))
        url=f.get("links",{}).get("self","")
        if name in EXPECTED and isinstance(url,str):
            u=urlparse(url)
            if u.scheme=="https" and u.hostname=="zenodo.org":
                result[name]=url
    return result,events

def digest_verified(name: str, raw: bytes):
    expected_md5,expected_size=EXPECTED[name]
    md5=hashlib.md5(raw,usedforsecurity=False).hexdigest()
    sha256=hashlib.sha256(raw).hexdigest()
    valid=len(raw)==expected_size and md5==expected_md5
    return valid,{"size":len(raw),"md5":md5,"sha256":sha256,
                  "expected_size":expected_size,"source_md5_match":md5==expected_md5,
                  "source_size_match":len(raw)==expected_size}

def safe_header(raw: bytes):
    try:
        text=raw.decode("utf-8-sig")
        header=next(csv.reader(io.StringIO(text),strict=True))
    except (UnicodeError,ValueError,StopIteration,csv.Error):
        return None
    if len(header)<5 or len(header)>1000 or any(not isinstance(x,str) or not x.strip() for x in header):
        return None
    return header

def run(directory:Path, request_fn=request_bytes):
    directory.mkdir(parents=True,exist_ok=True)
    provider_files,events=dryad_files(request_fn)
    secondary_files,mirror_events=zenodo_files(request_fn)
    events.extend(mirror_events)
    checked={}
    complete=True
    for name in EXPECTED:
        accepted=None
        attempts=[]
        candidates=(("Dryad",provider_files.get(name)),("Zenodo mirror",secondary_files.get(name)))
        for provider,url in candidates:
            if not url: continue
            raw,status=request_fn(url)
            attempts.append({"source":provider,"status":status})
            if raw is None: continue
            valid,info=digest_verified(name,raw)
            attempts[-1]["byte_integrity"]=info
            if valid:
                header=safe_header(raw)
                if header is None:
                    attempts[-1]["status"]="STOP_INVALID_CSV_HEADER"
                    continue
                accepted={"source":provider,"header":header,**info}
                (directory / name).write_bytes(raw)
                break
        checked[name]={"accepted":accepted,"attempts":attempts}
        if accepted is None:complete=False
    out={"schema":"eog.nutnet_hodapp_source_byte_gate.result.v1",
         "status":"BYTES_VERIFIED_SCHEMA_NOT_SCORED" if complete else "SOURCE_BYTE_STOP",
         "source_doi":DOI, "source_files":checked,"metadata_events":events,
         "number_post_treatment_responses_scored":0,
         "note":"This report inspected only source-file integrity and headers; it did not fit any response model or count any taxon."}
    (directory/"source_gate_result.json").write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    r=run(a.output_dir)
    print(json.dumps({"status":r["status"],"source_files":{k:v["accepted"] is not None for k,v in r["source_files"].items()},
                      "metadata_events":r["metadata_events"]},indent=2))

if __name__=="__main__":
    main()
