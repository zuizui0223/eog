from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "aland_glanville_fritillary_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "gate1_patch_contract.json").read_text())
SELECTED = CONTRACT["selected_response_independent_file"]
OUT = BUILD / "gate1_patch_profile.json"
AUTHORIZE_URL = CONTRACT["download_authorization"]["endpoint"]
AUTH_BODY = CONTRACT["download_authorization"]["request_json"]


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def firewall():
    return {
        "patch_authorization_requests": 0,
        "patch_payload_requests": 0,
        "patch_payload_bytes_opened": 0,
        "patch_header_opened": False,
        "patch_rows_opened": False,
        "patch_values_opened": False,
        "locality_visit_authorization_requests": 0,
        "locality_visit_payload_requests": 0,
        "locality_visit_payload_bytes_opened": 0,
        "nest_authorization_requests": 0,
        "nest_payload_requests": 0,
        "nest_payload_bytes_opened": 0,
        "other_dataset_file_payload_requests": 0,
        "scientific_model_fits": 0,
        "heldout_scores": 0,
    }


def base_result():
    return {
        "schema": "eog.aland_glanville_fritillary_replication_2.gate1_patch_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "selected_patch_file": SELECTED,
        "patch": {},
        "candidate_columns": {},
        "response_firewall": firewall(),
    }


def request_json(url: str, body: dict):
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 EOG-fresh-validation-patch-only/1.0",
            "Referer": "https://etsin.fairdata.fi/",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def get_bytes_once(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv,application/octet-stream,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 EOG-fresh-validation-patch-only/1.0",
            "Referer": "https://etsin.fairdata.fi/",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def normalize_name(name: str):
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def candidate_groups(header):
    ids = []
    geometry = []
    temporal = []
    for col in header:
        n = normalize_name(col)
        toks = set(n.split("_"))
        if n in {"id", "patch", "patchid", "patch_id", "patch_no", "patch_number"} or ("patch" in toks and ("id" in toks or "no" in toks or "number" in toks)):
            ids.append(col)
        if (
            n in {"x", "y", "lon", "long", "longitude", "lat", "latitude", "area", "perimeter"}
            or toks.intersection({"longitude", "latitude", "easting", "northing", "centroid", "coordinate", "coordinates", "geometry", "geom", "area", "perimeter"})
            or (len(toks) <= 2 and toks.intersection({"x", "y", "lon", "long", "lat"}))
        ):
            geometry.append(col)
        if toks.intersection({"year", "date", "created", "creation", "start", "begin", "first", "end", "finish", "last", "active", "inactive", "mapped", "mapping", "established", "deleted", "deletion", "retired", "split", "merged", "merge"}):
            temporal.append(col)
    return {
        "identifier": ids,
        "geometry": geometry,
        "temporal_eligibility": temporal,
    }


def maybe_number(x):
    try:
        return float(x)
    except Exception:
        return None


def profile_column(rows, col, max_examples=12):
    vals = []
    missing = 0
    for r in rows:
        v = r.get(col)
        if v is None or str(v).strip() == "":
            missing += 1
        else:
            vals.append(str(v).strip())
    unique = set(vals)
    nums = [maybe_number(v) for v in vals]
    all_numeric = bool(vals) and all(x is not None for x in nums)
    out = {
        "nonempty": len(vals),
        "missing": missing,
        "unique_count": len(unique),
        "examples": sorted(unique)[:max_examples],
    }
    if all_numeric:
        out["numeric_min"] = min(nums)
        out["numeric_max"] = max(nums)
    return out


def write_result(result):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = base_result()
    a = result["response_firewall"]
    try:
        # Only the prospectively frozen Patch path may be authorized.
        auth, auth_n, auth_final_url = request_json(AUTHORIZE_URL, AUTH_BODY)
        a["patch_authorization_requests"] = 1
        if urllib.parse.urlparse(auth_final_url).netloc != "etsin.fairdata.fi":
            raise RuntimeError("Patch authorization redirected outside etsin.fairdata.fi")
        if not isinstance(auth, dict) or not isinstance(auth.get("url"), str):
            raise RuntimeError(f"Patch authorization response lacks url; keys={sorted(auth.keys()) if isinstance(auth, dict) else type(auth).__name__}")
        download_url = auth["url"]

        data, final_download_url, content_type = get_bytes_once(download_url)
        a["patch_payload_requests"] = 1
        a["patch_payload_bytes_opened"] = len(data)
        if len(data) != int(SELECTED["size"]):
            raise RuntimeError(f"Patch byte-size mismatch: {len(data)} != {SELECTED['size']}")
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != SELECTED["sha256"]:
            raise RuntimeError(f"Patch SHA-256 mismatch: {actual_sha} != {SELECTED['sha256']}")

        try:
            text = data.decode("utf-8-sig")
            encoding = "utf-8-sig"
        except UnicodeDecodeError as exc:
            raise RuntimeError(f"Patch CSV is not UTF-8/UTF-8-SIG: {exc}")

        # Delimiter detection is response-independent and occurs only after exact byte verification.
        sample = text[:65536]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        header = list(reader.fieldnames or [])
        if not header:
            raise RuntimeError("Patch CSV has no header")
        a["patch_header_opened"] = True
        rows = list(reader)
        a["patch_rows_opened"] = True
        a["patch_values_opened"] = True

        candidates = candidate_groups(header)
        profiles = {}
        for group, cols in candidates.items():
            profiles[group] = {col: profile_column(rows, col) for col in cols}
        result["candidate_columns"] = profiles
        result["patch"] = {
            "authorization_response_bytes": auth_n,
            "payload_bytes": len(data),
            "verified_sha256": actual_sha,
            "content_type": content_type,
            "encoding": encoding,
            "delimiter": delimiter,
            "header": header,
            "column_count": len(header),
            "row_count": len(rows),
            "blank_header_columns": [i for i, c in enumerate(header) if not str(c).strip()],
            "duplicate_header_names": sorted([k for k, v in Counter(header).items() if v > 1]),
            "identifier_candidate_names": candidates["identifier"],
            "geometry_candidate_names": candidates["geometry"],
            "temporal_eligibility_candidate_names": candidates["temporal_eligibility"],
        }
        # Do not persist the returned tokenized download URL or any raw Patch rows.
        result["status"] = "gate1_patch_profile_complete_response_still_closed"
        result["reason"] = "Exact frozen Patch payload was opened and profiled after size/SHA verification; Locality Visit, Nest and all other dataset payloads remain unopened"
        write_result(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response" if a["patch_payload_requests"] == 0 else "engineering_failure_after_response_independent_patch_only"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write_result(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
