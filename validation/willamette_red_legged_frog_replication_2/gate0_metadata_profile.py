from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "willamette_red_legged_frog_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_metadata_profile.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept":"application/json", "User-Agent":"EOG-Willamette-metadata-only/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def checksum_of(file_obj):
    for key in ("checksum", "md5", "sha256"):
        v = file_obj.get(key)
        if v:
            return str(v)
    return None


def file_meta(file_obj, owner_id, owner_title):
    return {
        "owner_item_id": owner_id,
        "owner_title": owner_title,
        "name": file_obj.get("name") or file_obj.get("title"),
        "title": file_obj.get("title"),
        "size": file_obj.get("size"),
        "checksum": checksum_of(file_obj),
        "content_type": file_obj.get("contentType"),
        "date_uploaded": file_obj.get("dateUploaded"),
    }


def classify(name):
    n = (name or "").casefold()
    roles = []
    for role, tokens in {
        "site_registry_or_geometry": ("site", "location", "station", "wetland"),
        "survey_effort_or_availability": ("survey", "visit", "occasion", "effort", "sample"),
        "habitat_or_covariate": ("habitat", "covariate", "vegetation", "fish"),
        "species_detection_response": ("detect", "species", "amphib", "capture", "occurrence", "observation"),
        "metadata_or_dictionary": ("metadata", "dictionary", "readme", "xml"),
    }.items():
        if any(tok in n for tok in tokens):
            roles.append(role)
    if not roles:
        roles = ["unclassified"]
    return roles


def doi_tokens(item):
    vals = []
    for x in item.get("identifiers", []) or []:
        if isinstance(x, dict):
            vals.extend(str(x.get(k) or "") for k in ("type", "scheme", "key", "value", "id"))
        else:
            vals.append(str(x))
    vals.append(str(item.get("citation") or ""))
    vals.append(str(item.get("summary") or ""))
    return " | ".join(vals)


def write(result):
    result["fingerprint"] = fp({k:v for k,v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    firewall = dict(CONTRACT["biological_response_firewall"])
    result = {
        "schema": "eog.willamette_red_legged_frog_replication_2.gate0_metadata_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "top_item": {},
        "child_items": [],
        "files": [],
        "role_candidates": {},
        "biological_response_firewall": firewall,
        "all_attached_file_payload_requests": 0,
        "all_attached_file_payload_bytes_opened": 0
    }
    try:
        sid = CONTRACT["sciencebase"]["item_id"]
        item, item_bytes, final_url = get_json(f"https://www.sciencebase.gov/catalog/item/{sid}?format=json")
        if item.get("id") != sid:
            raise RuntimeError(f"ScienceBase item id mismatch: {item.get('id')} != {sid}")
        title = str(item.get("title") or "")
        if CONTRACT["sciencebase"]["expected_title_contains"] not in title:
            raise RuntimeError(f"ScienceBase title mismatch: {title!r}")
        doi = CONTRACT["sciencebase"]["doi"].casefold()
        if doi not in doi_tokens(item).casefold():
            raise RuntimeError("frozen DOI not found in top-level ScienceBase metadata")
        result["top_item"] = {
            "id": sid,
            "title": title,
            "metadata_bytes": item_bytes,
            "final_host": urllib.parse.urlparse(final_url).netloc,
            "file_count": len(item.get("files", []) or []),
        }

        files = []
        for f in item.get("files", []) or []:
            files.append(file_meta(f, sid, title))

        # One metadata-only child level is allowed because older USGS releases often
        # attach table components as child items. No child file content is followed.
        children_url = "https://www.sciencebase.gov/catalog/items?" + urllib.parse.urlencode({
            "parentId": sid, "format": "json", "max": 200
        })
        child_listing, child_listing_bytes, _ = get_json(children_url)
        child_candidates = child_listing.get("items", []) if isinstance(child_listing, dict) else []
        for child_stub in child_candidates:
            cid = str(child_stub.get("id") or "").strip()
            if not cid:
                continue
            child, child_bytes, _ = get_json(f"https://www.sciencebase.gov/catalog/item/{cid}?format=json")
            ctitle = str(child.get("title") or "")
            result["child_items"].append({
                "id": cid,
                "title": ctitle,
                "metadata_bytes": child_bytes,
                "file_count": len(child.get("files", []) or []),
            })
            for f in child.get("files", []) or []:
                files.append(file_meta(f, cid, ctitle))
        result["top_item"]["child_listing_metadata_bytes"] = child_listing_bytes
        files.sort(key=lambda x: (str(x.get("owner_item_id")), str(x.get("name"))))
        result["files"] = files

        roles = {}
        for f in files:
            for role in classify(f.get("name")):
                roles.setdefault(role, []).append({
                    "owner_item_id": f["owner_item_id"],
                    "name": f["name"],
                    "size": f["size"],
                    "checksum": f["checksum"],
                })
        result["role_candidates"] = roles

        if not files:
            result["status"] = "stop_no_attached_file_inventory"
            result["reason"] = "ScienceBase top item and one child level expose no attached files; no payload was opened"
        else:
            result["status"] = "gate0_metadata_profile_complete"
            result["reason"] = "ScienceBase top-item plus one-level child metadata were inventoried without opening any attached file payload; physical role separation must be frozen from this manifest before payload access"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
