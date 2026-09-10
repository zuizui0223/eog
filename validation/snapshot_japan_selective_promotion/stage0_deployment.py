from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "source_selection_contract.json"
OUTPUT = ROOT / "build/snapshot_japan_selective_promotion/stage0_deployment.json"
URL = "https://zenodo.org/records/15030965/files/oo_1202827.csv?download=1"


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def parse_dt(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"unsupported datetime: {value}")


def monday(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day) - timedelta(days=d.weekday())


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2-lat1, lon2-lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def quantile(vals: list[float], q: float) -> float:
    xs = sorted(vals)
    pos = (len(xs)-1)*q
    lo = math.floor(pos); hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo]*(hi-pos)+xs[hi]*(pos-lo)


def main() -> int:
    c = json.loads(CONTRACT.read_text())
    base = {
        "schema": "eog.snapshot_japan_selective_promotion.stage0_deployment.v1",
        "attempt_id": c["attempt_id"],
        "deployment_payload_requests": 0,
        "deployment_payload_bytes_opened": 0,
        "response_payload_requests": 0,
        "response_header_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(URL, headers={"User-Agent": "eog-response-blind-stage0/1.0"})
        with urlopen(req, timeout=30) as r:  # noqa: S310 - frozen public file URL
            raw = r.read()
        base["deployment_payload_requests"] = 1
        base["deployment_payload_bytes_opened"] = len(raw)
        md5 = hashlib.md5(raw, usedforsecurity=False).hexdigest()
        if md5 != c["source_identity"]["deployment_file_md5"]:
            raise RuntimeError(f"deployment MD5 mismatch: {md5}")
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required = c["stage0_deployment_only"]["required_deployment_columns"]
        missing = [x for x in required if x not in (reader.fieldnames or [])]
        if missing:
            raise RuntimeError(f"missing required deployment columns: {missing}")
        rows = list(reader)
        if len(rows) < c["stage0_deployment_only"]["minimum_deployments"]:
            raise RuntimeError(f"too few deployments: {len(rows)}")

        registry = []
        week_to_active: dict[str, set[str]] = {}
        coords: list[tuple[float,float]] = []
        seen_ids: set[str] = set()
        for row in rows:
            dep = row["deployment_id"].strip()
            if not dep or dep in seen_ids:
                raise RuntimeError("blank or duplicate deployment_id")
            seen_ids.add(dep)
            lat, lon = float(row["latitude"]), float(row["longitude"])
            start, end = parse_dt(row["start_date"]), parse_dt(row["end_date"])
            if end <= start:
                raise RuntimeError(f"nonpositive deployment interval: {dep}")
            coords.append((lat, lon))
            registry.append({"deployment_id": dep, "latitude": lat, "longitude": lon, "start": start.isoformat(), "end": end.isoformat(), "subproject_name": row["subproject_name"].strip()})
            w = monday(start)
            last = monday(end)
            while w <= last:
                key = w.date().isoformat()
                week_to_active.setdefault(key, set()).add(dep)
                w += timedelta(days=7)

        weeks = sorted(week_to_active)
        n = len(weeks)
        if n < c["stage0_deployment_only"]["minimum_unique_iso_weeks"]:
            raise RuntimeError(f"too few unique ISO weeks: {n}")
        b1, b2 = math.floor(0.60*n), math.floor(0.80*n)
        if not (1 <= b1 < b2 < n):
            raise RuntimeError("degenerate temporal split")
        splits = {"inner_train": weeks[:b1], "inner_validation": weeks[b1:b2], "outer_heldout": weeks[b2:]}
        active_counts = {k: sum(len(week_to_active[w]) for w in ws) for k, ws in splits.items()}
        minimum = c["stage0_deployment_only"]["minimum_active_deployments_per_split"]
        if any(v < minimum for v in active_counts.values()):
            raise RuntimeError(f"insufficient active deployment-weeks by split: {active_counts}")

        distances = [haversine_km(coords[i], coords[j]) for i in range(len(coords)) for j in range(i+1,len(coords)) if haversine_km(coords[i], coords[j]) > 0]
        if not distances:
            raise RuntimeError("no positive pairwise distances")
        thresholds = [quantile(distances, q) for q in (0.2,0.4,0.6,0.8)]
        if not all(thresholds[i] < thresholds[i+1] for i in range(3)):
            raise RuntimeError(f"non-distinct geometry thresholds: {thresholds}")

        result = {
            **base,
            "status": "stage0_deployment_qualified",
            "deployment_md5": md5,
            "deployment_rows": len(rows),
            "subproject_count": len({r['subproject_name'] for r in registry}),
            "unique_week_count": n,
            "week_range": [weeks[0], weeks[-1]],
            "split_weeks": {k: {"count": len(v), "first": v[0], "last": v[-1]} for k,v in splits.items()},
            "active_deployment_week_counts": active_counts,
            "distance_thresholds_km": thresholds,
            "registry_fingerprint": canonical_sha(registry),
            "active_calendar_fingerprint": canonical_sha({k: sorted(v) for k,v in week_to_active.items()}),
            "next_gate": "freeze deployment registry/calendar/thresholds plus response schema and full learner/Layer-B contract before any sequence payload access",
        }
    except Exception as exc:
        result = {**base, "status": "stop_pre_response_deployment_transport_schema_or_structure", "reason": str(exc), "next_gate": "none; no rescue within this attempt"}
    result["fingerprint"] = canonical_sha(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
