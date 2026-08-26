from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "peneda_roedeer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "location_alias_diagnostic.json"

PATTERN = re.compile(r"^L0*([0-9]+)$")


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Peneda-alias-diagnostic/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def parse_dt(s: str):
    return datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))


def main():
    raw = get_bytes(CONTRACT["response_independent"]["binary_url"])
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
    by_label = defaultdict(list)
    for r in rows:
        label = str(r["locationName"]).strip()
        m = PATTERN.fullmatch(label)
        norm = f"L{int(m.group(1))}" if m else None
        by_label[label].append({
            "deploymentID": str(r["deploymentID"]).strip(),
            "coord": (float(r["latitude"]), float(r["longitude"])),
            "year": parse_dt(r["start"]).year,
            "normalized": norm,
        })

    label_profiles = []
    all_match_regex = True
    normalized_groups = defaultdict(list)
    for label, rs in sorted(by_label.items()):
        norms = {x["normalized"] for x in rs}
        if None in norms or len(norms) != 1:
            all_match_regex = False
            norm = None
        else:
            norm = next(iter(norms))
            normalized_groups[norm].append(label)
        coords = sorted({x["coord"] for x in rs})
        label_profiles.append({
            "label": label,
            "normalized": norm,
            "deployment_count": len(rs),
            "years": sorted({x["year"] for x in rs}),
            "coordinates": [[a, b] for a, b in coords],
            "coordinate_variant_count": len(coords),
        })

    group_profiles = []
    coordinate_conflicts = []
    for norm, labels in sorted(normalized_groups.items(), key=lambda kv: int(kv[0][1:])):
        coords = set()
        years = set()
        dep_count = 0
        for label in labels:
            for x in by_label[label]:
                coords.add(x["coord"])
                years.add(x["year"])
                dep_count += 1
        gp = {
            "canonical_label": norm,
            "source_labels": sorted(labels),
            "source_label_count": len(labels),
            "deployment_count": dep_count,
            "years": sorted(years),
            "coordinates": [[a, b] for a, b in sorted(coords)],
            "coordinate_variant_count": len(coords),
        }
        group_profiles.append(gp)
        if len(coords) != 1:
            coordinate_conflicts.append(gp)

    multi_label_groups = [g for g in group_profiles if g["source_label_count"] > 1]
    canonical_count = len(group_profiles)
    alias_rule_pass = all_match_regex and not coordinate_conflicts and canonical_count == 64

    result = {
        "schema": "eog.peneda_roedeer_replication_2.location_alias_diagnostic.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "alias_rule_pass_exactly_64_canonical_sites" if alias_rule_pass else "alias_rule_not_justified",
        "prospective_rule": {
            "input_regex": "^L0*([0-9]+)$",
            "canonicalization": "L<int(captured numeric suffix)>",
            "accept_only_if_all_labels_match_regex": True,
            "accept_only_if_each_canonical_group_has_one_exact_coordinate": True,
            "accept_only_if_canonical_site_count_equals_published_64": True,
            "coordinate_tolerance": 0.0,
            "post_diagnostic_manual_aliases_allowed": False,
        },
        "deployment_rows": len(rows),
        "deployment_sha256": hashlib.sha256(raw).hexdigest(),
        "source_locationName_count": len(by_label),
        "all_labels_match_regex": all_match_regex,
        "canonical_site_count": canonical_count,
        "coordinate_conflict_count": len(coordinate_conflicts),
        "multi_label_group_count": len(multi_label_groups),
        "multi_label_groups": multi_label_groups,
        "coordinate_conflicts": coordinate_conflicts,
        "label_profiles": label_profiles,
        "canonical_registry_fingerprint": fp(group_profiles),
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    result["fingerprint"] = fp(result)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
