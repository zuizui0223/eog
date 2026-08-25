from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import gate0_response_free_run as gate_run


gate = gate_run.gate
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "snapshot_japan_sika_deer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate1_time_geometry_contract.json").read_text())
GATE0 = json.loads((HERE / "gate0_response_free_certificate.json").read_text())
IDENTITY = json.loads((HERE / "pensoft_xml_sequence_identity_certificate.json").read_text())
OUT = BUILD / "gate1_time_geometry.json"
JST = ZoneInfo("Asia/Tokyo")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def parse_jst(value: str) -> datetime:
    s = (value or "").strip()
    if not s:
        raise ValueError("blank deployment timestamp")
    normalized = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        dt = None
    if dt is None:
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        raise ValueError(f"unsupported deployment timestamp {s!r}")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=JST)
    return dt.astimezone(JST)


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    radius = 6371.0088
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(h)))


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]


def weighted_group_lcc(uf: UnionFind, groups: dict[str, list[int]], n: int) -> tuple[float, dict[str, int]]:
    largest = {}
    total = 0
    for group, idxs in groups.items():
        counts = defaultdict(int)
        for i in idxs:
            counts[uf.find(i)] += 1
        m = max(counts.values()) if counts else 0
        largest[group] = m
        total += m
    return total / n, largest


def build_structural_ladder(coords, arrays, ids, targets):
    n = len(ids)
    groups = defaultdict(list)
    for i, arr in enumerate(arrays):
        groups[arr].append(i)
    edges = []
    for arr, idxs in groups.items():
        for p in range(len(idxs)):
            for q in range(p + 1, len(idxs)):
                i, j = idxs[p], idxs[q]
                d = haversine(coords[i], coords[j])
                if d > 0:
                    edges.append((d, i, j, arr))
    edges.sort(key=lambda x: x[0])
    uf = UnionFind(n)
    initial_fraction, initial_largest = weighted_group_lcc(uf, groups, n)
    levels = []
    target_index = 0
    k = 0
    while k < len(edges) and target_index < len(targets):
        d = edges[k][0]
        same = []
        while k < len(edges) and edges[k][0] == d:
            same.append(edges[k])
            k += 1
        for _, i, j, _ in same:
            uf.union(i, j)
        frac, largest = weighted_group_lcc(uf, groups, n)
        while target_index < len(targets) and frac + 1e-12 >= targets[target_index]:
            threshold = d
            directed_edges = 0
            isolated = 0
            for i in range(n):
                degree = 0
                for j in groups[arrays[i]]:
                    if i != j and haversine(coords[i], coords[j]) <= threshold + 1e-12:
                        degree += 1
                directed_edges += degree
                if degree == 0:
                    isolated += 1
            levels.append({
                "level_id": f"within_array_lcc{int(round(targets[target_index]*1000)):03d}",
                "target_weighted_within_array_lcc_fraction": targets[target_index],
                "distance_threshold_km": threshold,
                "achieved_weighted_within_array_lcc_fraction": frac,
                "largest_component_nodes_by_array": dict(sorted(largest.items())),
                "directed_edge_count": directed_edges,
                "isolated_node_fraction": isolated / n,
            })
            target_index += 1
    return {
        "node_count": n,
        "array_count": len(groups),
        "within_array_pair_count": len(edges),
        "initial_weighted_within_array_lcc_fraction": initial_fraction,
        "initial_largest_component_nodes_by_array": dict(sorted(initial_largest.items())),
        "targets": list(targets),
        "levels": levels,
    }


def main() -> int:
    result = {
        "schema": "eog.snapshot_japan_sika_deer_replication_2.gate1_time_geometry.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "registry": {},
        "time_axis": {},
        "availability": {},
        "structural_ladder": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        if GATE0["status"] != "gate0_pass_response_free_source_registry_time_and_geometry_profile":
            raise RuntimeError("Gate0 certificate is not passing")
        if IDENTITY["status"] != "pensoft_xml_resolves_exact_sequence_supplement_identity":
            raise RuntimeError("sequence identity certificate is not passing")
        for cert in (GATE0, IDENTITY):
            a = cert["response_firewall"]
            for key in [k for k in a if "sequence" in k and ("payload" in k or "header" in k or "rows" in k or "values" in k)]:
                val = a[key]
                if isinstance(val, bool):
                    if val:
                        raise RuntimeError(f"prior certificate response firewall was already consumed: {key}")
                elif val != 0:
                    raise RuntimeError(f"prior certificate response firewall was already consumed: {key}={val}")

        dep_raw, _ = gate.fetch_known_supplement(gate.CONTRACT["response_independent"]["deployments"])
        dep_header, dep_rows, _, _ = gate.decode_csv(dep_raw, "deployments")
        dep_cols = gate.resolve_aliases(dep_header, gate.DEP_ALIASES, "deployments")
        if len(dep_rows) != 90:
            raise RuntimeError(f"Gate1 deployment row drift: {len(dep_rows)} != 90")

        rows = []
        registry_payload = []
        for r in dep_rows:
            did = r[dep_cols["deployment_id"]].strip()
            arr = r[dep_cols["subproject_name"]].strip()
            lat = float(r[dep_cols["latitude"]])
            lon = float(r[dep_cols["longitude"]])
            start = parse_jst(r[dep_cols["start_date"]])
            end = parse_jst(r[dep_cols["end_date"]])
            if end <= start:
                raise RuntimeError(f"nonpositive deployment interval for {did}")
            rows.append({"id": did, "array": arr, "lat": lat, "lon": lon, "start": start, "end": end})
            registry_payload.append({
                "deployment_id": did,
                "latitude": lat,
                "longitude": lon,
                "start_date": r[dep_cols["start_date"]].strip(),
                "end_date": r[dep_cols["end_date"]].strip(),
                "subproject_name": arr,
            })
        reg_fp = gate.fp(sorted(registry_payload, key=lambda x: x["deployment_id"]))
        if reg_fp != GATE0["deployments"]["registry_fingerprint"]:
            raise RuntimeError(f"registry fingerprint drift: {reg_fp} != {GATE0['deployments']['registry_fingerprint']}")

        by_array = defaultdict(list)
        for row in rows:
            by_array[row["array"]].append(row)
        anchors = {arr: min(x["start"] for x in xs) for arr, xs in by_array.items()}
        max_week = 0
        for arr, xs in by_array.items():
            latest = max(x["end"] for x in xs)
            span = (latest - anchors[arr]).total_seconds() / (7 * 86400.0)
            max_week = max(max_week, int(math.ceil(span)))

        min_hours = float(CONTRACT["time_axis"]["eligible_site_week_min_active_hours"])
        availability = {}
        eligible_keys = []
        for week in range(1, max_week + 1):
            eligible = []
            active_arrays = set()
            for arr, xs in by_array.items():
                b0 = anchors[arr] + timedelta(days=7 * (week - 1))
                b1 = b0 + timedelta(days=7)
                for x in xs:
                    overlap = max(0.0, (min(x["end"], b1) - max(x["start"], b0)).total_seconds() / 3600.0)
                    if overlap + 1e-9 >= min_hours:
                        eligible.append({"deployment_id": x["id"], "array": arr, "active_hours": overlap})
                        active_arrays.add(arr)
                        eligible_keys.append((x["id"], week))
            availability[str(week)] = {
                "eligible_deployments": len(eligible),
                "eligible_arrays": len(active_arrays),
                "eligible_deployment_ids_fingerprint": fp(sorted(x["deployment_id"] for x in eligible)),
                "active_hours_min": min((x["active_hours"] for x in eligible), default=None),
                "active_hours_max": max((x["active_hours"] for x in eligible), default=None),
            }

        cal_weeks = list(CONTRACT["time_axis"]["calibration_relative_weeks"])
        held_weeks = list(CONTRACT["time_axis"]["primary_heldout_relative_weeks"])
        ag = CONTRACT["availability_gate"]
        cal_pass = all(
            availability.get(str(w), {}).get("eligible_deployments", 0) >= ag["each_calibration_week_min_eligible_deployments"]
            and availability.get(str(w), {}).get("eligible_arrays", 0) >= ag["each_calibration_week_min_arrays"]
            for w in cal_weeks
        )
        held_pass = all(
            availability.get(str(w), {}).get("eligible_deployments", 0) >= ag["each_primary_heldout_week_min_eligible_deployments"]
            and availability.get(str(w), {}).get("eligible_arrays", 0) >= ag["each_primary_heldout_week_min_arrays"]
            for w in held_weeks
        )
        cal_total = sum(availability.get(str(w), {}).get("eligible_deployments", 0) for w in cal_weeks)
        held_total = sum(availability.get(str(w), {}).get("eligible_deployments", 0) for w in held_weeks)
        total_pass = cal_total >= ag["calibration_total_min_eligible_site_weeks"] and held_total >= ag["primary_heldout_total_min_eligible_site_weeks"]
        availability_pass = cal_pass and held_pass and total_pass

        ids = [x["id"] for x in rows]
        arrays = [x["array"] for x in rows]
        coords = [(x["lat"], x["lon"]) for x in rows]
        targets = [float(x) for x in CONTRACT["geometry"]["target_weighted_within_array_lcc_fractions"]]
        ladder = build_structural_ladder(coords, arrays, ids, targets)
        thresholds = [float(x["distance_threshold_km"]) for x in ladder["levels"]]
        distinct_positive = len({round(x, 12) for x in thresholds if x > 0})
        target09 = next((x for x in ladder["levels"] if abs(x["target_weighted_within_array_lcc_fraction"] - 0.9) < 1e-12), None)
        structural_pass = (
            len(ladder["levels"]) == len(targets)
            and distinct_positive >= int(CONTRACT["geometry"]["require_distinct_positive_thresholds"])
            and target09 is not None
            and target09["achieved_weighted_within_array_lcc_fraction"] + 1e-12 >= 0.9
        )

        result["registry"] = {
            "deployment_count": len(rows),
            "array_count": len(by_array),
            "registry_fingerprint": reg_fp,
            "array_sizes": dict(sorted((k, len(v)) for k, v in by_array.items())),
        }
        result["time_axis"] = {
            "timezone": "Asia/Tokyo",
            "bin_days": 7,
            "minimum_active_hours": min_hours,
            "array_anchors": {k: v.isoformat() for k, v in sorted(anchors.items())},
            "max_response_independent_relative_week": max_week,
            "week_1_role": CONTRACT["time_axis"]["week_1_role"],
            "calibration_relative_weeks": cal_weeks,
            "primary_heldout_relative_weeks": held_weeks,
        }
        result["availability"] = {
            "weeks": availability,
            "calibration_total_eligible_site_weeks": cal_total,
            "primary_heldout_total_eligible_site_weeks": held_total,
            "calibration_week_gate_pass": cal_pass,
            "primary_heldout_week_gate_pass": held_pass,
            "total_gate_pass": total_pass,
            "final_availability_pass": availability_pass,
            "eligible_site_week_registry_fingerprint": fp(sorted(eligible_keys)),
        }
        ladder["distinct_positive_thresholds"] = distinct_positive
        ladder["target_0_9_achieved"] = bool(target09 and target09["achieved_weighted_within_array_lcc_fraction"] + 1e-12 >= 0.9)
        ladder["final_structural_pass"] = structural_pass
        ladder["fingerprint"] = fp(ladder)
        result["structural_ladder"] = ladder

        if not availability_pass:
            result["status"] = CONTRACT["availability_gate"]["stop_if_failed"]
            result["reason"] = "prospectively frozen response-independent campaign-week availability gate failed; sequence response remains unopened"
        elif not structural_pass:
            result["status"] = CONTRACT["geometry"]["stop_if_failed"]
            result["reason"] = "prospectively frozen response-independent within-array structural ladder gate failed; sequence response remains unopened"
        else:
            result["status"] = "gate1_pass_response_independent_time_and_structure"
            result["reason"] = "response-independent deployment intervals support the frozen calibration/heldout campaign weeks and within-array geometry supplies the required distinct structural ladder; sequence response remains unopened"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
