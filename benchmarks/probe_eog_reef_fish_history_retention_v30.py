#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.parse
import urllib.request

TARGET_BCODMO_ID = "726890"
ERDDAP = "https://erddap.bco-dmo.org/erddap"


def _get(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-v30-metadata-probe/1.0"},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        payload = response.read()
    if not payload:
        raise RuntimeError(f"empty response: {url}")
    return payload


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _search_dataset() -> tuple[str, bytes]:
    query = urllib.parse.quote(TARGET_BCODMO_ID)
    url = (
        f"{ERDDAP}/search/index.csv"
        f"?page=1&itemsPerPage=1000&searchFor={query}"
    )
    payload = _get(url)
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    matches = []
    for row in rows:
        text = " ".join(str(value or "") for value in row.values())
        if TARGET_BCODMO_ID in text:
            matches.append(row)
    ids = []
    for row in matches:
        for key, value in row.items():
            if key and key.lower().replace(" ", "") in {"datasetid","dataset_id"}:
                if value:
                    ids.append(value)
    ids = sorted(set(ids))
    preferred = f"bcodmo_dataset_{TARGET_BCODMO_ID}"
    if preferred in ids:
        return preferred, payload
    if len(ids) == 1:
        return ids[0], payload
    raise RuntimeError(
        "could not uniquely resolve ERDDAP dataset for BCO-DMO 726890: "
        + json.dumps({"ids": ids, "matches": matches}, sort_keys=True)
    )


def _parse_info(payload: bytes) -> dict:
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))
    variables = []
    global_attributes = {}
    variable_attributes = {}
    for row in rows:
        row_type = row.get("Row Type") or row.get("rowType") or ""
        variable = row.get("Variable Name") or row.get("variableName") or ""
        attribute = row.get("Attribute Name") or row.get("attributeName") or ""
        value = row.get("Value") or row.get("value") or ""
        data_type = row.get("Data Type") or row.get("dataType") or ""
        if row_type == "variable":
            variables.append({"name": variable, "data_type": data_type})
        elif row_type == "attribute":
            if variable == "NC_GLOBAL":
                if attribute in {
                    "title","summary","infoUrl","doi","license",
                    "time_coverage_start","time_coverage_end"
                }:
                    global_attributes[attribute] = value
            else:
                if attribute in {
                    "long_name","standard_name","units","comment",
                    "actual_range","ioos_category"
                }:
                    variable_attributes.setdefault(variable, {})[attribute] = value
    return {
        "variables": variables,
        "global_attributes": global_attributes,
        "variable_attributes": variable_attributes,
    }


def run() -> dict:
    dataset_id, search_payload = _search_dataset()
    info_url = f"{ERDDAP}/info/{dataset_id}/index.csv"
    info_payload = _get(info_url)
    parsed = _parse_info(info_payload)
    names = [item["name"] for item in parsed["variables"]]
    lowered = {name.lower(): name for name in names}

    keyword_groups = {
        "reef_or_unit": ["reef","rep","id","site"],
        "history_or_timing": ["arrival","timing","competition","competitor","priority","treatment"],
        "habitat": ["habitat","complex","pocillopora","coral"],
        "block_or_date": ["block","date","run"],
        "survival": ["survival","survive","alive"],
        "aggression": ["aggression","aggressive","chase","bite","pca"],
    }
    candidates = {}
    for group, keywords in keyword_groups.items():
        candidates[group] = [
            name for name in names
            if any(keyword in name.lower() for keyword in keywords)
        ]

    result = {
        "schema":"eog.reef_fish_history_retention.metadata_probe.v30",
        "status":"metadata_materialized_before_response_access",
        "bcodmo_dataset_id":int(TARGET_BCODMO_ID),
        "erddap_dataset_id":dataset_id,
        "search_sha256":_sha256(search_payload),
        "info_sha256":_sha256(info_payload),
        "info_url":info_url,
        "metadata":parsed,
        "semantic_candidates":candidates,
        "response_rows_accessed":False,
        "scoring_performed":False,
    }
    fp=json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    result["fingerprint"]=_sha256(fp)
    return result


def main() -> None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
