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
BUILD = ROOT / "build" / "guam_brown_treesnake_replication_2"
BUILD.mkdir(parents=True, exist_ok=True)
CONTRACT = json.loads((HERE / "source_contract.json").read_text())
OUT = BUILD / "gate0_effort_only.json"

ID_RE = re.compile(r"(^id$|trap.*id|id.*trap|station.*id|site.*id|trap$|station$|site$)", re.I)
LAT_RE = re.compile(r"(latitude|\blat\b|northing|utm.*y|^y$)", re.I)
LON_RE = re.compile(r"(longitude|\blon\b|\blong\b|easting|utm.*x|^x$)", re.I)
TIME_RE = re.compile(r"(date|time|day|week|occasion|period|start|end|effort|active|check)", re.I)


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get_json(url):
    req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"EOG-Guam-BTS-metadata/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        return json.loads(raw), len(raw)


def file_name(f):
    return str(f.get("name") or f.get("title") or "")


def download_url(f):
    for key in ("downloadUri", "url"):
        v = f.get(key)
        if isinstance(v, str) and v.startswith("http"):
            return v
    return None


def get_bytes(url):
    req = urllib.request.Request(url, headers={"Accept":"text/csv,text/plain,application/octet-stream,*/*;q=0.5","User-Agent":"EOG-Guam-BTS-effort-only/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type")


def decode_csv(raw):
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
        raise RuntimeError("effort CSV is neither UTF-8-SIG nor CP1252")
    try:
        delim = csv.Sniffer().sniff(text[:65536], delimiters=",;\t").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = list(reader.fieldnames or [])
    rows = list(reader)
    if not header:
        raise RuntimeError("effort CSV has no header")
    return header, rows, encoding, delim


def profile(rows, col):
    vals=[]; missing=0
    for r in rows:
        v=str(r.get(col) or "").strip()
        if v: vals.append(v)
        else: missing += 1
    return {"nonempty":len(vals),"missing":missing,"unique_count":len(set(vals)),"examples":sorted(set(vals))[:15]}


def finish(result, code=0):
    result["fingerprint"] = hashlib.sha256(canonical({k:v for k,v in result.items() if k!="fingerprint"})).hexdigest()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)+"\n")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return code


def main():
    result={
        "schema":"eog.guam_brown_treesnake_replication_2.gate0_effort_only.v1",
        "attempt_id":CONTRACT["attempt_id"],
        "status":"engineering_failure_pre_response",
        "reason":None,
        "item_metadata":{},
        "effort":{},
        "candidate_columns":{},
        "response_firewall":dict(CONTRACT["response_firewall"]),
    }
    try:
        item, meta_bytes = get_json(f"https://www.sciencebase.gov/catalog/item/{CONTRACT['sciencebase_item_id']}?format=json")
        if str(item.get("title") or "") != CONTRACT["sciencebase_item_title"]:
            raise RuntimeError(f"ScienceBase title drift: {item.get('title')!r}")
        files=[f for f in (item.get("files") or []) if isinstance(f,dict)]
        by_name={file_name(f):f for f in files}
        required=[CONTRACT["response_independent_file"],*CONTRACT["forbidden_files"]]
        missing=[n for n in required if n not in by_name]
        if missing:
            raise RuntimeError(f"required physical files missing from item metadata: {missing}")
        slim={}
        for name in required:
            f=by_name[name]
            slim[name]={"size":f.get("size"),"checksum":f.get("checksum"),"contentType":f.get("contentType"),"has_download_url":bool(download_url(f))}
        result["item_metadata"]={"metadata_bytes":meta_bytes,"file_count":len(files),"frozen_files":slim}

        effort_meta=by_name[CONTRACT["response_independent_file"]]
        url=download_url(effort_meta)
        if not url:
            raise RuntimeError("response-independent effort file has no public download URL in ScienceBase metadata")
        raw, final_url, ctype=get_bytes(url)
        expected_size=effort_meta.get("size")
        if expected_size is not None and int(expected_size)!=len(raw):
            raise RuntimeError(f"effort size mismatch: {len(raw)} != {expected_size}")
        actual_sha=hashlib.sha256(raw).hexdigest()
        header,rows,enc,delim=decode_csv(raw)
        ids=[c for c in header if ID_RE.search(c)]
        lats=[c for c in header if LAT_RE.search(c)]
        lons=[c for c in header if LON_RE.search(c)]
        times=[c for c in header if TIME_RE.search(c)]
        result["effort"]={
            "payload_requests":1,
            "payload_bytes":len(raw),
            "sha256":actual_sha,
            "final_host":urllib.parse.urlparse(final_url).netloc,
            "content_type":ctype,
            "encoding":enc,
            "delimiter":delim,
            "header":header,
            "row_count":len(rows),
        }
        result["candidate_columns"]={
            "identifier":{c:profile(rows,c) for c in ids},
            "latitude_or_y":{c:profile(rows,c) for c in lats},
            "longitude_or_x":{c:profile(rows,c) for c in lons},
            "temporal_effort":{c:profile(rows,c) for c in times},
        }
        if not rows:
            result["status"]="stop_effort_table_empty"; result["reason"]="response-independent effort table is empty"; return finish(result)
        if not ids:
            result["status"]="stop_effort_identifier_not_identifiable"; result["reason"]="no trap/site/station identifier candidate exists in effort table"; return finish(result)
        if not lats or not lons:
            result["status"]="stop_effort_geometry_not_identifiable"; result["reason"]="effort table does not contain response-independent two-coordinate geometry candidates"; return finish(result)
        if not times:
            result["status"]="stop_effort_temporal_axis_not_identifiable"; result["reason"]="effort table does not contain response-independent repeated-time/effort candidates"; return finish(result)
        result["status"]="gate0_effort_profile_pass_response_closed"
        result["reason"]="exact trap-effort file supplies identifier, two-coordinate geometry and temporal-effort candidates; capture and camera-transcription payloads remain unopened"
        return finish(result)
    except Exception as exc:
        result["reason"]=f"{type(exc).__name__}: {exc}"
        return finish(result,1)

if __name__=="__main__":
    raise SystemExit(main())
