from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "white_mountain_camera_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate2_dictionary_contract.json").read_text())
OUT = BUILD / "gate2_dictionary.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get_json(url):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"EOG-WhiteMountain-dictionary/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read())


def get_bytes(url):
    req=urllib.request.Request(url,headers={"Accept":"text/csv,text/plain,*/*;q=0.5","User-Agent":"EOG-WhiteMountain-dictionary/1.0"})
    with urllib.request.urlopen(req,timeout=120) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def fname(f):
    return str(f.get("name") or f.get("title") or "")


def furl(f):
    for k in ("downloadUri","url"):
        v=f.get(k)
        if isinstance(v,str) and v.startswith("http"):
            return v
    return None


def decode(raw):
    for enc in ("utf-8-sig","cp1252"):
        try:
            text=raw.decode(enc); break
        except UnicodeDecodeError:
            text=None
    if text is None:
        raise RuntimeError("cannot decode dbdictionary.csv")
    try:
        delim=csv.Sniffer().sniff(text[:65536],delimiters=",;\t").delimiter
    except csv.Error:
        delim="," 
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    header=list(reader.fieldnames or [])
    rows=list(reader)
    if not header:
        raise RuntimeError("dbdictionary.csv has no header")
    return header,rows,enc,delim


def checksum_md5_from_meta(f):
    c=f.get("checksum")
    if isinstance(c,dict) and str(c.get("type") or "").upper()=="MD5":
        return str(c.get("value") or "").lower()
    if isinstance(c,str):
        return c.lower()
    return None


def main():
    result={
        "schema":"eog.white_mountain_camera_replication_2.gate2_dictionary.v1",
        "attempt_id":CONTRACT["attempt_id"],
        "status":"engineering_failure_pre_response",
        "reason":None,
        "dictionary":{},
        "matching_rows":[],
        "response_firewall":dict(CONTRACT["response_firewall"]),
    }
    try:
        item=get_json(f"https://www.sciencebase.gov/catalog/item/{CONTRACT['sciencebase_item_id']}?format=json")
        files=[x for x in (item.get("files") or []) if isinstance(x,dict)]
        matches=[x for x in files if fname(x)==CONTRACT["allowed_file"]["filename"]]
        if len(matches)!=1:
            raise RuntimeError(f"expected one dbdictionary.csv, found {len(matches)}")
        f=matches[0]
        if int(f.get("size"))!=int(CONTRACT["allowed_file"]["size"]):
            raise RuntimeError(f"dbdictionary size metadata drift: {f.get('size')}")
        md5meta=checksum_md5_from_meta(f)
        if md5meta!=CONTRACT["allowed_file"]["md5"]:
            raise RuntimeError(f"dbdictionary MD5 metadata drift: {md5meta}")
        url=furl(f)
        if not url:
            raise RuntimeError("dbdictionary.csv lacks public download URL")
        raw,final_url,ctype=get_bytes(url)
        if len(raw)!=int(CONTRACT["allowed_file"]["size"]):
            raise RuntimeError(f"dbdictionary payload size mismatch: {len(raw)}")
        actual=hashlib.md5(raw).hexdigest()
        if actual!=CONTRACT["allowed_file"]["md5"]:
            raise RuntimeError(f"dbdictionary payload MD5 mismatch: {actual}")
        header,rows,enc,delim=decode(raw)
        terms=[str(t).lower() for t in CONTRACT["persist"]["only_rows_matching_terms"]]
        matching=[]
        for i,row in enumerate(rows, start=2):
            joined=" | ".join(str(row.get(c) or "") for c in header).lower()
            hits=[t for t in terms if t in joined]
            if hits:
                matching.append({"physical_line":i,"hits":hits,"row":{c:row.get(c) for c in header}})
        result["dictionary"]={
            "filename":CONTRACT["allowed_file"]["filename"],
            "bytes":len(raw),
            "md5":actual,
            "sha256":hashlib.sha256(raw).hexdigest(),
            "encoding":enc,
            "delimiter":delim,
            "header":header,
            "row_count":len(rows),
            "matching_row_count":len(matching),
            "final_host":urllib.request.urlparse(final_url).netloc if False else final_url.split('/')[2],
            "column_nonempty_counts":{c:sum(1 for r in rows if str(r.get(c) or '').strip()) for c in header},
        }
        result["matching_rows"]=matching
        result["status"]="gate2_dictionary_profile_complete_response_still_closed"
        result["reason"]="Exact dbdictionary.csv was profiled response-independently; annotations/media/taxa/model outputs and photo payloads remained unopened"
        result["fingerprint"]=hashlib.sha256(canonical({k:v for k,v in result.items() if k!='fingerprint'})).hexdigest()
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"]=f"{type(exc).__name__}: {exc}"
        result["fingerprint"]=hashlib.sha256(canonical({k:v for k,v in result.items() if k!='fingerprint'})).hexdigest()
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
