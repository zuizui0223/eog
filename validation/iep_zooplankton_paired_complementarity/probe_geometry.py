#!/usr/bin/env python3
"""Response-blind geometry probe for the IEP zooplankton attempt.

Only immutable EML metadata and the physically separate StationLookup entity may
be requested. The Clarke-Bumpus response entity is identified from metadata but
is never requested by this program.
"""
from __future__ import annotations

import csv
from dataclasses import asdict
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)


HERE = Path(__file__).resolve().parent


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def digest(payload: bytes, algorithm: str) -> str:
    return hashlib.new(algorithm, payload).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/xml,text/csv,application/octet-stream;q=0.9,*/*;q=0.1",
            "User-Agent": "eog-iep-zooplankton-response-blind-geometry-probe/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return response.read()


def strip_namespaces(root: ET.Element) -> None:
    for element in root.iter():
        if "}" in element.tag:
            element.tag = element.tag.rsplit("}", 1)[1]


def normalized_text(value: str | None) -> str:
    return " ".join((value or "").split())


def entity_record(table: ET.Element) -> dict[str, object]:
    authentication = table.find("./physical/authentication")
    return {
        "object_name": table.findtext("./physical/objectName"),
        "object_id": table.attrib.get("id", ""),
        "bytes": int(table.findtext("./physical/size") or -1),
        "md5": authentication.text if authentication is not None else None,
        "records": int(table.findtext("numberOfRecords") or -1),
        "attributes": [
            attribute.findtext("attributeName")
            for attribute in table.findall("./attributeList/attribute")
        ],
    }


def verify_metadata(payload: bytes, contract: dict) -> dict[str, object]:
    package = contract["package"]
    if len(payload) != int(package["metadata_bytes"]):
        raise RuntimeError("EML metadata byte count drift")
    if digest(payload, "sha1") != package["metadata_sha1"]:
        raise RuntimeError("EML metadata SHA-1 drift")
    if digest(payload, "sha256") != package["metadata_sha256"]:
        raise RuntimeError("EML metadata SHA-256 drift")

    root = ET.fromstring(payload)
    strip_namespaces(root)
    if root.attrib.get("packageId") != "edi.522.14":
        raise RuntimeError("EML package identity drift")
    if root.findtext("./dataset/title") != package["title"]:
        raise RuntimeError("EML title drift")
    if root.findtext("./dataset/pubDate") != package["publication_date"]:
        raise RuntimeError("EML publication date drift")
    alternate = root.findtext("./dataset/alternateIdentifier") or ""
    if alternate != "doi:" + package["package_doi"]:
        raise RuntimeError("EML DOI drift")
    begin = root.findtext(".//temporalCoverage/rangeOfDates/beginDate/calendarDate")
    end = root.findtext(".//temporalCoverage/rangeOfDates/endDate/calendarDate")
    if [begin, end] != contract["candidate"]["temporal_coverage"]:
        raise RuntimeError("EML temporal coverage drift")

    abstract_element = root.find("./dataset/abstract")
    if abstract_element is None:
        raise RuntimeError("EML abstract missing")
    abstract = normalized_text(" ".join(abstract_element.itertext()))
    required_abstract_tokens = (
        "implemented in 1972",
        "For over five decades",
        "three gear types",
        "on a monthly basis",
    )
    for token in required_abstract_tokens:
        if token not in abstract:
            raise RuntimeError(f"published abstract token missing: {token!r}")

    entities = {
        table.findtext("entityName") or "": entity_record(table)
        for table in root.findall(".//dataTable")
    }
    for role in ("geometry", "response"):
        expected = contract["entities"][role]
        observed = entities.get(expected["entity_name"])
        if observed is None:
            raise RuntimeError(f"EML entity missing for role {role}")
        for key in ("object_name", "object_id", "bytes", "md5", "records"):
            if observed[key] != expected[key]:
                raise RuntimeError(f"EML {role} {key} drift")
        if observed["attributes"] != expected["expected_header"]:
            raise RuntimeError(f"EML {role} attribute-order drift")

    return {
        "bytes": len(payload),
        "sha1": digest(payload, "sha1"),
        "sha256": digest(payload, "sha256"),
        "title": package["title"],
        "publication_date": package["publication_date"],
        "temporal_coverage": [begin, end],
        "required_abstract_tokens": list(required_abstract_tokens),
        "entity_roles_verified_from_metadata": ["geometry", "response"],
    }


def preflight_declaration(contract: dict) -> CandidatePreflightDeclaration:
    frozen = contract["preflight_declaration"]
    return CandidatePreflightDeclaration(
        attempt_id=contract["attempt_id"],
        minimum_nodes=int(frozen["minimum_nodes"]),
        minimum_outer_units=int(frozen["minimum_outer_units"]),
        minimum_repeated_nodes=int(frozen["minimum_repeated_nodes"]),
        require_separate_geometry_and_response=bool(
            frozen["require_separate_geometry_and_response"]
        ),
        require_coordinate_geometry=bool(frozen["require_coordinate_geometry"]),
        require_closed_analysis_registry=bool(frozen["require_closed_analysis_registry"]),
    )


def candidate_evidence(
    contract: dict,
    *,
    node_count: int | None,
    repeated_node_count: int | None,
    note: str,
) -> CandidatePreflightEvidence:
    published = contract["published_response_blind_counts"]
    return CandidatePreflightEvidence(
        source_identity="EDI edi.522.14 / doi:" + contract["package"]["package_doi"],
        geometry_source_identity=(
            contract["entities"]["geometry"]["object_id"]
            + "/md5:"
            + contract["entities"]["geometry"]["md5"]
        ),
        response_source_identity=(
            contract["entities"]["response"]["object_id"]
            + "/md5:"
            + contract["entities"]["response"]["md5"]
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=node_count,
        outer_unit_count=len(published["heldout_target_years"]),
        repeated_node_count=repeated_node_count,
        layout_design="natural_irregular",
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note=note,
    )


def initial_unknown_count_gate(contract: dict) -> dict[str, object]:
    declaration = preflight_declaration(contract)
    evidence = candidate_evidence(
        contract,
        node_count=None,
        repeated_node_count=None,
        note=(
            "The EML publishes 90 StationLookup rows but not the exact Core-and-Current "
            "analysis count. Unknown counts remain uncertain; only the physically separate "
            "response-blind geometry entity may now be opened to resolve them exactly."
        ),
    )
    result = evaluate_candidate_preflight(declaration, evidence)
    if result.status != "incomplete_response_blind_metadata":
        raise RuntimeError(f"unexpected initial count disposition: {result.status}")
    if set(result.missing_metadata) != {"node_count", "repeated_node_count"}:
        raise RuntimeError(f"unexpected unresolved metadata: {result.missing_metadata!r}")
    return {
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "result": asdict(result),
    }


def missing(token: str, contract: dict) -> bool:
    return token.strip() in set(contract["geometry_rule"]["missing_tokens_after_outer_strip"])


def numeric(token: str, label: str, contract: dict, *, allow_missing: bool) -> float | None:
    stripped = token.strip()
    if missing(stripped, contract):
        if allow_missing:
            return None
        raise RuntimeError(f"selected geometry {label} is missing")
    try:
        value = float(stripped)
    except ValueError as exc:
        raise RuntimeError(f"geometry {label} is not schema-numeric: {stripped!r}") from exc
    if not math.isfinite(value):
        raise RuntimeError(f"geometry {label} is nonfinite")
    return value


def integral_year(
    token: str, label: str, contract: dict, *, allow_missing: bool
) -> int | None:
    value = numeric(token, label, contract, allow_missing=allow_missing)
    if value is None:
        return None
    if value != math.floor(value):
        raise RuntimeError(f"geometry {label} is not an integral year")
    return int(value)


def haversine_distance_matrix(
    lat_lon_degrees: np.ndarray, earth_radius_m: float
) -> np.ndarray:
    radians = np.deg2rad(np.asarray(lat_lon_degrees, dtype=float))
    latitude = radians[:, 0]
    longitude = radians[:, 1]
    delta_latitude = latitude[:, None] - latitude[None, :]
    delta_longitude = longitude[:, None] - longitude[None, :]
    hav = (
        np.sin(delta_latitude / 2.0) ** 2
        + np.cos(latitude[:, None])
        * np.cos(latitude[None, :])
        * np.sin(delta_longitude / 2.0) ** 2
    )
    central_angle = 2.0 * np.arcsin(np.sqrt(np.clip(hav, 0.0, 1.0)))
    distance = float(earth_radius_m) * central_angle
    np.fill_diagonal(distance, 0.0)
    return distance


def parse_geometry(
    payload: bytes, contract: dict
) -> tuple[tuple[str, ...], np.ndarray, dict[str, object]]:
    expected = contract["entities"]["geometry"]
    if len(payload) != int(expected["bytes"]):
        raise RuntimeError("geometry byte count drift")
    if digest(payload, "md5") != expected["md5"]:
        raise RuntimeError("geometry MD5 drift")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        header = list(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("geometry is not UTF-8") from exc
    if header != expected["expected_header"]:
        raise RuntimeError(f"physical geometry header drift: {header!r}")
    if len(rows) != int(expected["records"]):
        raise RuntimeError("physical geometry row count drift")

    selected: list[dict[str, str]] = []
    for row in rows:
        core = numeric(row["Core"], "Core", contract, allow_missing=True)
        current = numeric(row["Current"], "Current", contract, allow_missing=True)
        if core in {1.0, 2.0} and current == 1.0:
            selected.append(row)

    if not selected:
        raise RuntimeError("frozen registry rule selected zero rows")
    node_ids: list[str] = []
    coordinates: list[list[float]] = []
    core_codes: list[int] = []
    year_starts: list[int] = []
    year_ends: list[int | None] = []
    for row in selected:
        node_id = row["StationNZ"].strip()
        if not node_id:
            raise RuntimeError("selected geometry StationNZ is missing")
        latitude = numeric(row["latdec"], "latdec", contract, allow_missing=False)
        longitude = numeric(row["longdec"], "longdec", contract, allow_missing=False)
        core = numeric(row["Core"], "Core", contract, allow_missing=False)
        year_start = integral_year(
            row["YearStart"], "YearStart", contract, allow_missing=False
        )
        year_end = integral_year(
            row["YearEnd"], "YearEnd", contract, allow_missing=True
        )
        assert latitude is not None and longitude is not None
        assert core is not None and year_start is not None
        node_ids.append(node_id)
        coordinates.append([latitude, longitude])
        core_codes.append(int(core))
        year_starts.append(year_start)
        year_ends.append(year_end)

    if len(set(node_ids)) != len(node_ids):
        raise RuntimeError("selected StationNZ values are duplicated")
    coordinate_tuples = [tuple(value) for value in coordinates]
    if len(set(coordinate_tuples)) != len(coordinate_tuples):
        raise RuntimeError("selected decimal coordinate pairs are duplicated")

    values = np.asarray(coordinates, dtype=float)
    rule = contract["geometry_rule"]
    latitude_bounds = np.asarray(rule["latitude_bounds"], dtype=float)
    longitude_bounds = np.asarray(rule["longitude_bounds"], dtype=float)
    if not np.all((values[:, 0] >= latitude_bounds[0]) & (values[:, 0] <= latitude_bounds[1])):
        raise RuntimeError("selected latitudes are outside frozen EML bounds")
    if not np.all((values[:, 1] >= longitude_bounds[0]) & (values[:, 1] <= longitude_bounds[1])):
        raise RuntimeError("selected longitudes are outside frozen EML bounds")

    longitudinal = contract["longitudinal_rule"]
    repeated = [
        start <= int(longitudinal["year_start_latest"])
        and (end is None or end >= int(longitudinal["year_end_earliest"]))
        for start, end in zip(year_starts, year_ends, strict=True)
    ]

    order = np.argsort(np.asarray(node_ids, dtype=str), kind="stable")
    ordered_ids = tuple(node_ids[int(index)] for index in order)
    ordered_coordinates = values[order]
    radius = float(contract["structural_gate"]["earth_mean_radius_m"])
    distance = haversine_distance_matrix(ordered_coordinates, radius)
    upper = distance[np.triu_indices(len(ordered_ids), k=1)]
    if upper.size == 0 or not np.all(upper > 0.0):
        raise RuntimeError("selected geometry lacks positive pairwise distances")

    core_counts = {
        str(code): core_codes.count(code) for code in sorted(set(core_codes))
    }
    audit: dict[str, object] = {
        "bytes": len(payload),
        "md5": digest(payload, "md5"),
        "sha256": digest(payload, "sha256"),
        "header": header,
        "physical_rows": len(rows),
        "selected_nodes": len(ordered_ids),
        "repeated_eligible_nodes": int(sum(repeated)),
        "ordered_node_ids": list(ordered_ids),
        "ordered_node_ids_sha256": canonical_sha256(list(ordered_ids)),
        "ordered_coordinates_sha256": canonical_sha256(ordered_coordinates.tolist()),
        "core_counts": core_counts,
        "year_start_min": min(year_starts),
        "year_start_max": max(year_starts),
        "year_end_nonmissing_count": sum(value is not None for value in year_ends),
        "coordinate_min": np.min(ordered_coordinates, axis=0).tolist(),
        "coordinate_max": np.max(ordered_coordinates, axis=0).tolist(),
        "minimum_pair_distance_m": float(np.min(upper)),
        "maximum_pair_distance_m": float(np.max(upper)),
        "distance_matrix_symmetric": bool(np.allclose(distance, distance.T)),
        "registry_selection": rule["registry_selection"],
        "longitudinal_definition": longitudinal["definition"],
    }
    return ordered_ids, distance, audit


def exact_candidate_gate(contract: dict, geometry_audit: dict) -> dict[str, object]:
    declaration = preflight_declaration(contract)
    evidence = candidate_evidence(
        contract,
        node_count=int(geometry_audit["selected_nodes"]),
        repeated_node_count=int(geometry_audit["repeated_eligible_nodes"]),
        note=(
            "Exact counts were resolved solely from the frozen Core-and-Current rule, "
            "YearStart/YearEnd, and coordinates in the independent StationLookup entity."
        ),
    )
    result = evaluate_candidate_preflight(declaration, evidence)
    return {
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "result": asdict(result),
    }


def structural_gate(
    node_ids: tuple[str, ...], distance: np.ndarray, contract: dict
) -> dict[str, object]:
    frozen = contract["structural_gate"]
    declaration = StructuralScaleLadderDeclaration(
        axis_id=frozen["axis_id"],
        target_largest_component_fractions=tuple(
            frozen["target_largest_component_fractions"]
        ),
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    built = structural_scale_adjacencies(ladder, distance)
    unique_thresholds: list[float] = []
    unique_adjacencies: list[np.ndarray] = []
    for level in ladder.levels:
        threshold = float(level.distance_threshold)
        if unique_thresholds and abs(threshold - unique_thresholds[-1]) <= 1e-9:
            continue
        if threshold <= 0.0:
            continue
        unique_thresholds.append(threshold)
        unique_adjacencies.append(built[level.level_id])
    minimum_distinct = int(frozen["minimum_distinct_positive_thresholds"])
    if len(unique_thresholds) < minimum_distinct:
        raise RuntimeError(
            f"structural scale collapse: {len(unique_thresholds)} distinct positive "
            f"thresholds < {minimum_distinct}"
        )
    worlds = {
        f"geo_structural_{index + 1}": adjacency
        for index, adjacency in enumerate(unique_adjacencies)
    }
    full = np.ones((len(node_ids), len(node_ids)), dtype=bool)
    np.fill_diagonal(full, False)
    worlds["geo_full_support"] = full
    audit = audit_world_universe_structure(node_ids, worlds, horizon=1)
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.9,
        max_isolated_node_fraction=0.1,
        require_at_least_one_world_pass=True,
    )
    gate = apply_structural_adequacy_gate(audit, adequacy)
    if not gate.passed:
        raise RuntimeError("response-blind structural adequacy gate failed")
    return {
        "declaration": asdict(declaration),
        "ladder": asdict(ladder),
        "raw_thresholds_m": [float(value) for value in ladder.thresholds],
        "deduplicated_positive_thresholds_m": unique_thresholds,
        "distinct_positive_threshold_count": len(unique_thresholds),
        "world_ids": list(worlds),
        "world_audit": asdict(audit),
        "adequacy_declaration": asdict(adequacy),
        "adequacy_gate": asdict(gate),
    }


def run(output_path: Path) -> dict[str, object]:
    contract_path = HERE / "geometry_probe_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    audit: dict[str, object] = {
        "attempt_id": contract["attempt_id"],
        "stage": "response_blind_metadata_geometry_and_scale_probe",
        "contract_sha256": digest(contract_path.read_bytes(), "sha256"),
        "requested_entity_roles": [],
        "response_entity_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_rows_or_values_opened": False,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    try:
        audit["initial_unknown_count_gate"] = initial_unknown_count_gate(contract)
        metadata = download(contract["package"]["metadata_resolver_url"])
        audit["requested_entity_roles"].append("metadata")
        audit["metadata_audit"] = verify_metadata(metadata, contract)
        geometry = download(contract["entities"]["geometry"]["resolver_url"])
        audit["requested_entity_roles"].append("geometry")
        node_ids, distance, geometry_audit = parse_geometry(geometry, contract)
        audit["geometry_audit"] = geometry_audit
        exact_gate = exact_candidate_gate(contract, geometry_audit)
        audit["exact_candidate_gate"] = exact_gate
        exact_status = exact_gate["result"]["status"]
        if exact_status != "ready_for_geometry_gate":
            raise RuntimeError(
                f"exact response-blind candidate gate stopped: {exact_status}"
            )
        audit["structural_gate"] = structural_gate(node_ids, distance, contract)
        result: dict[str, object] = {
            **audit,
            "status": "eligible_for_full_response_blind_freeze",
        }
        result["fingerprint"] = canonical_sha256(result)
    except Exception as exc:
        result = {
            **audit,
            "status": "ineligible_pre_response",
            "stop_reason": repr(exc),
        }
        result["fingerprint"] = canonical_sha256(result)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise

    if result["requested_entity_roles"] != ["metadata", "geometry"]:
        raise AssertionError("geometry probe requested an undeclared entity role")
    if result["response_entity_requests"] != 0:
        raise AssertionError("geometry probe requested the response entity")
    if result["response_payload_bytes_opened"] != 0:
        raise AssertionError("geometry probe opened response payload bytes")
    if result["response_rows_or_values_opened"]:
        raise AssertionError("geometry probe opened response rows or values")
    if result["models_fit"] or result["heldout_scores"]:
        raise AssertionError("geometry probe fit or scored a model")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe_geometry.py OUTPUT_JSON")
    try:
        result = run(Path(sys.argv[1]))
    except Exception as exc:
        print(f"IEP zooplankton geometry probe stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "selected_nodes": result["geometry_audit"]["selected_nodes"],
                "repeated_eligible_nodes": result["geometry_audit"][
                    "repeated_eligible_nodes"
                ],
                "distinct_positive_threshold_count": result["structural_gate"][
                    "distinct_positive_threshold_count"
                ],
                "response_entity_requests": 0,
                "response_payload_bytes_opened": 0,
                "response_rows_or_values_opened": False,
                "models_fit": 0,
                "heldout_scores": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
