"""Exact-source Dryad seed-sowing gate: read file headers only, never score outcomes.

The protocol was committed first to validation/mediterranean_sowing_constraint_witness_v1/protocol.json.
Fetch official Dryad metadata, verify each original file size and SHA256/MD5
digest, and record only headers and integrity. No biological rows are parsed.
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

API = "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.t1g1jwtg3"
BASE = "https://datadryad.org"
REQUIRED = (
    "sowing_experiment.csv", "soil_physicochemical.csv",
    "soil_moisture_vwc_values.csv", "planting_experiment.csv", "README.md",
)
MAX_FILE = 12_000_000
MAX_META = 1_000_000
UA = {"User-Agent":"EOG-forest-sowing-source-integrity-gate/1.0",
      "Accept":"application/json,application/octet-stream"}

def get_bytes(url: str, limit: int) -> tuple[bytes | None, str]:
    u=urlparse(url)
    if u.scheme!="https" or u.hostname!="datadryad.org":
        return None,"STOP_UNAPPROVED_URL"
    try:
        with urlopen(Request(url, headers=UA), timeout=40) as f:
            # Final location may be an HTTPS signed object-store URL.
            final=urlparse(f.geturl())
            if final.scheme!="https":return None,"STOP_INSECURE_REDIRECT"
            content=f.read(limit+1)
            if len(content)>limit:return None,"STOP_OVERSIZE"
            return content,"HTTP_200"
    except HTTPError as e:return None,"HTTP_"+str(e.code)
    except (URLError,TimeoutError,OSError,ValueError) as e:
        return None,"ACCESS_STOP_"+type(e).__name__

def get_json(url,fetch=get_bytes):
    raw,status=fetch(url,MAX_META)
    if raw is None:return None,status
    try:
        payload=json.loads(raw.decode("utf-8"))
        if not isinstance(payload,dict):return None,"STOP_JSON_NOT_DICT"
        return payload,status
    except (ValueError, UnicodeError):return None,"STOP_NOT_JSON"

def allowed_meta_url(path: str) -> str | None:
    if not isinstance(path,str):return None
    url=urljoin(BASE,path)
    parsed=urlparse(url)
    if parsed.scheme=="https" and parsed.hostname=="datadryad.org" and parsed.path.startswith("/api/v2/"):
        return url
    return None

def file_manifest(meta,fetch=get_bytes):
    events=[]
    if meta is None:return {},events
    vers=meta.get("_links",{}).get("stash:version",{}).get("href")
    ver_url=allowed_meta_url(vers)
    if not ver_url:return {},[{"endpoint":"version","status":"STOP_INVALID_VERSION_URL"}]
    page_url=ver_url.rstrip("/")+"/files"
    files={}
    for i in range(8):
        data,status=get_json(page_url,fetch)
        events.append({"endpoint":"files_page_"+str(i+1),"status":status})
        if data is None:return files,events
        embedded=data.get("_embedded",{})
        ents=embedded.get("stash:files",[])
        if not isinstance(ents,list):return files,events+[{"endpoint":"files","status":"STOP_BAD_FILE_LIST"}]
        # Diagnostic metadata only: never inspect CSV rows. Archive provider field
        # keys/names so a SOURCE_STOP can be traced to schema or filename drift.
        events.append({
            "endpoint":"files_manifest_shape_"+str(i+1),
            "count":len(ents),
            "embedded_keys":sorted(embedded.keys()),
            "sample_keys":sorted(ents[0].keys()) if ents and isinstance(ents[0],dict) else [],
            "candidate_names":[{k:str(f.get(k,""))[:180] for k in ("path","filename","name","basename") if k in f}
                               for f in ents[:30] if isinstance(f,dict)],
        })
        for f in ents:
            if not isinstance(f,dict):continue
            candidates=set()
            for name_key in ("filename","path","name","key"):
                field=f.get(name_key)
                if isinstance(field,str):
                    leaf=field.rstrip("/").rsplit("/",1)[-1]
                    if leaf in REQUIRED:candidates.add(leaf)
            # A provider's path may hold a directory while filename holds the
            # actual leaf. Accept only a single unambiguous whitelisted name.
            if len(candidates)!=1:continue
            name=next(iter(candidates))
            id_=f.get("id")
            if not isinstance(id_,int) or id_<=0:
                # Dryad v2 embedded file rows often expose the file identity
                # in _links.self.href rather than as a top-level numeric id.
                # Only accept an exact official /api/v2/files/N identity.
                links=f.get("_links",{})
                if isinstance(links,dict):
                    for node in links.values():
                        href=node.get("href","") if isinstance(node,dict) else ""
                        official=allowed_meta_url(href)
                        if official:
                            match=re.fullmatch(r"/api/v2/files/(\d+)(?:/download)?",urlparse(official).path)
                            if match:
                                id_=int(match.group(1))
                                break
            digest=f.get("digest")
            algo=f.get("digestType","")
            size=f.get("size")
            if not isinstance(digest,str) or not isinstance(algo,str) or not isinstance(size,int) or not isinstance(id_,int):
                files[name]={"status":"STOP_INCOMPLETE_FILE_METADATA"};continue
            typ=algo.lower().replace("_","-")
            if typ in ("sha256","sha-256"):kind="sha256";needed=64
            elif typ in ("md5",):kind="md5";needed=32
            else:
                files[name]={"status":"STOP_UNSUPPORTED_DIGEST"};continue
            if size<1 or size>MAX_FILE or not re.fullmatch("[0-9a-fA-F]{"+str(needed)+"}",digest):
                files[name]={"status":"STOP_INVALID_DIGEST_OR_SIZE"};continue
            files[name]={"status":"MANIFEST_OK","size":size,"digest":digest.lower(),
                         "digest_type":kind,"id":id_,
                         "download_url":BASE+"/api/v2/files/"+str(id_)+"/download"}
        nex=data.get("_links",{}).get("next",{}).get("href")
        if not nex:break
        next_url=allowed_meta_url(nex)
        if not next_url or next_url==page_url:
            events.append({"endpoint":"pagination","status":"STOP_INVALID_NEXT"});break
        page_url=next_url
    return files,events

def verified_file(name:str,item:dict,fetch=get_bytes):
    if item.get("status")!="MANIFEST_OK":
        return None,{"status":"STOP_MISSING_MANIFEST"}
    raw,status=fetch(item["download_url"],item["size"])
    if raw is None:return None,{"status":status}
    if len(raw)!=item["size"]:return None,{"status":"STOP_SIZE_MISMATCH","observed_size":len(raw)}
    md5=hashlib.md5(raw,usedforsecurity=False).hexdigest()
    sha256=hashlib.sha256(raw).hexdigest()
    actual={"md5":md5,"sha256":sha256}[item["digest_type"]]
    if actual!=item["digest"]:
        return None,{"status":"STOP_DIGEST_MISMATCH"}
    if name.endswith(".csv"):
        try:header=next(csv.reader(io.StringIO(raw.decode("utf-8-sig")),strict=True))
        except (UnicodeError,csv.Error,StopIteration):return None,{"status":"STOP_BAD_CSV_HEADER"}
        if not 2<=len(header)<=80:return None,{"status":"STOP_BAD_CSV_COLUMN_COUNT"}
    else:
        header=None
    return raw,{"status":"VERIFIED","size":len(raw),"sha256":sha256,"md5":md5,
                "digest_type":item["digest_type"],"file_id":item["id"],
                "csv_header":header}

def run(directory:Path,fetch=get_bytes):
    directory.mkdir(parents=True,exist_ok=True)
    meta,status=get_json(API,fetch)
    events=[{"endpoint":"dataset","status":status}]
    manifest,more=file_manifest(meta,fetch);events.extend(more)
    results={}
    all_ok=True
    for name in REQUIRED:
        item=manifest.get(name,{"status":"STOP_NOT_LISTED"})
        raw,result=verified_file(name,item,fetch)
        results[name]=result
        if raw is None: all_ok=False
        else: (directory/name).write_bytes(raw)
    receipt={
        "schema":"eog.mediterranean_sowing_constraint_witness.source_gate.v1",
        "source_doi":"10.5061/dryad.t1g1jwtg3",
        "status":"SOURCE_BYTES_VERIFIED_NOT_SCORED" if all_ok else "SOURCE_STOP",
        "metadata_events":events,"source_files":results,
        "biological_outcome_values_read":False,
        "number_response_effects_scored":0,
        "limits":"Headers and exact bytes only. No germination/establishment outcome rows opened and no BAM causal mechanism identified."
    }
    (directory/"source_gate.json").write_text(json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n")
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    r=run(a.output_dir)
    print(json.dumps({"status":r["status"],"file_statuses":{k:v["status"] for k,v in r["source_files"].items()}},indent=2))
    # STOP is scientific outcome of source gate; CI itself should archive the receipt.
if __name__=="__main__":main()
