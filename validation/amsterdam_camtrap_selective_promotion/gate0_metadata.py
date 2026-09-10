from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "source_selection_contract.json"
OUTPUT = ROOT / "build/amsterdam_camtrap_selective_promotion/gate0_metadata.json"
URL = "https://zenodo.org/api/records/11440456"


def _sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _read_json(url: str) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "eog-response-blind-gate0/1.0", "Accept": "application/json"})
    with urlopen(req, timeout=30) as response:  # noqa: S310 - frozen public metadata URL
        raw = response.read()
        status = int(getattr(response, "status", 200))
        ctype = response.headers.get("Content-Type", "")
    if status != 200:
        raise RuntimeError(f"metadata HTTP status {status}")
    if "json" not in ctype.lower():
        raise RuntimeError(f"metadata content type is not JSON: {ctype}")
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Zenodo metadata is not an object")
    return data


def _safe_inventory(record: dict[str, Any]) -> list[dict[str, Any]]:
    files = record.get("files") or []
    if not isinstance(files, list):
        raise RuntimeError("Zenodo files metadata is not a list")
    out: list[dict[str, Any]] = []
    for f in files:
        if not isinstance(f, dict):
            raise RuntimeError("Zenodo file metadata entry is not an object")
        links = f.get("links") or {}
        out.append({
            "id": f.get("id"),
            "key": f.get("key"),
            "size": f.get("size"),
            "checksum": f.get("checksum"),
            "download": links.get("content") if isinstance(links, dict) else None,
        })
    return out


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.amsterdam_camtrap_selective_promotion.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "metadata_requests": 0,
        "file_payload_requests": 0,
        "file_payload_bytes_opened": 0,
        "csv_header_bytes_opened": 0,
        "observation_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        rec = _read_json(URL)
        base["metadata_requests"] = 1
        if int(rec.get("id")) != contract["source_identity"]["zenodo_record_id"]:
            raise RuntimeError("Zenodo record id drift")
        inventory = _safe_inventory(rec)
        if not inventory:
            raise RuntimeError("Zenodo file inventory empty")
        result = {
            **base,
            "status": "gate0_metadata_ready_for_nonresponse_package_identification",
            "record_id": rec.get("id"),
            "title": (rec.get("metadata") or {}).get("title") if isinstance(rec.get("metadata"), dict) else None,
            "file_count": len(inventory),
            "files": inventory,
            "next_gate": "freeze exact nonresponse package metadata path; observations remain forbidden",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; do not repair transport within this attempt",
        }
    result["fingerprint"] = _sha(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
