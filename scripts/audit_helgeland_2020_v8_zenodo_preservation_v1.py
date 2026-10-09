#!/usr/bin/env python3
"""Find legitimate Zenodo Dryad preservation COPY and verify ORIGINAL 2020-v8 SHA256.

Safety and epistemic contract:
- Search only public Zenodo records; read JSON metadata, not unknown datasets.
- Fetch only EXACT three pre-2021 published named files, max 4137 bytes each.
- Require that candidate metadata identifies Niskanen's exact study.
- Calculate SHA256 on full downloaded opaque bytes against frozen 2020-v8 values.
- No island/year/individual/biology rows decoded, emitted, stored or scored.
- A preservation record from 2023 can be an original-2020 content replica only
  when the actual file's SHA256 equals the ORIGINAL 2020-v8 published digest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json"
DOI="10.5061/dryad.m0cfxpp10"
V8_ID=78498
EXPECTED_TITLE="Consistent scaling of inbreeding depression in space and time in a house sparrow metapopulation"
ZENODO="https://zenodo.org"
QUERIES=(DOI,EXPECTED_TITLE)
MAX_METADATA=2_000_000


def public_json(url: str) -> dict:
    p=urllib.parse.urlparse(url)
    if (p.scheme!="https" or p.hostname!="zenodo.org" or p.port not in (None,443)
        or p.fragment or not p.path.startswith("/api/records")):
        raise ValueError("Refusing non-Zenodo public JSON API address")
    request=urllib.request.Request(url,headers={
        "Accept":"application/json","User-Agent":"EOG-2020-original-public-zenodo-mirror/1.0"})
    with urllib.request.urlopen(request,timeout=30) as stream:
        data=stream.read(MAX_METADATA+1)
    if len(data)>MAX_METADATA:
        raise ValueError("Public metadata response too large")
    obj=json.loads(data)
    if not isinstance(obj,dict):
        raise ValueError("Invalid public record JSON schema")
    return obj


def _title(rec:dict)->str:
    return " ".join(str(rec.get("metadata",{}).get("title","")).split()).casefold()


def matching_record(rec:dict)->bool:
    meta=rec.get("metadata",{})
    if not isinstance(meta,dict):
        return False
    if EXPECTED_TITLE.casefold() not in _title(rec):
        return False
    metadata_text=json.dumps(meta,ensure_ascii=False).casefold()
    creators=meta.get("creators") or []
    author_text=" ".join(str(p.get("name","")) for p in creators if isinstance(p,dict)).casefold()
    return ("niskanen" in author_text and
            (DOI.casefold() in metadata_text or "dryad" in metadata_text))


def candidates(fetch=public_json)->list[dict]:
    found={}
    for query in QUERIES:
        url=ZENODO+"/api/records?"+urllib.parse.urlencode({"q":query,"size":"25"})
        raw=fetch(url)
        hits=raw.get("hits",{}).get("hits",[])
        if not isinstance(hits,list):
            raise ValueError("Zenodo metadata search response unexpected")
        for rec in hits:
            if not isinstance(rec,dict) or not matching_record(rec):
                continue
            rid=rec.get("id")
            if not isinstance(rid,int) or rid<=0:
                continue
            found[rid]=rec
    return list(found.values())


def pinned_files(frozen:dict)->dict[str,dict]:
    if frozen.get("schema")!="eog.helgeland.historical_public_dryad_versions.frozen_observed_v1":
        raise ValueError("Historical frozen source evidence missing")
    hist=frozen["archives"]["niskanen_2020"]
    if (hist["doi"]!=DOI or hist["version_id"]!=V8_ID or
        hist["published_date"]!="2020-08-19" or hist["version_number"]!=8):
        raise ValueError("Original 2020 v8 public source identity mismatch")
    records={i["name"]:i for i in hist["critical_files"]}
    if set(records)!={"Dryad_readme.txt","Pop_size_1997_2012.csv","Pop_size_1998_2013.csv"}:
        raise ValueError("Wrong pre-2021 source file allowlist")
    return records


def zenodo_file_entries(rec:dict)->dict[str,dict]:
    files=rec.get("files")
    if isinstance(files,dict):
        items=files.get("entries",{})
        if not isinstance(items,dict):
            raise ValueError("Zenodo file entries unreadable")
        result=[dict(v, key=k) for k,v in items.items() if isinstance(v,dict)]
    elif isinstance(files,list):
        result=files
    else:
        return {}
    output={}
    for item in result:
        key=item.get("key") or item.get("filename")
        if not isinstance(key,str) or key in output:
            raise ValueError("Missing or duplicate Zenodo file name")
        output[key]=item
    return output


def _file_link(item:dict)->str:
    links=item.get("links",{})
    if not isinstance(links,dict):
        raise ValueError("Missing Zenodo content URL")
    uri=links.get("content") or links.get("self")
    if not isinstance(uri,str):
        raise ValueError("No exact Zenodo file link")
    parsed=urllib.parse.urlparse(uri)
    if (parsed.scheme!="https" or parsed.hostname!="zenodo.org" or
        parsed.port not in (None,443) or parsed.fragment or
        not parsed.path.startswith("/api/records/")):
        raise ValueError("Refusing unexpected Zenodo content URL")
    return uri


def stream_hash(uri:str,maximum:int)->tuple[str,int]:
    if maximum<=0 or maximum>5_000:
        raise ValueError("Refusing oversized or zero-length source file")
    request=urllib.request.Request(uri,headers={"User-Agent":"EOG-2020-v8-source-parity/1.0"})
    hash_=hashlib.sha256()
    total=0
    with urllib.request.urlopen(request,timeout=40) as response:
        end=urllib.parse.urlparse(response.geturl())
        if end.scheme!="https" or not end.hostname or end.port not in (None,443):
            raise ValueError("Non-HTTPS response redirect")
        for chunk in iter(lambda:response.read(8192),b""):
            total+=len(chunk)
            if total>maximum:
                raise ValueError("Byte content exceeds registered original source size")
            hash_.update(chunk)
    return hash_.hexdigest(),total


def compare(rec:dict, originals:dict, get_bytes=stream_hash)->dict:
    if not matching_record(rec):
        raise ValueError("Zenodo record is not this Dryad research dataset")
    source_files=zenodo_file_entries(rec)
    if not all(name in source_files for name in originals):
        raise ValueError("Preservation record lacks the 3 pre-2021 files")
    matches=[]
    for name in sorted(originals):
        old=originals[name]
        obj=source_files[name]
        if obj.get("size")!=old["size_bytes"]:
            raise ValueError(name+": size is not the original 2020-v8 byte size")
        uri=_file_link(obj)
        sha,size=get_bytes(uri,old["size_bytes"])
        if size!=old["size_bytes"] or sha.lower()!=old["source_digest"].lower():
            raise ValueError(name+": Zenodo actual SHA256 does not match original 2020 v8")
        matches.append({
            "file_name":name,"2020_v8_file_id":old["file_id"],
            "source_original_v8_sha256_matches_actual_zenodo_bytes":True,
            "original_2020_v8_size_bytes":size,
            "biological_rows_parsed":False,
        })
    return {
        "schema":"eog.helgeland.2020v8_zenodo_preservation_byte_parity.v1",
        "status":"THREE_ZENODO_PRESERVATION_FILES_FULL_HASH_MATCH_ORIGINAL_2020_V8",
        "source_doi":DOI,
        "original_version_id":V8_ID,
        "preservation_zenodo_record_id":rec["id"],
        "files":matches,
        "original_published_date":"2020-08-19",
        "historical_source_byte_identity_qualified":True,
        "zenodo_only_newer_files_authorized_for_2020":False,
        "file_contents_emitted":False,
        "rows_decoded_or_scored":False,
        "island_year_surveyed_zero_verified":False,
        "island_numeric_code_crosswalk_verified":False,
        "ecological_forecast_authorized":False,
    }


def audit(frozen:dict,lookup=candidates,get_bytes=stream_hash)->dict:
    originals=pinned_files(frozen)
    try:
        source_recs=lookup()
    except (urllib.error.URLError,TimeoutError,ValueError,TypeError,json.JSONDecodeError) as exc:
        return {"status":"HOLD_ZENODO_SOURCE_SEARCH_UNAVAILABLE","reason":type(exc).__name__,
                "biological_rows_read":False,"ecological_forecast_authorized":False}
    if not source_recs:
        return {"status":"HOLD_NO_MATCHING_ZENODO_SOURCE_RECORD","records_considered":0,
                "biological_rows_read":False,"ecological_forecast_authorized":False}
    outcomes=[]
    for rec in source_recs:
        try:
            return compare(rec,originals,get_bytes)
        except (urllib.error.URLError,TimeoutError,ValueError,TypeError) as exc:
            outcomes.append({"record_id":rec["id"],"reason":type(exc).__name__,
                             "description":str(exc)[:100] if isinstance(exc,ValueError)
                             else "Public source bytes not accessible"})
    return {"status":"HOLD_ZENODO_PRESERVATION_FILES_NOT_VERIFIED",
            "candidate_records_considered":len(outcomes),
            "failures":outcomes,
            "actual_complete_historical_bytes_sha256_verified":False,
            "biological_rows_read":False,"ecological_forecast_authorized":False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse existing source evidence output")
    frozen=json.loads(SOURCE.read_text(encoding="utf-8"))
    result=audit(frozen)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,sort_keys=True,indent=2,ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status":result["status"],
                      "record_id":result.get("preservation_zenodo_record_id")}))
if __name__=="__main__":
    main()
