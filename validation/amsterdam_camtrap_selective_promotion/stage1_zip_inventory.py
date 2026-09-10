from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage1_zip_inventory_contract.json"
OUTPUT = ROOT / "build/amsterdam_camtrap_selective_promotion/stage1_zip_inventory.json"


def _sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _central_names(raw: bytes) -> list[str]:
    names: list[str] = []
    sig = b"PK\x01\x02"
    pos = 0
    while True:
        i = raw.find(sig, pos)
        if i < 0:
            break
        if i + 46 > len(raw):
            break
        try:
            name_len, extra_len, comment_len = struct.unpack_from("<HHH", raw, i + 28)
        except struct.error:
            break
        start = i + 46
        end = start + name_len
        if end > len(raw):
            break
        name = raw[start:end].decode("utf-8", errors="replace")
        names.append(name)
        pos = end + extra_len + comment_len
    return names


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    archive = contract["frozen_archive"]
    auth = contract["authorized_access"]
    base = {
        "schema": "eog.amsterdam_camtrap_selective_promotion.stage1_zip_inventory.v1",
        "attempt_id": contract["attempt_id"],
        "head_requests": 0,
        "range_get_requests": 0,
        "bytes_read": 0,
        "archive_body_fully_downloaded": False,
        "member_body_bytes_opened": 0,
        "observation_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        head = Request(archive["content_url"], method="HEAD", headers={"User-Agent": "eog-response-blind-stage1/1.0"})
        with urlopen(head, timeout=30) as response:  # noqa: S310 - frozen public URL
            base["head_requests"] = 1
            length = response.headers.get("Content-Length")
            accept_ranges = response.headers.get("Accept-Ranges", "")
        if length is not None and int(length) != archive["size_bytes"]:
            raise RuntimeError(f"archive size drift: {length}")

        req = Request(
            archive["content_url"],
            headers={
                "User-Agent": "eog-response-blind-stage1/1.0",
                "Range": auth["range"],
                "Accept": "application/octet-stream",
            },
        )
        with urlopen(req, timeout=60) as response:  # noqa: S310 - frozen public URL
            status = int(getattr(response, "status", 200))
            content_range = response.headers.get("Content-Range")
            if status != 206:
                raise RuntimeError(f"range request not honored: HTTP {status}")
            raw = response.read(auth["max_bytes_read"] + 1)
            base["range_get_requests"] = 1
            base["bytes_read"] = len(raw)
        if len(raw) > auth["max_bytes_read"]:
            raise RuntimeError("range response exceeded frozen byte ceiling")
        names = _central_names(raw)
        if not names:
            raise RuntimeError("no ZIP central-directory entries found in frozen tail range")
        matched: dict[str, list[str]] = {}
        for role in contract["required_member_roles"]:
            hits = [n for n in names if n == role or n.endswith("/" + role)]
            matched[role] = hits
            if len(hits) != 1:
                raise RuntimeError(f"expected exactly one {role}, found {len(hits)}")
        result = {
            **base,
            "status": "stage1_zip_inventory_qualified",
            "head_content_length": int(length) if length is not None else None,
            "head_accept_ranges": accept_ranges,
            "content_range": content_range,
            "central_directory_entry_count_in_tail": len(names),
            "required_members": matched,
            "next_gate": "freeze exact member identities and authorize datapackage.json plus deployments.csv bodies only",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_archive_range_or_inventory",
            "reason": str(exc),
            "next_gate": "none; no range-size or route repair within this attempt",
        }
    result["fingerprint"] = _sha(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
