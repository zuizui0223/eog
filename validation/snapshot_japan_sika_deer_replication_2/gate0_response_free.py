from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import statistics
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "snapshot_japan_sika_deer_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_response_free.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-SnapshotJapan-metadata-only/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8", "User-Agent": "EOG-SnapshotJapan-response-free/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        return raw, r.geturl(), r.headers.get("Content-Type")


def checksum_parts(value):
    if not value:
        return None, None
    text = str(value)
    if ":" in text:
        a, b = text.split(":", 1)
        return a.lower(), b.lower()
    return None, text.lower()


def record_file_meta(record: dict, filename: str):
    matches = [f for f in record.get("files", []) if f.get("key") == filename]
    if len(matches) != 1:
        raise RuntimeError(f"record {record.get('id')} has {len(matches)} files named {filename}")
    f = matches[0]
    algo, digest = checksum_parts(f.get("checksum"))
    return {
        "record_id": int(record["id"]),
        "filename": filename,
        "size": int(f.get("size")),
        "checksum_algorithm": algo,
        "checksum": digest,
        "content_url": f.get("links", {}).get("content"),
    }


def fetch_known_supplement(spec: dict):
    rec, meta_bytes, _ = get_json(f"https://zenodo.org/api/records/{int(spec['zenodo_record_id'])}")
    observed_doi = str(rec.get("doi") or rec.get("metadata", {}).get("doi") or "")
    if observed_doi and observed_doi != spec["supplement_doi"]:
        raise RuntimeError(f"record DOI mismatch for {spec['filename']}: {observed_doi} != {spec['supplement_doi']}")
    fm = record_file_meta(rec, spec["filename"])
    if fm["checksum_algorithm"] not in {"md5", None}:
        raise RuntimeError(f"unexpected checksum type for {spec['filename']}: {fm['checksum_algorithm']}")
    if fm["checksum"] != spec["expected_md5"]:
        raise RuntimeError(f"Zenodo metadata MD5 mismatch for {spec['filename']}: {fm['checksum']} != {spec['expected_md5']}")
    if not fm["content_url"]:
        raise RuntimeError(f"missing content URL for response-independent file {spec['filename']}")
    raw, final_url, ctype = get_bytes(fm["content_url"])
    if len(raw) != fm["size"]:
        raise RuntimeError(f"size mismatch for {spec['filename']}: {len(raw)} != {fm['size']}")
    actual = hashlib.md5(raw).hexdigest()
    if actual != spec["expected_md5"]:
        raise RuntimeError(f"download MD5 mismatch for {spec['filename']}: {actual} != {spec['expected_md5']}")
    return raw, {
        "record_id": fm["record_id"],
        "supplement_doi": spec["supplement_doi"],
        "filename": fm["filename"],
        "size": fm["size"],
        "md5": actual,
        "record_metadata_bytes": meta_bytes,
        "final_download_host": urllib.parse.urlparse(final_url).netloc,
        "content_type": ctype,
    }


def discover_response_metadata_only():
    response = CONTRACT["forbidden_response"]
    queries = [
        f'doi:"{response["supplement_doi"]}"',
        f'"{response["filename"]}"',
    ]
    inspected = []
    candidates = []
    for q in queries:
        url = "https://zenodo.org/api/records?" + urllib.parse.urlencode({"q": q, "size": 20})
        obj, nbytes, _ = get_json(url)
        inspected.append({"query": q, "metadata_bytes": nbytes, "hit_count": obj.get("hits", {}).get("total", 0)})
        for hit in obj.get("hits", {}).get("hits", []):
            files = hit.get("files", [])
            if any(f.get("key") == response["filename"] for f in files):
                candidates.append(hit)
    dedup = {int(c["id"]): c for c in candidates}
    if len(dedup) != 1:
        raise RuntimeError(f"sequence metadata discovery found {len(dedup)} candidate Zenodo records: {sorted(dedup)}")
    rec = next(iter(dedup.values()))
    fm = record_file_meta(rec, response["filename"])
    title = str(rec.get("metadata", {}).get("title") or "")
    observed_doi = str(rec.get("doi") or rec.get("metadata", {}).get("doi") or "")
    if "Supplementary material 2" not in title:
        raise RuntimeError(f"sequence record title is not Supplementary material 2: {title!r}")
    if observed_doi and observed_doi != response["supplement_doi"]:
        raise RuntimeError(f"sequence supplement DOI mismatch: {observed_doi} != {response['supplement_doi']}")
    # Crucial firewall: never follow or persist the content URL here.
    return {
        "record_id": fm["record_id"],
        "supplement_doi": response["supplement_doi"],
        "title": title,
        "filename": fm["filename"],
        "size": fm["size"],
        "checksum_algorithm": fm["checksum_algorithm"],
        "checksum": fm["checksum"],
        "discovery_queries": inspected,
        "payload_requests": 0,
        "payload_bytes_opened": 0,
        "header_bytes_opened": 0,
        "rows_opened": False,
        "values_opened": False,
    }


def decode_csv(raw: bytes, name: str):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            text = None
    if text is None:
        raise RuntimeError(f"cannot decode {name} as UTF-8-SIG or CP1252")
    sample = text[:65536]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    rows = list(reader)
    if not header:
        raise RuntimeError(f"{name} has no header")
    return header, rows, enc, delim


def parse_dt(value: str, field: str):
    s = (value or "").strip()
    if not s:
        raise RuntimeError(f"blank {field}")
    s2 = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise RuntimeError(f"unsupported {field} datetime token: {s!r}")


def haversine(a, b):
    r = 6371.0088
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def summarize_distances(rows):
    by_array = defaultdict(list)
    for r in rows:
        by_array[r["subproject_name"].strip()].append((float(r["latitude"]), float(r["longitude"])))
    out = []
    pooled = []
    for name in sorted(by_array):
        pts = by_array[name]
        ds = []
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = haversine(pts[i], pts[j])
                ds.append(d)
                pooled.append(d)
        out.append({
            "array": name,
            "site_count": len(pts),
            "pair_count": len(ds),
            "within_array_min_km": min(ds) if ds else None,
            "within_array_median_km": statistics.median(ds) if ds else None,
            "within_array_max_km": max(ds) if ds else None,
        })
    return out, pooled


def percentile(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def write(result):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = {
        "schema": "eog.snapshot_japan_sika_deer_replication_2.gate0_response_free.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "sequence_response_metadata_only": {},
        "deployments": {},
        "habitats": {},
        "geometry_profile": {},
        "time_profile": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        result["sequence_response_metadata_only"] = discover_response_metadata_only()

        dep_raw, dep_meta = fetch_known_supplement(CONTRACT["response_independent"]["deployments"])
        hab_raw, hab_meta = fetch_known_supplement(CONTRACT["response_independent"]["habitats"])
        dep_header, dep_rows, dep_enc, dep_delim = decode_csv(dep_raw, "deployments")
        hab_header, hab_rows, hab_enc, hab_delim = decode_csv(hab_raw, "habitats")

        required_dep = ["deployment_id", "latitude", "longitude", "start_date", "end_date", "subproject_name"]
        missing_dep = [c for c in required_dep if c not in dep_header]
        if missing_dep:
            raise RuntimeError(f"deployments missing required columns: {missing_dep}; observed={dep_header}")
        required_hab = ["subproject_name", "prefecture", "habitat_type", "landscape_type", "ECO_NAME"]
        missing_hab = [c for c in required_hab if c not in hab_header]
        if missing_hab:
            raise RuntimeError(f"habitats missing required columns: {missing_hab}; observed={hab_header}")

        if len(dep_rows) != int(CONTRACT["paper"]["published_deployment_count"]):
            result["status"] = "stop_published_deployment_count_not_reproduced"
            result["reason"] = f"observed {len(dep_rows)} deployment rows, expected {CONTRACT['paper']['published_deployment_count']}"
            write(result); return 0

        ids = [(r.get("deployment_id") or "").strip() for r in dep_rows]
        if any(not x for x in ids) or len(set(ids)) != len(ids):
            result["status"] = "stop_deployment_identifier_registry_invalid"
            result["reason"] = "deployment_id is blank or non-unique"
            write(result); return 0

        starts = []
        ends = []
        durations = []
        coords = []
        arrays = []
        for r in dep_rows:
            try:
                lat = float((r.get("latitude") or "").strip())
                lon = float((r.get("longitude") or "").strip())
            except ValueError as exc:
                raise RuntimeError(f"invalid deployment coordinate for {r.get('deployment_id')}: {exc}")
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise RuntimeError(f"out-of-range coordinate for {r.get('deployment_id')}: {(lat, lon)}")
            s = parse_dt(r.get("start_date"), "start_date")
            e = parse_dt(r.get("end_date"), "end_date")
            if e <= s:
                raise RuntimeError(f"nonpositive deployment duration for {r.get('deployment_id')}: {s}..{e}")
            arr = (r.get("subproject_name") or "").strip()
            if not arr:
                raise RuntimeError(f"blank subproject_name for {r.get('deployment_id')}")
            starts.append(s); ends.append(e); durations.append((e-s).total_seconds()/86400.0); coords.append((lat, lon)); arrays.append(arr)

        array_count = len(set(arrays))
        if array_count != int(CONTRACT["paper"]["published_array_count"]):
            result["status"] = "stop_published_array_count_not_reproduced"
            result["reason"] = f"observed {array_count} arrays, expected {CONTRACT['paper']['published_array_count']}"
            write(result); return 0

        hab_arrays = {(r.get("subproject_name") or "").strip() for r in hab_rows if (r.get("subproject_name") or "").strip()}
        dep_arrays = set(arrays)
        if hab_arrays != dep_arrays:
            result["status"] = "stop_habitat_array_registry_mismatch"
            result["reason"] = f"habitat arrays != deployment arrays; missing={sorted(dep_arrays-hab_arrays)}, extra={sorted(hab_arrays-dep_arrays)}"
            write(result); return 0

        dist_arrays, pooled = summarize_distances(dep_rows)
        result["sequence_response_metadata_only"]["published_sequence_count"] = CONTRACT["forbidden_response"]["published_row_count"]
        result["deployments"] = {
            **dep_meta,
            "header": dep_header,
            "encoding": dep_enc,
            "delimiter": dep_delim,
            "row_count": len(dep_rows),
            "unique_deployment_id_count": len(set(ids)),
            "array_count": array_count,
            "array_sizes": dict(sorted(Counter(arrays).items())),
            "registry_fingerprint": fp(sorted({
                "deployment_id": r["deployment_id"].strip(),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "start_date": r["start_date"].strip(),
                "end_date": r["end_date"].strip(),
                "subproject_name": r["subproject_name"].strip(),
            } for r in dep_rows, key=lambda x: x["deployment_id"])),
        }
        result["habitats"] = {
            **hab_meta,
            "header": hab_header,
            "encoding": hab_enc,
            "delimiter": hab_delim,
            "row_count": len(hab_rows),
            "array_count": len(hab_arrays),
            "array_registry_fingerprint": fp(sorted(hab_arrays)),
        }
        result["time_profile"] = {
            "earliest_start": min(starts).isoformat(),
            "latest_start": max(starts).isoformat(),
            "earliest_end": min(ends).isoformat(),
            "latest_end": max(ends).isoformat(),
            "duration_days_min": min(durations),
            "duration_days_q25": percentile(durations, .25),
            "duration_days_median": statistics.median(durations),
            "duration_days_q75": percentile(durations, .75),
            "duration_days_max": max(durations),
            "duration_days_sum": sum(durations),
        }
        result["geometry_profile"] = {
            "arrays": dist_arrays,
            "pooled_within_array_pair_count": len(pooled),
            "pooled_within_array_distance_km_q10": percentile(pooled, .10),
            "pooled_within_array_distance_km_q25": percentile(pooled, .25),
            "pooled_within_array_distance_km_q50": percentile(pooled, .50),
            "pooled_within_array_distance_km_q75": percentile(pooled, .75),
            "pooled_within_array_distance_km_q90": percentile(pooled, .90),
            "cross_array_propagation_allowed": False,
        }

        result["status"] = "gate0_pass_response_free_source_registry_time_and_geometry_profile"
        result["reason"] = "Zenodo metadata resolved the physically separate sequence response without opening it; exact deployment and habitat supplements reproduced 90 deployments and nine arrays and supplied response-independent geometry/effort profiles"
        write(result)
        return 0
    except Exception as exc:
        result["status"] = "engineering_failure_pre_response"
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
