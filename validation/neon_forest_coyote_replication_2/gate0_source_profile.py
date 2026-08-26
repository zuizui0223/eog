from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "build" / "neon_forest_coyote_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_source_profile.json"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fp(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "EOG-NEON-coyote-metadata/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw), r.geturl()


def get_bytes(url: str):
    req = urllib.request.Request(url, headers={"Accept": "text/csv,application/octet-stream,*/*;q=0.8", "User-Agent": "EOG-NEON-coyote-response-free/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def checksum_parts(value):
    text = str(value or "")
    if ":" in text:
        a, b = text.split(":", 1)
        return a.lower(), b.lower()
    return None, text.lower()


def file_meta(record: dict, filename: str):
    matches = [f for f in record.get("files", []) if f.get("key") == filename]
    if len(matches) != 1:
        raise RuntimeError(f"expected one file {filename}, observed {len(matches)}")
    f = matches[0]
    algo, digest = checksum_parts(f.get("checksum"))
    url = f.get("links", {}).get("content") or f.get("links", {}).get("self")
    if not url:
        quoted = urllib.parse.quote(filename, safe="")
        url = f"https://zenodo.org/records/{int(record['id'])}/files/{quoted}?download=1"
    return {
        "record_id": int(record["id"]),
        "filename": filename,
        "size": int(f.get("size") or 0),
        "checksum_algorithm": algo,
        "checksum": digest,
        "download_url": url,
    }


def decode_csv(raw: bytes, name: str):
    text = None
    enc = None
    for candidate in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            text = raw.decode(candidate)
            enc = candidate
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError(f"cannot decode {name}")
    try:
        delim = csv.Sniffer().sniff(text[:65536], delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    rows = list(reader)
    if not header:
        raise RuntimeError(f"{name} has no header")
    return header, rows, enc, delim


def norm(s: str):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")


def semantic_candidates(header):
    out = {"deployment_id": [], "latitude": [], "longitude": [], "start": [], "end": [], "subproject": []}
    for c in header:
        n = norm(c)
        toks = set(n.split("_"))
        if n in {"deployment_id", "deploymentid"} or ("deployment" in toks and "id" in toks):
            out["deployment_id"].append(c)
        if n in {"latitude", "lat", "decimal_latitude"} or "latitude" in toks:
            out["latitude"].append(c)
        if n in {"longitude", "lon", "long", "decimal_longitude"} or "longitude" in toks:
            out["longitude"].append(c)
        if n in {"start", "start_date", "start_datetime", "start_time"} or ("start" in toks and toks.intersection({"date", "time", "datetime"})):
            out["start"].append(c)
        if n in {"end", "end_date", "end_datetime", "end_time"} or ("end" in toks and toks.intersection({"date", "time", "datetime"})):
            out["end"].append(c)
        if n in {"subproject", "subproject_name", "subproject_id", "project_id", "project_name"} or "subproject" in toks:
            out["subproject"].append(c)
    return out


def profile_columns(rows, header):
    out = {}
    for c in header:
        vals = [str(r.get(c) or "").strip() for r in rows]
        nonempty = [v for v in vals if v]
        out[c] = {
            "nonempty": len(nonempty),
            "missing": len(vals) - len(nonempty),
            "unique_count": len(set(nonempty)),
        }
    return out


def write(result):
    result["fingerprint"] = fp({k: v for k, v in result.items() if k != "fingerprint"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


def main():
    result = {
        "schema": "eog.neon_forest_coyote_replication_2.gate0_source_profile.v1",
        "attempt_id": CONTRACT["attempt_id"],
        "status": "engineering_failure_pre_response",
        "reason": None,
        "record": {},
        "deployments": {},
        "subprojects": {},
        "response_metadata_only": {},
        "response_firewall": dict(CONTRACT["response_firewall"]),
    }
    try:
        rid = int(CONTRACT["zenodo_record_id"])
        rec, meta_bytes, final_meta_url = get_json(f"https://zenodo.org/api/records/{rid}")
        if int(rec.get("id")) != rid:
            raise RuntimeError("Zenodo record id drift")

        expected = {
            CONTRACT["response_independent"]["deployments"]["filename"]: CONTRACT["response_independent"]["deployments"]["expected_md5"],
            CONTRACT["response_independent"]["subprojects"]["filename"]: CONTRACT["response_independent"]["subprojects"]["expected_md5"],
            CONTRACT["forbidden_response"]["filename"]: CONTRACT["forbidden_response"]["expected_md5"],
        }
        observed_keys = [f.get("key") for f in rec.get("files", [])]
        if any(name not in observed_keys for name in expected):
            raise RuntimeError(f"frozen file identity missing; observed={observed_keys}")

        metas = {name: file_meta(rec, name) for name in expected}
        for name, want_md5 in expected.items():
            m = metas[name]
            if m["checksum_algorithm"] not in {"md5", None}:
                raise RuntimeError(f"unexpected checksum algorithm for {name}: {m['checksum_algorithm']}")
            if m["checksum"] != want_md5:
                raise RuntimeError(f"metadata MD5 mismatch for {name}: {m['checksum']} != {want_md5}")
            if m["size"] <= 0:
                raise RuntimeError(f"nonpositive metadata size for {name}")

        response_name = CONTRACT["forbidden_response"]["filename"]
        response_meta = dict(metas[response_name])
        response_meta.pop("download_url", None)
        response_meta.update({
            "payload_requests": 0,
            "payload_bytes_opened": 0,
            "header_bytes_opened": 0,
            "rows_opened": False,
            "values_opened": False,
        })
        result["response_metadata_only"] = response_meta

        profiles = {}
        for role in ("deployments", "subprojects"):
            spec = CONTRACT["response_independent"][role]
            m = metas[spec["filename"]]
            raw, final_url, ctype = get_bytes(m["download_url"])
            if len(raw) != m["size"]:
                raise RuntimeError(f"size mismatch for {spec['filename']}: {len(raw)} != {m['size']}")
            actual = hashlib.md5(raw).hexdigest()
            if actual != spec["expected_md5"]:
                raise RuntimeError(f"payload MD5 mismatch for {spec['filename']}: {actual} != {spec['expected_md5']}")
            header, rows, enc, delim = decode_csv(raw, role)
            profiles[role] = {
                "filename": spec["filename"],
                "size": len(raw),
                "md5": actual,
                "content_type": ctype,
                "final_host": urllib.parse.urlparse(final_url).netloc,
                "encoding": enc,
                "delimiter": delim,
                "header": header,
                "row_count": len(rows),
                "semantic_candidates": semantic_candidates(header),
                "column_profiles": profile_columns(rows, header),
            }

        result["deployments"] = profiles["deployments"]
        result["subprojects"] = profiles["subprojects"]
        result["record"] = {
            "record_id": rid,
            "metadata_bytes": meta_bytes,
            "metadata_host": urllib.parse.urlparse(final_meta_url).netloc,
            "file_keys": observed_keys,
        }
        result["status"] = "gate0_pass_source_separation_and_response_independent_profiles"
        result["reason"] = "exact Zenodo file identities and MD5s verified; only deployment and subproject CSV payloads were opened; sequence response remained metadata-only"
        write(result)
        return 0
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__}: {exc}"
        write(result)
        return 1


if __name__ == "__main__":
    sys.exit(main())
