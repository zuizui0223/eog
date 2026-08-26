from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "peneda_roedeer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
C = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "grid_cell_identity_documentation_gate.json"
GRID_RE = re.compile(r"^([A-H])([1-8])_(2015|2016|2017|2018|2019|2020)$")


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(x):
    return hashlib.sha256(canon(x)).hexdigest()


def get(url, accept="*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Peneda-grid-identity-doc-gate/1.0", "Accept": accept})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def local(tag):
    return tag.split("}", 1)[-1]


def compact_text(elem):
    return " ".join("".join(elem.itertext()).split())


def main():
    result = {
        "schema": "eog.peneda_roedeer_replication_2.grid_cell_identity_documentation_gate.v1",
        "attempt_id": C["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "grid_rule": {},
        "documentation": {},
        "response_firewall": dict(C["response_firewall"]),
    }
    try:
        dep_raw, _, _ = get(C["response_independent"]["binary_url"], "text/csv,text/plain;q=0.9,*/*;q=0.1")
        if hashlib.sha256(dep_raw).hexdigest() != "c80ad16f362a46c9ea67d8d19b5da1cb5967929ca7dd9ab9197d6cdb2305cf74":
            raise RuntimeError("deployment payload SHA drift")
        rows = list(csv.DictReader(io.StringIO(dep_raw.decode("utf-8-sig")), delimiter=";"))
        if len(rows) != 331:
            raise RuntimeError(f"deployment row drift: {len(rows)} != 331")

        unmatched = []
        base_rows = defaultdict(list)
        year_counts = Counter()
        base_year_pairs = Counter()
        for r in rows:
            name = str(r["locationName"] or "").strip()
            m = GRID_RE.fullmatch(name)
            if not m:
                unmatched.append(name)
                continue
            base = f"{m.group(1)}{int(m.group(2))}"
            yr = int(m.group(3))
            coord = (float(r["latitude"]), float(r["longitude"]))
            base_rows[base].append({"year": yr, "coord": coord, "deploymentID": str(r["deploymentID"]).strip(), "raw": name})
            year_counts[yr] += 1
            base_year_pairs[(base, yr)] += 1

        expected_bases = [f"{letter}{n}" for letter in "ABCDEFGH" for n in range(1, 9)]
        observed_bases = sorted(base_rows, key=lambda x: (x[0], int(x[1:])))
        duplicate_base_years = [
            {"base": b, "year": y, "count": n}
            for (b, y), n in sorted(base_year_pairs.items()) if n > 1
        ]
        coordinate_profiles = []
        for b in expected_bases:
            rs = base_rows.get(b, [])
            coords = sorted({x["coord"] for x in rs})
            coordinate_profiles.append({
                "base_site": b,
                "deployment_count": len(rs),
                "years": sorted({x["year"] for x in rs}),
                "exact_coordinate_count": len(coords),
                "coordinates": [list(x) for x in coords],
            })

        grid_rule_pass = (
            not unmatched
            and observed_bases == expected_bases
            and not duplicate_base_years
            and dict(sorted(year_counts.items())) == {2015: 58, 2016: 61, 2017: 55, 2018: 53, 2019: 57, 2020: 47}
        )
        result["grid_rule"] = {
            "regex": GRID_RE.pattern,
            "canonical_base_rule": "<letter A-H><integer 1-8>; remove only the prospectively matched _YYYY suffix",
            "deployment_rows": len(rows),
            "matched_rows": len(rows) - len(unmatched),
            "unmatched_rows": len(unmatched),
            "unmatched_labels": sorted(set(unmatched)),
            "canonical_base_site_count": len(base_rows),
            "expected_base_site_count": 64,
            "expected_base_sites": expected_bases,
            "observed_base_sites": observed_bases,
            "duplicate_base_year_count": len(duplicate_base_years),
            "duplicate_base_years": duplicate_base_years,
            "start_year_counts": dict(sorted(year_counts.items())),
            "coordinate_mode": "cycle_specific_coordinates_by_base_site; no cross-cycle coordinate averaging",
            "base_sites_with_coordinate_changes": sum(x["exact_coordinate_count"] > 1 for x in coordinate_profiles),
            "max_exact_coordinates_per_base_site": max(x["exact_coordinate_count"] for x in coordinate_profiles),
            "coordinate_profiles": coordinate_profiles,
            "grid_registry_fingerprint": fp(coordinate_profiles),
            "pass": grid_rule_pass,
        }

        xml_raw, xml_final, xml_ctype = get(C["paper"]["article_xml_url"], "application/xml,text/xml;q=0.9,*/*;q=0.1")
        root = ET.fromstring(xml_raw)
        evidence = []
        terms = ("64", "grid", "camera", "location", "site", "sampling", "500 m", "500m", "8 x 8", "8×8")
        for elem in root.iter():
            if local(elem.tag) not in {"p", "title", "caption", "td", "th", "named-content"}:
                continue
            text = compact_text(elem)
            low = text.lower()
            score = sum(t.lower() in low for t in terms)
            if score >= 3 and ("64" in low or "grid" in low):
                evidence.append({
                    "tag": local(elem.tag),
                    "text": text[:1800],
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                })
        # Also capture any exact mentions of locationName or example grid labels if present.
        targeted = []
        for elem in root.iter():
            text = compact_text(elem)
            low = text.lower()
            if not text:
                continue
            if "locationname" in low or re.search(r"\bA1(?:_20\d\d)?\b", text) or "8 x 8" in low or "8×8" in text:
                targeted.append({
                    "tag": local(elem.tag),
                    "text": text[:1800],
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                })
        # Deduplicate by text hash.
        def dedup(items):
            out = []
            seen = set()
            for x in items:
                if x["sha256"] not in seen:
                    out.append(x); seen.add(x["sha256"])
            return out
        evidence = dedup(evidence)[:20]
        targeted = dedup(targeted)[:20]

        full_text = " ".join(compact_text(e) for e in root.iter() if local(e.tag) in {"p", "title", "caption", "td", "th"})
        full_low = full_text.lower()
        doc_has_64_and_grid = "64" in full_low and "grid" in full_low
        doc_has_camera_and_location = "camera" in full_low and ("location" in full_low or "site" in full_low)
        result["documentation"] = {
            "article_xml_url": C["paper"]["article_xml_url"],
            "final_url": xml_final,
            "content_type": xml_ctype,
            "xml_bytes": len(xml_raw),
            "xml_sha256": hashlib.sha256(xml_raw).hexdigest(),
            "has_64_and_grid": doc_has_64_and_grid,
            "has_camera_and_location_or_site": doc_has_camera_and_location,
            "high_relevance_fragments": evidence,
            "targeted_fragments": targeted,
        }

        if not grid_rule_pass:
            result["status"] = "stop_grid_cell_year_rule_does_not_reproduce_deployment_registry"
            result["reason"] = "The prospectively tested A-H × 1-8 plus year suffix rule did not uniquely reproduce all 331 deployment rows and 64 base cells."
        elif not (doc_has_64_and_grid and doc_has_camera_and_location):
            result["status"] = "stop_grid_cell_rule_not_supported_by_official_documentation"
            result["reason"] = "The deployment-only grid-cell/year rule is internally exact but official article XML does not independently document a 64-location camera grid strongly enough to authorize it as the site identity."
        else:
            result["status"] = "grid_cell_year_rule_reproduces_64_sites_and_official_xml_documents_64_camera_grid"
            result["reason"] = "All 331 response-independent deployment labels uniquely map to A-H × 1-8 base cells with year suffixes, producing exactly 64 base sites and the frozen six cycle counts; official article XML independently documents the 64-location camera grid. Coordinates are retained cycle-specifically and never averaged across cycles."
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
    sys.exit(main())
