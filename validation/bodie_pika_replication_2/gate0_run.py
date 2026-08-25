from __future__ import annotations

import hashlib
import sys
import urllib.request

import gate0_geometry as gate


def _fixed_base_result():
    return {
        "schema": "eog.bodie_pika_replication_2.gate0.v1",
        "attempt_id": gate.CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "dryad": {},
        "non_response_downloads": [],
        "geometry": {},
        "response_firewall": {
            "census_payload_requests": 0,
            "census_payload_bytes_opened": 0,
            "census_header_bytes_opened": 0,
            "census_sheet_names_opened": False,
            "census_rows_opened": False,
            "census_values_opened": False,
            "scientific_model_fits": 0,
            "heldout_scores": 0,
        },
    }


def _public_get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
            "Accept": "application/octet-stream,*/*;q=0.8",
            "Referer": "https://datadryad.org/dataset/doi%3A10.5061%2Fdryad.51c59zwbd",
            "X-API-Version": "2.1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def _digest(data: bytes, dtype: str) -> str:
    d = dtype.lower().replace("_", "-")
    if d in {"sha-256", "sha256"}:
        return hashlib.sha256(data).hexdigest()
    if d == "md5":
        return hashlib.md5(data).hexdigest()
    raise RuntimeError(f"unsupported Dryad digest type: {dtype}")


def _download_allowed(f):
    meta = gate.file_meta(f)
    name = str(meta["path"])
    if name not in gate.ALLOWED:
        raise RuntimeError(f"attempted non-response download outside allowlist: {name}")
    fid = int(meta["id"])
    href = f.get("_links", {}).get("stash:download", {}).get("href")
    routes = []
    if href:
        routes.append(gate.api_url(href))
    routes.extend([
        f"https://datadryad.org/api/v2/files/{fid}/download",
        f"https://datadryad.org/stash/downloads/file_stream/{fid}",
        f"https://datadryad.org/stash/downloads/file_stream/{fid}?download=1",
    ])
    expected_size = int(meta["size"]) if meta["size"] is not None else None
    dtype = str(meta.get("digestType") or "")
    expected_digest = str(meta.get("digest") or "").lower()
    errors = []
    accepted = None
    used = None
    verified_digest = None
    for url in dict.fromkeys(routes):
        try:
            data = _public_get(url)
        except Exception as exc:
            errors.append(f"{url}: transport {type(exc).__name__} {exc}")
            continue
        if expected_size is not None and len(data) != expected_size:
            errors.append(f"{url}: byte_count {len(data)} != {expected_size}")
            continue
        if expected_digest:
            try:
                actual = _digest(data, dtype)
            except Exception as exc:
                errors.append(f"{url}: digest_setup {type(exc).__name__} {exc}")
                continue
            if actual != expected_digest:
                errors.append(f"{url}: digest {actual} != {expected_digest}")
                continue
            verified_digest = actual
        else:
            verified_digest = hashlib.sha256(data).hexdigest()
            dtype = "locally-computed-sha-256"
        accepted = data
        used = url
        break
    if accepted is None:
        raise RuntimeError(
            "all known public transports failed exact byte/digest validation for allowed non-response file "
            + name + " | " + " | ".join(errors)
        )
    out = gate.BUILD / name
    out.write_bytes(accepted)
    return out, {
        **meta,
        "downloaded_bytes": len(accepted),
        "verified_digest": verified_digest,
        "verified_digest_type": dtype,
        "public_transport_used": used,
        "rejected_transport_attempts": errors,
    }


gate.base_result = _fixed_base_result
gate.download_allowed = _download_allowed

if __name__ == "__main__":
    sys.exit(gate.main())
