from __future__ import annotations

import base64, csv, hashlib, io, json, math
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage0_nonresponse_contract.json"
OUTPUT = ROOT / "build/cbc_wild_turkey_selective_promotion/stage0_nonresponse.json"
BLOB_SHA = "a06a27aca69debb005d2850144d138a168e7c5fd"
BLOB_URL = f"https://api.github.com/repos/pwilliams0/Bird_biotic_homogenization/git/blobs/{BLOB_SHA}"
R = 6371.0088


def sha(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def fetch_blob():
    req = Request(BLOB_URL, headers={"User-Agent": "eog-cbc-response-blind-stage0/1.0", "Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as r:  # noqa: S310
        obj = json.loads(r.read().decode())
    if obj.get("sha") != BLOB_SHA or obj.get("encoding") != "base64":
        raise RuntimeError("survey blob identity/encoding mismatch")
    return base64.b64decode(obj["content"])


def mean(x): return sum(x) / len(x)


def qlin(xs, q):
    xs = sorted(xs); p = (len(xs)-1)*q; lo = math.floor(p); hi = math.ceil(p)
    return xs[lo] if lo == hi else xs[lo]*(hi-p)+xs[hi]*(p-lo)


def hav(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c); dp=math.radians(c-a); dl=math.radians(d-b)
    z=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(z))


def main():
    contract=json.loads(CONTRACT.read_text())
    base={"schema":"eog.cbc_wild_turkey_selective_promotion.stage0_nonresponse.v1","attempt_id":contract["attempt_id"],"survey_blob_requests":0,"response_blob_requests":0,"response_header_bytes_opened":0,"response_rows_opened":0,"response_values_opened":False,"model_fits":0,"heldout_scores":0,"counts_as_predictive_evidence":False}
    try:
        blob=fetch_blob(); base["survey_blob_requests"]=1
        rd=csv.DictReader(io.StringIO(blob.decode("utf-8-sig")))
        req={"cell_id","Year","Latitude","Longitude","total_hours"}
        if not req.issubset(set(rd.fieldnames or [])): raise RuntimeError(f"missing columns {sorted(req-set(rd.fieldnames or []))}")
        g={}; years=set()
        for row in rd:
            cell=int(row["cell_id"]); year=int(row["Year"]); years.add(year); k=(cell,year)
            z=g.setdefault(k,{"lat":[],"lon":[],"hours":0.0,"n":0})
            z["lat"].append(float(row["Latitude"])); z["lon"].append(float(row["Longitude"])); z["hours"]+=float(row["total_hours"]); z["n"]+=1
        cy=[{"cell_id":c,"Year":y,"Latitude":mean(z["lat"]),"Longitude":mean(z["lon"]),"effort_hours":z["hours"],"survey_count":z["n"]} for (c,y),z in sorted(g.items())]
        bc=defaultdict(lambda:{"lat":[],"lon":[]})
        for r in cy: bc[r["cell_id"]]["lat"].append(r["Latitude"]); bc[r["cell_id"]]["lon"].append(r["Longitude"])
        cent={c:(mean(v["lat"]),mean(v["lon"])) for c,v in bc.items()}; ids=sorted(cent)
        ds=[]
        for i,a in enumerate(ids):
            for b in ids[i+1:]: ds.append(hav(*cent[a],*cent[b]))
        th=[qlin(ds,q) for q in (.2,.4,.6,.8)]
        parts={"inner_train":(1980,2009),"inner_validation":(2010,2015),"outer_heldout":(2016,2022)}; ps={}
        for n,(lo,hi) in parts.items():
            rows=[r for r in cy if lo<=r["Year"]<=hi]; ps[n]={"year_min":min((r["Year"] for r in rows),default=None),"year_max":max((r["Year"] for r in rows),default=None),"cell_year_rows":len(rows),"unique_cells":len({r["cell_id"] for r in rows})}
        ok=min(years)<=1980 and max(years)>=2022 and all(v["unique_cells"]>=20 and v["cell_year_rows"]>=100 for v in ps.values()) and all(a<b for a,b in zip(th,th[1:]))
        out={**base,"status":"stage0_nonresponse_qualified" if ok else "stop_pre_response_nonresponse_structure","survey_blob_sha":BLOB_SHA,"survey_blob_bytes":len(blob),"year_min":min(years),"year_max":max(years),"unique_cells":len(ids),"cell_year_rows":len(cy),"partition_stats":ps,"distance_thresholds_km":th,"external_open_world":True,"next_gate":"freeze exact response semantics and final model contract" if ok else "none; no repair within this attempt"}
    except Exception as e:
        out={**base,"status":"stop_pre_response_nonresponse_transport_or_schema","reason":str(e),"next_gate":"none; no repair within this attempt"}
    out["fingerprint"]=sha(out); OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
