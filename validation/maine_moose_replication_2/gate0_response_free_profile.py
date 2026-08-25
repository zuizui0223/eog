from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "maine_moose_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_response_free_profile.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-MaineMoose-Gate0/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8", "User-Agent": "EOG-MaineMoose-Gate0/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def md5_of(data: bytes):
    return hashlib.md5(data).hexdigest()


def norm(s: str):
    return re.sub(r"[^a-z0-9]+", "", (s or "").strip().lower())


def decode_csv(data: bytes, name: str):
    text = None
    encoding = None
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = data.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            pass
    if text is None:
        raise RuntimeError(f"{name}: unsupported text encoding")
    sample = text[:65536]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    header = list(reader.fieldnames or [])
    if not header:
        raise RuntimeError(f"{name}: no header")
    rows = list(reader)
    return header, rows, encoding, delimiter


def profile_column(rows, col):
    vals = []
    missing = 0
    for r in rows:
        v = r.get(col)
        if v is None or str(v).strip() == "":
            missing += 1
        else:
            vals.append(str(v).strip())
    unique = sorted(set(vals))
    out = {
        "nonempty": len(vals),
        "missing": missing,
        "unique_count": len(unique),
        "examples": unique[:8],
    }
    try:
        nums = [float(v) for v in vals]
        if nums:
            out["numeric_min"] = min(nums)
            out["numeric_max"] = max(nums)
    except ValueError:
        pass
    return out


def find_exact_semantic(header, role):
    nmap = {c: norm(c) for c in header}
    allowed = {
        "id": {"locationid", "cameraid", "siteid"},
        "lat": {"latitude", "decimallatitude", "lat"},
        "lon": {"longitude", "decimallongitude", "lon", "long"},
        "visit_id": {"visitid", "deploymentid", "occasionid"},
        "start": {"startdate", "visitstart", "startdatetime", "deploymentstart", "begindate"},
        "end": {"enddate", "visitend", "enddatetime", "deploymentend", "finishdate"},
    }[role]
    return [c for c, n in nmap.items() if n in allowed]


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def main():
    firewall = dict(CONTRACT["response_firewall"])
    result = {
        "schema": "eog.maine_moose_replication_2.gate0_response_free_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "sciencebase": {},
        "locations": {},
        "visits": {},
        "response_firewall": firewall,
    }
    try:
        item_id = CONTRACT["sciencebase"]["item_id"]
        item = get_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        files = {f.get("name"): f for f in item.get("files") or [] if isinstance(f, dict) and f.get("name")}
        result["sciencebase"] = {
            "item_id": item_id,
            "title": item.get("title"),
            "dates": item.get("dates") or [],
            "identifiers": item.get("identifiers") or [],
        }

        parsed = {}
        for name, expected in CONTRACT["allowed_response_independent_files"].items():
            f = files.get(name)
            if f is None:
                raise RuntimeError(f"missing frozen ScienceBase file metadata: {name}")
            observed_size = int(f.get("size") or -1)
            checksum = str((f.get("checksum") or {}).get("value") or f.get("checksum") or "").lower()
            if observed_size != int(expected["size"]):
                raise RuntimeError(f"{name}: metadata size mismatch {observed_size} != {expected['size']}")
            if expected["md5"] not in checksum:
                raise RuntimeError(f"{name}: metadata MD5 mismatch {checksum!r}")
            url = f.get("downloadUri")
            if not url:
                raise RuntimeError(f"{name}: no ScienceBase downloadUri")
            data, final_url, content_type = get_bytes(url)
            if len(data) != int(expected["size"]):
                raise RuntimeError(f"{name}: payload size mismatch {len(data)} != {expected['size']}")
            actual_md5 = md5_of(data)
            if actual_md5 != expected["md5"]:
                raise RuntimeError(f"{name}: payload MD5 mismatch {actual_md5} != {expected['md5']}")
            header, rows, encoding, delimiter = decode_csv(data, name)
            parsed[name] = (header, rows)
            base = {
                "payload_bytes": len(data),
                "verified_md5": actual_md5,
                "content_type": content_type,
                "final_download_host": __import__("urllib.parse").parse.urlparse(final_url).netloc,
                "encoding": encoding,
                "delimiter": delimiter,
                "header": header,
                "column_count": len(header),
                "row_count": len(rows),
                "column_profiles": {c: profile_column(rows, c) for c in header},
            }
            if name == "locations.csv":
                result["locations"] = base
            else:
                result["visits"] = base

        loc_header, loc_rows = parsed["locations.csv"]
        id_cols = find_exact_semantic(loc_header, "id")
        lat_cols = find_exact_semantic(loc_header, "lat")
        lon_cols = find_exact_semantic(loc_header, "lon")
        result["locations"]["semantic_candidates"] = {"id": id_cols, "latitude": lat_cols, "longitude": lon_cols}

        paper_n = int(CONTRACT["paper"]["camera_count"])
        if len(loc_rows) != paper_n:
            result["status"] = "stop_locations_row_count_does_not_reproduce_paper_camera_count"
            result["reason"] = f"locations.csv has {len(loc_rows)} rows; paper freezes {paper_n} cameras"
        elif not (len(id_cols) == len(lat_cols) == len(lon_cols) == 1):
            result["status"] = "stop_locations_schema_not_unambiguous"
            result["reason"] = f"semantic candidates are id={id_cols}, lat={lat_cols}, lon={lon_cols}"
        else:
            id_col, lat_col, lon_col = id_cols[0], lat_cols[0], lon_cols[0]
            ids = [(r.get(id_col) or "").strip() for r in loc_rows]
            if any(not x for x in ids) or len(set(ids)) != paper_n:
                result["status"] = "stop_location_identifier_registry_invalid"
                result["reason"] = "location identifiers are blank or non-unique"
            else:
                pts = []
                for r in loc_rows:
                    pts.append((float(r[lat_col]), float(r[lon_col])))
                ds = []
                for i in range(len(pts)):
                    for j in range(i + 1, len(pts)):
                        ds.append(haversine(*pts[i], *pts[j]))
                result["locations"]["registry_fingerprint"] = fp(sorted({"id": ids[i], "lat": pts[i][0], "lon": pts[i][1]} for i in range(paper_n), key=lambda x: x["id"]))
                result["locations"]["geometry_profile"] = {
                    "pair_count": len(ds),
                    "min_km": min(ds),
                    "median_km": sorted(ds)[len(ds)//2],
                    "max_km": max(ds),
                }
                visit_header, _ = parsed["visits.csv"]
                result["visits"]["semantic_candidates"] = {
                    "location_id": find_exact_semantic(visit_header, "id"),
                    "visit_id": find_exact_semantic(visit_header, "visit_id"),
                    "start": find_exact_semantic(visit_header, "start"),
                    "end": find_exact_semantic(visit_header, "end"),
                }
                result["status"] = "gate0_profile_pass_response_still_closed"
                result["reason"] = "Exact locations/visits payloads reproduced the 84-row response-independent camera registry; visit semantics are profiled for prospective Gate1 freezing"

        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
