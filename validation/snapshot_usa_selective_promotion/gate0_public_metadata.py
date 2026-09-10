from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUTH = HERE / "gate0_execution_authorization.json"
OUTPUT = ROOT / "build/snapshot_usa_selective_promotion/gate0_public_metadata.json"


def _fp(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def main() -> int:
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.snapshot_usa_selective_promotion.gate0_public_metadata.v1",
        "attempt_id": auth["attempt_id"],
        "landing_requests": 0,
        "deployment_payload_requests": 0,
        "sequence_payload_requests": 0,
        "sequence_header_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(auth["authorized_url"], headers={"User-Agent": "eog-response-blind-gate0/1.0"})
        with urlopen(req, timeout=int(auth["timeout_seconds"])) as response:  # noqa: S310 exact frozen public URL
            raw = response.read()
            status = int(getattr(response, "status", 200))
            final_url = response.geturl()
        base["landing_requests"] = 1
        if status != 200:
            raise RuntimeError(f"landing HTTP status {status}")
        text = raw.decode("utf-8", errors="replace")
        missing = [token for token in auth["required_public_tokens"] if token not in text]
        if missing:
            raise RuntimeError(f"required public tokens missing: {missing}")
        result = {
            **base,
            "status": "gate0_public_metadata_qualified",
            "landing_http_status": status,
            "landing_final_url": final_url,
            "landing_bytes_opened": len(raw),
            "required_public_tokens_verified": list(auth["required_public_tokens"]),
            "next_gate": "freeze exact deployment-file transport identity before deployment payload access; sequences remains closed",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_metadata_identity_or_transport",
            "reason": str(exc),
            "next_gate": "none; no route or retry repair within this attempt",
        }
    result["fingerprint"] = _fp(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
