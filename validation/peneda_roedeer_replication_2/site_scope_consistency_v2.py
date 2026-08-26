from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "peneda_roedeer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "site_scope_consistency_v2.json"
L_RE = re.compile(r"^L0*([0-9]+)$")


def fp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Peneda-site-scope-consistency-v2/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def main():
    raw = get_bytes(CONTRACT["response_independent"]["binary_url"])
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
    if len(rows) != 331:
        raise RuntimeError(f"deployment rows {len(rows)} != 331")

    l_rows = []
    non_l_rows = []
    l_coords = set()
    non_l_coords = set()
    all_coords = set()
    canonical_coords = defaultdict(set)
    canonical_raw_labels = defaultdict(set)
    non_l_labels = defaultdict(lambda: {"rows": 0, "coords": set()})

    for r in rows:
        label = str(r["locationName"] or "").strip()
        coord = (float(r["latitude"]), float(r["longitude"]))
        all_coords.add(coord)
        m = L_RE.fullmatch(label)
        if m:
            canonical = f"L{int(m.group(1))}"
            l_rows.append((label, coord))
            l_coords.add(coord)
            canonical_coords[canonical].add(coord)
            canonical_raw_labels[canonical].add(label)
        else:
            non_l_rows.append((label, coord))
            non_l_coords.add(coord)
            non_l_labels[label]["rows"] += 1
            non_l_labels[label]["coords"].add(coord)

    overlap = l_coords & non_l_coords
    algebra_expected = len(l_coords) + len(non_l_coords) - len(overlap)
    if len(l_rows) + len(non_l_rows) != 331:
        raise RuntimeError("row-count algebra failure")
    if len(all_coords) != algebra_expected:
        raise RuntimeError(
            f"coordinate-set algebra failure: all={len(all_coords)} != L={len(l_coords)} + nonL={len(non_l_coords)} - overlap={len(overlap)}"
        )

    multi_coord_groups = []
    for canonical in sorted(canonical_coords, key=lambda x: int(x[1:])):
        coords = sorted(canonical_coords[canonical])
        if len(coords) > 1:
            multi_coord_groups.append({
                "canonical_site": canonical,
                "raw_labels": sorted(canonical_raw_labels[canonical]),
                "coordinate_count": len(coords),
                "coordinates": [list(c) for c in coords],
            })

    result = {
        "schema": "eog.peneda_roedeer_replication_2.site_scope_consistency.v2",
        "attempt_id": CONTRACT["attempt_id"],
        "deployment_rows": len(rows),
        "deployment_sha256": hashlib.sha256(raw).hexdigest(),
        "L_pattern": L_RE.pattern,
        "L_row_count": len(l_rows),
        "non_L_row_count": len(non_l_rows),
        "L_plus_nonL_rows": len(l_rows) + len(non_l_rows),
        "unique_all_exact_coordinates": len(all_coords),
        "unique_L_exact_coordinates": len(l_coords),
        "unique_non_L_exact_coordinates": len(non_l_coords),
        "L_nonL_coordinate_overlap_count": len(overlap),
        "coordinate_algebra_expected_all": algebra_expected,
        "coordinate_algebra_pass": len(all_coords) == algebra_expected,
        "canonical_L_group_count": len(canonical_coords),
        "canonical_L_groups_with_multiple_coordinates": len(multi_coord_groups),
        "canonical_L_multi_coordinate_groups": multi_coord_groups,
        "non_L_labels": [
            {
                "label": label,
                "row_count": info["rows"],
                "coordinate_count": len(info["coords"]),
                "coordinates": [list(c) for c in sorted(info["coords"])],
                "overlaps_any_L_coordinate": any(c in l_coords for c in info["coords"]),
            }
            for label, info in sorted(non_l_labels.items())
        ],
        "published_grid_cameras": CONTRACT["paper"]["published_grid_cameras"],
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    result["status"] = "scope_consistency_pass"
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
