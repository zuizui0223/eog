from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "source_selection_contract.json"
OUTPUT = ROOT / "build/massachusetts_wildlife_selective_promotion/gate0_metadata.json"
ITEM_URL = "https://www.sciencebase.gov/catalog/item/6672de8dd34e84915adbb4f3?format=json"


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def _read_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "eog-response-blind-gate0/1.0"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - frozen public metadata URL
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
        status = int(getattr(response, "status", 200))
    if status != 200:
        raise RuntimeError(f"metadata HTTP status {status}")
    if "json" not in content_type.lower():
        raise RuntimeError(f"metadata content type is not JSON: {content_type}")
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise RuntimeError("ScienceBase item metadata is not an object")
    return parsed


def _metadata_inventory(item: dict[str, Any]) -> dict[str, Any]:
    files = item.get("files") or []
    if not isinstance(files, list):
        raise RuntimeError("ScienceBase files metadata is not a list")
    safe_files = []
    for entry in files:
        if not isinstance(entry, dict):
            raise RuntimeError("ScienceBase file metadata entry is not an object")
        safe_files.append(
            {
                "name": entry.get("name"),
                "id": entry.get("id"),
                "size": entry.get("size"),
                "checksum": entry.get("checksum"),
                "checksumType": entry.get("checksumType"),
                "contentType": entry.get("contentType"),
                "url": entry.get("url"),
            }
        )
    children = item.get("childIds") or []
    if not isinstance(children, list):
        raise RuntimeError("ScienceBase childIds metadata is not a list")
    return {
        "item_id": item.get("id"),
        "title": item.get("title"),
        "files": safe_files,
        "child_ids": list(children),
    }


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.massachusetts_wildlife_selective_promotion.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "metadata_only": True,
        "metadata_requests": 0,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "csv_header_bytes_opened": 0,
        "csv_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        item = _read_json(ITEM_URL)
        base["metadata_requests"] = 1
        inventory = _metadata_inventory(item)
        if inventory["item_id"] != contract["source_identity"]["sciencebase_item_id"]:
            raise RuntimeError("ScienceBase item id drift")
        if inventory["title"] != contract["source_identity"]["title"]:
            raise RuntimeError("ScienceBase title drift")
        names = [row.get("name") for row in inventory["files"]]
        result = {
            **base,
            "status": "gate0_metadata_ready_for_schema_freeze",
            "sciencebase_inventory": inventory,
            "top_level_file_count": len(inventory["files"]),
            "child_item_count": len(inventory["child_ids"]),
            "publicly_named_role_presence": {
                "dictionary.csv": "dictionary.csv" in names,
                "media.csv": "media.csv" in names,
                "annotations.csv": "annotations.csv" in names,
                "modeloutputs.csv": "modeloutputs.csv" in names,
            },
            "next_gate": "freeze exact file/child identities and authorize dictionary-only schema read; biological response remains forbidden",
        }
    except Exception as exc:  # fail closed before payload access
        result = {
            **base,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; do not repair this attempt after live Gate0",
        }
    result["fingerprint"] = _canonical_sha256(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
