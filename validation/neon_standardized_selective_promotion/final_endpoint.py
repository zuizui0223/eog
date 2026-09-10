from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss, brier_score_loss

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "final_endpoint_contract.json"
SCHEMA_CONTRACT = HERE / "response_schema_contract.json"
DEPLOYMENT_CONTRACT = HERE / "stage1_response_blind_contract.json"
OUTPUT = ROOT / "build/neon_standardized_selective_promotion/final_endpoint_result.json"
BASE = "https://zenodo.org/api/records/20826511/files/{name}/content"
EPS = 1e-6
EARTH_KM = 6371.0088


def fetch_exact(name: str, expected_md5: str, expected_size: int, user_agent: str) -> bytes:
    req = Request(BASE.format(name=name), headers={"User-Agent": user_agent})
    with urlopen(req, timeout=60) as r:
        raw = r.read()
    if len(raw) != expected_size:
        raise RuntimeError(f"size mismatch for {name}: {len(raw)} != {expected_size}")
    got = hashlib.md5(raw).hexdigest()
    if got != expected_md5:
        raise RuntimeError(f"md5 mismatch for {name}: {got}")
    return raw


def rows(raw: bytes):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    return list(reader.fieldnames or []), list(reader)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value.strip()[:10], "%Y-%m-%d")


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, (a[0], a[1]))
    lat2, lon2 = map(math.radians, (b[0], b[1]))
    dlat, dlon = lat2-lat1, lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * EARTH_KM * math.asin(min(1.0, math.sqrt(h)))


def frozen_thresholds(deployments: list[dict]) -> list[float]:
    coords = sorted({(float(r["latitude"]), float(r["longitude"])) for r in deployments})
    if len(coords) < 5:
        raise RuntimeError("fewer than five distinct deployment coordinates")
    nn=[]
    for i,a in enumerate(coords):
        ds=[haversine(a,b) for j,b in enumerate(coords) if i != j]
        positive=[d for d in ds if d > 0]
        if positive:
            nn.append(min(positive))
    if len(nn) < 5:
        raise RuntimeError("insufficient positive nearest-neighbour distances")
    return [float(np.quantile(nn,q,method="linear")) for q in (0.25,0.50,0.75,0.90)]


def support_summary(target: tuple[float,float], source_coords: set[tuple[float,float]], surviving: list[int], thresholds: list[float]) -> np.ndarray:
    vals=[]
    for idx in surviving:
        th=thresholds[idx]
        vals.append(1.0 if any(haversine(s,target) <= th for s in source_coords) else 0.0)
    vals.append(1.0)  # external_open
    a=np.asarray(vals,dtype=float)
    return np.asarray([
        len(vals)/5.0,
        float(np.mean(a)),
        float(np.std(a)),
        float(np.min(a)),
        float(np.max(a)),
        float(np.quantile(a,0.25,method="linear")),
        float(np.quantile(a,0.50,method="linear")),
        float(np.quantile(a,0.75,method="linear")),
        float(np.mean(a > 0.0)),
        float(np.max(a)-np.min(a)),
    ])


def update_worlds(new_positive_coords: set[tuple[float,float]], source_coords: set[tuple[float,float]], surviving: list[int], thresholds: list[float]) -> tuple[set[tuple[float,float]], list[int]]:
    keep=list(surviving)
    if source_coords and new_positive_coords:
        next_keep=[]
        for idx in surviving:
            th=thresholds[idx]
            compatible=True
            for target in new_positive_coords:
                if not any(haversine(src,target) <= th for src in source_coords):
                    compatible=False
                    break
            if compatible:
                next_keep.append(idx)
        keep=next_keep
    return source_coords | new_positive_coords, keep


def resolve_header(header: list[str], aliases: list[str], required: bool=True) -> str | None:
    for alias in aliases:
        if header.count(alias) == 1:
            return alias
    if required:
        raise RuntimeError(f"required response semantic missing; accepted={aliases}; observed={header}")
    return None


def macro_loss(y, p, groups) -> float:
    vals=[]
    for g in sorted(set(groups)):
        m=np.asarray([x == g for x in groups],dtype=bool)
        vals.append(float(log_loss(y[m],p[m],labels=[0,1])))
    return float(np.mean(vals))


def macro_brier(y,p,groups) -> float:
    vals=[]
    for g in sorted(set(groups)):
        m=np.asarray([x == g for x in groups],dtype=bool)
        vals.append(float(brier_score_loss(y[m],p[m])))
    return float(np.mean(vals))


def fit_model(hp, x, y):
    model=RandomForestClassifier(
        n_estimators=int(hp["n_estimators"]),
        max_features=str(hp["max_features"]),
        min_samples_leaf=int(hp["min_samples_leaf"]),
        class_weight=None,
        random_state=int(hp["random_state"]),
        n_jobs=int(hp["n_jobs"]),
    )
    model.fit(x,y)
    if list(model.classes_) != [0,1]:
        raise RuntimeError(f"unexpected model classes {model.classes_}")
    return model


def pred(model,x):
    return np.clip(model.predict_proba(x)[:,1],EPS,1-EPS)


def run():
    c=json.loads(CONTRACT.read_text())
    sc=json.loads(SCHEMA_CONTRACT.read_text())
    dc=json.loads(DEPLOYMENT_CONTRACT.read_text())
    base={
        "schema":"eog.neon_standardized_selective_promotion.final_endpoint_result.v1",
        "attempt_id":c["attempt_id"],
        "response_gets":0,
        "response_consumed":False,
        "counts_as_fresh_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }
    # Response-independent files are re-read only by exact frozen identity to construct the endpoint.
    dep_spec=dc["authorized_payloads"]["camera_trap_deployments.csv"]
    dep_raw=fetch_exact("camera_trap_deployments.csv",dep_spec["md5"],dep_spec["size"],"eog-neon-final/1")
    dep_header, dep_rows=rows(dep_raw)
    required_dep={"deployment_id","longitude","latitude","start_date","end_date","subproject_name"}
    if not required_dep.issubset(dep_header):
        raise RuntimeError(f"frozen deployment schema drift: {dep_header}")
    if len(dep_rows) != 820 or len({r["deployment_id"] for r in dep_rows}) != 820:
        raise RuntimeError("frozen deployment row/id count drift")
    ordered=sorted(dep_rows,key=lambda r:(parse_date(r["start_date"]),r["deployment_id"]))
    n=len(ordered); cut1=math.floor(0.60*n); cut2=math.floor(0.80*n)
    split=np.asarray([0]*cut1+[1]*(cut2-cut1)+[2]*(n-cut2),dtype=int)
    thresholds=frozen_thresholds(ordered)

    # Sole biological response access.
    response=c["authoritative_response"]
    try:
        raw=fetch_exact(response["file"],response["md5"],response["size"],"eog-neon-final/1")
        base["response_gets"]=1; base["response_consumed"]=True
        header, seq=rows(raw)
        did_col=resolve_header(header,sc["required_semantics"]["deployment_id"]["accepted_exact_headers"])
        sci_col=resolve_header(header,sc["required_semantics"]["scientific_name"]["accepted_exact_headers"])
        common_col=resolve_header(header,sc["required_semantics"]["common_name_optional"]["accepted_exact_headers"],required=False)
    except Exception as exc:
        result={**base,"terminal_class":"stop_response_schema_or_identity","reason":str(exc)}
        OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return result

    valid_ids={r["deployment_id"] for r in ordered}
    focal_sci=sc["focal_matching"]["scientific_exact_after_strip_casefold"]
    focal_common=set(sc["focal_matching"]["common_exact_after_strip_casefold_optional"])
    positives=set()
    exact_scientific_matches=0; common_fallback_matches=0
    for r in seq:
        did=(r.get(did_col) or "").strip()
        if did not in valid_ids:
            continue
        sci=(r.get(sci_col) or "").strip().casefold()
        if sci == focal_sci:
            positives.add(did); exact_scientific_matches += 1
        elif common_col and not sci and (r.get(common_col) or "").strip().casefold() in focal_common:
            positives.add(did); common_fallback_matches += 1
    y=np.asarray([int(r["deployment_id"] in positives) for r in ordered],dtype=int)
    minima=c["estimability_minima"]
    counts={
        "inner_train_positive":int(np.sum(y[split==0]==1)),"inner_train_negative":int(np.sum(y[split==0]==0)),
        "inner_validation_positive":int(np.sum(y[split==1]==1)),"inner_validation_negative":int(np.sum(y[split==1]==0)),
        "outer_positive":int(np.sum(y[split==2]==1)),"outer_negative":int(np.sum(y[split==2]==0)),
        "inner_validation_subprojects":len({ordered[i]["subproject_name"] for i in range(n) if split[i]==1}),
        "outer_subprojects":len({ordered[i]["subproject_name"] for i in range(n) if split[i]==2}),
    }
    ok=(counts["inner_train_positive"]>=minima["inner_train_each_class"] and counts["inner_train_negative"]>=minima["inner_train_each_class"] and counts["inner_validation_positive"]>=minima["inner_validation_each_class"] and counts["inner_validation_negative"]>=minima["inner_validation_each_class"] and counts["outer_positive"]>=minima["outer_each_class"] and counts["outer_negative"]>=minima["outer_each_class"] and counts["inner_validation_subprojects"]>=minima["inner_validation_subprojects"] and counts["outer_subprojects"]>=minima["outer_subprojects"])
    if not ok:
        result={**base,"terminal_class":"stop_response_estimability","response_rows":len(seq),"focal_sequence_matches":exact_scientific_matches+common_fallback_matches,"deployment_class_counts":counts,"minima":minima}
        OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return result

    # Conventional feature matrix; category universe is response-independent and frozen by deployments.
    cats=sorted({r["subproject_name"] for r in ordered}); cmap={v:i for i,v in enumerate(cats)}
    baseline=[]
    for r in ordered:
        st=parse_date(r["start_date"]); en=parse_date(r["end_date"]); phase=2*math.pi*(st.month-1)/12
        vec=[float(r["longitude"]),float(r["latitude"]),float((en-st).days),math.sin(phase),math.cos(phase)]
        one=[0.0]*len(cats); one[cmap[r["subproject_name"]]]=1.0; vec.extend(one); baseline.append(vec)
    xb=np.asarray(baseline,dtype=float)

    # Construct temporally legal Layer-B features. State updates at deployment end, before each later start.
    events=sorted([(parse_date(r["end_date"]),i) for i,r in enumerate(ordered)],key=lambda x:(x[0],ordered[x[1]]["deployment_id"]))
    event_pos=0; sources=set(); surviving=[0,1,2,3]; contraction=[]; layer=[]
    for i,r in enumerate(ordered):
        start=parse_date(r["start_date"])
        newly=set()
        while event_pos < len(events) and events[event_pos][0] < start:
            _,j=events[event_pos]
            if y[j] == 1:
                newly.add((float(ordered[j]["latitude"]),float(ordered[j]["longitude"])))
            event_pos += 1
        if newly:
            before=list(surviving)
            sources,surviving=update_worlds(newly,sources,surviving,thresholds)
            if before != surviving:
                contraction.append({"before":before,"after":list(surviving),"start_date":r["start_date"]})
        target=(float(r["latitude"]),float(r["longitude"]))
        layer.append(support_summary(target,sources,surviving,thresholds))
    xl=np.asarray(layer,dtype=float); xa=np.hstack([xb,xl])

    train=split==0; val=split==1; outer=split==2; calibration=split<2
    hp=c["baseline"]["hyperparameters"]
    mb=fit_model(hp,xb[train],y[train]); ma=fit_model(hp,xa[train],y[train])
    pbv=pred(mb,xb[val]); pav=pred(ma,xa[val]); gv=[ordered[i]["subproject_name"] for i in range(n) if val[i]]
    inner_base=macro_loss(y[val],pbv,gv); inner_aug=macro_loss(y[val],pav,gv); promoted=inner_aug < inner_base

    mbf=fit_model(hp,xb[calibration],y[calibration]); maf=fit_model(hp,xa[calibration],y[calibration])
    pbo=pred(mbf,xb[outer]); pao=pred(maf,xa[outer]); go=[ordered[i]["subproject_name"] for i in range(n) if outer[i]]
    outer_base=macro_loss(y[outer],pbo,go); outer_aug=macro_loss(y[outer],pao,go); selected=outer_aug if promoted else outer_base
    delta=selected-outer_base
    terminal="favorable_selective_added_value" if delta < 0 else ("adverse_selective_added_value" if delta > 0 else "null_selective_added_value")
    selected_brier=macro_brier(y[outer],pao if promoted else pbo,go); base_brier=macro_brier(y[outer],pbo,go); aug_brier=macro_brier(y[outer],pao,go)
    result={
        **base,"terminal_class":terminal,"counts_as_fresh_predictive_evidence":True,
        "response_rows":len(seq),"resolved_headers":{"deployment_id":did_col,"scientific_name":sci_col,"common_name_optional":common_col},
        "focal_sequence_matches":{"scientific":exact_scientific_matches,"common_fallback":common_fallback_matches,"positive_deployments":len(positives)},
        "deployment_class_counts":counts,"split_sizes":{"inner_train":int(np.sum(train)),"inner_validation":int(np.sum(val)),"outer":int(np.sum(outer))},
        "layer_b":{"threshold_km":thresholds,"contraction_events":contraction,"surviving_local_worlds_final":surviving},
        "inner_validation":{"baseline_macro_log_loss":inner_base,"augmented_macro_log_loss":inner_aug,"augmented_minus_baseline":inner_aug-inner_base,"promoted":bool(promoted)},
        "outer":{"baseline_macro_log_loss":outer_base,"always_augmented_macro_log_loss":outer_aug,"selected_macro_log_loss":selected,"selected_minus_baseline":delta,"selected_minus_always_augmented":selected-outer_aug,"selected_oracle_regret":selected-min(outer_base,outer_aug),"baseline_macro_brier":base_brier,"always_augmented_macro_brier":aug_brier,"selected_macro_brier":selected_brier,"selected_minus_baseline_brier":selected_brier-base_brier},
    }
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); print(json.dumps(result,indent=2,sort_keys=True)); return result


if __name__ == "__main__":
    run()
