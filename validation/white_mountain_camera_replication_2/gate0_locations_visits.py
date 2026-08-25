from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "white_mountain_camera_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_locations_visits.json"

ID_HINT = re.compile(r"(id|location|site|station|camera|visit|deployment|sample)", re.I)
COORD_HINT = re.compile(r"(lat|lon|long|xcoord|ycoord|easting|northing|utm|coordinate)", re.I)
TIME_HINT = re.compile(r"(date|time|start|end|begin|visit|deploy|retrieve|check|year|month|day|duration|effort)", re.I)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-WhiteMountain-metadata/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw)


def file_name(f: dict) -> str:
    return str(f.get("name") or f.get("title") or "")


def download_url(f: dict) -> str | None:
    for key in ("downloadUri", "url"):
        value = f.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    return None


def get_bytes(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv,text/plain,application/octet-stream,*/*;q=0.5",
            "User-Agent": "EOG-WhiteMountain-response-free/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def verify_checksum(raw: bytes, checksum_obj):
    if not checksum_obj:
        return {"metadata_checksum_present": False, "verified": None}
    if isinstance(checksum_obj, str):
        return {"metadata_checksum_present": True, "type": None, "value": checksum_obj, "verified": None}
    ctype = str(checksum_obj.get("type") or "").upper()
    expected = str(checksum_obj.get("value") or "").lower()
    if ctype == "MD5":
        actual = hashlib.md5(raw).hexdigest()
    elif ctype in {"SHA-1", "SHA1"}:
        actual = hashlib.sha1(raw).hexdigest()
    elif ctype in {"SHA-256", "SHA256"}:
        actual = hashlib.sha256(raw).hexdigest()
    else:
        return {"metadata_checksum_present": True, "type": ctype, "value": expected, "verified": None}
    if actual != expected:
        raise RuntimeError(f"checksum mismatch for {ctype}: {actual} != {expected}")
    return {"metadata_checksum_present": True, "type": ctype, "value": expected, "actual": actual, "verified": True}


def decode_csv(raw: bytes, name: str):
    text = None
    encoding = None
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError(f"cannot decode {name}")
    try:
        delimiter = csv.Sniffer().sniff(text[:65536], delimiters=",;\t").delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    header = list(reader.fieldnames or [])
    rows = list(reader)
    if not header:
        raise RuntimeError(f"{name} has no header")
    return header, rows, encoding, delimiter


def maybe_float(value: str):
    try:
        return float(value)
    except Exception:
        return None


def profile_column(rows: list[dict], col: str):
    values = []
    missing = 0
    for row in rows:
        raw = row.get(col)
        value = "" if raw is None else str(raw).strip()
        if value == "":
            missing += 1
        else:
            values.append(value)
    uniq = set(values)
    nums = [maybe_float(v) for v in values]
    numeric = bool(values) and all(v is not None for v in nums)
    result = {
        "nonempty": len(values),
        "missing": missing,
        "unique_count": len(uniq),
        "examples": sorted(uniq)[:12],
    }
    if numeric:
        result["numeric_min"] = min(nums)
        result["numeric_max"] = max(nums)
    return result


def profile_table(name: str, raw: bytes, meta: dict):
    header, rows, encoding, delimiter = decode_csv(raw, name)
    profiles = {col: profile_column(rows, col) for col in header}
    return {
        "metadata": meta,
        "payload_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "encoding": encoding,
        "delimiter": delimiter,
        "header": header,
        "column_count": len(header),
        "row_count": len(rows),
        "duplicate_header_names": sorted([key for key, count in Counter(header).items() if count > 1]),
        "column_profiles": profiles,
        "identifier_hint_columns": [c for c in header if ID_HINT.search(c)],
        "coordinate_hint_columns": [c for c in header if COORD_HINT.search(c)],
        "time_effort_hint_columns": [c for c in header if TIME_HINT.search(c)],
    }, rows


def finish(result, code=0):
    result["fingerprint"] = hashlib.sha256(canonical({k: v for k, v in result.items() if k != "fingerprint"})).hexdigest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


def main():
    result = {
        "schema": "eog.white_mountain_camera_replication_2.gate0_locations_visits.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "item_metadata": {},
        "locations": {},
        "visits": {},
        "join_key_candidates": [],
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        item, metadata_bytes = get_json(f"https://www.sciencebase.gov/catalog/item/{CONTRACT['sciencebase_item_id']}?format=json")
        if str(item.get("title") or "") != CONTRACT["sciencebase_item_title"]:
            raise RuntimeError(f"ScienceBase title drift: {item.get('title')!r}")
        files = [f for f in (item.get("files") or []) if isinstance(f, dict)]
        by_name = {file_name(f): f for f in files}
        required = list(CONTRACT["response_independent_files"])
        missing = [name for name in required if name not in by_name]
        if missing:
            raise RuntimeError(f"response-independent files missing: {missing}")
        forbidden_present = [name for name in CONTRACT["forbidden_response_files"] if name in by_name]
        item_meta = {
            "metadata_bytes": metadata_bytes,
            "file_count": len(files),
            "allowed_files": {},
            "forbidden_files_present": forbidden_present,
        }
        raw_by_name = {}
        for name in required:
            f = by_name[name]
            url = download_url(f)
            if not url:
                raise RuntimeError(f"{name} has no public download URL")
            raw, final_url, content_type = get_bytes(url)
            expected_size = f.get("size")
            if expected_size is not None and int(expected_size) != len(raw):
                raise RuntimeError(f"{name} size mismatch: {len(raw)} != {expected_size}")
            checksum = verify_checksum(raw, f.get("checksum"))
            raw_by_name[name] = raw
            item_meta["allowed_files"][name] = {
                "size": len(raw),
                "content_type": content_type,
                "final_host": urllib.parse.urlparse(final_url).netloc,
                "checksum": checksum,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        result["item_metadata"] = item_meta

        loc_profile, loc_rows = profile_table("locations.csv", raw_by_name["locations.csv"], item_meta["allowed_files"]["locations.csv"])
        visit_profile, visit_rows = profile_table("visits.csv", raw_by_name["visits.csv"], item_meta["allowed_files"]["visits.csv"])
        result["locations"] = loc_profile
        result["visits"] = visit_profile

        if CONTRACT["gate0"]["require_nonempty_locations"] and not loc_rows:
            result["status"] = "stop_locations_empty"
            result["reason"] = "locations.csv is empty"
            return finish(result)
        if CONTRACT["gate0"]["require_nonempty_visits"] and not visit_rows:
            result["status"] = "stop_visits_empty"
            result["reason"] = "visits.csv is empty"
            return finish(result)

        common = sorted(set(loc_profile["header"]) & set(visit_profile["header"]))
        result["join_key_candidates"] = [
            {
                "column": col,
                "locations_unique_count": loc_profile["column_profiles"][col]["unique_count"],
                "locations_nonempty": loc_profile["column_profiles"][col]["nonempty"],
                "visits_unique_count": visit_profile["column_profiles"][col]["unique_count"],
                "visits_nonempty": visit_profile["column_profiles"][col]["nonempty"],
            }
            for col in common
        ]
        result["status"] = "gate0_response_free_locations_visits_profile_complete"
        result["reason"] = "exact locations and visits tables were verified and fully profiled; no annotations/media/taxa/model/photo payload was requested"
        return finish(result)
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        return finish(result, 1)


if __name__ == "__main__":
    raise SystemExit(main())
