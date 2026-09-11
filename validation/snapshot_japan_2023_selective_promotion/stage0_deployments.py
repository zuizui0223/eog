from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage0_deployments_contract.json"
OUTPUT = ROOT / "build/snapshot_japan_2023_selective_promotion/stage0_deployments.json"
EARTH_RADIUS_KM = 6371.0088


def canon_sha(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def parse_date(value: str) -> date:
    s = value.strip()
    if not s:
        raise ValueError("empty date")
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    return date.fromisoformat(s[:10])


def quantile_linear(xs: list[float], q: float) -> float:
    vals = sorted(xs)
    pos = (len(vals) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return vals[lo]
    f = pos - lo
    return vals[lo] * (1 - f) + vals[hi] * f


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(x))


def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.snapshot_japan_2023_selective_promotion.stage0_deployments.result.v1",
        "attempt_id": c["attempt_id"],
        "deployment_requests": 0,
        "response_file_requests": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(c["authorized_access"]["url"], headers={"User-Agent": "eog-snapshot-japan-stage0/1.0"})
        with urlopen(req, timeout=30) as r:  # noqa: S310 - prospectively frozen public URL
            blob = r.read()
            status = int(getattr(r, "status", 200))
        base["deployment_requests"] = 1
        if status != 200:
            raise RuntimeError(f"deployment HTTP status {status}")
        md5 = hashlib.md5(blob).hexdigest()  # noqa: S324 - immutable-source identity only
        if md5 != c["authorized_access"]["expected_md5"]:
            raise RuntimeError(f"deployment MD5 drift: {md5}")

        reader = csv.DictReader(io.StringIO(blob.decode("utf-8-sig")))
        fields = set(reader.fieldnames or [])
        required = set(c["required_columns"])
        if not required.issubset(fields):
            raise RuntimeError(f"missing required deployment columns: {sorted(required - fields)}")

        deployments: dict[str, dict[str, object]] = {}
        active_rows: list[tuple[date, str]] = []
        for row in reader:
            did = row["deployment_id"].strip()
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            start = parse_date(row["start_date"])
            end = parse_date(row["end_date"])
            if not did or end < start:
                raise RuntimeError("invalid deployment id/date interval")
            deployments[did] = {"lat": lat, "lon": lon, "start": start.isoformat(), "end": end.isoformat()}
            d = start
            while d <= end:
                active_rows.append((d, did))
                d += timedelta(days=1)

        coords = {(float(v["lat"]), float(v["lon"])) for v in deployments.values()}
        if len(deployments) < c["qualification"]["min_unique_deployments"]:
            raise RuntimeError("too few deployments")
        if len(coords) < c["qualification"]["min_unique_coordinates"]:
            raise RuntimeError("too few unique coordinates")
        if len(active_rows) < c["qualification"]["min_total_active_deployment_days"]:
            raise RuntimeError("too few active deployment-days")

        unique_dates = sorted({d for d, _ in active_rows})
        if len(unique_dates) < 3:
            raise RuntimeError("too few active calendar dates")
        total = len(active_rows)
        target = c["qualification"]["partition_fractions"]
        min_dep = c["qualification"]["min_unique_deployments_each_partition"]
        best = None
        for i in range(len(unique_dates) - 2):
            cut1 = unique_dates[i]
            for j in range(i + 1, len(unique_dates) - 1):
                cut2 = unique_dates[j]
                groups = [
                    [(d, did) for d, did in active_rows if d <= cut1],
                    [(d, did) for d, did in active_rows if cut1 < d <= cut2],
                    [(d, did) for d, did in active_rows if d > cut2],
                ]
                if any(len({did for _, did in g}) < min_dep for g in groups):
                    continue
                fracs = [len(g) / total for g in groups]
                score = sum(abs(a - b) for a, b in zip(fracs, target))
                key = (score, cut1, cut2)
                if best is None or key < best[0]:
                    best = (key, groups)
        if best is None:
            raise RuntimeError("no admissible 60/20/20 chronological partition")

        (_, cut1, cut2), groups = best
        part_names = ["inner_train", "inner_validation", "outer_heldout"]
        partition_stats = {}
        for name, g in zip(part_names, groups):
            partition_stats[name] = {
                "active_deployment_days": len(g),
                "fraction": len(g) / total,
                "unique_deployments": len({did for _, did in g}),
                "date_min": min(d for d, _ in g).isoformat(),
                "date_max": max(d for d, _ in g).isoformat(),
            }

        dep_items = sorted((did, float(v["lat"]), float(v["lon"])) for did, v in deployments.items())
        distances = []
        for idx, (_, lat1, lon1) in enumerate(dep_items):
            for _, lat2, lon2 in dep_items[idx + 1 :]:
                distances.append(haversine((lat1, lon1), (lat2, lon2)))
        qs = c["qualification"]["distance_world_quantiles"]
        thresholds = [quantile_linear(distances, float(q)) for q in qs]
        if c["qualification"]["require_four_strictly_increasing_positive_thresholds"]:
            if not (len(thresholds) == 4 and all(x > 0 for x in thresholds) and all(a < b for a, b in zip(thresholds, thresholds[1:]))):
                raise RuntimeError("distance-world thresholds are not four positive strictly increasing values")

        result = {
            **base,
            "status": "stage0_deployments_qualified",
            "deployment_md5": md5,
            "deployment_bytes": len(blob),
            "unique_deployments": len(deployments),
            "unique_coordinates": len(coords),
            "total_active_deployment_days": total,
            "active_date_min": min(unique_dates).isoformat(),
            "active_date_max": max(unique_dates).isoformat(),
            "cut_dates": [cut1.isoformat(), cut2.isoformat()],
            "partition_stats": partition_stats,
            "distance_thresholds_km": thresholds,
            "external_open_world": True,
            "next_gate": "freeze final model/response contract before any response payload access",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_transport_identity_or_structure",
            "reason": str(exc),
            "next_gate": "none; no repair within this attempt",
        }
    result["fingerprint"] = canon_sha(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
