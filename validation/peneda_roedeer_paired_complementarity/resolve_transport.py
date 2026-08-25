from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_CONTRACT = HERE / "source_contract.json"
TRANSPORT_CONTRACT = HERE / "transport_contract.json"
RESOLUTION = HERE / "transport_resolution.json"


def bounded_json(url: str, *, user_agent: str, maximum: int = 2_000_000) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": "application/json", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(maximum + 1)
        status = int(getattr(response, "status", 200))
    if status != 200 or len(body) > maximum:
        raise RuntimeError(f"bounded metadata request failed: status={status}, bytes={len(body)}, url={url}")
    return json.loads(body.decode("utf-8"))


def resolve_one(role: str, spec: dict, audit: dict) -> dict:
    doi = str(spec["supplement_doi"])
    encoded = urllib.parse.quote(doi, safe="")
    datacite_url = f"https://api.datacite.org/dois/{encoded}"
    datacite = bounded_json(datacite_url, user_agent="EOG-Peneda-transport-metadata/1.0")
    audit["datacite_metadata_requests"] += 1
    attrs = (datacite.get("data") or {}).get("attributes") or {}
    observed_doi = str(attrs.get("doi") or "")
    if observed_doi.casefold() != doi.casefold():
        raise RuntimeError(f"DataCite DOI identity mismatch for {role}: {observed_doi!r} != {doi!r}")
    landing = str(attrs.get("url") or "")
    match = re.search(r"zenodo\.org/(?:record|records)/(\d+)", landing)
    if not match:
        raise RuntimeError(f"DataCite landing URL is not a Zenodo record for {role}: {landing!r}")
    record_id = int(match.group(1))
    zenodo_url = f"https://zenodo.org/api/records/{record_id}"
    record = bounded_json(zenodo_url, user_agent="EOG-Peneda-transport-metadata/1.0")
    audit["zenodo_metadata_requests"] += 1
    metadata = record.get("metadata") or {}
    zenodo_doi = str(metadata.get("doi") or "")
    if zenodo_doi.casefold() != doi.casefold():
        raise RuntimeError(f"Zenodo DOI identity mismatch for {role}: {zenodo_doi!r} != {doi!r}")
    expected_name = str(spec["zenodo_file_name"])
    files = [row for row in (record.get("files") or []) if str(row.get("key") or "") == expected_name]
    if len(files) != 1:
        raise RuntimeError(
            f"Zenodo file identity did not resolve uniquely for {role}: expected={expected_name!r}, matches={len(files)}"
        )
    row = files[0]
    links = row.get("links") or {}
    content_url = str(links.get("content") or links.get("self") or "")
    if not content_url:
        raise RuntimeError(f"Zenodo file content URL missing for {role}")
    return {
        "role": role,
        "supplement_doi": doi,
        "datacite_landing_url": landing,
        "zenodo_record_id": record_id,
        "zenodo_record_url": zenodo_url,
        "file_name": expected_name,
        "file_size": int(row.get("size") or 0),
        "file_checksum": str(row.get("checksum") or ""),
        "content_url": content_url,
    }


def main() -> None:
    transport = json.loads(TRANSPORT_CONTRACT.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_CONTRACT.read_text(encoding="utf-8"))
    audit = {
        "schema": "eog.peneda_roedeer_transport_resolution.v1",
        "candidate_id": transport["candidate_id"],
        "status": "not_evaluated",
        "datacite_metadata_requests": 0,
        "zenodo_metadata_requests": 0,
        "supplement_file_payload_requests": 0,
        "supplement_file_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        deployment = resolve_one("deployment", transport["deployment"], audit)
        response = resolve_one("response", transport["response"], audit)
    except Exception as exc:
        audit.update(status="stop_transport_metadata_resolution", reason=repr(exc))
        RESOLUTION.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(audit, indent=2, sort_keys=True))
        raise SystemExit(3)

    if deployment["file_size"] <= 0 or response["file_size"] <= 0:
        audit.update(status="stop_transport_metadata_resolution", reason="resolved supplement file size is non-positive")
        RESOLUTION.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(audit, indent=2, sort_keys=True))
        raise SystemExit(3)

    source["response_firewall"]["deployment_geometry_url"] = deployment["content_url"]
    source["response_firewall"]["response_url"] = response["content_url"]
    source["response_firewall"]["resolved_transport_metadata"] = {
        "deployment_supplement_doi": deployment["supplement_doi"],
        "deployment_zenodo_record_id": deployment["zenodo_record_id"],
        "deployment_file_name": deployment["file_name"],
        "deployment_file_size": deployment["file_size"],
        "deployment_file_checksum": deployment["file_checksum"],
        "response_supplement_doi": response["supplement_doi"],
        "response_zenodo_record_id": response["zenodo_record_id"],
        "response_file_name": response["file_name"],
        "response_file_size": response["file_size"],
        "response_file_checksum": response["file_checksum"],
    }
    SOURCE_CONTRACT.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    audit.update(
        status="transport_metadata_resolved",
        deployment=deployment,
        response=response,
        supplement_file_payload_requests=0,
        supplement_file_payload_bytes_opened=0,
        response_header_bytes_opened=0,
        response_rows_opened=False,
        response_values_opened=False,
        model_fits=0,
        heldout_scores=0,
    )
    RESOLUTION.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
