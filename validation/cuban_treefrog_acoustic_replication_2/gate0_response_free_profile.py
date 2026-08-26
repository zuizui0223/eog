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
BUILD = ROOT / "build" / "cuban_treefrog_acoustic_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_response_free_profile.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def request_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-CubanTreefrog-response-free/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def request_bytes(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.5", "User-Agent": "EOG-CubanTreefrog-response-free/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
        return raw, r.geturl(), r.headers.get("Content-Type")


def checksum_value(x):
    if isinstance(x, dict):
        return str(x.get("value") or "").lower()
    return str(x or "").lower()


def exact_file(item: dict, name: str):
    matches = [f for f in item.get("files", []) if f.get("name") == name]
    if len(matches) != 1:
        raise RuntimeError(f"ScienceBase item has {len(matches)} files named {name}")
    return matches[0]


def get_allowed_file(item: dict, name: str, spec: dict):
    f = exact_file(item, name)
    observed_size = int(f.get("size") or -1)
    observed_md5 = checksum_value(f.get("checksum") or f.get("md5"))
    if observed_size != int(spec["size"]):
        raise RuntimeError(f"metadata size mismatch for {name}: {observed_size} != {spec['size']}")
    if observed_md5 != spec["md5"]:
        raise RuntimeError(f"metadata MD5 mismatch for {name}: {observed_md5} != {spec['md5']}")
    url = f.get("downloadUri") or f.get("url")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError(f"no HTTPS download URI for permitted file {name}")
    raw, final_url, content_type = request_bytes(url)
    if len(raw) != int(spec["size"]):
        raise RuntimeError(f"download size mismatch for {name}: {len(raw)} != {spec['size']}")
    actual_md5 = hashlib.md5(raw).hexdigest()
    if actual_md5 != spec["md5"]:
        raise RuntimeError(f"download MD5 mismatch for {name}: {actual_md5} != {spec['md5']}")
    return raw, {
        "name": name,
        "size": len(raw),
        "md5": actual_md5,
        "content_type": content_type,
        "final_host": urllib.parse.urlparse(final_url).netloc,
    }


def decode_csv(raw: bytes, name: str):
    text = None
    encoding = None
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError(f"cannot decode {name}")
    sample = text[:65536]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    header = list(reader.fieldnames or [])
    if not header:
        raise RuntimeError(f"{name} has no CSV header")
    rows = list(reader)
    return header, rows, encoding, delimiter


def norm(s: str):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def column_roles(header):
    out = {"identifier": [], "location_link": [], "visit_link": [], "geometry": [], "start_time": [], "end_time": [], "datetime": [], "table_or_field_definition": []}
    for col in header:
        n = norm(col)
        toks = set(n.split("_"))
        if n == "id" or n.endswith("_id") or "uuid" in toks or "guid" in toks:
            out["identifier"].append(col)
        if "location" in toks or n.startswith("location") or "site" in toks or "station" in toks:
            out["location_link"].append(col)
        if "visit" in toks or "deployment" in toks or "occasion" in toks or "survey" in toks:
            out["visit_link"].append(col)
        if toks.intersection({"lat", "latitude", "lon", "long", "longitude", "x", "y", "easting", "northing", "bbox", "bounding", "geometry", "coordinate", "coordinates"}):
            out["geometry"].append(col)
        if "start" in toks or n.startswith("start") or "begin" in toks:
            out["start_time"].append(col)
        if "end" in toks or n.startswith("end") or "stop" in toks:
            out["end_time"].append(col)
        if toks.intersection({"date", "datetime", "timestamp", "time"}):
            out["datetime"].append(col)
        if toks.intersection({"table", "field", "column", "variable", "description", "definition", "relationship", "foreign", "primary"}):
            out["table_or_field_definition"].append(col)
    return out


def profile_column(rows, col, max_examples=12):
    vals = []
    missing = 0
    for r in rows:
        v = r.get(col)
        if v is None or str(v).strip() == "":
            missing += 1
        else:
            vals.append(str(v).strip())
    uniq = sorted(set(vals))
    return {
        "nonempty": len(vals),
        "missing": missing,
        "unique_count": len(uniq),
        "examples": uniq[:max_examples],
    }


def dictionary_matches(rows, header):
    targets = tuple(CONTRACT["gate0"]["profile_dictionary_relationship_rows_for_tables"])
    matches = []
    for i, row in enumerate(rows, start=1):
        joined = " | ".join(str(row.get(c) or "") for c in header).lower()
        if any(t.lower() in joined for t in targets):
            compact = {c: str(row.get(c) or "").strip() for c in header if str(row.get(c) or "").strip()}
            matches.append({"row_index": i, "values": compact})
    return matches


def result_base():
    return {
        "schema": "eog.cuban_treefrog_acoustic_replication_2.gate0_response_free_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "sciencebase_metadata": {},
        "files": {},
        "dictionary_relationship_rows": [],
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }


def write(r):
    r["fingerprint"] = fingerprint({k: v for k, v in r.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(r, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    r = result_base()
    try:
        item_id = CONTRACT["sciencebase"]["item_id"]
        item, meta_bytes, final_url = request_json(f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json")
        if item.get("id") != item_id:
            raise RuntimeError(f"ScienceBase item id mismatch: {item.get('id')} != {item_id}")
        r["sciencebase_metadata"] = {
            "item_id": item_id,
            "title": item.get("title"),
            "metadata_bytes": meta_bytes,
            "final_host": urllib.parse.urlparse(final_url).netloc,
            "top_level_file_count": len(item.get("files", [])),
        }

        parsed = {}
        for name, spec in CONTRACT["response_independent_files"].items():
            raw, meta = get_allowed_file(item, name, spec)
            header, rows, encoding, delimiter = decode_csv(raw, name)
            roles = column_roles(header)
            profile_cols = sorted(set(sum(roles.values(), [])))
            parsed[name] = (header, rows)
            r["files"][name] = {
                **meta,
                "encoding": encoding,
                "delimiter": delimiter,
                "header": header,
                "row_count": len(rows),
                "blank_header_columns": [i for i, c in enumerate(header) if not str(c).strip()],
                "duplicate_header_names": sorted([k for k, v in Counter(header).items() if v > 1]),
                "candidate_roles": roles,
                "candidate_column_profiles": {c: profile_column(rows, c) for c in profile_cols},
            }

        d_header, d_rows = parsed["dbdictionary.csv"]
        r["dictionary_relationship_rows"] = dictionary_matches(d_rows, d_header)
        r["status"] = "gate0_response_free_profile_complete"
        r["reason"] = "Exact dbdictionary, locations and visits payloads were checksum-verified and profiled; all media/annotation/model response-bearing payloads remain unopened"
        write(r)
        return 0
    except Exception as exc:
        r["reason"] = f"{type(exc).__name__}: {exc}"
        write(r)
        return 1


if __name__ == "__main__":
    sys.exit(main())
