from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1_response_identity_contract.json"
OUTPUT = ROOT / "build/snapshot_japan_selective_promotion/stage1_response_identity.json"


def sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def main() -> int:
    c = json.loads(CONTRACT.read_text())
    a = c["authorized_access"]
    base = {
        "schema": "eog.snapshot_japan_selective_promotion.stage1_response_identity.v1",
        "attempt_id": c["attempt_id"],
        "metadata_requests": 0,
        "response_file_requests": 0,
        "response_header_bytes_opened": 0,
        "response_payload_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        req = Request(a["metadata_url"], headers={"Accept": "application/vnd.api+json", "User-Agent": "eog-response-blind-stage1/1.0"})
        with urlopen(req, timeout=30) as r:  # noqa: S310 - frozen DOI metadata URL
            data = json.load(r)
        base["metadata_requests"] = 1
        attrs = (data.get("data") or {}).get("attributes") or {}
        doi = str(attrs.get("doi") or "").lower()
        if doi != c["response_identity"]["doi"].lower():
            raise RuntimeError(f"DOI metadata drift: {doi}")
        url = attrs.get("url")
        if not isinstance(url, str) or not url.startswith("http"):
            raise RuntimeError("DataCite metadata lacks stable landing URL")
        titles = attrs.get("titles") or []
        result = {
            **base,
            "status": "stage1_response_identity_resolved",
            "doi": doi,
            "landing_url": url,
            "titles": [x.get("title") for x in titles if isinstance(x, dict) and isinstance(x.get("title"), str)],
            "publisher": attrs.get("publisher"),
            "next_gate": "freeze full endpoint and one authorized response-file route before any response bytes",
        }
    except Exception as exc:
        result = {**base, "status": "stop_pre_response_source_identity_or_transport", "reason": str(exc), "next_gate": "none; no alternate DOI resolver within this attempt"}
    result["fingerprint"] = sha(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
