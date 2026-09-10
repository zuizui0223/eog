from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "source_selection_contract.json"
OUTPUT = ROOT / "build/rhode_island_wildlife_selective_promotion/gate0_metadata.json"


def _fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _safe_file(entry: dict[str, Any]) -> dict[str, Any]:
    links = entry.get("links") or {}
    return {
        "id": entry.get("id"),
        "key": entry.get("key"),
        "size": entry.get("size"),
        "checksum": entry.get("checksum"),
        "content_url": links.get("content"),
        "self_url": links.get("self"),
    }


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.rhode_island_wildlife_selective_promotion.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "metadata_requests": 0,
        "zip_payload_requests": 0,
        "zip_payload_bytes_opened": 0,
        "csv_header_bytes_opened": 0,
        "csv_rows_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        url = contract["gate0_metadata_only"]["authorized_url"]
        req = Request(url, headers={"User-Agent": "eog-response-blind-gate0/1.0"})
        with urlopen(req, timeout=30) as response:  # noqa: S310 - frozen public metadata URL
            raw = response.read()
            status = int(getattr(response, "status", 200))
            ctype = response.headers.get("Content-Type", "")
        base["metadata_requests"] = 1
        if status != 200:
            raise RuntimeError(f"Zenodo metadata HTTP status {status}")
        if "json" not in ctype.lower():
            raise RuntimeError(f"Zenodo metadata content type is not JSON: {ctype}")
        record = json.loads(raw.decode("utf-8"))
        if int(record.get("id")) != int(contract["source_identity"]["zenodo_record_id"]):
            raise RuntimeError("Zenodo record id drift")
        files = [_safe_file(x) for x in (record.get("files") or [])]
        expected = contract["source_identity"]["public_landing_declared_files"]
        if len(expected) != 1:
            raise RuntimeError("contract expected-file cardinality drift")
        matches = [x for x in files if x["key"] == expected[0]["name"]]
        if len(matches) != 1:
            raise RuntimeError(f"expected file {expected[0]['name']} occurs {len(matches)} times")
        selected = matches[0]
        checksum = str(selected.get("checksum") or "")
        if checksum.removeprefix("md5:") != expected[0]["md5"]:
            raise RuntimeError("DataS1.zip checksum drift")
        if not selected.get("content_url"):
            raise RuntimeError("DataS1.zip has no content URL in record metadata")
        result = {
            **base,
            "status": "gate0_metadata_ready_for_zip_inventory_freeze",
            "record_title": (record.get("metadata") or {}).get("title"),
            "record_version": (record.get("metadata") or {}).get("version"),
            "record_file_count": len(files),
            "files": files,
            "selected_zip": selected,
            "next_gate": "freeze ZIP size/content URL and authorize bounded EOCD/central-directory/local-header Range reads only",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; no repair within this attempt",
        }
    result["fingerprint"] = _fingerprint(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
