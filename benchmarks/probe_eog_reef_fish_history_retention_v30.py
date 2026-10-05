#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
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


def _resolve_metadata_source() -> tuple[str, bytes, dict]:
    preferred = f"bcodmo_dataset_{TARGET_BCODMO_ID}"
    info_url = f"{ERDDAP}/info/{preferred}/index.csv"
    try:
        payload = _get(info_url)
        return preferred, payload, {
            "mode": "direct_erddap_info",
            "info_url": info_url,
        }
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise

    # Older BCO-DMO datasets may not be exposed in the current ERDDAP catalog.
    # Fall back to the public BCO-DMO metadata page/API without requesting data rows.
    api_url = f"https://www.bco-dmo.org/api/dataset/{TARGET_BCODMO_ID}"
    try:
        api_payload = _get(api_url)
        text = api_payload.decode("utf-8", errors="replace")
        return "", api_payload, {
            "mode": "bcodmo_public_api",
            "api_url": api_url,
            "content_type": "json_or_metadata",
            "text_preview": text[:2000],
        }
    except urllib.error.HTTPError as api_error:
        if api_error.code not in {403, 404}:
            raise

    page_url = f"https://www.bco-dmo.org/dataset/{TARGET_BCODMO_ID}"
    page_payload = _get(page_url)
    page_text = page_payload.decode("utf-8", errors="replace")
    hrefs = sorted(set(re.findall(r'href=[\"\\\']([^\"\\\']+)[\"\\\']', page_text)))
    csv_links = [
        href for href in hrefs
        if ".csv" in href.lower()
        or "datadocs.bco-dmo.org" in href.lower()
        or "erddap" in href.lower()
    ]
    return "", page_payload, {
        "mode": "bcodmo_dataset_page",
        "page_url": page_url,
        "candidate_data_links": csv_links,
        "page_sha256": _sha256(page_payload),
    }


def _extract_api_schema(payload: bytes) -> dict:
    data = json.loads(payload.decode("utf-8"))
    urls = set()
    relevant = []
    key_names = set()
    terms = (
        "surviv", "aggress", "arrival", "timing", "compet",
        "habitat", "complex", "reef", "block", "date",
        "pocillopora", "treatment", "replicate",
    )

    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                key_names.add(str(key))
                walk(item, path + [str(key)])
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, path + [str(i)])
        elif isinstance(value, str):
            low = value.lower()
            if (
                value.startswith("http://")
                or value.startswith("https://")
                or ".csv" in low
            ):
                urls.add(value)
            if any(term in low for term in terms):
                relevant.append(
                    {
                        "path": "/".join(path),
                        "value": value[:4000],
                    }
                )

    walk(data, [])

    parameter_nodes = []
    graph = data.get("@graph", []) if isinstance(data, dict) else []
    for wrapper in graph:
        if not isinstance(wrapper, dict):
            continue
        for node_id, node in wrapper.items():
            if "dataset-parameter/" not in str(node_id):
                continue
            literals = []
            def collect_literals(value, path):
                if isinstance(value, dict):
                    if "@value" in value and isinstance(value["@value"], (str, int, float)):
                        literals.append(
                            {
                                "path": "/".join(path + ["@value"]),
                                "value": str(value["@value"]),
                            }
                        )
                    for key, item in value.items():
                        if key != "@value":
                            collect_literals(item, path + [str(key)])
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        collect_literals(item, path + [str(i)])
                elif isinstance(value, (str, int, float)):
                    literals.append(
                        {"path": "/".join(path), "value": str(value)}
                    )
            collect_literals(node, [])
            parameter_nodes.append(
                {
                    "id": str(node_id),
                    "literals": literals,
                }
            )

    return {
        "urls": sorted(urls),
        "relevant_literals": relevant[:500],
        "jsonld_predicates": sorted(key_names),
        "dataset_parameters": parameter_nodes,
    }


def _parameter_metadata_from_ids(api_schema: dict | None) -> list[dict]:
    if not api_schema:
        return []
    ids = []
    for url in api_schema.get("urls", []):
        match = re.search(r"dataset-parameter/(\\d+)", url)
        if match:
            ids.append(match.group(1))
    output = []
    for parameter_id in sorted(set(ids), key=int):
        endpoints = (
            f"https://www.bco-dmo.org/api/dataset-parameter/{parameter_id}",
            f"https://lod.bco-dmo.org/id/dataset-parameter/{parameter_id}",
        )
        record = {"id": int(parameter_id), "attempts": []}
        for endpoint in endpoints:
            try:
                payload = _get(endpoint)
                text = payload.decode("utf-8", errors="replace")
                attempt = {
                    "url": endpoint,
                    "sha256": _sha256(payload),
                    "bytes": len(payload),
                }
                try:
                    parsed = json.loads(text)
                    literals = []
                    def walk(value, path):
                        if isinstance(value, dict):
                            for key, item in value.items():
                                walk(item, path + [str(key)])
                        elif isinstance(value, list):
                            for i, item in enumerate(value):
                                walk(item, path + [str(i)])
                        elif isinstance(value, (str, int, float, bool)):
                            sval = str(value)
                            if (
                                len(sval) <= 1000
                                and not sval.startswith("http://www.w3.org/")
                                and not sval.startswith("http://purl.org/")
                            ):
                                literals.append(
                                    {"path": "/".join(path), "value": sval}
                                )
                    walk(parsed, [])
                    attempt["format"] = "json"
                    attempt["literals"] = literals[:200]
                except json.JSONDecodeError:
                    attempt["format"] = "text"
                    clean = re.sub(r"<[^>]+>", " ", text)
                    clean = re.sub(r"\\s+", " ", clean).strip()
                    attempt["text"] = clean[:4000]
                record["attempts"].append(attempt)
                break
            except urllib.error.HTTPError as error:
                record["attempts"].append(
                    {"url": endpoint, "http_error": int(error.code)}
                )
        output.append(record)
    return output


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
    dataset_id, metadata_payload, resolution = _resolve_metadata_source()
    if resolution["mode"] == "direct_erddap_info":
        parsed = _parse_info(metadata_payload)
        api_schema = None
    elif resolution["mode"] == "bcodmo_public_api":
        parsed = {
            "variables": [],
            "global_attributes": {},
            "variable_attributes": {},
        }
        api_schema = _extract_api_schema(metadata_payload)
    else:
        parsed = {
            "variables": [],
            "global_attributes": {},
            "variable_attributes": {},
        }
        api_schema = None
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

    parameter_metadata = _parameter_metadata_from_ids(api_schema)

    result = {
        "schema":"eog.reef_fish_history_retention.metadata_probe.v30",
        "status":"metadata_materialized_before_response_access",
        "bcodmo_dataset_id":int(TARGET_BCODMO_ID),
        "erddap_dataset_id": dataset_id or None,
        "metadata_source_resolution": resolution,
        "metadata_payload_sha256": _sha256(metadata_payload),
        "metadata": parsed,
        "bcodmo_api_schema": api_schema,
        "dataset_parameter_metadata": parameter_metadata,
        "semantic_candidates": candidates,
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
