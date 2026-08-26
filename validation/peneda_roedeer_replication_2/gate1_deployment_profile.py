from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import gate0_response_free as gate0

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "peneda_roedeer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
SITE_CERT = json.loads((HERE / "site_registry_certificate.json").read_text())
OUT = BUILD / "gate1_deployment_profile.json"

ALIAS_RE = re.compile(r"^L0*([0-9]+)$")
EXPECTED_YEARS = [2015, 2016, 2017, 2018, 2019, 2020]
EXPECTED_START_YEAR_COUNTS = {2015: 58, 2016: 61, 2017: 55, 2018: 53, 2019: 57, 2020: 47}
LCC_TARGETS = [0.25, 0.50, 0.75, 0.90]
EARTH_RADIUS_KM = 6371.0088


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def response_firewall():
    return {
        "observation_payload_requests": 0,
        "observation_payload_bytes_opened": 0,
        "observation_header_bytes_opened": 0,
        "observation_rows_opened": False,
        "observation_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }


def finish(result, code=0):
    result["fingerprint"] = fingerprint({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


def canonical_site(raw_name: str) -> str:
    m = ALIAS_RE.fullmatch(str(raw_name or "").strip())
    if not m:
        raise RuntimeError(f"locationName violates frozen alias regex: {raw_name!r}")
    return f"L{int(m.group(1))}"


def decode_csv(raw: bytes):
    text = None
    encoding = None
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("deployment CSV decode failure")
    try:
        delimiter = csv.Sniffer().sniff(text[:32768], delimiters=",;\t").delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return list(reader.fieldnames or []), list(reader), encoding, delimiter


def percentile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    p = (len(xs) - 1) * q
    lo = int(math.floor(p))
    hi = int(math.ceil(p))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - p) + xs[hi] * (p - lo)


def union_days(intervals):
    intervals = sorted(intervals, key=lambda x: x[0])
    if not intervals:
        return 0.0
    merged = []
    cur_s, cur_e = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_e:
            if e > cur_e:
                cur_e = e
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))
    return sum((e - s).total_seconds() for s, e in merged) / 86400.0


def haversine_km(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def structural_ladder(site_coords):
    sites = sorted(site_coords)
    n = len(sites)
    edges = []
    all_distances = []
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(site_coords[sites[i]], site_coords[sites[j]])
            all_distances.append(d)
            if d > 0:
                edges.append((d, i, j))
    if not edges:
        raise RuntimeError("no positive inter-site distances")
    edges.sort(key=lambda x: (x[0], x[1], x[2]))

    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return size[ra]
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        return size[ra]

    thresholds = {}
    max_component = 1
    idx = 0
    while idx < len(edges) and len(thresholds) < len(LCC_TARGETS):
        d = edges[idx][0]
        while idx < len(edges) and edges[idx][0] == d:
            _, i, j = edges[idx]
            max_component = max(max_component, union(i, j))
            idx += 1
        frac = max_component / n
        for target in LCC_TARGETS:
            key = f"lcc_{target:.2f}"
            if key not in thresholds and frac >= target:
                thresholds[key] = d
    if len(thresholds) != len(LCC_TARGETS):
        raise RuntimeError(f"could not resolve all LCC targets: {thresholds}")
    vals = [thresholds[f"lcc_{t:.2f}"] for t in LCC_TARGETS]
    distinct = sorted(set(vals))
    return {
        "node_count": n,
        "earth_radius_km": EARTH_RADIUS_KM,
        "targets": LCC_TARGETS,
        "thresholds_km": thresholds,
        "distinct_positive_thresholds_km": distinct,
        "distinct_positive_threshold_count": len(distinct),
        "pair_count": len(all_distances),
        "distance_km_min": min(all_distances),
        "distance_km_q25": percentile(all_distances, 0.25),
        "distance_km_median": statistics.median(all_distances),
        "distance_km_q75": percentile(all_distances, 0.75),
        "distance_km_max": max(all_distances),
    }


def main():
    result = {
        "schema": "eog.peneda_roedeer_replication_2.gate1_deployment_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "site_registry": {},
        "cycles": {},
        "structural_ladder": {},
        "response_firewall": response_firewall(),
    }
    try:
        alias = SITE_CERT["alias_rule"]
        if SITE_CERT["decision"] != "accept_response_independent_leading_zero_alias_as_physical_site_registry":
            raise RuntimeError("site registry certificate decision mismatch")
        if alias["regex"] != ALIAS_RE.pattern or alias["canonical_site_count"] != 64 or alias["coordinate_conflict_count"] != 0:
            raise RuntimeError("site registry certificate does not match frozen Gate1 alias rule")

        spec = CONTRACT["response_independent"]
        raw, final_url, content_type, content_disposition = gate0.get(
            spec["binary_url"], "text/csv,text/plain;q=0.9,*/*;q=0.1"
        )
        raw_sha = hashlib.sha256(raw).hexdigest()
        expected_sha = SITE_CERT["gate0"]["deployment_payload_sha256"]
        if raw_sha != expected_sha:
            raise RuntimeError(f"deployment SHA drift: {raw_sha} != {expected_sha}")
        header, rows, encoding, delimiter = decode_csv(raw)
        missing = [c for c in spec["required_essential_columns"] if c not in header]
        if missing:
            raise RuntimeError(f"deployment essential schema drift: missing={missing}; observed={header}")
        if len(rows) != 331:
            raise RuntimeError(f"deployment row drift: {len(rows)} != 331")

        canonical_coords = defaultdict(set)
        by_cycle_site = defaultdict(lambda: defaultdict(list))
        by_cycle_deployments = Counter()
        cycle_starts = defaultdict(list)
        cycle_ends = defaultdict(list)
        cycle_raw_durations = defaultdict(list)
        registry_rows = []

        for row in rows:
            site = canonical_site(row["locationName"])
            lat = float(str(row["latitude"]).strip())
            lon = float(str(row["longitude"]).strip())
            canonical_coords[site].add((lat, lon))
            start = gate0.parse_dt(row["start"])
            end = gate0.parse_dt(row["end"])
            if end <= start:
                raise RuntimeError(f"nonpositive deployment interval {row['deploymentID']}")
            year = start.year
            by_cycle_site[year][site].append((start, end))
            by_cycle_deployments[year] += 1
            cycle_starts[year].append(start)
            cycle_ends[year].append(end)
            cycle_raw_durations[year].append((end - start).total_seconds() / 86400.0)
            registry_rows.append({
                "deploymentID": str(row["deploymentID"]).strip(),
                "raw_locationName": str(row["locationName"]).strip(),
                "canonical_site": site,
                "latitude": lat,
                "longitude": lon,
                "start": str(row["start"]).strip(),
                "end": str(row["end"]).strip(),
                "cycle_start_year": year,
            })

        if len(canonical_coords) != 64:
            result["status"] = "stop_canonical_site_count_drift"
            result["reason"] = f"frozen alias rule now yields {len(canonical_coords)} sites instead of 64"
            return finish(result)
        conflicts = {s: sorted(v) for s, v in canonical_coords.items() if len(v) != 1}
        if conflicts:
            result["status"] = "stop_canonical_site_coordinate_conflict"
            result["reason"] = f"canonical sites no longer have exact invariant coordinates: {sorted(conflicts)[:10]}"
            return finish(result)
        site_coords = {s: next(iter(v)) for s, v in canonical_coords.items()}
        years = sorted(by_cycle_site)
        if years != EXPECTED_YEARS:
            result["status"] = "stop_six_cycle_start_years_not_reproduced"
            result["reason"] = f"observed deployment start-year cycles {years}, expected {EXPECTED_YEARS}"
            return finish(result)
        observed_counts = dict(sorted(by_cycle_deployments.items()))
        if observed_counts != EXPECTED_START_YEAR_COUNTS:
            result["status"] = "stop_response_independent_cycle_counts_drift"
            result["reason"] = f"start-year deployment counts {observed_counts} != frozen {EXPECTED_START_YEAR_COUNTS}"
            return finish(result)

        cycle_profiles = {}
        for year in EXPECTED_YEARS:
            site_intervals = by_cycle_site[year]
            active_days = {site: union_days(intervals) for site, intervals in site_intervals.items()}
            interval_counts = {site: len(intervals) for site, intervals in site_intervals.items()}
            vals = list(active_days.values())
            cycle_profiles[str(year)] = {
                "deployment_count": by_cycle_deployments[year],
                "canonical_site_count": len(site_intervals),
                "coverage_fraction_of_64": len(site_intervals) / 64.0,
                "sites_with_multiple_deployments": sum(v > 1 for v in interval_counts.values()),
                "max_deployments_per_site": max(interval_counts.values()),
                "earliest_start": min(cycle_starts[year]).isoformat(),
                "latest_start": max(cycle_starts[year]).isoformat(),
                "earliest_end": min(cycle_ends[year]).isoformat(),
                "latest_end": max(cycle_ends[year]).isoformat(),
                "active_union_days_min": min(vals),
                "active_union_days_q25": percentile(vals, 0.25),
                "active_union_days_median": statistics.median(vals),
                "active_union_days_q75": percentile(vals, 0.75),
                "active_union_days_max": max(vals),
                "raw_deployment_duration_days_median": statistics.median(cycle_raw_durations[year]),
                "site_active_days_fingerprint": fingerprint(sorted(
                    [{"site": s, "active_union_days": active_days[s], "deployment_count": interval_counts[s]} for s in active_days],
                    key=lambda x: x["site"],
                )),
            }

        ladder = structural_ladder(site_coords)
        if ladder["distinct_positive_threshold_count"] < 3:
            result["status"] = "stop_insufficient_structural_scale_diversity"
            result["reason"] = f"only {ladder['distinct_positive_threshold_count']} distinct positive LCC thresholds"
            result["structural_ladder"] = ladder
            return finish(result)

        result["site_registry"] = {
            "canonical_site_count": 64,
            "raw_location_name_count": len({r["raw_locationName"] for r in registry_rows}),
            "alias_regex": ALIAS_RE.pattern,
            "canonical_form": "L<int(numeric suffix)>",
            "coordinate_conflict_count": 0,
            "registry_fingerprint": fingerprint(sorted(
                [{"site": s, "latitude": site_coords[s][0], "longitude": site_coords[s][1]} for s in site_coords],
                key=lambda x: x["site"],
            )),
            "deployment_registry_fingerprint": fingerprint(sorted(registry_rows, key=lambda x: x["deploymentID"])),
            "deployment_payload_sha256": raw_sha,
            "deployment_payload_bytes": len(raw),
            "encoding": encoding,
            "delimiter": delimiter,
            "content_type": content_type,
            "content_disposition": content_disposition,
            "final_host": final_url.split("/")[2],
        }
        result["cycles"] = {
            "cycle_definition": "calendar year of response-independent deployment start timestamp",
            "cycle_years": EXPECTED_YEARS,
            "cycle_count": 6,
            "profiles": cycle_profiles,
            "eligibility_threshold_frozen_at_gate1": False,
            "calibration_heldout_split_frozen_at_gate1": False,
            "cross_cycle_propagation": False,
        }
        result["structural_ladder"] = ladder
        result["status"] = "gate1_pass_response_free_six_cycle_availability_and_structural_ladder"
        result["reason"] = "The frozen leading-zero alias exactly reproduced 64 invariant physical camera sites, deployment start years reproduced six 2015-2020 cycles, response-independent site-cycle effort was profiled without imposing an eligibility threshold, and the 64-site geometry produced at least three distinct positive structural scales while observations remained unopened."
        return finish(result)
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return finish(result, 1)


if __name__ == "__main__":
    sys.exit(main())
