from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "peneda_roedeer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "site_scope_diagnostic.json"
L_RE = re.compile(r"^L0*([0-9]+)$")


def fp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Peneda-site-scope-diagnostic/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def year(s):
    return datetime.fromisoformat(str(s).strip().replace("Z", "+00:00")).year


def main():
    raw = get_bytes(CONTRACT["response_independent"]["binary_url"])
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    if len(rows) != 331:
        raise RuntimeError(f"deployment rows {len(rows)} != 331")

    by_coord = defaultdict(list)
    by_label = defaultdict(list)
    l_groups = defaultdict(list)
    non_l = []
    prefix_counts = Counter()

    for r in rows:
        label = str(r["locationName"]).strip()
        coord = (float(r["latitude"]), float(r["longitude"]))
        rec = {
            "deploymentID": str(r["deploymentID"]).strip(),
            "locationID": str(r["locationID"]).strip(),
            "locationName": label,
            "latitude": coord[0],
            "longitude": coord[1],
            "start_year": year(r["start"]),
        }
        by_coord[coord].append(rec)
        by_label[label].append(rec)
        m = L_RE.fullmatch(label)
        if m:
            l_groups[f"L{int(m.group(1))}"].append(rec)
        else:
            non_l.append(rec)
            m2 = re.match(r"^([A-Za-z]+)", label)
            prefix_counts[(m2.group(1) if m2 else "<other>")] += 1

    l_coord_map = defaultdict(set)
    for canonical, rs in l_groups.items():
        for r in rs:
            l_coord_map[canonical].add((r["latitude"], r["longitude"]))

    non_l_by_label = []
    for label, rs in sorted(by_label.items()):
        if L_RE.fullmatch(label):
            continue
        coords = sorted({(r["latitude"], r["longitude"]) for r in rs})
        coord_matches = []
        for coord in coords:
            matching_l = sorted(k for k, vals in l_coord_map.items() if coord in vals)
            coord_matches.append({"coordinate": list(coord), "matching_L_canonical_sites": matching_l})
        non_l_by_label.append({
            "label": label,
            "deployment_count": len(rs),
            "years": sorted({r["start_year"] for r in rs}),
            "coordinates": [list(c) for c in coords],
            "coordinate_variant_count": len(coords),
            "coordinate_matches_to_L_groups": coord_matches,
        })

    coord_profiles = []
    for coord, rs in sorted(by_coord.items()):
        labels = sorted({r["locationName"] for r in rs})
        coord_profiles.append({
            "latitude": coord[0],
            "longitude": coord[1],
            "deployment_count": len(rs),
            "raw_labels": labels,
            "years": sorted({r["start_year"] for r in rs}),
            "has_L_label": any(L_RE.fullmatch(x) for x in labels),
            "has_non_L_label": any(not L_RE.fullmatch(x) for x in labels),
        })

    result = {
        "schema": "eog.peneda_roedeer_replication_2.site_scope_diagnostic.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "deployment_rows": len(rows),
        "deployment_sha256": hashlib.sha256(raw).hexdigest(),
        "published_grid_cameras": CONTRACT["paper"]["published_grid_cameras"],
        "unique_locationName": len(by_label),
        "unique_exact_coordinates": len(by_coord),
        "L_pattern": L_RE.pattern,
        "L_canonical_group_count": len(l_groups),
        "L_coordinate_conflict_count": sum(len(v) != 1 for v in l_coord_map.values()),
        "non_L_row_count": len(non_l),
        "non_L_label_count": len(non_l_by_label),
        "non_L_prefix_row_counts": dict(sorted(prefix_counts.items())),
        "coordinates_with_L_and_non_L_labels": sum(x["has_L_label"] and x["has_non_L_label"] for x in coord_profiles),
        "coordinates_without_any_L_label": sum(not x["has_L_label"] for x in coord_profiles),
        "non_L_labels": non_l_by_label,
        "coordinate_profiles": coord_profiles,
        "coordinate_registry_fingerprint": fp(coord_profiles),
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    result["status"] = (
        "exact_coordinate_registry_matches_published_64"
        if len(by_coord) == int(CONTRACT["paper"]["published_grid_cameras"])
        else "exact_coordinate_registry_does_not_match_published_64"
    )
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
