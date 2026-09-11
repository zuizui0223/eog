#!/usr/bin/env python3
from __future__ import annotations
import base64, csv, io, json, math
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"validation/btnw_selective_promotion/source_contract_v1.json"
OUTPUT=ROOT/"build/btnw_selective_promotion/stage0_metadata_geometry.json"
UA="eog-btnw-response-blind-stage0/1.0"
DRYAD="https://datadryad.org"

class Stop(RuntimeError): pass

def get_json(url):
    req=Request(url,headers={"User-Agent":UA,"Accept":"application/json","X-API-Version":"2.1.0"})
    with urlopen(req,timeout=60) as r:
        raw=r.read(); status=int(getattr(r,"status",200))
    if status!=200: raise Stop(f"HTTP {status}")
    x=json.loads(raw.decode("utf-8-sig"))
    if not isinstance(x,dict): raise Stop("JSON root not object")
    return x

def get_blob(repo,sha):
    req=Request(f"https://api.github.com/repos/{repo}/git/blobs/{sha}",headers={"User-Agent":UA,"Accept":"application/vnd.github+json"})
    with urlopen(req,timeout=60) as r:
        x=json.loads(r.read().decode("utf-8"))
    if x.get("sha")!=sha or x.get("encoding")!="base64": raise Stop("GitHub blob identity/encoding mismatch")
    return base64.b64decode(x["content"])

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)

def response_meta(manifest,name):
    found=[]; seen=set()
    for d in walk(manifest):
        p=d.get("path")
        if not isinstance(p,str) or Path(p).name!=name: continue
        if not any(k in d for k in ("id","size","digest","digestType")): continue
        key=json.dumps(d,sort_keys=True,default=str)
        if key not in seen: seen.add(key); found.append(d)
    if len(found)!=1: raise Stop(f"expected one {name}, found {len(found)}")
    d=found[0]
    if d.get("id") in (None,"") or not d.get("digest") or not d.get("digestType"): raise Stop("response metadata lacks immutable identity/digest")
    size=int(d.get("size",0))
    if size<=0: raise Stop("response metadata size invalid")
    return {"id":d["id"],"path":d["path"],"size":size,"digest":d["digest"],"digestType":d["digestType"],"mimeType":d.get("mimeType")}

def qlinear(x,q):
    h=(len(x)-1)*q; lo=math.floor(h); hi=math.ceil(h)
    return float(x[lo] if lo==hi else x[lo]+(h-lo)*(x[hi]-x[lo]))

def hav(a,b,R):
    p1,p2=map(math.radians,(a[0],b[0])); dl=math.radians(b[1]-a[1])
    z=math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(min(1,max(0,z))))

def geometry(raw,c):
    rows=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    cols=c["independent_documentation"]["geometry_columns_exact"]
    req=[cols["site_id"],cols["longitude"],cols["latitude"]]
    if not rows or any(k not in rows[0] for k in req): raise Stop("exact geometry columns missing")
    pts=[]; ids=set()
    for r in rows:
        sid=str(r[cols["site_id"]]).strip(); lon=float(r[cols["longitude"]]); lat=float(r[cols["latitude"]])
        if not sid or sid in ids or not all(map(math.isfinite,(lon,lat))) or not(-180<=lon<=180 and -90<=lat<=90): raise Stop("invalid/duplicate geometry")
        ids.add(sid); pts.append((lat,lon))
    n=c["response_semantics_frozen_from_independent_documentation"]["survey_sites"]
    if len(pts)!=n: raise Stop(f"geometry denominator {len(pts)} != {n}")
    R=c["geometry_world_rule"]["earth_radius_km"]
    ds=sorted(d for i in range(n) for j in range(i+1,n) if (d:=hav(pts[i],pts[j],R))>0 and math.isfinite(d))
    qs=c["geometry_world_rule"]["local_quantiles"]; th=[qlinear(ds,float(q)) for q in qs]
    if len(ds)!=n*(n-1)//2 or any(not(a<b) for a,b in zip(th,th[1:])) or any(x<=0 for x in th): raise Stop("distance-world gate failed")
    return len(pts),len(ds),th

def main():
    c=json.loads(CONTRACT.read_text())
    out={"schema":"eog.btnw_selective_promotion.stage0_metadata_geometry.v1","attempt_id":c["attempt_id"],"status":"stop_pre_response_metadata_identity_transport_or_geometry","response_payload_requests":0,"response_payload_bytes":0,"response_header_bytes":0,"response_rows":0,"response_values_opened":False,"model_fits":0,"selector_decisions":0,"heldout_scores":0,"counts_as_predictive_evidence":False,"counts_as_empirical_conclusion":False,"changes_closed_eog_wf":False}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        if c["response_opening_authorized_by_this_contract"] is not False: raise Stop("response firewall drift")
        if any(c["stage0_authorized_access_only"][k]!=0 for k in ("dryad_response_file_payload_gets","dryad_response_file_payload_bytes","response_headers_rows_values","model_fits","selector_decisions","heldout_scores")): raise Stop("authorized-access firewall drift")
        doi=c["published_dataset"]["dryad_doi"]; enc=quote("doi:"+doi,safe="")
        ds=get_json(f"{DRYAD}/api/v2/datasets/{enc}")
        if str(ds.get("identifier","")).lower()!=("doi:"+doi).lower(): raise Stop("Dryad DOI mismatch")
        v=ds.get("_links",{}).get("stash:version",{}).get("href")
        if not isinstance(v,str) or not v.startswith("/api/v2/versions/"): raise Stop("Dryad current version missing")
        vid=v.rstrip("/").split("/")[-1]
        if not vid.isdigit(): raise Stop("Dryad version id malformed")
        fm=get_json(f"{DRYAD}{v}/files?per_page=100")
        rm=response_meta(fm,c["published_dataset"]["response_file_name"])
        doc=c["independent_documentation"]; repo=doc["author_repository"]
        readme=get_blob(repo,doc["author_readme_blob_sha"])
        text=readme.decode("utf-8-sig")
        tokens=("114","25","4","model_data.rds","thinnedpoints.csv")
        if any(t not in text for t in tokens): raise Stop("pinned README documentation token missing")
        geo=get_blob(repo,doc["geometry_blob_sha"])
        if len(geo)!=doc["geometry_file_size_bytes"]: raise Stop("geometry blob size drift")
        n,npairs,th=geometry(geo,c)
        out.update({"status":"stage0_source_geometry_qualified_class_support_pending","dryad":{"dataset_identifier":ds.get("identifier"),"dataset_id":ds.get("id"),"version_href":v,"version_id":int(vid),"version_number":ds.get("versionNumber"),"version_status":ds.get("versionStatus"),"response_file_metadata":rm,"dataset_metadata_gets":1,"version_metadata_gets":0,"file_manifest_metadata_gets":1},"author_repository":{"repository":repo,"commit":doc["author_repository_commit"],"readme_blob_sha":doc["author_readme_blob_sha"],"readme_sha256":sha256(readme).hexdigest(),"geometry_blob_sha":doc["geometry_blob_sha"],"geometry_sha256":sha256(geo).hexdigest(),"geometry_bytes":len(geo),"unique_valid_sites":n,"github_blob_gets":2},"geometry":{"distance":"haversine_km","pairwise_nonzero_distance_count":npairs,"quantiles":c["geometry_world_rule"]["local_quantiles"],"local_thresholds_km":th,"world_ids":c["geometry_world_rule"]["world_ids"]},"next_gate":"separate_pre_response_class_support_audit","final_response_opening_authorized":False})
    except Exception as e:
        out["stop_reason"]=f"{type(e).__name__}:{e}"
    OUTPUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
