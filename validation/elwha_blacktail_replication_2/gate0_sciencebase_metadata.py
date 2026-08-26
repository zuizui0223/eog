from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "elwha_blacktail_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_sciencebase_metadata.json"
UA = "EOG-Elwha-ScienceBase-metadata-only/1.0"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str, audit: dict):
    audit["metadata_requests"].append(url)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read(10_000_001)
        final_url = r.geturl()
    if len(raw) > 10_000_000:
        raise RuntimeError(f"ScienceBase metadata exceeded 10 MB bound: {url}")
    obj = json.loads(raw.decode("utf-8"))
    return obj, len(raw), final_url


def file_meta(f: dict) -> dict:
    checksum = f.get("checksum")
    if isinstance(checksum, dict):
        checksum = {str(k): v for k, v in checksum.items()}
    return {
        "name": f.get("name"),
        "title": f.get("title"),
        "size": f.get("size"),
        "contentType": f.get("contentType"),
        "checksum": checksum,
        "url": f.get("url"),
        "downloadUri": f.get("downloadUri"),
    }


def item_summary(item: dict, metadata_bytes: int | None = None) -> dict:
    files = item.get("files") or []
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "summary": item.get("summary"),
        "body_preview": str(item.get("body") or "")[:1000],
        "metadata_bytes": metadata_bytes,
        "file_count": len(files) if isinstance(files, list) else None,
        "files": [file_meta(f) for f in files if isinstance(f, dict)] if isinstance(files, list) else [],
        "hasChildren": item.get("hasChildren"),
    }


def main() -> int:
    c = CONTRACT["source"]
    firewall = dict(CONTRACT["response_firewall"])
    result = {
        "schema": "eog.elwha_blacktail_replication_2.gate0_sciencebase_metadata.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "metadata_requests": [],
        "top_item": {},
        "children": [],
        "flat_file_inventory": [],
        "response_firewall": firewall,
    }
    try:
        item_id = c["sciencebase_item_id"]
        top_url = f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json"
        top, top_n, _ = get_json(top_url, result)
        result["top_item"] = item_summary(top, top_n)

        child_url = "https://www.sciencebase.gov/catalog/items?" + urllib.parse.urlencode({
            "parentId": item_id,
            "format": "json",
            "max": 100,
        })
        child_listing, _, _ = get_json(child_url, result)
        child_records = child_listing.get("items") or child_listing.get("records") or []
        if not isinstance(child_records, list):
            child_records = []

        children = []
        for child in child_records:
            if not isinstance(child, dict) or not child.get("id"):
                continue
            child_id = str(child["id"])
            child_obj, child_n, _ = get_json(
                f"https://www.sciencebase.gov/catalog/item/{child_id}?format=json", result
            )
            children.append(item_summary(child_obj, child_n))
        result["children"] = children

        flat = []
        for source_role, entry in [("top", result["top_item"])] + [
            ("child", x) for x in children
        ]:
            for f in entry.get("files", []):
                flat.append({
                    "source_role": source_role,
                    "item_id": entry.get("id"),
                    "item_title": entry.get("title"),
                    **f,
                })
        result["flat_file_inventory"] = flat
        result["status"] = "gate0_sciencebase_metadata_profile_complete_response_closed"
        result["reason"] = (
            "ScienceBase item and one child level were profiled using JSON metadata only; "
            "no attached file payload/header/row/value was requested or opened"
        )
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
