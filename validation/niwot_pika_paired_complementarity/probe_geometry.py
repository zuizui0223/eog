#!/usr/bin/env python3
"""Response-blind geometry and scale probe for the Niwot pika attempt.

Only the immutable EML metadata and the physically separate plot-location
entity may be requested.  No survey or detection entity is requested.
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
MISSING = {"", "NaN"}


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
            "User-Agent": "eog-niwot-pika-response-blind-geometry-probe/1.0",
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
    if root.findtext("./dataset/title") != package["title"]:
        raise RuntimeError("EML title drift")
    if root.findtext("./dataset/pubDate") != package["publication_date"]:
        raise RuntimeError("EML publication date drift")
    begin = root.findtext(".//temporalCoverage/rangeOfDates/beginDate/calendarDate")
    end = root.findtext(".//temporalCoverage/rangeOfDates/endDate/calendarDate")
    if [begin, end] != contract["candidate"]["temporal_coverage"]:
        raise RuntimeError("EML temporal coverage drift")

    abstract = normalized_text(" ".join(root.find("./dataset/abstract").itertext()))
    required_abstract_tokens = (
        "Survey plots (n = 72)",
        "Each year, 48 of the 72 plots are surveyed in a rotating panel design",
        "24 plots are surveyed annually, 24 in even years and 24 in odd years",
        "A subset of plots (n = 12) are selected for double surveys each year",
    )
    for token in required_abstract_tokens:
        if token not in abstract:
            raise RuntimeError(f"published abstract token missing: {token!r}")

    entities: dict[str, dict[str, object]] = {}
    for table in root.findall(".//dataTable"):
        object_id = table.attrib.get("id", "")
        auth = table.find("./physical/authentication")
        entities[table.findtext("entityName") or ""] = {
            "object_name": table.findtext("./physical/objectName"),
            "object_id": object_id,
            "bytes": int(table.findtext("./physical/size") or -1),
            "md5": auth.text if auth is not None else None,
            "records": int(table.findtext("numberOfRecords") or -1),
            "attributes": [
                attribute.findtext("attributeName")
                for attribute in table.findall("./attributeList/attribute")
            ],
        }
    for role in (
        "geometry",
        "survey_registry",
        "timed_search_response",
        "extra_search_response",
    ):
        expected = contract["entities"][role]
        observed = entities.get(expected["entity_name"])
        if observed is None:
            raise RuntimeError(f"EML entity missing for role {role}")
        for key in ("object_name", "object_id", "bytes", "md5", "records"):
            if observed[key] != expected[key]:
                raise RuntimeError(f"EML {role} {key} drift")
    observed_header = entities[contract["entities"]["geometry"]["entity_name"]][
        "attributes"
    ]
    if observed_header != contract["entities"]["geometry"]["expected_header"]:
        raise RuntimeError("EML geometry attribute-order drift")

    return {
        "bytes": len(payload),
        "sha1": digest(payload, "sha1"),
        "sha256": digest(payload, "sha256"),
        "title": package["title"],
        "publication_date": package["publication_date"],
        "temporal_coverage": [begin, end],
        "geographic_coverage_records": len(root.findall(".//geographicCoverage")),
        "required_abstract_tokens": list(required_abstract_tokens),
        "entity_roles_verified": [
            "geometry",
            "survey_registry",
            "timed_search_response",
            "extra_search_response",
        ],
    }


def candidate_gate(contract: dict) -> dict[str, object]:
    frozen = contract["preflight_declaration"]
    declaration = CandidatePreflightDeclaration(
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
    published = contract["published_response_blind_counts"]
    evidence = CandidatePreflightEvidence(
        source_identity=(
            "EDI knb-lter-nwt.17.4 / doi:" + contract["package"]["package_doi"]
        ),
        geometry_source_identity=(
            contract["entities"]["geometry"]["object_id"]
            + "/md5:"
            + contract["entities"]["geometry"]["md5"]
        ),
        response_source_identity=(
            "plot conditions + timed search sign + extra survey sign entities, exact "
            "EML object IDs/bytes/MD5 frozen"
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=int(published["analysis_nodes"]),
        outer_unit_count=len(published["heldout_transition_years"]),
        repeated_node_count=int(published["annual_panel_nodes"]),
        layout_design="GRTS spatially balanced random sample",
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note=(
            "The EML abstract fixes 72 analysis plots and the rotating 24/24/24 panel; "
            "the exact response-blind current-panel/final-coordinate rule is frozen "
            "before the location entity is opened."
        ),
    )
    result = evaluate_candidate_preflight(declaration, evidence)
    if result.status != "ready_for_geometry_gate":
        raise RuntimeError(f"candidate preflight stopped: {result.status}")
    return {
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "result": asdict(result),
    }


def required(value: str, label: str) -> str:
    token = value.strip()
    if token in MISSING:
        raise RuntimeError(f"selected geometry {label} is missing")
    return token


def finite(value: str, label: str) -> float:
    try:
        number = float(required(value, label))
    except ValueError as exc:
        raise RuntimeError(f"selected geometry {label} is not numeric") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"selected geometry {label} is nonfinite")
    return number


def parse_geometry(payload: bytes, contract: dict) -> tuple[tuple[str, ...], np.ndarray, dict]:
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

    selected = []
    for row in rows:
        panel = row["panel_current"].strip()
        replacement = row["replaced_by"].strip()
        east = row["easting_final"].strip()
        north = row["northing_final"].strip()
        if panel not in MISSING and replacement in MISSING and east not in MISSING and north not in MISSING:
            selected.append(row)

    rule = contract["geometry_rule"]
    if len(selected) != int(rule["expected_selected_nodes"]):
        raise RuntimeError(
            f"frozen registry rule selected {len(selected)} rather than 72 rows"
        )
    node_ids = tuple(required(row["plot"], "plot") for row in selected)
    if len(set(node_ids)) != len(node_ids):
        raise RuntimeError("selected plot IDs are duplicated")
    coordinates = np.asarray(
        [
            [finite(row["easting_final"], "easting_final"), finite(row["northing_final"], "northing_final")]
            for row in selected
        ],
        dtype=float,
    )
    if len({tuple(value) for value in coordinates.tolist()}) != len(node_ids):
        raise RuntimeError("selected final coordinate pairs are duplicated")
    if not (
        np.all((coordinates[:, 0] >= 400_000.0) & (coordinates[:, 0] <= 500_000.0))
        and np.all((coordinates[:, 1] >= 4_300_000.0) & (coordinates[:, 1] <= 4_500_000.0))
    ):
        raise RuntimeError("selected coordinates are outside frozen UTM Zone 13 bounds")

    panels = tuple(row["panel_current"].strip().casefold() for row in selected)
    panel_counts = {panel: panels.count(panel) for panel in sorted(set(panels))}
    expected_panels = sorted(rule["expected_normalized_panel_tokens"])
    if sorted(panel_counts) != expected_panels:
        raise RuntimeError(f"current-panel token schema drift: {sorted(panel_counts)!r}")
    if set(panel_counts.values()) != {int(rule["expected_nodes_per_panel"])}:
        raise RuntimeError(f"current-panel counts drift: {panel_counts!r}")

    order = np.argsort(np.asarray(node_ids, dtype=str), kind="stable")
    ordered_ids = tuple(node_ids[int(i)] for i in order)
    ordered_coordinates = coordinates[order]
    pairs = np.sqrt(
        np.sum((ordered_coordinates[:, None, :] - ordered_coordinates[None, :, :]) ** 2, axis=2)
    )
    np.fill_diagonal(pairs, 0.0)
    upper = pairs[np.triu_indices(len(ordered_ids), k=1)]
    audit = {
        "bytes": len(payload),
        "md5": digest(payload, "md5"),
        "sha256": digest(payload, "sha256"),
        "header": header,
        "physical_rows": len(rows),
        "selected_nodes": len(ordered_ids),
        "ordered_node_ids": list(ordered_ids),
        "ordered_node_ids_sha256": canonical_sha256(list(ordered_ids)),
        "ordered_coordinates_sha256": canonical_sha256(ordered_coordinates.tolist()),
        "panel_counts": panel_counts,
        "coordinate_min": np.min(ordered_coordinates, axis=0).tolist(),
        "coordinate_max": np.max(ordered_coordinates, axis=0).tolist(),
        "minimum_pair_distance_m": float(np.min(upper)),
        "maximum_pair_distance_m": float(np.max(upper)),
        "distance_matrix_symmetric": bool(np.allclose(pairs, pairs.T)),
        "selection_rule": rule["selection"],
    }
    return ordered_ids, pairs, audit


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
        unique_thresholds.append(threshold)
        unique_adjacencies.append(built[level.level_id])
    minimum_distinct = int(frozen["minimum_distinct_positive_thresholds"])
    if len(unique_thresholds) < minimum_distinct:
        raise RuntimeError(
            f"structural scale collapse: {len(unique_thresholds)} distinct thresholds < {minimum_distinct}"
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
        "deduplicated_thresholds_m": unique_thresholds,
        "distinct_threshold_count": len(unique_thresholds),
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
        "requested_entity_roles": [],
        "response_entity_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_rows_or_values_opened": False,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    try:
        candidate = candidate_gate(contract)
        metadata = download(contract["package"]["metadata_resolver_url"])
        audit["requested_entity_roles"].append("metadata")
        metadata_audit = verify_metadata(metadata, contract)
        geometry = download(contract["entities"]["geometry"]["resolver_url"])
        audit["requested_entity_roles"].append("geometry")
        node_ids, distance, geometry_audit = parse_geometry(geometry, contract)
        structural = structural_gate(node_ids, distance, contract)
        result: dict[str, object] = {
            **audit,
            "status": "eligible_for_full_response_blind_freeze",
            "contract_sha256": digest(contract_path.read_bytes(), "sha256"),
            "candidate_preflight": candidate,
            "metadata_audit": metadata_audit,
            "geometry_audit": geometry_audit,
            "structural_gate": structural,
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
        raise AssertionError("geometry probe requested a response entity")
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
        print(f"Niwot pika geometry probe stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "selected_nodes": result["geometry_audit"]["selected_nodes"],
                "panel_counts": result["geometry_audit"]["panel_counts"],
                "distinct_threshold_count": result["structural_gate"][
                    "distinct_threshold_count"
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
