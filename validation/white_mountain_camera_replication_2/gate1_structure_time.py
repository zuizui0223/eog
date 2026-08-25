from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import gate0_locations_visits as g0

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "white_mountain_camera_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate1_structure_time_contract.json").read_text())
SOURCE = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate1_structure_time.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def parse_number(v: str, field: str, key: str) -> float:
    try:
        x = float(str(v).strip())
    except Exception as exc:
        raise RuntimeError(f"invalid {field} for {key}: {v!r}") from exc
    if not math.isfinite(x):
        raise RuntimeError(f"non-finite {field} for {key}: {v!r}")
    return x


def parse_datetime(date_token: str, time_token: str, key: str) -> datetime:
    text = f"{str(date_token).strip()} {str(time_token).strip()}".strip()
    candidates = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f",
        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise RuntimeError(f"unsupported visit datetime for {key}: {text!r}") from exc


def haversine(a, b):
    r = float(CONTRACT["structural_ladder"]["earth_radius_km"])
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


class DSU:
    def __init__(self, n):
        self.p = list(range(n))
        self.sz = [1] * n
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a = self.find(a); b = self.find(b)
        if a == b:
            return
        if self.sz[a] < self.sz[b]:
            a, b = b, a
        self.p[b] = a
        self.sz[a] += self.sz[b]
    def largest(self):
        return max(self.sz[self.find(i)] for i in range(len(self.p)))


def structural_ladder(points: list[tuple[float, float]]):
    n = len(points)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((haversine(points[i], points[j]), i, j))
    pairs.sort(key=lambda z: z[0])
    targets = [float(x) for x in CONTRACT["structural_ladder"]["target_largest_component_fractions"]]
    dsu = DSU(n)
    results = []
    idx = 0
    for target in targets:
        needed = max(1, math.ceil(target * n - 1e-12))
        while dsu.largest() < needed and idx < len(pairs):
            d = pairs[idx][0]
            while idx < len(pairs) and abs(pairs[idx][0] - d) <= 1e-12:
                _, i, j = pairs[idx]
                dsu.union(i, j)
                idx += 1
            if dsu.largest() >= needed:
                results.append({
                    "target_fraction": target,
                    "threshold_km": d,
                    "largest_component_n": dsu.largest(),
                    "largest_component_fraction": dsu.largest() / n,
                })
                break
        else:
            if dsu.largest() >= needed:
                prev = results[-1]["threshold_km"] if results else 0.0
                results.append({
                    "target_fraction": target,
                    "threshold_km": prev,
                    "largest_component_n": dsu.largest(),
                    "largest_component_fraction": dsu.largest() / n,
                })
            else:
                raise RuntimeError(f"could not reach LCC target {target}")
    distinct = sorted({round(x["threshold_km"], 12) for x in results if x["threshold_km"] > 0})
    return {
        "targets": results,
        "distinct_positive_threshold_count": len(distinct),
        "distinct_positive_thresholds_km": distinct,
        "pair_count": len(pairs),
    }


def get_allowed_rows():
    item, _ = g0.get_json(f"https://www.sciencebase.gov/catalog/item/{SOURCE['sciencebase_item_id']}?format=json")
    if str(item.get("title") or "") != SOURCE["sciencebase_item_title"]:
        raise RuntimeError("ScienceBase title drift")
    files = [f for f in (item.get("files") or []) if isinstance(f, dict)]
    by_name = {g0.file_name(f): f for f in files}
    out = {}
    for name in ("locations.csv", "visits.csv"):
        if name not in by_name:
            raise RuntimeError(f"missing {name}")
        url = g0.download_url(by_name[name])
        if not url:
            raise RuntimeError(f"missing public URL for {name}")
        raw, _, _ = g0.get_bytes(url)
        if by_name[name].get("size") is not None and len(raw) != int(by_name[name]["size"]):
            raise RuntimeError(f"size mismatch for {name}")
        g0.verify_checksum(raw, by_name[name].get("checksum"))
        header, rows, _, _ = g0.decode_csv(raw, name)
        out[name] = {"raw": raw, "header": header, "rows": rows}
    return out


def main():
    result = {
        "schema": "eog.white_mountain_camera_replication_2.gate1_structure_time.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "universe": {},
        "geometry": {},
        "structural_ladder": {},
        "visit_sequence": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        data = get_allowed_rows()
        loc_rows = data["locations.csv"]["rows"]
        visit_rows = data["visits.csv"]["rows"]
        lm = CONTRACT["relational_mapping"]

        visited_ids = sorted({str(r.get(lm["visit_location_foreign_key"]) or "").strip() for r in visit_rows})
        if "" in visited_ids:
            raise RuntimeError("blank visit location foreign key")
        loc_by_id = defaultdict(list)
        for r in loc_rows:
            loc_by_id[str(r.get(lm["location_primary_key"]) or "").strip()].append(r)
        missing = [x for x in visited_ids if x not in loc_by_id]
        duplicate = [x for x in visited_ids if len(loc_by_id.get(x, [])) != 1]
        if missing or duplicate:
            result["status"] = "stop_response_independent_location_registry_not_one_to_one"
            result["reason"] = f"missing={missing[:20]} duplicate_or_nonunique={duplicate[:20]}"
            result["universe"] = {"visited_location_count": len(visited_ids), "missing_count": len(missing), "nonunique_count": len(duplicate)}
            return finish(result)

        midpoints = {}
        bound_widths = []
        for key in visited_ids:
            r = loc_by_id[key][0]
            vals = {}
            for col in ("lat_min", "lat_max", "long_min", "long_max"):
                if str(r.get(col) or "").strip() == "":
                    result["status"] = "stop_missing_response_independent_location_bounds"
                    result["reason"] = f"{key} missing {col}"
                    return finish(result)
                vals[col] = parse_number(r[col], col, key)
            if not (-90 <= vals["lat_min"] <= vals["lat_max"] <= 90):
                raise RuntimeError(f"invalid latitude bounds for {key}: {vals}")
            if not (-180 <= vals["long_min"] <= vals["long_max"] <= 180):
                raise RuntimeError(f"invalid longitude bounds for {key}: {vals}")
            lat = (vals["lat_min"] + vals["lat_max"]) / 2.0
            lon = (vals["long_min"] + vals["long_max"]) / 2.0
            midpoints[key] = (lat, lon)
            bound_widths.append({
                "location_id": key,
                "lat_width_deg": vals["lat_max"] - vals["lat_min"],
                "lon_width_deg": vals["long_max"] - vals["long_min"],
            })

        ladder = structural_ladder([midpoints[k] for k in visited_ids])
        if ladder["distinct_positive_threshold_count"] < int(CONTRACT["structural_ladder"]["require_at_least_distinct_positive_thresholds"]):
            result["status"] = "stop_insufficient_response_blind_structural_scales"
            result["reason"] = f"only {ladder['distinct_positive_threshold_count']} distinct positive thresholds"
            result["structural_ladder"] = ladder
            return finish(result)

        allowed_types = set(CONTRACT["visit_sequence_profile"]["allowed_visit_types_exact"])
        by_loc = defaultdict(list)
        type_counts = Counter()
        for r in visit_rows:
            typ = str(r.get(lm["visit_type"]) or "").strip()
            if typ not in allowed_types:
                result["status"] = "stop_unexpected_visit_type"
                result["reason"] = f"unexpected visit_type={typ!r}"
                return finish(result)
            loc = str(r[lm["visit_location_foreign_key"]]).strip()
            vid = str(r.get(lm["visit_primary_key"]) or "").strip()
            dt = parse_datetime(r.get(lm["visit_date"]), r.get(lm["visit_time"]), vid)
            try:
                numeric_id = int(float(vid))
            except Exception:
                numeric_id = 10**18
            by_loc[loc].append((dt, numeric_id, vid, typ))
            type_counts[typ] += 1

        first_types = Counter(); last_types = Counter(); transitions = Counter(); violations = []
        interval_counts = []
        for loc in visited_ids:
            seq = sorted(by_loc[loc], key=lambda x: (x[0], x[1], x[2]))
            if not seq:
                raise RuntimeError(f"visited location {loc} has no visit sequence")
            first_types[seq[0][3]] += 1
            last_types[seq[-1][3]] += 1
            for a, b in zip(seq, seq[1:]):
                transitions[f"{a[3]}->{b[3]}"] += 1
            active = False
            opens = 0
            for dt, _, vid, typ in seq:
                if typ == "set":
                    if active:
                        violations.append({"location_id": loc, "visit_id": vid, "type": "set_while_active"})
                    active = True; opens += 1
                elif typ == "check":
                    if not active:
                        violations.append({"location_id": loc, "visit_id": vid, "type": "check_while_inactive"})
                elif typ == "pull":
                    if not active:
                        violations.append({"location_id": loc, "visit_id": vid, "type": "pull_while_inactive"})
                    active = False
            if active:
                violations.append({"location_id": loc, "visit_id": seq[-1][2], "type": "ends_active_without_pull"})
            interval_counts.append(opens)

        result["universe"] = {
            "location_rows": len(loc_rows),
            "visit_rows": len(visit_rows),
            "visited_location_count": len(visited_ids),
            "visited_location_ids_fingerprint": fingerprint(visited_ids),
            "one_to_one_registry_pass": True,
        }
        result["geometry"] = {
            "coordinate_rule": CONTRACT["geometry"]["coordinate_rule"],
            "midpoint_registry_fingerprint": fingerprint([{"id": k, "lat": midpoints[k][0], "lon": midpoints[k][1]} for k in visited_ids]),
            "latitude_bound_width_deg_min": min(x["lat_width_deg"] for x in bound_widths),
            "latitude_bound_width_deg_max": max(x["lat_width_deg"] for x in bound_widths),
            "longitude_bound_width_deg_min": min(x["lon_width_deg"] for x in bound_widths),
            "longitude_bound_width_deg_max": max(x["lon_width_deg"] for x in bound_widths),
        }
        result["structural_ladder"] = ladder
        result["visit_sequence"] = {
            "visit_type_counts": dict(sorted(type_counts.items())),
            "first_type_counts": dict(sorted(first_types.items())),
            "last_type_counts": dict(sorted(last_types.items())),
            "transition_counts": dict(sorted(transitions.items())),
            "strict_active_state_violation_count": len(violations),
            "strict_active_state_violation_types": dict(sorted(Counter(x["type"] for x in violations).items())),
            "strict_active_state_violation_examples": violations[:30],
            "set_interval_count_total": sum(interval_counts),
            "set_interval_count_per_location_min": min(interval_counts),
            "set_interval_count_per_location_max": max(interval_counts),
        }
        result["status"] = "gate1_response_free_structure_and_visit_sequence_profile_complete"
        result["reason"] = "Visited-location midpoint geometry supports the frozen structural ladder and visit sequences were profiled without response access; prediction intervals remain intentionally unfrozen"
        return finish(result)
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return finish(result, 1)


def finish(result, code=0):
    result["fingerprint"] = fingerprint({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
