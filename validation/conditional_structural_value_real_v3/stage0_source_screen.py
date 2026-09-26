#!/usr/bin/env python3
"""Response-blind Stage0 for the WildINTEL Camtrap DP candidate.

Only datapackage.json, deployments.csv and checksums-sha256.txt may be read.
observations.csv is never requested by this runner.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "validation/conditional_structural_value_real_v3/stage0_source_contract_v1.json"
OUT = ROOT / "build/conditional_structural_value_real_v3/stage0_result.json"

def _get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent":"eog-csv-stage0/1.0","Accept":"*/*"})
    with urlopen(req, timeout=60) as r:  # noqa: S310 - frozen public source URLs
        status = int(getattr(r, "status", 200))
        if status != 200:
            raise RuntimeError(f"HTTP {status} for {url}")
        return r.read()

def _parse_dt(value: str) -> datetime:
    v=(value or "").strip()
    if not v:
        raise ValueError("blank datetime")
    if v.endswith("Z"):
        v=v[:-1] + "+00:00"
    dt=datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def _week_start(dt: datetime) -> datetime:
    day=dt.date() - timedelta(days=dt.weekday())
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)

def _checksum_map(text: str) -> dict[str,str]:
    out={}
    for raw in text.splitlines():
        line=raw.strip()
        if not line:
            continue
        parts=line.replace(" *","  ").split()
        if len(parts) < 2:
            continue
        digest=parts[0].lower()
        name=parts[-1].lstrip("*")
        if len(digest)==64:
            out[name]=digest
    return out

def main() -> int:
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    src=c["source"]
    rev=src["frozen_revision"]
    base=f"https://huggingface.co/datasets/{src['repository']}/resolve/{rev}"
    allowed=c["authorized_stage0_access"]["allowed_files"]

    result={
        "schema":"eog.conditional_structural_value.real_v3.stage0_result.v1",
        "candidate_id":c["candidate_id"],
        "frozen_revision":rev,
        "get_requests":0,
        "requested_files":[],
        "response_file_gets":0,
        "response_header_bytes_opened":0,
        "response_rows_opened":0,
        "response_values_opened":False,
        "model_fits":0,
        "heldout_scores":0,
        "counts_as_predictive_evidence":False,
        "changes_closed_eog_wf_synthesis":False,
    }
    try:
        payload={}
        for name in allowed:
            payload[name]=_get(f"{base}/{name}")
            result["get_requests"] += 1
            result["requested_files"].append(name)

        if result["get_requests"] != c["authorized_stage0_access"]["max_get_requests"]:
            raise RuntimeError("unexpected Stage0 GET count")

        package=json.loads(payload["datapackage.json"].decode("utf-8"))
        resources={str(r.get("name")):str(r.get("path")) for r in package.get("resources",[]) if isinstance(r,dict)}
        for required in c["stage0_gates"]["camtrap_dp_resources_must_include"]:
            if required not in resources:
                raise RuntimeError(f"datapackage missing resource {required}")
        if resources["deployments"] != "deployments.csv":
            raise RuntimeError(f"unexpected deployments path: {resources['deployments']}")
        if resources["observations"] != "observations.csv":
            raise RuntimeError(f"unexpected observations path: {resources['observations']}")

        checks=_checksum_map(payload["checksums-sha256.txt"].decode("utf-8"))
        for required in c["stage0_gates"]["checksum_manifest_must_name"]:
            if required not in checks:
                raise RuntimeError(f"checksum manifest missing {required}")
        dep_sha=hashlib.sha256(payload["deployments.csv"]).hexdigest()
        if dep_sha != checks["deployments.csv"]:
            raise RuntimeError("deployments.csv SHA-256 mismatch")

        text=payload["deployments.csv"].decode("utf-8-sig")
        rows=list(csv.DictReader(io.StringIO(text)))
        required_cols={"deploymentID","latitude","longitude","deploymentStart","deploymentEnd"}
        missing=required_cols-set(rows[0].keys() if rows else [])
        if missing:
            raise RuntimeError(f"deployments missing columns: {sorted(missing)}")

        complete=[]
        for row in rows:
            try:
                did=(row.get("deploymentID") or "").strip()
                lat=float(row["latitude"]); lon=float(row["longitude"])
                start=_parse_dt(row["deploymentStart"]); end=_parse_dt(row["deploymentEnd"])
                if not did or end < start:
                    continue
                complete.append((did,lat,lon,start,end))
            except Exception:
                continue

        unique_ids={x[0] for x in complete}
        unique_coords={(round(x[1],8),round(x[2],8)) for x in complete}
        if len(unique_ids) < int(c["stage0_gates"]["minimum_complete_deployments"]):
            raise RuntimeError(f"complete deployments {len(unique_ids)} < minimum")
        if len(unique_coords) < int(c["stage0_gates"]["minimum_unique_coordinates"]):
            raise RuntimeError(f"unique coordinates {len(unique_coords)} < minimum")

        week_counts={}
        all_weeks=set()
        for _,_,_,start,end in complete:
            w=_week_start(start)
            last=_week_start(end)
            while w <= last:
                all_weeks.add(w)
                week_counts[w]=week_counts.get(w,0)+1
                w += timedelta(days=7)
        weeks=sorted(all_weeks)
        if len(weeks) < int(c["stage0_gates"]["minimum_temporal_weeks"]):
            raise RuntimeError(f"temporal weeks {len(weeks)} < minimum")

        thirds=[
            weeks[: max(1,len(weeks)//3)],
            weeks[max(1,len(weeks)//3): max(2,2*len(weeks)//3)],
            weeks[max(2,2*len(weeks)//3):],
        ]
        third_minima=[]
        for part in thirds:
            if not part:
                raise RuntimeError("empty temporal third")
            third_minima.append(max(week_counts[w] for w in part))
        min_active=int(c["stage0_gates"]["minimum_active_deployments_per_time_third"])
        if any(v < min_active for v in third_minima):
            raise RuntimeError(f"temporal-third active deployment support {third_minima} below {min_active}")

        result.update({
            "status":c["if_pass"]["status"],
            "next_gate":c["if_pass"]["next_gate"],
            "datapackage_profile":package.get("profile"),
            "resource_paths":resources,
            "deployment_rows":len(rows),
            "complete_deployments":len(unique_ids),
            "unique_coordinates":len(unique_coords),
            "temporal_weeks":len(weeks),
            "active_date_min":min(x[3] for x in complete).isoformat(),
            "active_date_max":max(x[4] for x in complete).isoformat(),
            "temporal_third_peak_active_deployments":third_minima,
            "deployments_sha256":dep_sha,
            "observations_sha256_frozen_without_opening":checks["observations.csv"],
        })
    except Exception as exc:
        result.update({
            "status":c["if_fail"]["status"],
            "reason":str(exc),
            "next_gate":"none",
            "repair_within_attempt":False,
        })

    raw=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    result["fingerprint"]=hashlib.sha256(raw).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
