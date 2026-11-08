"""Probe fixed NEON native CSV public access, preserving honest failure status."""
from __future__ import annotations
import argparse,hashlib,json,urllib.request,urllib.error,urllib.parse
from pathlib import Path

API="https://data.neonscience.org/api/v0/data/DP1.10072.001/HARV/2023-06"
TABLES=("mam_perplotnight","mam_pertrapnight")
LIMIT=15000000

def get(url):
    request=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"EOG-NEON-source-qualification/1.0"})
    with urllib.request.urlopen(request,timeout=35) as r:
        return r.read(LIMIT+1),r.status

def probe(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result={"api":API,"site":"HARV","month":"2023-06","status":"STOP_NOT_INGESTED","files":[]}
    try:
        raw,status=get(API)
        result["api_http_status"]=status
        if len(raw)>LIMIT:raise ValueError("metadata too large")
        obj=json.loads(raw)
        items=obj.get("data",{}).get("files",[])
        if not isinstance(items,list):raise ValueError("API metadata files not list")
        for table in TABLES:
            matching=[x for x in items if table in x.get("name","") and x.get("name","").lower().endswith(".csv")]
            if len(matching)!=1:
                raise ValueError(f"{table}: expected exactly one native CSV, found {len(matching)}")
            item=matching[0]
            name=item["name"]
            if "/" in name or "\\" in name:raise ValueError("unsafe file name")
            parsed=urllib.parse.urlparse(item["url"])
            if parsed.scheme!="https" or not parsed.hostname or not (
                parsed.hostname=="neonscience.org" or parsed.hostname.endswith(".neonscience.org")
            ):raise ValueError("untrusted source download host")
            request=urllib.request.Request(item["url"],headers={"User-Agent":"EOG-NEON-source-qualification/1.0"})
            with urllib.request.urlopen(request,timeout=50) as response:
                content=response.read(LIMIT+1)
            if len(content)>LIMIT:raise ValueError("file too large")
            digest=hashlib.md5(content).hexdigest()
            if item.get("md5") and digest.lower()!=item["md5"].lower():
                raise ValueError(f"{table}: NEON MD5 mismatch")
            path=out/name;path.write_bytes(content)
            result["files"].append({"table":table,"filename":name,"bytes":len(content),
                 "sha256":hashlib.sha256(content).hexdigest(),"md5":digest,"neon_md5":item.get("md5"),
                 "source_url":item["url"]})
        result["status"]="SOURCE_BYTES_RETRIEVED_PENDING_QUALITY_GATE"
    except urllib.error.HTTPError as e:
        result["api_http_status"]=e.code
        result["reason"]=f"HTTP_{e.code}"
    except Exception as e:
        result["reason"]=f"{type(e).__name__}: {e}"
    (out/"probe_receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("NEON_SOURCE_PROBE="+json.dumps(result,sort_keys=True))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output-dir",required=True)
    a=p.parse_args();probe(a.output_dir)
