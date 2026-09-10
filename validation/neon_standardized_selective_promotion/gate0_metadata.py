from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "source_selection_contract.json"
OUTPUT = Path("build/neon_standardized_selective_promotion/gate0_metadata.json")


def _fingerprint(payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def run() -> dict:
    contract = json.loads(CONTRACT.read_text())
    base = {
        "schema": "eog.neon_standardized_selective_promotion.gate0_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "metadata_only": True,
        "metadata_requests": 0,
        "csv_payload_requests": 0,
        "csv_payload_bytes_opened": 0,
        "csv_header_bytes_opened": 0,
        "csv_rows_opened": 0,
        "biological_response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(contract["selection_boundary"]["zenodo_api"], headers={"Accept": "application/json", "User-Agent": "eog-fresh-gate0/1"})
        base["metadata_requests"] = 1
        with urlopen(req, timeout=20) as r:
            raw = r.read()
        meta = json.loads(raw)
        files = meta.get("files", [])
        observed = {}
        for f in files:
            key = f.get("key")
            checksum = f.get("checksum")
            if key:
                observed[key] = {
                    "checksum": checksum,
                    "size": f.get("size"),
                    "links": {k: v for k, v in (f.get("links") or {}).items() if k in {"self", "content"}},
                }
        expected = contract["publicly_observed_file_identity"]
        for name, spec in expected.items():
            if name not in observed:
                raise RuntimeError(f"expected file absent: {name}")
            checksum = observed[name].get("checksum") or ""
            if checksum.removeprefix("md5:") != spec["md5"]:
                raise RuntimeError(f"checksum mismatch for {name}: {checksum}")
        result = {
            **base,
            "status": "gate0_metadata_ready_for_deployment_schema_freeze",
            "record_id": meta.get("id"),
            "title": (meta.get("metadata") or {}).get("title"),
            "observed_files": observed,
            "next_gate": "freeze exact deployment/context file identities and authorize only response-independent schema/payload access; sequence response remains forbidden",
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
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    run()
