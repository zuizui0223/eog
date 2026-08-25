from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "build" / "replication_2_source_screen"
BUILD.mkdir(parents=True, exist_ok=True)
OUT = BUILD / "maine_moose_metadata_identity.json"
ITEM_ID = "6669b08cd34e9bcc607bd881"
EXPECTED_DOI = "10.5066/P132SU4S"
PAPER = {
    "doi": "10.1002/wlb3.01676",
    "camera_count": 84,
    "start": "2021-11-19",
    "end": "2024-04-30",
    "moose_pictures": 160498,
    "moose_clusters": 6212,
}


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-MaineMoose-metadata-only/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw)


def slim_file(f: dict):
    return {
        "name": f.get("name"),
        "title": f.get("title"),
        "size": f.get("size"),
        "contentType": f.get("contentType"),
        "checksum": f.get("checksum"),
    }


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main():
    item, item_bytes = get_json(f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json")
    children_obj, child_index_bytes = get_json(
        "https://www.sciencebase.gov/catalog/items?" + urllib.parse.urlencode({"parentId": ITEM_ID, "format": "json", "max": 100})
    )
    children = []
    child_metadata_bytes = 0
    for child in children_obj.get("items") or []:
        cid = child.get("id")
        if not cid:
            continue
        full, n = get_json(f"https://www.sciencebase.gov/catalog/item/{cid}?format=json")
        child_metadata_bytes += n
        children.append({
            "id": cid,
            "title": full.get("title"),
            "summary": (full.get("summary") or "")[:1200],
            "files": [slim_file(f) for f in full.get("files") or [] if isinstance(f, dict)],
            "dates": full.get("dates") or [],
        })
    identifiers = item.get("identifiers") or []
    identifier_text = json.dumps(identifiers, ensure_ascii=False)
    result = {
        "schema": "eog.replication_2_source_screen.maine_moose_metadata_identity.v1",
        "status": "metadata_only_complete",
        "item": {
            "id": ITEM_ID,
            "title": item.get("title"),
            "summary": (item.get("summary") or "")[:2500],
            "body": (item.get("body") or "")[:2500],
            "dates": item.get("dates") or [],
            "identifiers": identifiers,
            "files": [slim_file(f) for f in item.get("files") or [] if isinstance(f, dict)],
            "contacts": item.get("contacts") or [],
            "parentId": item.get("parentId"),
        },
        "children": children,
        "paper_public_aggregate_reference": PAPER,
        "identity_checks": {
            "sciencebase_doi_present": EXPECTED_DOI.lower() in identifier_text.lower(),
            "title_mentions_moose_project": "moose" in str(item.get("title") or "").lower(),
            "has_locations_csv": any((f.get("name") or "").lower() == "locations.csv" for f in item.get("files") or []),
            "has_visits_csv": any((f.get("name") or "").lower() == "visits.csv" for f in item.get("files") or []),
            "has_annotations_csv": any((f.get("name") or "").lower() == "annotations.csv" for f in item.get("files") or []),
            "has_taxa_csv": any((f.get("name") or "").lower() == "taxa.csv" for f in item.get("files") or []),
        },
        "metadata_bytes": {
            "item": item_bytes,
            "children_index": child_index_bytes,
            "children_full": child_metadata_bytes,
        },
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
    }
    result["fingerprint"] = hashlib.sha256(canon(result)).hexdigest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({
        "status": result["status"],
        "item": result["item"],
        "identity_checks": result["identity_checks"],
        "children": children,
        "file_payload_requests": 0,
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
