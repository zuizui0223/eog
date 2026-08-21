from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import urllib.parse
import urllib.request

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)


ROOT = Path(__file__).resolve().parent
DRYAD = "https://datadryad.org"
UA = "EOG-Snapshot-USA-WTD-response-blind-preflight/2.0"


def _json_get(url: str, audit: dict) -> dict:
    audit["metadata_urls"].append(url)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json", "X-API-Version": "2.1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = response.read(8_000_001)
    if len(payload) > 8_000_000:
        raise RuntimeError(f"Dryad metadata exceeded bounded cap: {url}")
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Dryad metadata root must be an object: {url}")
    return value


def _absolute(href: str) -> str:
    return urllib.parse.urljoin(DRYAD, href)


def _latest_files(source: dict, audit: dict) -> tuple[dict, list[dict]]:
    encoded = urllib.parse.quote(f"doi:{source['doi']}", safe="")
    dataset = _json_get(f"{DRYAD}/api/v2/datasets/{encoded}", audit)
    version_href = dataset.get("_links", {}).get("stash:version", {}).get("href")
    if not version_href:
        raise RuntimeError(f"Dryad dataset has no latest-version link: {source['doi']}")
    version = _json_get(_absolute(version_href), audit)
    files_href = version.get("_links", {}).get("stash:files", {}).get("href")
    if not files_href:
        version_id = version.get("id")
        if not version_id:
            raise RuntimeError("Dryad version has neither files link nor id")
        files_href = f"/api/v2/versions/{version_id}/files"
    listing = _json_get(_absolute(files_href), audit)
    files = listing.get("_embedded", {}).get("stash:files", [])
    if not isinstance(files, list):
        raise RuntimeError("Dryad files listing malformed")
    return version, [row for row in files if isinstance(row, dict)]


def _file_id(row: dict) -> int:
    self_href = row.get("_links", {}).get("self", {}).get("href")
    if not self_href:
        raise RuntimeError(f"Dryad file lacks self link: {row.get('path')}")
    try:
        return int(str(self_href).rstrip("/").split("/")[-1])
    except Exception as exc:
        raise RuntimeError(f"cannot resolve Dryad file id: {self_href}") from exc


def _file_identity(row: dict) -> dict:
    return {
        "file_id": _file_id(row),
        "path": row.get("path"),
        "size": row.get("size"),
        "mimeType": row.get("mimeType"),
        "digest": row.get("digest"),
        "digestType": row.get("digestType"),
        "api_download_href": row.get("_links", {}).get("stash:download", {}).get("href"),
    }


def _download_public_deployment(row: dict, expected_name: str, audit: dict) -> bytes:
    fid = _file_id(row)
    # Dryad's public landing-page file links use this exact file ID. The API download
    # endpoint may require authorization even for public datasets, so transport is kept
    # separate from identity resolution. No response file ID is ever passed here.
    url = f"{DRYAD}/downloads/file_stream/{fid}"
    audit["deployment_download_urls"].append(url)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
            "Referer": f"{DRYAD}/dataset/doi:{urllib.parse.quote('10.5061/dryad', safe='')}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = response.read(5_000_001)
        final_url = response.geturl()
    if len(payload) > 5_000_000:
        raise RuntimeError(f"deployment file exceeded 5 MB cap: {expected_name}")
    expected_size = int(row.get("size"))
    if len(payload) != expected_size:
        raise RuntimeError(
            f"Dryad deployment byte-size drift for {expected_name}: {len(payload)} != {expected_size}"
        )
    if str(row.get("digestType") or "").casefold() == "sha-256":
        observed = hashlib.sha256(payload).hexdigest()
        if observed != row.get("digest"):
            raise RuntimeError(f"Dryad SHA-256 drift for {expected_name}")
    audit["deployment_final_urls"].append(final_url)
    return payload


def run(output_root: Path) -> dict:
    contract = json.loads((ROOT / "source_contract.json").read_text(encoding="utf-8"))
    output_root.mkdir(parents=True, exist_ok=True)
    input_root = output_root.parent / "input"
    input_root.mkdir(parents=True, exist_ok=True)
    audit: dict = {
        "attempt_id": contract["attempt_id"],
        "metadata_urls": [],
        "deployment_download_urls": [],
        "deployment_final_urls": [],
        "response_download_urls": [],
        "response_bytes_opened": 0,
        "response_rows_opened": False,
        "source_audit": [],
        "observed_deployment_headers": {},
        "errors": [],
    }

    deployment_payloads: list[tuple[dict, bytes]] = []
    for source in contract["sources"]:
        version, files = _latest_files(source, audit)
        by_path = {str(row.get("path")): row for row in files}
        dep_name = source["deployment_file"]
        resp_name = source["response_file"]
        if dep_name not in by_path or resp_name not in by_path:
            raise RuntimeError(
                f"expected Dryad files not found for {source['label']}: "
                f"deployment={dep_name in by_path}, response={resp_name in by_path}"
            )
        dep_row = by_path[dep_name]
        resp_row = by_path[resp_name]
        payload = _download_public_deployment(dep_row, dep_name, audit)
        (input_root / dep_name).write_bytes(payload)
        deployment_payloads.append((source, payload))
        audit["source_audit"].append(
            {
                "label": source["label"],
                "doi": source["doi"],
                "version": {
                    "id": version.get("id"),
                    "versionNumber": version.get("versionNumber"),
                    "publicationDate": version.get("publicationDate"),
                    "lastModificationDate": version.get("lastModificationDate"),
                },
                "deployment": _file_identity(dep_row),
                "response": _file_identity(resp_row),
                "deployment_opened": True,
                "response_opened": False,
            }
        )

    key_fields = contract["response_blind_node_rule"]["stable_node_key_fields"]
    all_records: list[dict] = []
    for source, payload in deployment_payloads:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        header = list(reader.fieldnames or [])
        audit["observed_deployment_headers"][source["label"]] = header
        required = set(key_fields) | {
            "Survey_Nights",
            "Latitude",
            "Longitude",
            "Camera_Trap_Array",
            "Site_Name",
            "State",
        }
        if source["label"] == "snapshot_usa_2019_2023":
            required.add("Year")
        missing = sorted(required.difference(header))
        if missing:
            raise RuntimeError(
                f"deployment schema missing required fields for {source['label']}: {missing}"
            )
        allowed_years = {int(value) for value in source["years"]}
        for row in reader:
            if source["label"] == "snapshot_usa_2024" and "Year" not in header:
                year = 2024
            else:
                year = int(float(str(row.get("Year", "")).strip()))
            if year not in allowed_years:
                raise RuntimeError(f"deployment row year outside frozen source years: {year}")
            key = tuple(str(row.get(field, "")).strip() for field in key_fields)
            if any(not value for value in key):
                raise RuntimeError(f"empty stable-node key component: {key}")
            nights = float(str(row.get("Survey_Nights", "")).strip())
            lat = float(str(row.get("Latitude", "")).strip())
            lon = float(str(row.get("Longitude", "")).strip())
            if not all(math.isfinite(value) for value in (nights, lat, lon)):
                raise RuntimeError("deployment nights/coordinates must be finite")
            if nights < 0 or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise RuntimeError("invalid deployment nights or WGS84 coordinates")
            all_records.append(
                {"key": key, "year": year, "nights": nights, "lat": lat, "lon": lon}
            )

    if not all_records:
        raise RuntimeError("no response-independent deployment rows")

    node_year_nights: dict[tuple[str, ...], dict[int, float]] = {}
    coords: dict[tuple[str, ...], list[tuple[float, float]]] = {}
    for row in all_records:
        key = row["key"]
        coords.setdefault(key, []).append((row["lat"], row["lon"]))
        years = node_year_nights.setdefault(key, {})
        years[row["year"]] = years.get(row["year"], 0.0) + row["nights"]

    outer_units = tuple(int(value) for value in contract["outer_units"])
    observed_years = tuple(sorted({row["year"] for row in all_records}))
    if observed_years != outer_units:
        raise RuntimeError(
            f"deployment files do not cover exactly frozen years: {observed_years} != {outer_units}"
        )

    registry: list[dict] = []
    repeated_count = 0
    counts_by_year = {year: 0 for year in outer_units}
    for key in sorted(node_year_nights):
        coordinate_values = coords[key]
        lat = float(statistics.median(value[0] for value in coordinate_values))
        lon = float(statistics.median(value[1] for value in coordinate_values))
        available_years = [
            year for year in outer_units if node_year_nights[key].get(year, 0.0) > 0.0
        ]
        for year in available_years:
            counts_by_year[year] += 1
        if len(available_years) >= 2:
            repeated_count += 1
        registry.append(
            {
                "node_key": list(key),
                "latitude": lat,
                "longitude": lon,
                "available_years": available_years,
                "survey_nights_by_year": {
                    str(year): node_year_nights[key].get(year, 0.0) for year in outer_units
                },
            }
        )

    minima = contract["generic_minima"]
    declaration = CandidatePreflightDeclaration(
        attempt_id=contract["attempt_id"],
        minimum_nodes=int(minima["minimum_nodes"]),
        minimum_outer_units=int(minima["minimum_outer_units"]),
        minimum_repeated_nodes=int(minima["minimum_repeated_nodes"]),
        require_separate_geometry_and_response=True,
        require_coordinate_geometry=True,
        require_closed_analysis_registry=True,
    )
    geometry_identity = json.dumps(
        [row["deployment"] for row in audit["source_audit"]],
        sort_keys=True,
        separators=(",", ":"),
    )
    response_identity = json.dumps(
        [row["response"] for row in audit["source_audit"]],
        sort_keys=True,
        separators=(",", ":"),
    )
    evidence = CandidatePreflightEvidence(
        source_identity="Snapshot USA Dryad versions and file digests frozen in source_audit",
        geometry_source_identity=geometry_identity,
        response_source_identity=response_identity,
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=len(registry),
        outer_unit_count=len(outer_units),
        repeated_node_count=repeated_count,
        layout_design="natural_irregular",
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note=(
            "Stable node key State+Camera_Trap_Array+Site_Name; repeated means "
            "positive Survey_Nights in at least two frozen outer years."
        ),
    )
    preflight = evaluate_candidate_preflight(declaration, evidence)
    audit.update(
        {
            "deployment_row_count": len(all_records),
            "analysis_node_count": len(registry),
            "repeated_node_count": repeated_count,
            "available_node_counts_by_year": {str(k): v for k, v in counts_by_year.items()},
            "outer_units": list(outer_units),
            "preflight": {
                "status": preflight.status,
                "ready": preflight.ready,
                "missing_metadata": list(preflight.missing_metadata),
                "warnings": list(preflight.warnings),
                "reason": preflight.reason,
                "fingerprint": preflight.fingerprint,
            },
        }
    )
    (output_root / "preflight.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_root / "closed_registry.json").write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return audit


def main() -> None:
    output = Path("build/snapshot_usa_wtd/output")
    try:
        result = run(output)
    except Exception as exc:
        output.mkdir(parents=True, exist_ok=True)
        failure = {
            "status": "preflight_execution_error",
            "error": repr(exc),
            "response_download_urls": [],
            "response_bytes_opened": 0,
            "response_rows_opened": False,
        }
        (output / "failure.json").write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(failure, indent=2, sort_keys=True))
        raise
    print(
        json.dumps(
            {
                "preflight_status": result["preflight"]["status"],
                "preflight_ready": result["preflight"]["ready"],
                "analysis_node_count": result["analysis_node_count"],
                "repeated_node_count": result["repeated_node_count"],
                "available_node_counts_by_year": result["available_node_counts_by_year"],
                "response_bytes_opened": result["response_bytes_opened"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not result["preflight"]["ready"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
