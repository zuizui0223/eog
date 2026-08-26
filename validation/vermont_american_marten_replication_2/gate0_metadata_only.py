from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "vermont_american_marten_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_metadata_only.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"EOG-Vermont-Marten-metadata-only/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw=r.read()
        return json.loads(raw), len(raw), r.geturl()


def checksum_value(x):
    if isinstance(x, dict):
        return str(x.get("value") or "").lower()
    return str(x or "").lower()


def file_meta(f):
    return {
        "name": f.get("name"),
        "size": f.get("size"),
        "content_type": f.get("contentType"),
        "checksum": checksum_value(f.get("checksum") or f.get("md5")),
        "checksum_type": (f.get("checksum") or {}).get("type") if isinstance(f.get("checksum"), dict) else None,
        "has_download_uri": isinstance(f.get("downloadUri"), str),
    }


def write(r):
    r["fingerprint"] = fp({k:v for k,v in r.items() if k!="fingerprint"})
    OUT.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False))


def main():
    r={
        "schema":"eog.vermont_american_marten_replication_2.gate0_metadata_only.v1",
        "attempt_id":CONTRACT["attempt_id"],
        "status":"engineering_failure_pre_response",
        "reason":None,
        "item":{},
        "response_independent_files":{},
        "biological_response_files":{},
        "other_top_level_files":[],
        "biological_response_firewall":dict(CONTRACT["biological_response_firewall"]),
    }
    try:
        item_id=CONTRACT["sciencebase"]["item_id"]
        obj,nbytes,final=get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        if obj.get("id")!=item_id:
            raise RuntimeError(f"item id mismatch: {obj.get('id')} != {item_id}")
        if obj.get("title")!=CONTRACT["sciencebase"]["title"]:
            raise RuntimeError(f"title mismatch: {obj.get('title')!r}")
        r["item"]={
            "id":item_id,
            "title":obj.get("title"),
            "metadata_bytes":nbytes,
            "final_host":urllib.parse.urlparse(final).netloc,
            "top_level_file_count":len(obj.get("files",[])),
        }
        independent=set(CONTRACT["prospective_data_roles"]["response_independent_exact_names_if_present"])
        response=set(CONTRACT["prospective_data_roles"]["biological_response_exact_names_if_present"])
        seen={}
        for f in obj.get("files",[]):
            name=f.get("name")
            if not name:
                continue
            if name in seen:
                raise RuntimeError(f"duplicate top-level filename {name}")
            seen[name]=f
            meta=file_meta(f)
            if name in independent:
                r["response_independent_files"][name]=meta
            elif name in response:
                r["biological_response_files"][name]=meta
            else:
                r["other_top_level_files"].append(meta)
        required={"locations.csv","visits.csv","media.csv"}
        missing=sorted(required-set(r["response_independent_files"]))
        if missing:
            r["status"]="stop_required_label_free_source_files_missing"
            r["reason"]=f"missing response-independent required files: {missing}"
            write(r); return 0
        dict_names={"dictionary.csv","dbdictionary.csv"}.intersection(r["response_independent_files"])
        if len(dict_names)!=1:
            r["status"]="stop_dictionary_identity_not_unique"
            r["reason"]=f"expected exactly one dictionary file, observed={sorted(dict_names)}"
            write(r); return 0
        if not {"annotations.csv","modeloutputs.csv"}.intersection(r["biological_response_files"]):
            r["status"]="stop_no_separate_biological_response_table"
            r["reason"]="neither annotations.csv nor modeloutputs.csv exists as separate top-level file"
            write(r); return 0
        # Physical separation is by distinct named ScienceBase file objects; no payload opened.
        r["status"]="gate0_metadata_only_pass"
        r["reason"]="ScienceBase metadata exposes distinct label-free locations/visits/media file objects and separate biological-response annotation/model-output file objects; no file payload was requested"
        write(r); return 0
    except Exception as exc:
        r["reason"]=f"{type(exc).__name__}: {exc}"
        write(r); return 1

if __name__=="__main__":
    sys.exit(main())
