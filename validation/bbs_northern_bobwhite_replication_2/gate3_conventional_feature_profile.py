from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import gate1_registry_effort as g1
import gate2_structural as g2

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "bbs_northern_bobwhite_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
OUT = BUILD / "gate3_conventional_feature_profile.json"
EXPECTED_REGISTRY_FP = "40672b6433f130a667ed045c36399fe2987290f0cb50736d16577ba86f733386"


def val(row, col):
    return str(row.get(col) or "").strip()


def profile(rows, col, max_tokens=30):
    values = [val(r, col) for r in rows]
    nonblank = [x for x in values if x != ""]
    counts = Counter(nonblank)
    return {
        "row_count": len(rows),
        "nonblank_count": len(nonblank),
        "blank_count": len(rows) - len(nonblank),
        "unique_nonblank_count": len(counts),
        "tokens": sorted(counts)[:max_tokens] if len(counts) <= max_tokens else [],
        "most_common": counts.most_common(12),
    }


def main():
    result = {
        "schema": "eog.bbs_northern_bobwhite_replication_2.gate3_conventional_feature_profile.v1",
        "attempt_id": g1.CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "analysis_registry": {},
        "bcr": {},
        "weather_profiles": {},
        "response_firewall": dict(g1.CONTRACT["response_firewall"]),
    }
    try:
        route_header, route_rows, _ = g2.fetch_allowed("Routes.csv")
        weather_header, weather_rows, _ = g2.fetch_allowed("Weather.csv")
        reg = g2.reconstruct_registry(route_rows, route_header, weather_rows, weather_header)
        observed_fp = g2.fp(reg)
        if observed_fp != EXPECTED_REGISTRY_FP or len(reg) != 1880:
            raise RuntimeError(f"analysis registry drift: count={len(reg)}, fp={observed_fp}")

        rsem = g1.resolve_semantics(route_header, g1.CONTRACT["semantic_aliases"]["routes"], {"country_num", "state_num", "route", "bcr"})
        route_map = {}
        for r in route_rows:
            key=(g1.intval(r.get(rsem["country_num"]),"country"),g1.intval(r.get(rsem["state_num"]),"state"),g1.intval(r.get(rsem["route"]),"route"))
            route_map[key]=r
        keys=[(int(r["country_num"]),int(r["state_num"]),int(r["route"])) for r in reg]
        bcr_values=[]
        for key in keys:
            token=val(route_map[key], rsem["bcr"])
            if not token:
                raise RuntimeError(f"blank BCR for analysis route {key}")
            bcr_values.append(int(float(token)))
        bcr_counts=Counter(bcr_values)

        wsem = g1.resolve_semantics(weather_header, g1.CONTRACT["semantic_aliases"]["weather"], {"country_num","state_num","route","year","quality_current_id","run_type"})
        analysis_keyset=set(keys)
        years=set(map(int,g1.CONTRACT["eligibility"]["modeled_years"]))
        eligible=[]
        for w in weather_rows:
            if g1.intval(w.get(wsem["country_num"]),"country") != 840: continue
            y=g1.intval(w.get(wsem["year"]),"year")
            if y not in years: continue
            if g1.intval(w.get(wsem["run_type"]),"RunType") != 1: continue
            if g1.intval(w.get(wsem["quality_current_id"]),"QualityCurrentID") != 1: continue
            key=(840,g1.intval(w.get(wsem["state_num"]),"state"),g1.intval(w.get(wsem["route"]),"route"))
            if key in analysis_keyset:
                eligible.append(w)

        fields=["Year","Month","Day","ObsN","StartTemp","EndTemp","TempScale","StartWind","EndWind","StartSky","EndSky","StartTime","EndTime"]
        missing=[f for f in fields if f not in weather_header]
        if missing:
            raise RuntimeError(f"weather feature fields missing: {missing}; header={weather_header}")
        profiles={f:profile(eligible,f) for f in fields}
        if profiles["Month"]["blank_count"] or profiles["Day"]["blank_count"] or profiles["ObsN"]["blank_count"]:
            raise RuntimeError("Month/Day/ObsN must be complete in frozen analysis route-years")
        temp_tokens=set(profiles["TempScale"]["tokens"])
        if not temp_tokens.issubset({"C","F"}):
            raise RuntimeError(f"unexpected TempScale tokens: {sorted(temp_tokens)}")

        result["analysis_registry"]={"route_count":len(reg),"route_year_count":len(eligible),"registry_fingerprint":observed_fp}
        result["bcr"]={"categories":sorted(bcr_counts),"counts":dict(sorted(bcr_counts.items())),"category_count":len(bcr_counts)}
        result["weather_profiles"]=profiles
        result["status"]="gate3_pass_response_independent_conventional_feature_profile"
        result["reason"]="BCR categories and all planned current-survey conventional weather/time/observer fields were profiled on the exact Gate1 analysis route-years without bird response access"
        result["fingerprint"]=g2.fp({k:v for k,v in result.items() if k!="fingerprint"})
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"]=f"{type(exc).__name__}: {exc}"
        result["fingerprint"]=g2.fp({k:v for k,v in result.items() if k!="fingerprint"})
        OUT.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
