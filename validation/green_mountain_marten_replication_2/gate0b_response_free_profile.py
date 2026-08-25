from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "green_mountain_marten_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
META = json.loads((HERE / "gate0a_metadata_certificate.json").read_text())
OUT = BUILD / "gate0b_response_free_profile.json"
ALLOWED = META["response_independent_files"]


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(o):
    return hashlib.sha256(canonical(o)).hexdigest()


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-GreenMountainMarten-Gate0b/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def get_bytes(url):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8", "User-Agent": "EOG-GreenMountainMarten-Gate0b/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def checksum_value(v):
    return str((v or {}).get("value") if isinstance(v, dict) else (v or "")).lower()


def decode_csv(data, name):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = data.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            text = None
    if text is None:
        raise RuntimeError(f"{name}: unsupported encoding")
    try:
        delim = csv.Sniffer().sniff(text[:65536], delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    if not header:
        raise RuntimeError(f"{name}: missing header")
    return header, list(reader), encoding, delim


def norm(x):
    return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())


def profile_column(rows, col):
    vals, missing = [], 0
    for r in rows:
        v = r.get(col)
        if v is None or str(v).strip() == "":
            missing += 1
        else:
            vals.append(str(v).strip())
    unique = sorted(set(vals))
    out = {"nonempty": len(vals), "missing": missing, "unique_count": len(unique), "examples": unique[:12]}
    try:
        nums = [float(v) for v in vals]
        if nums:
            out["numeric_min"] = min(nums); out["numeric_max"] = max(nums)
    except ValueError:
        pass
    return out


def semantic_candidates(header):
    roles = {
        "location_id": {"pklocationid", "locationid", "fklocationid", "siteid", "cameraid"},
        "visit_id": {"pkvisitid", "visitid", "deploymentid", "occasionid"},
        "visit_date": {"visitdate", "date", "startdate"},
        "visit_type": {"visittype", "type"},
        "latitude": {"lat", "latitude", "decimallatitude"},
        "longitude": {"long", "lon", "longitude", "decimallongitude"},
        "name": {"name", "locationname", "sitename", "cameraname"},
        "notes": {"notes", "comments", "description"},
    }
    return {role: [c for c in header if norm(c) in allowed] for role, allowed in roles.items()}


def main():
    firewall = dict(CONTRACT["response_firewall"])
    result = {
        "schema": "eog.green_mountain_marten_replication_2.gate0b_response_free_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "files": {},
        "dictionary_relevant_rows": [],
        "response_firewall": firewall,
    }
    try:
        item_id = CONTRACT["sciencebase_candidate"]["item_id"]
        item = get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        by_name = {f.get("name"): f for f in item.get("files") or [] if isinstance(f, dict) and f.get("name")}
        parsed = {}
        for name, expected in ALLOWED.items():
            f = by_name.get(name)
            if f is None:
                raise RuntimeError(f"{name}: missing ScienceBase file metadata")
            if int(f.get("size") or -1) != int(expected["size"]):
                raise RuntimeError(f"{name}: metadata size mismatch")
            if expected["md5"] not in checksum_value(f.get("checksum")):
                raise RuntimeError(f"{name}: metadata MD5 mismatch")
            url = f.get("downloadUri")
            if not url:
                raise RuntimeError(f"{name}: missing downloadUri")
            data, final_url, ctype = get_bytes(url)
            if len(data) != int(expected["size"]):
                raise RuntimeError(f"{name}: payload size mismatch {len(data)} != {expected['size']}")
            md5 = hashlib.md5(data).hexdigest()
            if md5 != expected["md5"]:
                raise RuntimeError(f"{name}: payload MD5 mismatch {md5} != {expected['md5']}")
            header, rows, encoding, delim = decode_csv(data, name)
            parsed[name] = (header, rows)
            result["files"][name] = {
                "payload_bytes": len(data), "verified_md5": md5,
                "content_type": ctype, "final_download_host": urllib.parse.urlparse(final_url).netloc,
                "encoding": encoding, "delimiter": delim, "header": header,
                "row_count": len(rows), "column_count": len(header),
                "semantic_candidates": semantic_candidates(header),
                "column_profiles": {c: profile_column(rows, c) for c in header},
            }

        dh, dr = parsed["dbdictionary.csv"]
        relevant = []
        for row in dr:
            text = " ".join(str(v or "") for v in row.values()).lower()
            if any(token in text for token in ("locations", "visits", "location", "visit")):
                relevant.append({k: row.get(k) for k in dh})
        result["dictionary_relevant_rows"] = relevant[:250]
        result["dictionary_relevant_row_count"] = len(relevant)
        result["status"] = "gate0b_profile_complete_response_closed"
        result["reason"] = "Exact response-independent locations/visits/dictionary payloads were checksum-verified and profiled; no biological response file was opened"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps({
            "status": result["status"], "reason": result["reason"],
            "files": {k: {"payload_bytes": v["payload_bytes"], "verified_md5": v["verified_md5"], "header": v["header"], "row_count": v["row_count"], "semantic_candidates": v["semantic_candidates"], "column_profiles": v["column_profiles"]} for k,v in result["files"].items()},
            "dictionary_relevant_rows": result["dictionary_relevant_rows"],
            "response_firewall": result["response_firewall"], "fingerprint": result["fingerprint"]
        }, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
