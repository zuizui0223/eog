from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "fukushima_wild_boar_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_response_free.json"
BASE = "https://db.cger.nies.go.jp/JaLTER/metacat/metacat"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def base_result():
    return {
        "schema": "eog.fukushima_wild_boar_replication_2.gate0_response_free.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "source_files": {},
        "registry": {},
        "temporal_availability": {},
        "structural_ladder": {},
        "evacuation": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 EOG-response-free/1.0", "Accept": "text/plain,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def transport_candidates(data_id: str):
    q = urllib.parse.urlencode({"action": "read", "docid": data_id})
    qxml = urllib.parse.urlencode({"action": "read", "docid": data_id, "qformat": "xml"})
    qjalter = urllib.parse.urlencode({"action": "read", "docid": data_id, "qformat": "jalter-en"})
    return [f"{BASE}?{q}", f"{BASE}?{qxml}", f"{BASE}?{qjalter}"]


def fetch_allowed_file(spec: dict):
    errors = []
    expected = spec["expected_header"]
    for url in transport_candidates(spec["data_id"]):
        try:
            raw, final_url, ctype = get_bytes(url)
            if b"<html" in raw[:1000].lower() or b"<!doctype" in raw[:1000].lower():
                errors.append(f"{url}: html_instead_of_data bytes={len(raw)}")
                continue
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                errors.append(f"{url}: non_utf8 {exc}")
                continue
            first = text.splitlines()[0] if text.splitlines() else ""
            cols = first.rstrip("\r\n").split("\t")
            if cols != expected:
                errors.append(f"{url}: header_mismatch {cols!r}")
                continue
            return raw, text, {
                "data_id": spec["data_id"],
                "filename": spec["filename"],
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "content_type": ctype,
                "transport_final_host": urllib.parse.urlparse(final_url).netloc,
                "transport_final_path": urllib.parse.urlparse(final_url).path,
                "header": cols,
            }
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    raise RuntimeError("all frozen public transports failed for response-independent file " + spec["filename"] + " | " + " | ".join(errors))


def parse_tsv(text: str):
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    return list(reader)


def parse_date_time(d: str, t: str, field: str):
    ds = (d or "").strip()
    ts = (t or "").strip()
    if not ds:
        raise RuntimeError(f"missing {field} date")
    # Freeze a small response-independent parser grammar. Seconds are optional.
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"]
    combined = f"{ds} {ts or '00:00'}"
    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise RuntimeError(f"unsupported {field} datetime token: {combined!r}")


def halfyear_bounds(label: str):
    year = int(label[:4])
    half = label[-2:]
    if half == "H1":
        start = datetime(year, 1, 1, tzinfo=timezone.utc)
        end = datetime(year, 7, 1, tzinfo=timezone.utc)
    elif half == "H2":
        start = datetime(year, 7, 1, tzinfo=timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        raise RuntimeError(label)
    return start, end


def union_duration_days(intervals):
    if not intervals:
        return 0.0
    xs = sorted(intervals)
    total = 0.0
    cur_s, cur_e = xs[0]
    for s, e in xs[1:]:
        if s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            total += (cur_e - cur_s).total_seconds() / 86400.0
            cur_s, cur_e = s, e
    total += (cur_e - cur_s).total_seconds() / 86400.0
    return total


def haversine_km(a, b):
    r = float(CONTRACT["geometry_design"]["earth_radius_km"])
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def lcc_fraction(n, edges):
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
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    for i, j in edges:
        union(i, j)
    counts = defaultdict(int)
    for i in range(n):
        counts[find(i)] += 1
    return max(counts.values()) / n


def structural_ladder(coords_sorted):
    pairs = []
    n = len(coords_sorted)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(coords_sorted[i][1], coords_sorted[j][1])
            if d > 0:
                pairs.append((d, i, j))
    if not pairs:
        raise RuntimeError("no positive pairwise distances")
    pairs.sort()
    unique = sorted({d for d, _, _ in pairs})
    out = []
    for target in CONTRACT["geometry_design"]["lcc_targets"]:
        chosen = None
        for threshold in unique:
            edges = [(i, j) for d, i, j in pairs if d <= threshold]
            frac = lcc_fraction(n, edges)
            if frac >= float(target):
                chosen = {"target": target, "threshold_km": threshold, "lcc_fraction": frac}
                break
        if chosen is None:
            raise RuntimeError(f"no threshold reaches LCC target {target}")
        out.append(chosen)
    return out


def write(result):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = base_result()
    try:
        occ_raw, occ_text, occ_meta = fetch_allowed_file(CONTRACT["response_independent_files"]["occasion"])
        eva_raw, eva_text, eva_meta = fetch_allowed_file(CONTRACT["response_independent_files"]["evacuation"])
        result["source_files"] = {"occasion": occ_meta, "evacuation": eva_meta}
        occ_rows = parse_tsv(occ_text)
        eva_rows = parse_tsv(eva_text)
        result["source_files"]["occasion"]["row_count"] = len(occ_rows)
        result["source_files"]["evacuation"]["row_count"] = len(eva_rows)

        # Registry and stable coordinates.
        by_site_coords = defaultdict(set)
        site_intervals = defaultdict(list)
        occasion_ids = set()
        invalid_abort_tokens = set()
        for row in occ_rows:
            site = (row.get("locationID") or "").strip()
            occasion = (row.get("occasionID") or "").strip()
            if not site or not occasion:
                raise RuntimeError("blank locationID or occasionID in occasion table")
            key = (site, occasion)
            if key in occasion_ids:
                raise RuntimeError(f"duplicate site×occasion key: {key}")
            occasion_ids.add(key)
            try:
                lat = float((row.get("decimalLatitude") or "").strip())
                lon = float((row.get("decimalLongitude") or "").strip())
            except ValueError as exc:
                raise RuntimeError(f"invalid coordinate at {key}: {exc}")
            by_site_coords[site].add((lat, lon))
            s = parse_date_time(row.get("startDate"), row.get("startTime"), "start")
            e = parse_date_time(row.get("endDate"), row.get("endTime"), "end")
            if e <= s:
                raise RuntimeError(f"nonpositive occasion interval at {key}: {s}..{e}")
            site_intervals[site].append((s, e))
            abort = (row.get("Abort") or "").strip()
            if abort not in {"0", "1", ""}:
                invalid_abort_tokens.add(abort)
        if invalid_abort_tokens:
            raise RuntimeError(f"unexpected Abort tokens: {sorted(invalid_abort_tokens)}")
        site_count = len(by_site_coords)
        if site_count != int(CONTRACT["source"]["published_site_count"]):
            result["status"] = "stop_published_site_registry_not_reproduced"
            result["reason"] = f"occasion table has {site_count} unique sites, expected {CONTRACT['source']['published_site_count']}"
            write(result)
            return 0
        unstable = {s: sorted(v) for s, v in by_site_coords.items() if len(v) != 1}
        if unstable:
            result["status"] = "stop_site_coordinates_not_stable"
            result["reason"] = f"{len(unstable)} site IDs have multiple coordinate pairs"
            result["registry"]["unstable_site_coordinate_count"] = len(unstable)
            write(result)
            return 0
        coords_sorted = sorted((s, next(iter(v))) for s, v in by_site_coords.items())
        result["registry"] = {
            "site_count": site_count,
            "occasion_row_count": len(occ_rows),
            "coordinate_pair_count": len(coords_sorted),
            "registry_fingerprint": fp([{"locationID": s, "lat": xy[0], "lon": xy[1]} for s, xy in coords_sorted]),
            "latitude_range": [min(xy[0] for _, xy in coords_sorted), max(xy[0] for _, xy in coords_sorted)],
            "longitude_range": [min(xy[1] for _, xy in coords_sorted), max(xy[1] for _, xy in coords_sorted)],
        }

        # Frozen half-year availability from unioned active intervals.
        min_days = float(CONTRACT["temporal_design"]["eligibility_min_active_camera_days"])
        period_summary = []
        eligible_keys = []
        for label in CONTRACT["temporal_design"]["periods"]:
            ps, pe = halfyear_bounds(label)
            active = {}
            for site in sorted(site_intervals):
                clipped = []
                for s, e in site_intervals[site]:
                    cs, ce = max(s, ps), min(e, pe)
                    if ce > cs:
                        clipped.append((cs, ce))
                days = union_duration_days(clipped)
                active[site] = days
                if days >= min_days:
                    eligible_keys.append((site, label))
            eligible_sites = [s for s, d in active.items() if d >= min_days]
            period_summary.append({
                "period": label,
                "eligible_site_count": len(eligible_sites),
                "active_days_min": min(active.values()) if active else 0.0,
                "active_days_max": max(active.values()) if active else 0.0,
            })
        min_heldout = int(CONTRACT["temporal_design"]["minimum_eligible_sites_each_heldout_period"])
        bad_heldout = [p for p in period_summary if p["period"] in CONTRACT["temporal_design"]["heldout_periods"] and p["eligible_site_count"] < min_heldout]
        result["temporal_availability"] = {
            "eligibility_min_active_camera_days": min_days,
            "period_summary": period_summary,
            "eligible_site_halfyear_count": len(eligible_keys),
            "eligible_registry_fingerprint": fp([{"locationID": s, "period": p} for s, p in sorted(eligible_keys)]),
            "calibration_periods": CONTRACT["temporal_design"]["calibration_periods"],
            "heldout_periods": CONTRACT["temporal_design"]["heldout_periods"],
        }
        if bad_heldout:
            result["status"] = "stop_heldout_effort_non_estimable_response_independently"
            result["reason"] = f"heldout periods below frozen {min_heldout}-site availability floor: {bad_heldout}"
            write(result)
            return 0

        ladder = structural_ladder(coords_sorted)
        distinct = sorted({round(x["threshold_km"], 12) for x in ladder if x["threshold_km"] > 0})
        result["structural_ladder"] = {
            "scales": ladder,
            "distinct_positive_threshold_count": len(distinct),
            "fingerprint": fp(ladder),
        }
        if len(distinct) < int(CONTRACT["geometry_design"]["minimum_distinct_positive_thresholds"]):
            result["status"] = "stop_insufficient_response_blind_structural_scales"
            result["reason"] = f"only {len(distinct)} distinct positive thresholds"
            write(result)
            return 0

        # Evacuation file is context only; verify site keys and public token grammar.
        eva_sites = set()
        categories = set()
        designated_missing = 0
        for row in eva_rows:
            site = (row.get("locationID") or "").strip()
            if not site:
                raise RuntimeError("blank locationID in evacuation table")
            eva_sites.add(site)
            cat = (row.get("evacuationCategory") or "").strip()
            categories.add(cat)
            d = (row.get("designatedDate") or "").strip()
            if not d or d.upper() == "NA":
                designated_missing += 1
        if not eva_sites.issubset(set(by_site_coords)):
            result["status"] = "stop_evacuation_registry_outside_occasion_registry"
            result["reason"] = "evacuation table contains site IDs absent from occasion registry"
            write(result)
            return 0
        result["evacuation"] = {
            "row_count": len(eva_rows),
            "site_count": len(eva_sites),
            "category_tokens": sorted(categories),
            "missing_designated_date_rows": designated_missing,
            "fingerprint": fp(sorted((row.get("locationID"), row.get("evacuationCategory"), row.get("designatedDate")) for row in eva_rows)),
        }

        # Raw response-independent bytes are not persisted.
        result["status"] = "gate0_pass_response_free_registry_effort_and_structural_scales"
        result["reason"] = "Occasion and evacuation tables reproduce the published response-independent registry, effort windows and >=3 structural scales; detection response remained completely unopened"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
