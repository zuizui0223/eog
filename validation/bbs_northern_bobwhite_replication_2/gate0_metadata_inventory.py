from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "bbs_northern_bobwhite_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_metadata_inventory.json"


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canon(obj)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "EOG-BBS-2026-metadata-only/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def slim_checksum(value):
    if isinstance(value, dict):
        return {k: value.get(k) for k in sorted(value) if k in {"type", "value", "algorithm", "checksum"}}
    return value


def slim_file(f: dict):
    return {
        "name": f.get("name"),
        "title": f.get("title"),
        "size": f.get("size"),
        "contentType": f.get("contentType"),
        "checksum": slim_checksum(f.get("checksum")),
        "id": f.get("id"),
        "url": f.get("url"),
        "downloadUri": f.get("downloadUri"),
        "originalMetadata": f.get("originalMetadata"),
    }


def item_summary(item: dict, metadata_bytes: int):
    return {
        "item_id": str(item.get("id") or ""),
        "title": item.get("title"),
        "summary": item.get("summary"),
        "metadata_bytes": metadata_bytes,
        "identifiers": item.get("identifiers") or [],
        "files": [slim_file(f) for f in (item.get("files") or []) if isinstance(f, dict)],
    }


def text_for_file(rec: dict):
    return " ".join(str(rec.get(k) or "") for k in ("name", "title")).lower()


def hits(rec: dict, words: list[str]):
    text = text_for_file(rec)
    return any(re.search(r"(^|[^a-z0-9])" + re.escape(w.lower()) + r"([^a-z0-9]|$)", text) for w in words)


def main():
    result = {
        "schema": "eog.bbs_northern_bobwhite_replication_2.gate0_metadata_inventory.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "root": {},
        "children": [],
        "all_files": [],
        "tentative_role_hits": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
    }
    try:
        root, root_n, root_final = get_json(CONTRACT["source"]["metadata_item_url"])
        if str(root.get("id")) != CONTRACT["source"]["sciencebase_item_id"]:
            raise RuntimeError(f"ScienceBase root id mismatch: {root.get('id')}")
        result["root"] = item_summary(root, root_n)
        result["root"]["final_metadata_url"] = root_final

        children_obj, child_list_n, _ = get_json(CONTRACT["source"]["metadata_children_url"])
        child_stubs = children_obj.get("items") or children_obj.get("results") or []
        result["child_listing_metadata_bytes"] = child_list_n
        for stub in child_stubs:
            cid = str(stub.get("id") or "")
            if not cid:
                continue
            child, n, _ = get_json(f"https://www.sciencebase.gov/catalog/item/{cid}?format=json")
            result["children"].append(item_summary(child, n))

        all_files = []
        for item in [result["root"], *result["children"]]:
            for f in item.get("files") or []:
                rec = dict(f)
                rec["parent_item_id"] = item.get("item_id")
                rec["parent_title"] = item.get("title")
                all_files.append(rec)
        result["all_files"] = all_files

        hints = CONTRACT["gate0"]["role_filename_hints"]
        role_hits = {}
        for role, words in hints.items():
            role_hits[role] = [
                {"parent_item_id": f["parent_item_id"], "parent_title": f["parent_title"], "name": f.get("name"), "title": f.get("title"), "size": f.get("size"), "contentType": f.get("contentType"), "checksum": f.get("checksum")}
                for f in all_files if hits(f, words)
            ]
        result["tentative_role_hits"] = role_hits
        result["metadata_item_count"] = 1 + len(result["children"])
        result["file_count"] = len(all_files)
        result["status"] = "gate0_metadata_inventory_complete_response_unopened"
        result["reason"] = "ScienceBase root and one child level were inventoried through metadata only; no file payload URL was requested"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps({
            "status": result["status"],
            "root_title": result["root"].get("title"),
            "metadata_item_count": result["metadata_item_count"],
            "file_count": result["file_count"],
            "files": [{"parent": f["parent_item_id"], "parent_title": f["parent_title"], "name": f.get("name"), "size": f.get("size"), "contentType": f.get("contentType"), "checksum": f.get("checksum")} for f in all_files],
            "tentative_role_hits": role_hits,
            "response_firewall": result["response_firewall"],
            "file_payload_requests": 0,
            "fingerprint": result["fingerprint"],
        }, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
