from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "hog_island_small_mammal_metadata_screen"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "metadata_screen.json"


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(x):
    return hashlib.sha256(canonical(x)).hexdigest()


def get_text(url: str, accept: str = "text/plain,application/xml;q=0.9,*/*;q=0.1"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "EOG-HogIsland-metadata-only-screen/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return raw.decode("utf-8", errors="replace"), len(raw), r.geturl(), r.headers.get("Content-Type")


def localname(tag: str):
    return tag.rsplit("}", 1)[-1]


def child_text(node, name):
    for child in list(node):
        if localname(child.tag) == name:
            return (child.text or "").strip()
    return ""


def descendants(node, name):
    return [x for x in node.iter() if localname(x.tag) == name]


def main():
    result = {
        "schema": "eog.hog_island_small_mammal_metadata_screen.result.v1",
        "status": "engineering_failure_metadata_only",
        "reason": None,
        "resource_map": {},
        "package": {},
        "entity_names": [],
        "eml_data_tables": [],
        "role_diagnosis": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        doi = CONTRACT["source"]["doi"]
        shoulder, pasta, md5 = doi.split("/", 2)
        resource_url = f"https://pasta.lternet.edu/package/doi/doi:{shoulder}/{pasta}/{md5}"
        text, n, final_url, ctype = get_text(resource_url)
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        result["resource_map"] = {
            "request_url": resource_url,
            "response_bytes": n,
            "final_url": final_url,
            "content_type": ctype,
            "line_count": len(lines),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        package_matches = []
        for line in lines:
            m = re.search(r"/package/eml/([^/]+)/([0-9]+)/([^/?#\s]+)$", line)
            if m:
                package_matches.append(m.groups())
            m = re.search(r"/package/metadata/eml/([^/]+)/([0-9]+)/([^/?#\s]+)$", line)
            if m:
                package_matches.append(m.groups())
        package_matches = sorted(set(package_matches))
        if len(package_matches) != 1:
            raise RuntimeError(f"DOI resource map did not resolve exactly one package id: {package_matches}")
        scope, identifier, revision = package_matches[0]
        result["package"] = {"scope": scope, "identifier": int(identifier), "revision": revision}

        names_url = f"https://pasta.lternet.edu/package/name/eml/{scope}/{identifier}/{revision}"
        names_text, names_n, _, _ = get_text(names_url)
        entity_names = []
        for line in names_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "," in line:
                entity_id, name = line.split(",", 1)
            else:
                entity_id, name = line, ""
            entity_names.append({"entity_id": entity_id.strip(), "name": name.strip()})
        result["entity_names"] = entity_names
        result["package"]["entity_names_response_bytes"] = names_n

        metadata_url = f"https://pasta.lternet.edu/package/metadata/eml/{scope}/{identifier}/{revision}"
        metadata_text, metadata_n, metadata_final, metadata_ctype = get_text(metadata_url, "application/xml,text/xml;q=0.9,*/*;q=0.1")
        result["package"]["metadata_response_bytes"] = metadata_n
        result["package"]["metadata_sha256"] = hashlib.sha256(metadata_text.encode()).hexdigest()
        result["package"]["metadata_final_url"] = metadata_final
        result["package"]["metadata_content_type"] = metadata_ctype
        root = ET.fromstring(metadata_text)
        tables = []
        for dt in descendants(root, "dataTable"):
            entity = descendants(dt, "entityName")
            entity_name = (entity[0].text or "").strip() if entity else ""
            physical = descendants(dt, "objectName")
            object_name = (physical[0].text or "").strip() if physical else ""
            attrs = []
            for attr in descendants(dt, "attribute"):
                names = descendants(attr, "attributeName")
                if names:
                    nm = (names[0].text or "").strip()
                    if nm:
                        attrs.append(nm)
            tables.append({
                "entity_name": entity_name,
                "object_name": object_name,
                "attribute_count": len(attrs),
                "attributes": attrs,
            })
        result["eml_data_tables"] = tables

        response_terms = {"species", "speciescode", "taxon", "weight", "sex", "individual", "capture", "tag", "ear", "animal"}
        effort_terms = {"effort", "sampled", "trapnight", "trap_night", "trapping", "session", "census", "survey"}
        geometry_terms = {"latitude", "longitude", "utm", "easting", "northing", "station", "transect", "plot", "location"}
        diagnoses = []
        for t in tables:
            norm = [a.lower().replace(" ", "_") for a in t["attributes"]]
            has_response = any(any(term in a for term in response_terms) for a in norm)
            has_effort = any(any(term in a for term in effort_terms) for a in norm)
            has_geometry = any(any(term in a for term in geometry_terms) for a in norm)
            diagnoses.append({
                "entity_name": t["entity_name"],
                "object_name": t["object_name"],
                "has_response_like_fields": has_response,
                "has_effort_like_fields": has_effort,
                "has_geometry_like_fields": has_geometry,
            })
        result["role_diagnosis"] = {"tables": diagnoses}
        separate_effort = any(x["has_effort_like_fields"] and not x["has_response_like_fields"] for x in diagnoses)
        separate_geometry = any(x["has_geometry_like_fields"] and not x["has_response_like_fields"] for x in diagnoses)
        response_tables = [x for x in diagnoses if x["has_response_like_fields"]]

        if not response_tables:
            result["status"] = "stop_metadata_does_not_identify_capture_response_entity"
            result["reason"] = "PASTA EML metadata does not identify a biological capture-response table distinctly enough for an audited fresh endpoint"
        elif separate_effort and separate_geometry:
            result["status"] = "metadata_screen_pass_physical_response_independent_effort_and_geometry_entities_exist"
            result["reason"] = "PASTA metadata exposes response-independent effort and geometry entities separately from capture-response entity; candidate may advance to a response-free source gate"
        else:
            result["status"] = "stop_metadata_lacks_physical_response_independent_effort_or_geometry"
            result["reason"] = f"separate_effort={separate_effort}, separate_geometry={separate_geometry}; no data entity payload was opened"

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
