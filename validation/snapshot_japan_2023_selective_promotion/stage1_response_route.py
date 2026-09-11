from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1_response_route_contract.json"
OUTPUT = ROOT / "build/snapshot_japan_2023_selective_promotion/stage1_response_route.json"


def canon_sha(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.snapshot_japan_2023_selective_promotion.stage1_response_route.result.v1",
        "attempt_id": c["attempt_id"],
        "landing_page_gets": 0,
        "response_payload_gets": 0,
        "response_header_requests": 0,
        "response_bytes_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        url = c["authorized_access"]["landing_page_url"]
        req = Request(url, headers={"User-Agent": "eog-snapshot-japan-route-stage1/1.0"})
        with urlopen(req, timeout=30) as r:  # noqa: S310 - prospectively frozen public landing page
            raw = r.read()
            status = int(getattr(r, "status", 200))
            final_url = r.geturl()
        base["landing_page_gets"] = 1
        if status != 200:
            raise RuntimeError(f"landing page HTTP status {status}")
        text = raw.decode("utf-8", errors="replace")
        required_name = c["required_public_identity"]["published_file_name"]
        display_name = c["required_public_identity"]["published_display_name"]
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I)
        candidates = []
        for href in hrefs:
            decoded = html.unescape(href)
            absolute = urljoin(final_url, decoded)
            low = absolute.lower()
            context_match = required_name.lower() in low or display_name.lower() in low
            if context_match:
                candidates.append(absolute)
        candidates = sorted(set(candidates))
        if len(candidates) != 1:
            raise RuntimeError(f"expected exactly one published supplementary download href, found {len(candidates)}")
        result = {
            **base,
            "status": "stage1_response_route_qualified",
            "landing_page_final_url": final_url,
            "landing_page_bytes": len(raw),
            "response_download_url": candidates[0],
            "required_published_file_name": required_name,
            "required_published_display_name": display_name,
            "next_gate": "freeze final once-only response/model contract using this exact route",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_route_metadata",
            "reason": str(exc),
            "next_gate": "none; no route repair within this attempt",
        }
    result["fingerprint"] = canon_sha(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
