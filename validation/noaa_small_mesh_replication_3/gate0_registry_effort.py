"""Response-blind Gate 0 for the NOAA small-mesh shrimp candidate.

The Haul table is registry/effort data.  Catch receives one read-free Range probe;
its byte, header, rows, and values remain unopened.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = (
    HERE.parents[1]
    / "build"
    / "noaa_small_mesh_replication_3"
    / "gate0_registry_effort.json"
)
ALLOWED_DATA_HOST = "storage.googleapis.com"
USER_AGENT = "EOG-response-blind-NOAA-small-mesh-gate0/1.0"


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _clean_object_url(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_DATA_HOST:
        raise ValueError(f"{label} must use https://{ALLOWED_DATA_HOST}")
    return value


def _status(response: Any) -> int:
    value = getattr(response, "status", None)
    return int(value if value is not None else response.getcode())


def _header(response: Any, name: str) -> str | None:
    value = response.headers.get(name)
    return None if value is None else str(value)


def _verify_object_headers(response: Any, object_contract: dict[str, Any]) -> None:
    final_url = _clean_object_url(response.geturl(), "final object URL")
    if final_url != object_contract["url"]:
        raise ValueError("object URL redirected or drifted")
    generation = _header(response, "x-goog-generation")
    if generation != object_contract["generation"]:
        raise ValueError("object generation drift")
    etag = (_header(response, "ETag") or "").strip('"').lower()
    if etag != object_contract["md5"]:
        raise ValueError("object ETag/MD5 drift")
    content_type = (_header(response, "Content-Type") or "").split(";", 1)[0]
    if content_type != object_contract["content_type"]:
        raise ValueError("object content type drift")


def _probe_response_transport(
    response_contract: dict[str, Any],
    transport: dict[str, Any],
    ledger: list[dict[str, object]],
    opener: Any,
) -> None:
    if any(
        response_contract[key]
        for key in (
            "payload_access_allowed",
            "header_access_allowed",
            "row_access_allowed",
            "value_access_allowed",
        )
    ):
        raise ValueError("Catch access must remain closed in Gate 0")
    url = _clean_object_url(response_contract["url"], "Catch URL")
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Range": transport["range_header"],
            "Accept-Encoding": "identity",
        },
    )
    with opener(request, timeout=60) as response:
        status = _status(response)
        content_range = _header(response, "Content-Range")
        _verify_object_headers(response, response_contract)
        expected_range = transport["required_content_range_template"].format(
            size_bytes=response_contract["size_bytes"]
        )
        ledger.append(
            {
                "role": "catch_transport_probe",
                "requested_url": url,
                "http_status": status,
                "content_range": content_range,
                "bytes_opened": 0,
            }
        )
        if status != transport["required_status"] or content_range != expected_range:
            raise ValueError(
                "Catch object no longer supports the exact read-free Range gate"
            )
        # Deliberately do not call response.read(): even the returned one byte is unopened.


def _open_haul(
    haul_contract: dict[str, Any],
    ledger: list[dict[str, object]],
    opener: Any,
) -> bytes:
    url = _clean_object_url(haul_contract["url"], "Haul URL")
    request = Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    )
    with opener(request, timeout=60) as response:
        if _status(response) != 200:
            raise ValueError(f"Haul object returned HTTP {_status(response)}")
        _verify_object_headers(response, haul_contract)
        payload = response.read()
    observed_md5 = hashlib.md5(payload).hexdigest()
    ledger.append(
        {
            "role": "haul_registry_effort",
            "requested_url": url,
            "http_status": 200,
            "bytes_opened": len(payload),
            "md5": observed_md5,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    if len(payload) != haul_contract["size_bytes"]:
        raise ValueError("Haul object size drift")
    if observed_md5 != haul_contract["md5"]:
        raise ValueError("Haul object MD5 drift")
    return payload


def _integer(value: str, label: str) -> int:
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(f"{label} must be numeric") from error
    if not math.isfinite(number) or not number.is_integer():
        raise ValueError(f"{label} must be a finite integer")
    return int(number)


def _positive(value: str) -> float | None:
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) and number > 0 else None


def _coordinate(
    row: dict[str, str], rules: dict[str, Any]
) -> tuple[float, float] | None:
    try:
        latitude = float(row["START_LATITUDE"])
        longitude = float(row["START_LONGITUDE"])
    except ValueError:
        return None
    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return None
    if 130.0 <= longitude <= 180.0:
        longitude = -longitude
    lat_min, lat_max = rules["coordinate_bounds"]["latitude"]
    lon_min, lon_max = rules["coordinate_bounds"]["longitude"]
    if not (lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max):
        return None
    return latitude, longitude


def _distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    value = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(value))


def _maximum_spread_km(coordinates: list[tuple[float, float]]) -> float:
    # ponytail: source groups are small; replace this O(n^2) scan only if measured slow.
    return max(
        (
            _distance_km(a, b)
            for i, a in enumerate(coordinates)
            for b in coordinates[i + 1 :]
        ),
        default=0.0,
    )


def _audit_haul(payload: bytes, contract: dict[str, Any]) -> dict[str, object]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_header = contract["objects"]["registry_effort"]["expected_header"]
    if reader.fieldnames != expected_header:
        raise ValueError(f"Haul CSV header drift: {reader.fieldnames!r}")
    raw_rows = list(reader)
    if not raw_rows or any(None in row for row in raw_rows):
        raise ValueError("Haul CSV is empty or contains excess fields")
    rows = [{key.upper(): value for key, value in row.items()} for row in raw_rows]

    endpoint = contract["endpoint"]
    rules = contract["haul_eligibility"]
    heldout_years = set(endpoint["primary_heldout_years"])
    join_fields = endpoint["haul_join_key"]
    join_key_counts: Counter[tuple[str, ...]] = Counter()
    exclusions: Counter[str] = Counter()
    station_year_coordinates: dict[tuple[str, int], list[tuple[float, float]]] = (
        defaultdict(list)
    )
    eligible_haul_keys: set[tuple[str, ...]] = set()

    for row in rows:
        join_key = tuple(row[field].strip() for field in join_fields)
        join_key_counts[join_key] += 1
        if row["REGION"].strip() != rules["region"]:
            exclusions["outside_region"] += 1
            continue
        try:
            cruise = _integer(row["CRUISE"].strip(), "CRUISE")
        except ValueError:
            exclusions["invalid_cruise"] += 1
            continue
        cruise_text = str(cruise)
        if len(cruise_text) != 6:
            exclusions["invalid_cruise"] += 1
            continue
        year = int(cruise_text[:4])
        if not rules["year_min"] <= year <= rules["year_max"]:
            exclusions["outside_year_window"] += 1
            continue
        integer_rules = (
            ("HAUL_TYPE", rules["haul_type"], "wrong_haul_type"),
            ("PERFORMANCE", rules["performance"], "nonzero_performance"),
            ("GEAR", rules["gear"], "wrong_gear"),
        )
        rejected = False
        for field, expected, reason in integer_rules:
            try:
                observed = _integer(row[field].strip(), field)
            except ValueError:
                observed = None
            if observed != expected:
                exclusions[reason] += 1
                rejected = True
                break
        if rejected:
            continue
        try:
            sample_method = _integer(row["SUBSAMPLE"].strip(), "SUBSAMPLE")
        except ValueError:
            sample_method = None
        if sample_method not in rules["allowed_catch_sample_methods"]:
            exclusions["ineligible_catch_sample_method"] += 1
            continue
        effort_fields = ("DURATION", "DISTANCE_FISHED", "NET_WIDTH", "NET_HEIGHT")
        if any(_positive(row[field].strip()) is None for field in effort_fields):
            exclusions["invalid_effort"] += 1
            continue
        coordinate = _coordinate(row, rules)
        if coordinate is None:
            exclusions["invalid_coordinate"] += 1
            continue
        station = row["STATIONID"].strip()
        if not station:
            exclusions["missing_station"] += 1
            continue
        station_year_coordinates[(station, year)].append(coordinate)
        eligible_haul_keys.add(join_key)

    max_spread = rules["maximum_within_station_year_spread_km"]
    closed_station_years: dict[tuple[str, int], tuple[float, float]] = {}
    spread_failures = 0
    for station_year, coordinates in station_year_coordinates.items():
        if _maximum_spread_km(coordinates) > max_spread:
            spread_failures += 1
            continue
        closed_station_years[station_year] = (
            sum(value[0] for value in coordinates) / len(coordinates),
            sum(value[1] for value in coordinates) / len(coordinates),
        )

    years_by_station: dict[str, set[int]] = defaultdict(set)
    for station, year in closed_station_years:
        years_by_station[station].add(year)
    repeated_stations = {
        station
        for station, years in years_by_station.items()
        if any(year + 1 in years for year in years)
    }
    registry = [
        {
            "station_id": station,
            "year": year,
            "latitude": round(coordinate[0], 9),
            "longitude": round(coordinate[1], 9),
        }
        for (station, year), coordinate in sorted(closed_station_years.items())
        if station in repeated_stations
    ]
    heldout_counts = {
        str(year): sum(1 for row in registry if row["year"] == year)
        for year in sorted(heldout_years)
    }
    supported_heldout_years = {
        int(year) for year, count in heldout_counts.items() if count > 0
    }
    duplicate_join_key_count = sum(1 for count in join_key_counts.values() if count > 1)
    blank_join_key_row_count = sum(
        count
        for key, count in join_key_counts.items()
        if any(not value for value in key)
    )
    heldout_goa_rows = [
        row
        for row in rows
        if row["REGION"].strip() == rules["region"]
        and row["CRUISE"].strip()[:4].isdigit()
        and int(row["CRUISE"].strip()[:4]) in heldout_years
    ]
    eligible_join_key_sha256 = _canonical_sha256(sorted(eligible_haul_keys))
    registry_sha256 = _canonical_sha256(registry)

    return {
        "source_row_count": len(rows),
        "unique_haul_join_key_count": len(join_key_counts),
        "duplicate_haul_join_key_count": duplicate_join_key_count,
        "blank_haul_join_key_row_count": blank_join_key_row_count,
        "heldout_goa_row_count": len(heldout_goa_rows),
        "heldout_goa_missing_station_count": sum(
            1 for row in heldout_goa_rows if not row["STATIONID"].strip()
        ),
        "heldout_goa_missing_net_width_count": sum(
            1 for row in heldout_goa_rows if _positive(row["NET_WIDTH"].strip()) is None
        ),
        "heldout_goa_missing_net_height_count": sum(
            1
            for row in heldout_goa_rows
            if _positive(row["NET_HEIGHT"].strip()) is None
        ),
        "eligible_haul_count_before_station_spread": len(eligible_haul_keys),
        "eligibility_exclusion_counts": dict(sorted(exclusions.items())),
        "station_year_spread_failure_count": spread_failures,
        "closed_station_year_count": len(closed_station_years),
        "repeated_station_count": len(repeated_stations),
        "registry_station_year_count": len(registry),
        "supported_heldout_years": sorted(supported_heldout_years),
        "heldout_registry_counts_by_year": heldout_counts,
        "eligible_haul_join_key_sha256": eligible_join_key_sha256,
        "analysis_registry_sha256": registry_sha256,
        "analysis_registry": registry,
    }


def execute_gate0(
    contract_path: Path = DEFAULT_CONTRACT, *, opener: Any = urlopen
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    ledger: list[dict[str, object]] = []
    _probe_response_transport(
        contract["objects"]["response"],
        contract["transport_admission"],
        ledger,
        opener,
    )
    haul_payload = _open_haul(contract["objects"]["registry_effort"], ledger, opener)
    audit = _audit_haul(haul_payload, contract)

    preflight = contract["preflight"]
    declaration = CandidatePreflightDeclaration(
        attempt_id=contract["attempt_id"],
        minimum_nodes=preflight["minimum_nodes"],
        minimum_outer_units=preflight["minimum_outer_units"],
        minimum_repeated_nodes=preflight["minimum_repeated_nodes"],
        require_separate_geometry_and_response=preflight[
            "require_separate_geometry_and_response"
        ],
        require_coordinate_geometry=preflight["require_coordinate_geometry"],
        require_closed_analysis_registry=preflight["require_closed_analysis_registry"],
    )
    evidence = CandidatePreflightEvidence(
        source_identity=f"inport:{contract['source']['inport_item_id']}",
        geometry_source_identity=(
            "inport:55270@generation:"
            f"{contract['objects']['registry_effort']['generation']}"
        ),
        response_source_identity=(
            f"inport:55271@generation:{contract['objects']['response']['generation']}"
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=bool(audit["heldout_goa_row_count"]),
        node_count=audit["repeated_station_count"],
        outer_unit_count=len(audit["supported_heldout_years"]),
        repeated_node_count=audit["repeated_station_count"],
        layout_design=preflight["layout_design"],
        analysis_registry_closed=(
            audit["duplicate_haul_join_key_count"] == 0
            and audit["blank_haul_join_key_row_count"] == 0
            and bool(audit["registry_station_year_count"])
        ),
        response_rows_opened=False,
        response_bytes_opened=False,
        note="Catch cannot repair the Haul-derived station-year registry or effort.",
    )
    result = evaluate_candidate_preflight(declaration, evidence)
    nondetection = contract["target_nondetection_license"]
    nondetection_status = (
        "licensed_pre_response"
        if len(nondetection["required_support"]) == 3
        and contract["haul_eligibility"]["allowed_catch_sample_methods"]
        else "stop_target_nondetection_not_licensed"
    )
    status = result.status
    reason = result.reason
    if result.ready and nondetection_status != "licensed_pre_response":
        status = nondetection_status
        reason = "target-specific absent-row nondetection is not licensed"

    return {
        "schema": "eog.noaa_small_mesh_replication_3.gate0_registry_effort.v1",
        "attempt_id": contract["attempt_id"],
        "status": status,
        "reason": reason,
        "source_contract_fingerprint": _canonical_sha256(contract),
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "preflight": asdict(result),
        "target_nondetection_status": nondetection_status,
        "haul_audit": audit,
        "request_ledger": ledger,
        "opened_roles": ["haul_registry_effort"],
        "response_firewall": contract["response_firewall"],
        "next_required_gate": (
            "structural_geometry" if status == "ready_for_geometry_gate" else None
        ),
    }


def main() -> int:
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        artifact = execute_gate0()
        exit_code = 0 if artifact["status"] == "ready_for_geometry_gate" else 2
    except Exception as error:  # noqa: BLE001 - executable boundary records failure
        contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
        artifact = {
            "schema": "eog.noaa_small_mesh_replication_3.gate0_registry_effort.v1",
            "attempt_id": contract["attempt_id"],
            "status": "engineering_failure",
            "reason": f"{type(error).__name__}: {error}",
            "source_contract_fingerprint": _canonical_sha256(contract),
            "response_firewall": contract["response_firewall"],
        }
        exit_code = 1
    DEFAULT_OUTPUT.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
