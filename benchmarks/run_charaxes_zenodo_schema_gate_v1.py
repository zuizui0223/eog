#!/usr/bin/env python3
"""Charaxes: one verified file transfer per source; inspect dictionary + CSV headers.

Complete CSV bytes are necessarily read into ephemeral memory for MD5 verification.
No scientific data rows are parsed, summarized, logged, saved or model-scored.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"validation/charaxes_zenodo_schema_v1/protocol_v1.json"
PROTOCOL_COMMIT="82fcc93096d85f7994304e10bd2a2f81f131d599"


def fingerprint(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,
       separators=(",",":"),allow_nan=False,ensure_ascii=True).encode()).hexdigest()


def fetch_once(entry):
    url=entry["url"]
    parsed=urlsplit(url)
    if parsed.scheme!="https" or parsed.hostname!="zenodo.org":
        raise ValueError("SOURCE_STOP_UNAUTHORIZED_FILE_HOST")
    request=Request(url,headers={
        "Accept":"text/csv,application/octet-stream;q=0.9",
        "Accept-Encoding":"identity",
        "User-Agent":"EOG-BAM-CharaxesSchemaGate/1"
    })
    with urlopen(request,timeout=35) as response:
        final=urlsplit(response.geturl())
        if final.scheme!="https" or final.hostname!="zenodo.org":
            raise ValueError("SOURCE_STOP_REDIRECT_HOST")
        if response.status!=200:
            raise ValueError(f"SOURCE_STOP_HTTP_{response.status}")
        if (response.headers.get("Content-Encoding") or "identity").lower()!="identity":
            raise ValueError("SOURCE_STOP_CONTENT_ENCODING")
        body=response.read(entry["size"]+1)
    if len(body)!=entry["size"]:
        raise ValueError("SOURCE_STOP_BYTE_SIZE_MISMATCH")
    return body


def verified_payload(raw,entry):
    if not isinstance(raw,bytes) or len(raw)!=entry["size"]:
        raise ValueError("SOURCE_STOP_BYTE_SIZE_MISMATCH")
    if hashlib.md5(raw).hexdigest()!=entry["md5"]:
        raise ValueError("SOURCE_STOP_MD5_MISMATCH")
    return hashlib.sha256(raw).hexdigest()


def first_header(raw):
    # csv.reader is invoked on *only the first physical line*, never data rows.
    line=raw.split(b"\n",1)[0].rstrip(b"\r")
    if not line or b"\x00" in line:
        raise ValueError("SOURCE_STOP_MISSING_CSV_FIRST_LINE")
    try: text=line.decode("utf-8-sig")
    except UnicodeError as ex:
        raise ValueError("SOURCE_STOP_NON_UTF8_HEADER") from ex
    best=None
    for sep in (",",";","\t"):
        cols=next(csv.reader(io.StringIO(text),delimiter=sep),[])
        if len(cols)>=2 and all(x.strip() for x in cols):
            if best is None or len(cols)>len(best):
                best=[x.strip() for x in cols]
    if best is None or len(set(best))!=len(best):
        raise ValueError("SOURCE_STOP_HEADER_PARSE")
    return best


def source_semantics(file_summaries):
    data=next(x for x in file_summaries if x["name"]=="C_jasius_reduced_dataset.csv")
    names=[n.lower().replace("_","").replace(" ","") for n in data["first_line_header"]]
    flags={
        "possible_time":any("year" in x or "date" in x for x in names),
        "possible_trap_identifier":any("trap" in x or "site" in x or "point" in x for x in names),
        "possible_focal_observation":any("charaxes" in x or "abundan" in x or "count" in x or "presen" in x or "occup" in x for x in names),
        "possible_host_cover":any("cover" in x or "arbut" in x or "host" in x for x in names),
        "possible_host_distance":any("distance" in x or "dist" in x for x in names),
        "possible_connectivity":any("connect" in x or "hanski" in x for x in names),
        "possible_habitat_class":any("forest" in x or "habitat" in x or "wood" in x for x in names),
        "possible_coordinates":any(x in ("lat","latitude","lon","longitude","x","y","easting","northing") or "coord" in x for x in names)
    }
    return {
        "column_token_flags":flags,
        "B_host_plant_proxy_qualified":False,
        "M_movement_only_proxy_qualified":False,
        "A_abiotic_tolerance_qualified":False,
        "G_observation_and_detection_qualified":False,
        "site_year_unique_join_qualified":False,
        "reason":"Column-name presence does not establish sampling unit, independent measurement, geographic connectivity or observation effort."
    }


def run_gate(protocol_path=PROTOCOL, fetch=fetch_once):
    raw_contract=Path(protocol_path).read_bytes()
    p=json.loads(raw_contract)
    if p.get("schema")!="eog.charaxes_zenodo_content_schema_gate.v1":
        raise ValueError("unsupported protocol")
    files=p["parent"]["files"]
    if [x["name"] for x in files]!=[
        "C_jasius_readme.csv","C_jasius_reduced_dataset.csv"
    ]:
        raise ValueError("source list mismatch")
    receipt={
        "schema":"eog.charaxes_zenodo_schema_receipt.v1",
        "protocol_commit":PROTOCOL_COMMIT,
        "protocol_sha256":hashlib.sha256(raw_contract).hexdigest(),
        "status":"NOT_RUN",
        "files_verified":[],
        "requests_attempted":0,"raw_bytes_transferred":0,
        "biological_data_bytes_transferred":0,
        "biological_data_rows_parsed":0,
        "ecological_scores":0,
        "source_semantics":None
    }
    for entry in files:
        try:
            receipt["requests_attempted"]+=1
            body=fetch(entry)
            receipt["raw_bytes_transferred"]+=len(body)
            if entry["role"]=="biological_data":
                receipt["biological_data_bytes_transferred"]+=len(body)
            sha=verified_payload(body,entry)
            header=first_header(body)
            receipt["files_verified"].append({
                "name":entry["name"],"file_size":len(body),
                "md5":entry["md5"],"sha256":sha,
                "first_line_header":header
            })
        except HTTPError as ex:
            receipt["status"]=f"SOURCE_STOP_HTTP_{ex.code}"
            receipt["stopped_at_filename"]=entry["name"]
            break
        except URLError:
            receipt["status"]="SOURCE_STOP_NETWORK_TRANSPORT"
            receipt["stopped_at_filename"]=entry["name"]
            break
        except (ValueError,OSError,TypeError) as ex:
            receipt["status"]=(
                str(ex) if str(ex).startswith("SOURCE_STOP_")
                else "SOURCE_STOP_SCHEMA_OR_TRANSPORT"
            )
            receipt["stopped_at_filename"]=entry["name"]
            break
    else:
        receipt["source_semantics"]=source_semantics(receipt["files_verified"])
        receipt["status"]="FILES_MD5_VERIFIED_HEADERS_ONLY__ECOLOGICAL_AXES_UNQUALIFIED"
    receipt["fingerprint"]=fingerprint(receipt)
    return receipt


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=run_gate()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("CHARAXES_SCHEMA_GATE="+json.dumps({
        "status":r["status"],"verified_files":len(r["files_verified"]),
        "data_bytes_transferred":r["biological_data_bytes_transferred"],
        "data_rows_parsed":r["biological_data_rows_parsed"],
        "fingerprint":r["fingerprint"]
    },sort_keys=True))


if __name__=="__main__":
    main()
