from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation" / "carrier_prevalence_mechanism_v1"
PROTOCOL = BASE / "protocol_v1.json"
OUTPUT = ROOT / "results" / "generated" / "carrier_prevalence_fresh_roster_v1.json"

USER_AGENT = "neon-carrier-prevalence-metadata/1.0"
FORBIDDEN = ("/api/v0/data/query", "/api/v0/data/", "/api/v0/data?")

def sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    ).hexdigest()

def get_json(url: str) -> object:
    if any(x in url for x in FORBIDDEN):
        raise RuntimeError(f"biological response endpoint forbidden: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def post_graphql(query: str, variables: dict[str, object]) -> object:
    body=json.dumps({"query":query,"variables":variables}).encode()
    req=urllib.request.Request(
        "https://data.neonscience.org/graphql",data=body,method="POST",
        headers={"User-Agent":USER_AGENT,"Content-Type":"application/json"}
    )
    with urllib.request.urlopen(req,timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def collect_site_codes(value: object) -> set[str]:
    out=set()
    if isinstance(value,dict):
        x=value.get("siteCode")
        if isinstance(x,str) and re.fullmatch(r"[A-Z0-9]{4}",x):
            out.add(x)
        for v in value.values(): out.update(collect_site_codes(v))
    elif isinstance(value,list):
        for v in value: out.update(collect_site_codes(v))
    return out

def collect_location_names(value: object) -> set[str]:
    out=set()
    if isinstance(value,dict):
        x=value.get("locationName")
        if isinstance(x,str): out.add(x)
        for v in value.values(): out.update(collect_location_names(v))
    elif isinstance(value,list):
        for v in value: out.update(collect_location_names(v))
    return out

def is_trap(site: str, name: str) -> bool:
    if not name.startswith(site+"_") or ".mammalGrid.mam." not in name:
        return False
    coord=name.rsplit(".",1)[-1].strip().upper()
    return "X" not in coord and bool(re.fullmatch(r"[A-Z][0-9]+",coord))

def fetch_locations(names: list[str]) -> list[dict[str,object]]:
    query="""
    query FindLocations($query: LocationQuery!) {
      locations: findLocations(query: $query) {
        locationName locationType domainCode siteCode
        locationDecimalLatitude locationDecimalLongitude locationElevation
      }
    }"""
    rows=[]
    for start in range(0,len(names),500):
        payload=post_graphql(query,{"query":{"locationNames":names[start:start+500]}})
        if not isinstance(payload,dict) or payload.get("errors"):
            raise RuntimeError(f"GraphQL failure: {payload!r}")
        data=payload.get("data")
        if not isinstance(data,dict) or not isinstance(data.get("locations"),list):
            raise RuntimeError("unexpected GraphQL schema")
        rows.extend(x for x in data["locations"] if isinstance(x,dict))
    return rows

def registry(site: str) -> tuple[list[str], list[dict[str,object]], str]:
    hierarchy=get_json(
        "https://data.neonscience.org/api/v0/locations/"
        +urllib.parse.quote(site)+"?hierarchy=true"
    )
    names=sorted(x for x in collect_location_names(hierarchy) if is_trap(site,x))
    if not names:
        return [],[],sha([])
    wanted=set(names)
    rows=[]
    seen=set()
    for r in fetch_locations(names):
        name=str(r.get("locationName","")).strip()
        if name not in wanted: continue
        if name in seen: raise RuntimeError(f"{site}: duplicate {name}")
        try:
            lat=float(r.get("locationDecimalLatitude"))
            lon=float(r.get("locationDecimalLongitude"))
        except (TypeError,ValueError):
            continue
        if not math.isfinite(lat) or not math.isfinite(lon): continue
        seen.add(name)
        rows.append({
            "locationName":name,"latitude":lat,"longitude":lon,
            "locationType":r.get("locationType"),"domainCode":r.get("domainCode"),
            "siteCode":r.get("siteCode"),
        })
    missing=sorted(wanted-seen)
    if missing: raise RuntimeError(f"{site}: {len(missing)} trap coordinates missing")
    rows.sort(key=lambda r:r["locationName"])
    return [r["locationName"] for r in rows],rows,sha(rows)

def haversine(rows: list[dict[str,object]]) -> np.ndarray:
    lat=np.radians(np.array([float(r["latitude"]) for r in rows]))
    lon=np.radians(np.array([float(r["longitude"]) for r in rows]))
    dlat=lat[:,None]-lat[None,:]
    dlon=lon[:,None]-lon[None,:]
    a=np.sin(dlat/2)**2+np.cos(lat[:,None])*np.cos(lat[None,:])*np.sin(dlon/2)**2
    return 6371.0088*2*np.arcsin(np.sqrt(np.clip(a,0,1)))

def adjacency(dist: np.ndarray, threshold: float) -> np.ndarray:
    a=dist <= threshold + 1e-12
    np.fill_diagonal(a,False)
    return a

def comp_summary(a: np.ndarray) -> tuple[int,int,float]:
    n=len(a); seen=np.zeros(n,dtype=bool); sizes=[]
    for s in range(n):
        if seen[s]: continue
        stack=[s]; seen[s]=True; size=0
        while stack:
            u=stack.pop(); size+=1
            for v in np.flatnonzero(a[u]):
                v=int(v)
                if not seen[v]: seen[v]=True; stack.append(v)
        sizes.append(size)
    deg=np.sum(a,axis=1)
    return len(sizes),max(sizes),float(np.mean(deg==0))

def completed_targets(n: int, protocol: dict) -> list[float]:
    wf=protocol["world_family"]; aq=wf["adequacy"]
    vals={float(x) for x in wf["base_lcc_targets"]}
    vals.add(math.ceil(float(aq["min_largest_weak_component_fraction"])*n-1e-12)/n)
    max_iso=math.floor(float(aq["max_isolated_node_fraction"])*n+1e-12)
    vals.add((n-max_iso)/n)
    return sorted(vals)

class _UnionFind:
    def __init__(self, n: int):
        self.parent=list(range(n))
        self.size=[1]*n
        self.largest=1

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x]=self.parent[self.parent[x]]
            x=self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra=self.find(a); rb=self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra,rb=rb,ra
        self.parent[rb]=ra
        self.size[ra]+=self.size[rb]
        if self.size[ra] > self.largest:
            self.largest=self.size[ra]

def planned_thresholds(dist: np.ndarray, targets: list[float]) -> dict[float,float]:
    n=len(dist)
    rows,cols=np.triu_indices(n,1)
    values=dist[rows,cols]
    order=np.lexsort((cols,rows,values))
    rows=rows[order]; cols=cols[order]; values=values[order]

    thresholds: dict[float,float]={}
    ti=0
    while ti < len(targets) and 1/n >= targets[ti]-1e-15:
        thresholds[targets[ti]]=0.0
        ti+=1

    uf=_UnionFind(n)
    i=0
    while i < len(values) and ti < len(targets):
        threshold=float(values[i])
        j=i+1
        while j < len(values) and float(values[j]) <= threshold + 1e-12:
            j+=1
        for k in range(i,j):
            uf.union(int(rows[k]),int(cols[k]))
        achieved=uf.largest/n
        while ti < len(targets) and achieved >= targets[ti]-1e-15:
            thresholds[targets[ti]]=threshold
            ti+=1
        i=j

    if len(thresholds) != len(targets):
        raise RuntimeError("complete distance graph failed target")
    return thresholds

def worlds(site: str, dist: np.ndarray, protocol: dict) -> dict[str,object]:
    targets=completed_targets(len(dist),protocol)
    threshold_by_target=planned_thresholds(dist,targets)
    declared=[]
    for target in targets:
        threshold=threshold_by_target[target]
        a=adjacency(dist,threshold)
        cc,largest,iso=comp_summary(a)
        declared.append({
            "world_id":f"{site.lower()}_trap_haversine_km_lcc{int(round(target*1000)):03d}",
            "target_lcc_fraction":target,
            "distance_threshold_km":threshold,
            "largest_component_fraction":largest/len(dist),
            "weak_component_count":cc,
            "isolated_node_fraction":iso,
            "directed_edge_count":int(np.sum(a)),
            "adjacency_fingerprint":sha({"shape":list(a.shape),"adjacency":a.astype(int).tolist()}),
        })
    # exact adjacency dedup; lexical world ID is canonical
    groups={}
    for row in declared:
        groups.setdefault(row["adjacency_fingerprint"],[]).append(row)
    canonical=[]
    aliases=[]
    for fp,rows in groups.items():
        rows=sorted(rows,key=lambda r:r["world_id"])
        canonical.append(rows[0])
        aliases.append({
            "canonical_world_id":rows[0]["world_id"],
            "alias_world_ids":[r["world_id"] for r in rows],
            "adjacency_fingerprint":fp,
        })
    canonical.sort(key=lambda r:r["world_id"])
    aliases.sort(key=lambda r:r["canonical_world_id"])
    aq=protocol["world_family"]["adequacy"]
    passing=[
        r["world_id"] for r in canonical
        if r["largest_component_fraction"] >= float(aq["min_largest_weak_component_fraction"])
        and r["isolated_node_fraction"] <= float(aq["max_isolated_node_fraction"])
    ]
    return {
        "completed_lcc_targets":targets,
        "declared_world_count":len(declared),
        "distinct_world_count":len(canonical),
        "canonical_worlds":canonical,
        "alias_groups":aliases,
        "passing_world_ids":passing,
        "passed":bool(passing),
        "world_universe_fingerprint":sha({
            "canonical":[(r["world_id"],r["adjacency_fingerprint"]) for r in canonical],
            "passing_world_ids":passing,"horizon":1
        })
    }

def target_taxa(protocol: dict) -> tuple[list[dict[str,str]],str]:
    payload=get_json(
        "https://data.neonscience.org/api/v0/taxonomy?"
        "taxonTypeCode=SMALL_MAMMAL&verbose=true&offset=0&limit=1000"
    )
    excluded={x["scientific_name"] for x in protocol["target_taxa"]["design_contamination_exclusions"]}
    taxa=[]
    for row in payload.get("data",[]):
        if str(row.get("dwc:taxonRank","")).lower()!="species": continue
        if str(row.get("taxonProtocolCategory","")).lower()!="target": continue
        tid=str(row.get("taxonID","")).strip(); name=str(row.get("dwc:scientificName","")).strip()
        if tid and name and name not in excluded:
            taxa.append({"taxon_id":tid,"scientific_name":name})
    taxa.sort(key=lambda x:(x["scientific_name"],x["taxon_id"]))
    return taxa,sha(payload)

def main():
    protocol=json.loads(PROTOCOL.read_text())
    ds=protocol["data_source"]
    product=get_json(
        "https://data.neonscience.org/api/v0/products/"
        +urllib.parse.quote(ds["product_code"])
        +"?release="+urllib.parse.quote(ds["release"])
    )
    all_sites=sorted(collect_site_codes(product))
    fd=protocol["fresh_denominator"]
    excluded=set(fd["excluded_previous_method_sites"])|set(fd["excluded_design_contaminated_sites"])|set(fd["excluded_paper_A_consumed_sites"])
    candidates=[x for x in all_sites if x not in excluded]
    taxa,taxfp=target_taxa(protocol)
    selected=[]; stops=[]
    for index,site in enumerate(candidates, start=1):
        print(f"ROSTER_SITE_START {index}/{len(candidates)} {site}", flush=True)
        try:
            ids,rows,regfp=registry(site)
            if len(ids)<int(fd["minimum_geolocatable_non_x_traps"]):
                stops.append({"site_code":site,"status":"insufficient_nodes","node_count":len(ids)})
                continue
            w=worlds(site,haversine(rows),protocol)
            if not w["passed"]:
                stops.append({"site_code":site,"status":"structural_gate_failed","node_count":len(ids)})
                continue
            selected.append({
                "site_code":site,"node_count":len(ids),"node_ids":ids,
                "node_registry_fingerprint":regfp,**w
            })
            print(f"ROSTER_SITE_SELECTED {site} nodes={len(ids)} worlds={w['distinct_world_count']}", flush=True)
        except Exception as e:
            stops.append({"site_code":site,"status":"metadata_stop","detail":f"{type(e).__name__}: {e}"})
            print(f"ROSTER_SITE_STOP {site} {type(e).__name__}: {e}", flush=True)
    payload={
        "schema":"neon.carrier_prevalence_mechanism.fresh_roster.v1",
        "programme":protocol["programme"],
        "status":"response_blind_roster_locked",
        "product_code":ds["product_code"],"release":ds["release"],
        "available_site_count":len(all_sites),
        "excluded_site_count":len(set(all_sites)&excluded),
        "candidate_site_count":len(candidates),
        "selected_site_count":len(selected),
        "selected_site_codes":[x["site_code"] for x in selected],
        "selected_sites":selected,"pre_response_stops":stops,
        "eligible_target_taxon_count":len(taxa),"eligible_target_taxa":taxa,
        "taxonomy_metadata_fingerprint":taxfp,
        "product_metadata_fingerprint":sha(product),
        "response_endpoint_requests":0,"biological_response_bytes_opened":0,"model_fits":0,
    }
    payload["fingerprint"]=sha(payload)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print("ROSTER_SUMMARY "+json.dumps({
        "available":len(all_sites),"excluded":len(set(all_sites)&excluded),
        "candidates":len(candidates),"selected":len(selected),
        "selected_site_codes":payload["selected_site_codes"],
        "stops":stops,"fingerprint":payload["fingerprint"],
        "response_endpoint_requests":0,"biological_response_bytes_opened":0
    },sort_keys=True))

if __name__=="__main__":
    main()
