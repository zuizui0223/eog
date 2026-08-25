from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "green_mountain_marten_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0a_metadata_only.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-GreenMountainMarten-metadata-only/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw)


def slim_file(f: dict):
    checksum = f.get("checksum")
    if isinstance(checksum, dict):
        checksum = {"type": checksum.get("type"), "value": checksum.get("value")}
    return {
        "name": f.get("name"),
        "size": f.get("size"),
        "contentType": f.get("contentType"),
        "checksum": checksum,
        "title": f.get("title"),
    }


def main():
    item_id = CONTRACT["sciencebase_candidate"]["item_id"]
    item, metadata_bytes = get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
    files = [slim_file(f) for f in item.get("files") or [] if isinstance(f, dict)]
    by_name = {f.get("name"): f for f in files if f.get("name")}
    required = CONTRACT["gate0a"]["required_file_names"]
    missing = [name for name in required if name not in by_name]
    identifiers = item.get("identifiers") or []
    id_text = json.dumps(identifiers, ensure_ascii=False).lower()
    if missing:
        status = "stop_required_physical_files_missing"
        reason = f"missing required metadata-only files: {missing}"
    elif CONTRACT["sciencebase_candidate"]["doi"].lower() not in id_text:
        status = "stop_sciencebase_doi_not_reproduced"
        reason = "frozen ScienceBase DOI is absent from item identifiers"
    else:
        status = "gate0a_metadata_identity_pass_response_closed"
        reason = "ScienceBase item metadata exposes all prospectively required separated files; no file payload was requested"
    result = {
        "schema": "eog.green_mountain_marten_replication_2.gate0a_metadata_only.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": status,
        "reason": reason,
        "item": {
            "id": item_id,
            "title": item.get("title"),
            "summary": (item.get("summary") or "")[:2000],
            "dates": item.get("dates") or [],
            "identifiers": identifiers,
            "metadata_bytes": metadata_bytes,
        },
        "files": {name: by_name.get(name) for name in required},
        "all_file_names": sorted(by_name),
        "response_firewall": dict(CONTRACT["response_firewall"]),
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
    }
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
