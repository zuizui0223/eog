from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "source_selection_contract.json"
OUTPUT = ROOT / "build/neon_camera_selective_promotion/gate0_metadata.json"
RECORD_URL = "https://zenodo.org/api/records/20826511"


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def _read_json(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "eog-response-blind-neon-gate0/1.0"})
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
        raise RuntimeError("Zenodo record metadata is not an object")
    return parsed


def _safe_inventory(record: dict[str, Any]) -> dict[str, Any]:
    files = record.get("files") or []
    if not isinstance(files, list):
        raise RuntimeError("Zenodo files metadata is not a list")
    out = []
    for entry in files:
        if not isinstance(entry, dict):
            raise RuntimeError("Zenodo file metadata entry is not an object")
        links = entry.get("links") or {}
        out.append({
            "key": entry.get("key"),
            "size": entry.get("size"),
            "checksum": entry.get("checksum"),
            "id": entry.get("id"),
            "content": links.get("content") if isinstance(links, dict) else None,
            "self": links.get("self") if isinstance(links, dict) else None,
        })
    metadata = record.get("metadata") or {}
    return {
        "record_id": str(record.get("id")),
        "doi": metadata.get("doi") if isinstance(metadata, dict) else None,
        "title": metadata.get("title") if isinstance(metadata, dict) else None,
        "files": out,
    }


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.neon_camera_selective_promotion.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "metadata_only": True,
        "metadata_requests": 0,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "csv_header_bytes_opened": 0,
        "csv_rows_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        record = _read_json(RECORD_URL)
        base["metadata_requests"] = 1
        inventory = _safe_inventory(record)
        if inventory["record_id"] != contract["source"]["record_id"]:
            raise RuntimeError("Zenodo record id drift")
        if inventory["doi"] != contract["source"]["doi"]:
            raise RuntimeError("Zenodo DOI drift")
        if inventory["title"] != contract["source"]["title"]:
            raise RuntimeError("Zenodo title drift")

        by_name = {row["key"]: row for row in inventory["files"]}
        expected = contract["public_file_expectations"]
        for name, spec in expected.items():
            if name not in by_name:
                raise RuntimeError(f"missing frozen file: {name}")
            row = by_name[name]
            checksum = str(row.get("checksum") or "")
            if checksum != f"md5:{spec['md5']}":
                raise RuntimeError(f"checksum drift for {name}: {checksum}")

        result = {
            **base,
            "status": "gate0_metadata_ready_for_nonresponse_schema_freeze",
            "zenodo_inventory": inventory,
            "file_count": len(inventory["files"]),
            "expected_files_present": sorted(expected),
            "next_gate": "freeze exact deployment/context file identities and authorize nonresponse schema reads only; camera_trap_sequences.csv remains forbidden",
        }
    except Exception as exc:
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
