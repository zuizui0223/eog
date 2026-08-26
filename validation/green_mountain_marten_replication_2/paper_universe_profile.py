from __future__ import annotations

import csv
import hashlib
import io
import json
import statistics
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "green_mountain_marten_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
META = json.loads((HERE / "gate0a_metadata_certificate.json").read_text())
GATE0B = json.loads((HERE / "gate0b_response_free_certificate.json").read_text())
OUT = BUILD / "paper_universe_profile.json"

VISIT_ALLOWED = {"pk_visitid", "fk_locationid", "fk_equipmentid", "visit_type", "visit_date", "visit_time"}
LOCATION_ALLOWED = {"pk_locationid", "location_type", "long_min", "long_max", "lat_min", "lat_max"}
FORBIDDEN_VISIT_COLUMNS = {"track_sign"}


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(o):
    return hashlib.sha256(canonical(o)).hexdigest()


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-GreenMountainMarten-PaperUniverse/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def get_bytes(url):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8", "User-Agent": "EOG-GreenMountainMarten-PaperUniverse/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def checksum_value(v):
    return str((v or {}).get("value") if isinstance(v, dict) else (v or "")).lower()


def parse_csv_projected(data: bytes, filename: str, allowed: set[str]):
    text = data.decode("utf-8-sig")
    try:
        delim = csv.Sniffer().sniff(text[:65536], delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    if not header:
        raise RuntimeError(f"{filename}: missing header")
    rows = []
    for row in reader:
        # Projection happens immediately. Biological columns such as track_sign are never read by name/value.
        rows.append({k: row.get(k) for k in allowed})
    return header, rows


def load_allowed_files():
    item_id = CONTRACT["sciencebase_candidate"]["item_id"]
    item = get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
    by_name = {f.get("name"): f for f in item.get("files") or [] if isinstance(f, dict) and f.get("name")}
    out = {}
    for name, allowed in (("locations.csv", LOCATION_ALLOWED), ("visits.csv", VISIT_ALLOWED)):
        expected = META["response_independent_files"][name]
        f = by_name.get(name)
        if not f:
            raise RuntimeError(f"{name}: missing metadata")
        if int(f.get("size") or -1) != int(expected["size"]):
            raise RuntimeError(f"{name}: metadata size mismatch")
        if expected["md5"] not in checksum_value(f.get("checksum")):
            raise RuntimeError(f"{name}: metadata MD5 mismatch")
        data = get_bytes(f["downloadUri"])
        if len(data) != int(expected["size"]) or hashlib.md5(data).hexdigest() != expected["md5"]:
            raise RuntimeError(f"{name}: exact payload identity mismatch")
        header, rows = parse_csv_projected(data, name, allowed)
        out[name] = {"header": header, "rows": rows, "bytes": len(data), "md5": expected["md5"]}
    return out


def d(s):
    return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()


def winter_label(day: date, convention: str):
    # Only December-April belongs to a paper winter season.
    if day.month not in {12, 1, 2, 3, 4}:
        return None
    if convention == "end_year":
        return day.year + 1 if day.month == 12 else day.year
    if convention == "start_year":
        return day.year if day.month == 12 else day.year - 1
    raise ValueError(convention)


def pair_set_pull(visits):
    by_key = defaultdict(list)
    for r in visits:
        key = (str(r["fk_locationid"] or "").strip(), str(r["fk_equipmentid"] or "").strip())
        if not all(key):
            continue
        by_key[key].append(r)
    assignments = []
    unpaired_sets = []
    for key, rows in by_key.items():
        rows = sorted(rows, key=lambda r: (d(r["visit_date"]), str(r["visit_time"] or ""), int(r["pk_visitid"])))
        for i, r in enumerate(rows):
            if str(r["visit_type"] or "").strip().lower() != "set":
                continue
            pull = None
            for q in rows[i + 1:]:
                typ = str(q["visit_type"] or "").strip().lower()
                if typ == "set":
                    break
                if typ == "pull":
                    pull = q
                    break
            if pull is None:
                unpaired_sets.append({"location_id": key[0], "equipment_id": key[1], "set_date": r["visit_date"]})
                continue
            sd, pd = d(r["visit_date"]), d(pull["visit_date"])
            assignments.append({
                "location_id": key[0],
                "equipment_id": key[1],
                "set_visit_id": int(r["pk_visitid"]),
                "pull_visit_id": int(pull["pk_visitid"]),
                "set_date": sd,
                "pull_date": pd,
                "duration_days": (pd - sd).days,
            })
    return assignments, unpaired_sets


def summarize_convention(assignments, convention):
    selected = []
    for a in assignments:
        lab = winter_label(a["set_date"], convention)
        if lab in {2019, 2020, 2021}:
            b = dict(a); b["season_label"] = lab; selected.append(b)
    by_season = Counter(a["season_label"] for a in selected)
    by_set_date = Counter(a["set_date"].isoformat() for a in selected)
    durations = [a["duration_days"] for a in selected]
    exact15 = sum(x == 15 for x in durations)
    within12_18 = sum(12 <= x <= 18 for x in durations)
    return {
        "convention": convention,
        "assignment_count": len(selected),
        "assignments_by_season": {str(k): by_season.get(k, 0) for k in (2019, 2020, 2021)},
        "unique_locations": len({a["location_id"] for a in selected}),
        "unique_equipment": len({a["equipment_id"] for a in selected}),
        "unique_set_dates": len(by_set_date),
        "set_date_group_size_counts": dict(sorted(Counter(by_set_date.values()).items())),
        "largest_set_date_groups": sorted(([k, v] for k, v in by_set_date.items()), key=lambda x: (-x[1], x[0]))[:20],
        "duration_days_min": min(durations) if durations else None,
        "duration_days_median": statistics.median(durations) if durations else None,
        "duration_days_max": max(durations) if durations else None,
        "duration_exactly_15_count": exact15,
        "duration_12_to_18_count": within12_18,
        "location_equipment_pair_count": len({(a["location_id"], a["equipment_id"]) for a in selected}),
    }


def main():
    result = {
        "schema": "eog.green_mountain_marten_replication_2.paper_universe_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "profile": {},
        "blacklist": {
            "track_sign_present_in_physical_visits_header": None,
            "track_sign_value_accessed_by_this_script": False,
            "taxa_mapping_opened": False,
        },
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        loaded = load_allowed_files()
        lh, locations = loaded["locations.csv"]["header"], loaded["locations.csv"]["rows"]
        vh, visits = loaded["visits.csv"]["header"], loaded["visits.csv"]["rows"]
        result["blacklist"]["track_sign_present_in_physical_visits_header"] = "track_sign" in vh
        if not FORBIDDEN_VISIT_COLUMNS.issubset(set(vh)):
            raise RuntimeError("expected blacklisted visit field is absent; source schema changed")

        visit_types = Counter(str(r["visit_type"] or "").strip().lower() for r in visits)
        assignments, unpaired = pair_set_pull(visits)
        loc_bbox = [r for r in locations if all(str(r.get(c) or "").strip() for c in ("long_min", "long_max", "lat_min", "lat_max"))]
        centers = set()
        for r in loc_bbox:
            centers.add((round((float(r["lat_min"])+float(r["lat_max"]))/2, 8), round((float(r["long_min"])+float(r["long_max"]))/2, 8)))

        result["profile"] = {
            "paper_required": {
                "cameras": 238,
                "units": 40,
                "units_by_field_season": [15, 19, 6],
                "nominal_cameras_per_unit": 6,
                "survey_days": 15,
            },
            "locations": {
                "rows": len(locations),
                "unique_location_ids": len({str(r["pk_locationid"] or "").strip() for r in locations}),
                "bbox_rows": len(loc_bbox),
                "unique_bbox_centers": len(centers),
                "explicit_unit_id_column_present": any("unit" in str(c).lower() for c in lh),
            },
            "visits": {
                "rows": len(visits),
                "visit_type_counts": dict(sorted(visit_types.items())),
                "unique_locations": len({str(r["fk_locationid"] or "").strip() for r in visits}),
                "unique_equipment": len({str(r["fk_equipmentid"] or "").strip() for r in visits}),
                "paired_set_pull_assignments_all_years": len(assignments),
                "unpaired_set_count": len(unpaired),
                "explicit_unit_id_column_present": any("unit" in str(c).lower() for c in vh),
            },
            "winter_conventions": [summarize_convention(assignments, "end_year"), summarize_convention(assignments, "start_year")],
            "response_independent_mapping_warning": "No paper sample-unit identifier is exposed in the allowed locations/visits schema; any 40-unit mapping would need to emerge uniquely from survey timing/geometry rather than from a declared source key.",
        }
        result["status"] = "paper_universe_response_free_profile_complete"
        result["reason"] = "Response-independent deployment structure profiled under both natural winter-year conventions; no annotations/taxa/media response was opened and track_sign values were not accessed"
        result["fingerprint"] = fp({k: v for k,v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k,v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
