#!/usr/bin/env python3
"""Read only first complete CSV headers from two frozen Dryad file IDs.

Uses strict 206 Range bounds. May physically transfer bytes beyond the first
line within the fixed prefix; it never parses or stores data rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))

from eog.v2.http_range_transport import (  # noqa: E402
    StrictHttpRangeTransport, HttpRangeTransportError,
)

PROTOCOL=ROOT/"validation/pyrgus_bam_header_gate_v1/protocol_v1.json"
PROTOCOL_COMMIT="e758455eebe1d223684f50318893766dfc472875"


def fingerprint(obj):
    return hashlib.sha256(json.dumps(
        obj,sort_keys=True,separators=(",",":"),allow_nan=False
    ).encode()).hexdigest()


def normalize(s):
    return re.sub("[^a-z0-9]+","",s.casefold())


def parse_first_header(prefix:bytes) -> list[str]:
    if not isinstance(prefix,bytes) or b"\n" not in prefix:
        raise ValueError("SOURCE_STOP_HEADER_NOT_COMPLETE_IN_DECLARED_PREFIX")
    line=prefix.split(b"\n",1)[0].rstrip(b"\r")
    if not line or b"\x00" in line:
        raise ValueError("SOURCE_STOP_HEADER_NOT_TEXT")
    try:
        decoded=line.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("SOURCE_STOP_HEADER_NOT_UTF8") from exc
    try:
        headers=next(csv.reader(io.StringIO(decoded),strict=True))
    except (csv.Error,StopIteration) as exc:
        raise ValueError("SOURCE_STOP_CSV_HEADER_PARSE") from exc
    names=[h.strip() for h in headers]
    if len(names)<2 or not all(names):
        raise ValueError("SOURCE_STOP_NOT_MULTICOLUMN_HEADER")
    if not all(any(ch.isalpha() for ch in s) for s in names):
        raise ValueError("SOURCE_STOP_HEADER_LACKS_LABELS")
    if len(set(normalize(s) for s in names)) != len(names):
        raise ValueError("SOURCE_STOP_DUPLICATE_NORMALIZED_COLUMN")
    return names


def classify_headers(files):
    heads={row["path"]:{normalize(h) for h in row["headers"]} for row in files}
    m=heads["Monitoring_data.csv"]
    s=heads["Site_data.csv"]
    common=sorted(m&s)
    candidate_site_keys=[
        c for c in common
        if c in ("site","siteid","patch","patchid","id","location","plot","locality")
    ]
    return {
        "common_headers":common,
        "candidate_join_header_names":candidate_site_keys,
        "same_patch_key_verified":False,
        "site_abiotic_header_candidates":sorted(
            c for c in s if any(t in c for t in ("solar","sun","irradiance","microclim","temperature"))
        ),
        "site_host_header_candidates":sorted(
            c for c in s if any(t in c for t in ("host","plant","filipendula","helianthemum"))
        ),
        "site_location_header_candidates":sorted(
            c for c in s if c in ("x","y","lat","latitude","lon","longitude","east","north","easting","northing") or "coord" in c
        ),
        "scientific_status":"A_B_M_PROXY_COLUMNS_UNVERIFIED_UNTIL_SAMPLING_UNIT_AND_MEASUREMENT_AUDIT"
    }


def run_gate(protocol_path=PROTOCOL, transport_factory=StrictHttpRangeTransport):
    raw=Path(protocol_path).read_bytes()
    contract=json.loads(raw)
    if contract["schema"]!="eog.pyrgus_bam_header_gate.v1":
        raise ValueError("unsupported protocol")
    receipt={
        "schema":"eog.pyrgus_bam_header_receipt.v1",
        "protocol_commit":PROTOCOL_COMMIT,
        "protocol_sha256":hashlib.sha256(raw).hexdigest(),
        "parent_metadata_fingerprint":contract["parent_metadata"]["metadata_fingerprint"],
        "status":"NOT_RUN",
        "file_results":[],
        "header_only_bytes_transferred":0,
        "biological_data_rows_parsed":0,
        "biology_models_fitted":0,
        "response_rows_may_be_present_within_prefix":True,
        "column_join_verified":False,
        "header_assessment":None
    }
    for entry in contract["parent_metadata"]["files"]:
        transport=None
        try:
            transport=transport_factory(
                entry["url"],
                allowed_hosts=tuple(contract["acquisition"]["allowed_hosts"]),
                maximum_archive_size=contract["parent_metadata"]["files"][0]["size"]+100,
            )
            transport.bind_frozen_size(entry["size"])
            n=contract["acquisition"]["max_bytes_per_file"]
            prefix=transport.read_range(0,n-1,role="frozen_csv_header")
            receipt["header_only_bytes_transferred"]+=len(prefix)
            headers=parse_first_header(prefix)
            receipt["file_results"].append({
                "path":entry["name"],"file_id":entry["file_id"],
                "frozen_size":entry["size"],
                "repository_digest":entry["digest"],
                "repository_digest_verified_from_prefix":False,
                "transferred_prefix_sha256":hashlib.sha256(prefix).hexdigest(),
                "header_columns_n":len(headers),"headers":headers
            })
        except (HttpRangeTransportError, ValueError, RuntimeError, TypeError) as exc:
            reason=str(exc)
            if "HTTP 403" in reason:
                status="SOURCE_STOP_HTTP_403"
            elif "HTTP 429" in reason:
                status="SOURCE_STOP_HTTP_429"
            elif "HTTP 200" in reason:
                status="SOURCE_STOP_RANGE_UNSUPPORTED_HTTP_200"
            elif reason.startswith("SOURCE_STOP_"):
                status=reason
            else:
                status="SOURCE_STOP_RANGE_OR_HEADER"
            receipt["status"]=status
            receipt["stopped_at_file_id"]=entry["file_id"]
            receipt["transport_error_class"]=type(exc).__name__
            receipt["fingerprint"]=fingerprint(receipt)
            return receipt
    receipt["header_assessment"]=classify_headers(receipt["file_results"])
    receipt["status"]="HEADERS_PARSED_NO_BIOLOGY__PATCH_JOIN_NOT_VERIFIED"
    receipt["fingerprint"]=fingerprint(receipt)
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    r=run_gate()
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("PYRGUS_HEADER_GATE="+json.dumps({
        "status":r["status"],"verified_headers":len(r["file_results"]),
        "transferred_prefix_bytes":r["header_only_bytes_transferred"],
        "data_rows_parsed":r["biological_data_rows_parsed"],
        "fingerprint":r["fingerprint"]
    },sort_keys=True))


if __name__=="__main__":
    main()
