from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1_dictionary_contract.json"
OUTPUT = ROOT / "build/massachusetts_wildlife_selective_promotion/stage1_dictionary.json"


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    spec = contract["authorized_file"]
    base = {
        "schema": "eog.massachusetts_wildlife_selective_promotion.stage1_dictionary.v1",
        "attempt_id": contract["attempt_id"],
        "dictionary_payload_requests": 0,
        "dictionary_payload_bytes_opened": 0,
        "other_file_payload_requests": 0,
        "biological_response_payload_requests": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        request = Request(spec["url"], headers={"User-Agent": "eog-response-blind-stage1/1.0"})
        with urlopen(request, timeout=30) as response:  # noqa: S310 - exact frozen public file URL
            raw = response.read()
            status = int(getattr(response, "status", 200))
        base["dictionary_payload_requests"] = 1
        base["dictionary_payload_bytes_opened"] = len(raw)
        if status != 200:
            raise RuntimeError(f"dictionary HTTP status {status}")
        if len(raw) != int(spec["size"]):
            raise RuntimeError(f"dictionary size drift: {len(raw)} != {spec['size']}")
        md5 = hashlib.md5(raw).hexdigest()  # noqa: S324 - integrity match to frozen source metadata
        if md5 != spec["md5"]:
            raise RuntimeError(f"dictionary MD5 drift: {md5}")
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise RuntimeError("dictionary has no CSV header")
        rows = [dict(row) for row in reader]
        if not rows:
            raise RuntimeError("dictionary has zero rows")
        result = {
            **base,
            "status": "stage1_dictionary_schema_ready",
            "dictionary_md5": md5,
            "dictionary_header": list(reader.fieldnames),
            "dictionary_row_count": len(rows),
            "dictionary_rows": rows,
            "next_gate": "freeze safe locations/visits schema-dependent payload contract before opening either file; response remains closed",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_dictionary_transport_identity_or_schema",
            "reason": str(exc),
            "next_gate": "none; no repair within this attempt",
        }
    result["fingerprint"] = _canonical_sha256(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "dictionary_rows"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
