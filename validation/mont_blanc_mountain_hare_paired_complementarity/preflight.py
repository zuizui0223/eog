#!/usr/bin/env python3
"""Response-blind admission for the Mont-Blanc mountain-hare attempt."""
from __future__ import annotations

import calendar
import csv
from dataclasses import asdict
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import sys

import numpy as np

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.outcome_access import (
    FrozenOutcomeAccessContract,
    REQUIRED_FREEZE_KEYS,
    evaluate_outcome_access_gate,
)
from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
    prospective_estimability_disposition,
)
from eog.v2.response_header_schema import (
    ResponseHeaderSchemaDeclaration,
    ResponseHeaderSchemaEvidence,
    evaluate_response_header_schema,
)
from eog.v2.temporal_source_closure import (
    TemporalSourceClosureDeclaration,
    evaluate_temporal_source_closure,
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

from transport import (
    download_nonresponse_member,
    fetch_file_manifest,
    read_bounded_response_header,
)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "build/mont_blanc_mountain_hare_paired_complementarity/preflight"
EARTH_RADIUS_M = 6_371_008.8
ANALYSIS_MONTHS = tuple(
    (year, month)
    for year in range(2019, 2023)
    for month in range(1, 13)
    if (year, month) <= (2022, 6)
)
CAMERA_HEADER = (
    "Station",
    "Exposition",
    "Elevation",
    "longitude",
    "Latitude",
    "Slope",
    "Habitat",
    "Model",
    "setup_date",
    *tuple(
        value
        for number in range(1, 15)
        for value in (
            f"Problem{number}",
            f"Problem{number}_from",
            f"Problem{number}_to",
        )
    ),
)


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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _required_token(value: str, label: str) -> str:
    token = value.strip()
    if not token or token == "NA":
        raise RuntimeError(f"{label} is missing")
    return token


def _finite(value: str, label: str) -> float:
    token = _required_token(value, label)
    try:
        result = float(token)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise RuntimeError(f"{label} is nonfinite")
    return result


def _date(token: str, label: str) -> date:
    try:
        return datetime.strptime(_required_token(token, label), "%d/%m/%Y").date()
    except ValueError as exc:
        raise RuntimeError(f"{label} is not strict DD/MM/YYYY") from exc


def audit_readme(payload: bytes) -> dict[str, object]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("README.md is not UTF-8") from exc
    required = (
        "Camera traps reveal seasonal variation in activity and occupancy of the Alpine mountain hare",
        "Pictures from 46 camera traps",
        'Mountain hare contacts from camera traps are available in the "taghare_1day.csv" dataset.',
        'Descriptions of camera traps are available in the "camerainfo.csv" dataset.',
        '"setup_date" corresponds to the date at which the camera was setup',
        '"Problem[X]" corresponds to the cause of the problem',
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(f"fixed README semantic token missing: {missing[0]!r}")
    return {
        "encoding": "utf-8",
        "declared_camera_count": 46,
        "response_file": "taghare_1day.csv",
        "geometry_effort_file": "camerainfo.csv",
        "semantic_tokens_verified": list(required),
    }


def _haversine_distance(coordinates: np.ndarray) -> np.ndarray:
    longitude = np.radians(coordinates[:, 0])
    latitude = np.radians(coordinates[:, 1])
    dlon = longitude[None, :] - longitude[:, None]
    dlat = latitude[None, :] - latitude[:, None]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(latitude[:, None])
        * np.cos(latitude[None, :])
        * np.sin(dlon / 2.0) ** 2
    )
    distance = 2.0 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
    np.fill_diagonal(distance, 0.0)
    return distance


def parse_camera_info(
    payload: bytes,
    contract: dict,
) -> tuple[
    tuple[str, ...],
    dict[str, object],
    np.ndarray,
    np.ndarray,
    np.ndarray,
    dict[str, object],
]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("cp1252")), delimiter=";")
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("camerainfo.csv is not cp1252") from exc
    if header != CAMERA_HEADER:
        raise RuntimeError(f"camerainfo.csv header drift: {header!r}")
    if len(rows) != 46:
        raise RuntimeError("camerainfo.csv row count differs from 46")

    node_ids = tuple(_required_token(row["Station"], "Station") for row in rows)
    if len(set(node_ids)) != 46:
        raise RuntimeError("camerainfo.csv Station values are duplicated")
    expected_ids = contract["freezes"]["node_geometry"]["ordered_node_ids_sha256"]
    if canonical_sha256(list(node_ids)) != expected_ids:
        raise RuntimeError("ordered 46-station registry fingerprint drift")

    coordinates = np.asarray(
        [
            [_finite(row["longitude"], "longitude"), _finite(row["Latitude"], "Latitude")]
            for row in rows
        ],
        dtype=float,
    )
    if len({tuple(value) for value in coordinates.tolist()}) != 46:
        raise RuntimeError("camerainfo.csv coordinate pairs are duplicated")
    elevation = np.asarray([_finite(row["Elevation"], "Elevation") for row in rows])
    slope = np.asarray([_finite(row["Slope"], "Slope") for row in rows])
    setup_dates = tuple(_date(row["setup_date"], "setup_date") for row in rows)
    aspect = tuple(_required_token(row["Exposition"], "Exposition") for row in rows)
    habitat = tuple(_required_token(row["Habitat"], "Habitat") for row in rows)
    model = tuple(_required_token(row["Model"], "Model") for row in rows)

    preprocessing = contract["freezes"]["preprocessing_model_fit"]
    if set(aspect) != set(preprocessing["aspect_degrees_clockwise_from_north"]):
        raise RuntimeError("camera aspect token schema drift")
    if set(habitat) != set(preprocessing["habitat_mapping"]):
        raise RuntimeError("camera habitat token schema drift")
    if set(model) != set(preprocessing["model_tokens"]):
        raise RuntimeError("camera model token schema drift")

    intervals: list[list[tuple[date, date]]] = [[] for _ in rows]
    complete_interval_count = 0
    missing_description_count = 0
    for row_index, row in enumerate(rows):
        for number in range(1, 15):
            description = row[f"Problem{number}"].strip()
            start_token = row[f"Problem{number}_from"].strip()
            end_token = row[f"Problem{number}_to"].strip()
            start_present = start_token not in {"", "NA"}
            end_present = end_token not in {"", "NA"}
            if start_present != end_present:
                raise RuntimeError("camera problem interval has only one dated endpoint")
            if not start_present:
                if description not in {"", "NA"}:
                    raise RuntimeError("camera problem description has no dated interval")
                continue
            start = _date(start_token, f"Problem{number}_from")
            end = _date(end_token, f"Problem{number}_to")
            if end < start:
                raise RuntimeError("camera problem interval ends before it starts")
            intervals[row_index].append((start, end))
            complete_interval_count += 1
            if description in {"", "NA"}:
                missing_description_count += 1

    effort_spec = contract["freezes"]["node_geometry"]["survey_effort"]
    if complete_interval_count != int(effort_spec["problem_interval_count"]):
        raise RuntimeError("complete camera-problem interval count drift")
    if missing_description_count != int(effort_spec["missing_description_interval_count"]):
        raise RuntimeError("missing problem-description interval count drift")

    active_days = np.zeros((46, len(ANALYSIS_MONTHS)), dtype=float)
    for i, setup in enumerate(setup_dates):
        unavailable = {
            ordinal
            for start, end in intervals[i]
            for ordinal in range(start.toordinal(), end.toordinal() + 1)
        }
        for t, (year, month) in enumerate(ANALYSIS_MONTHS):
            first = date(year, month, 1)
            last = date(year, month, calendar.monthrange(year, month)[1])
            active_days[i, t] = sum(
                day >= setup.toordinal() and day not in unavailable
                for day in range(first.toordinal(), last.toordinal() + 1)
            )

    distance = _haversine_distance(coordinates)
    pairs = distance[np.triu_indices(46, k=1)]
    attributes: dict[str, object] = {
        "elevation": elevation,
        "slope": slope,
        "setup_dates": setup_dates,
        "aspect": aspect,
        "habitat": habitat,
        "model": model,
    }
    audit = {
        "header": list(header),
        "encoding": "cp1252",
        "node_count": 46,
        "pair_count": int(pairs.size),
        "coordinate_reference": "WGS84 longitude/latitude",
        "coordinate_pairs_unique": True,
        "coordinate_min": np.min(coordinates, axis=0).tolist(),
        "coordinate_max": np.max(coordinates, axis=0).tolist(),
        "minimum_distance_m": float(np.min(pairs)),
        "maximum_distance_m": float(np.max(pairs)),
        "derived_matrix_symmetric": bool(np.allclose(distance, distance.T)),
        "ordered_node_ids_sha256": canonical_sha256(list(node_ids)),
        "setup_date_range": [str(min(setup_dates)), str(max(setup_dates))],
        "problem_interval_count": complete_interval_count,
        "missing_description_interval_count": missing_description_count,
        "active_days_range": [float(np.min(active_days)), float(np.max(active_days))],
        "observed_station_months_at_20_days": int(np.sum(active_days >= 20.0)),
        "aspect_tokens": sorted(set(aspect)),
        "habitat_tokens": sorted(set(habitat)),
        "model_tokens": sorted(set(model)),
    }
    return node_ids, attributes, coordinates, distance, active_days, audit


def candidate_gate(contract: dict) -> dict[str, object]:
    declared = contract["preflight_declaration"]
    declaration = CandidatePreflightDeclaration(
        attempt_id=contract["attempt_id"],
        minimum_nodes=int(declared["minimum_nodes"]),
        minimum_outer_units=int(declared["minimum_outer_units"]),
        minimum_repeated_nodes=int(declared["minimum_repeated_nodes"]),
        require_separate_geometry_and_response=bool(
            declared["require_separate_geometry_and_response"]
        ),
        require_coordinate_geometry=bool(declared["require_coordinate_geometry"]),
        require_closed_analysis_registry=bool(declared["require_closed_analysis_registry"]),
    )
    evidence = CandidatePreflightEvidence(
        source_identity="Dryad 10.5061/dryad.b2rbnzsp7 version 1 / version 277486",
        geometry_source_identity=(
            "camerainfo.csv sha256:" + contract["files"]["camerainfo.csv"]["sha256"]
        ),
        response_source_identity=(
            "taghare_1day.csv sha256:" + contract["files"]["taghare_1day.csv"]["sha256"]
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=46,
        outer_unit_count=6,
        repeated_node_count=46,
        layout_design="natural_irregular",
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note=(
            "The 46-site geometry, setup dates, camera problem ledger, and fixed attributes "
            "are physically separate from the two-column contact-date response."
        ),
    )
    result = evaluate_candidate_preflight(declaration, evidence)
    if result.status != "ready_for_geometry_gate":
        raise RuntimeError(f"candidate metadata gate stopped: {result.status}")
    return {
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "result": asdict(result),
    }


def structural_gates(
    contract: dict,
    node_ids: tuple[str, ...],
    distance: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    declaration = StructuralScaleLadderDeclaration(
        axis_id="camera_station_wgs84_haversine_distance",
        target_largest_component_fractions=tuple(contract["structural_targets"]),
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    raw = np.asarray(ladder.thresholds, dtype=float)
    expected_raw = np.asarray(
        contract["freezes"]["world_scale"]["raw_lcc_thresholds_m"], dtype=float
    )
    if not np.allclose(raw, expected_raw, atol=1e-9, rtol=0.0):
        raise RuntimeError(
            f"response-blind raw LCC threshold drift: {raw.tolist()} != {expected_raw.tolist()}"
        )

    built = structural_scale_adjacencies(ladder, distance)
    unique_adjacencies: list[np.ndarray] = []
    unique_thresholds: list[float] = []
    for level in ladder.levels:
        threshold = float(level.distance_threshold)
        if unique_thresholds and abs(threshold - unique_thresholds[-1]) <= 1e-9:
            continue
        unique_thresholds.append(threshold)
        unique_adjacencies.append(built[level.level_id])
    scale = contract["freezes"]["world_scale"]
    expected_unique = np.asarray(scale["thresholds_m"], dtype=float)
    if not np.allclose(unique_thresholds, expected_unique, atol=1e-9, rtol=0.0):
        raise RuntimeError("response-blind deduplicated LCC threshold drift")
    required_distinct = int(
        contract["freezes"]["structural_adequacy"][
            "required_distinct_lcc_thresholds"
        ]
    )
    if len(unique_thresholds) != required_distinct:
        raise RuntimeError("declared LCC regimes do not yield three distinct thresholds")
    threshold_world_ids = tuple(scale["threshold_world_ids"])
    worlds = dict(zip(threshold_world_ids, unique_adjacencies, strict=True))
    full = np.ones((len(node_ids), len(node_ids)), dtype=bool)
    np.fill_diagonal(full, False)
    worlds[scale["full_world_id"]] = full

    audit = audit_world_universe_structure(node_ids, worlds, horizon=1)
    spec = contract["freezes"]["structural_adequacy"]
    adequacy_declaration = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(
            spec["minimum_largest_weak_component_fraction_for_one_world"]
        ),
        max_isolated_node_fraction=float(
            spec["maximum_isolated_node_fraction_for_one_world"]
        ),
        require_at_least_one_world_pass=bool(spec["require_at_least_one_world_pass"]),
    )
    gate = apply_structural_adequacy_gate(audit, adequacy_declaration)
    if not gate.passed:
        raise RuntimeError("response-blind structural adequacy gate failed")
    return worlds, {
        "ladder": asdict(ladder),
        "raw_thresholds_m": raw.tolist(),
        "deduplicated_thresholds_m": unique_thresholds,
        "distinct_threshold_count": len(unique_thresholds),
        "duplicate_lcc_policy_applied": True,
        "world_audit": asdict(audit),
        "adequacy_gate": asdict(gate),
    }


def temporal_closure(
    node_ids: tuple[str, ...],
    active_days: np.ndarray,
    worlds: dict[str, np.ndarray],
) -> dict[str, object]:
    observed = active_days >= 20.0
    declaration = TemporalSourceClosureDeclaration(
        closure_id="mont_blanc_monthly_internal_conditional_full_support_v1",
        source_semantics=(
            "all response-blind adequately observed stations are possible initial internal "
            "source states; the endpoint later conditions on current recorded contacts"
        ),
        transition_semantics=(
            "same-station persistence and every distinct internal pair admitted by the "
            "already-frozen full-support world across all 41 monthly transitions; target "
            "eligibility is determined only by at least 20 response-independent active days"
        ),
    )
    result = evaluate_temporal_source_closure(
        declaration,
        node_ids,
        observed[:, 0],
        observed[:, 1:],
        observed[:, 1:],
        worlds["geo_exponential_full"],
    )
    if not result.passed:
        raise RuntimeError(f"temporal source closure stopped: {result.status}")
    return {
        "declaration": asdict(declaration),
        "response_blind_observed_station_months": int(np.sum(observed)),
        "minimum_observed_stations_per_month": int(np.min(np.sum(observed, axis=0))),
        "result": asdict(result),
    }


def header_gate(contract: dict, manifest: dict[str, str], audit: dict) -> dict[str, object]:
    frozen = contract["response_header_firewall"]
    header_text, terminator, consumed, transport = read_bounded_response_header(
        contract, manifest, audit
    )
    if int(transport["transport_reconnects"]) != 0:
        raise RuntimeError("bounded response header required a reconnect")
    if header_text != frozen["expected_header_text"]:
        raise RuntimeError("bounded physical response header text drift")
    if transport["header_sha256"] != frozen["expected_header_sha256"]:
        raise RuntimeError("bounded physical response header SHA-256 drift")
    if terminator != frozen["expected_terminator"]:
        raise RuntimeError("bounded physical response terminator drift")
    if consumed != int(frozen["expected_bytes_consumed_including_terminator"]):
        raise RuntimeError("bounded physical response header length drift")
    declaration = ResponseHeaderSchemaDeclaration(
        schema_id="mont_blanc_mountain_hare_response_header_v1",
        expected_columns=tuple(frozen["expected_columns"]),
        delimiter=frozen["delimiter"],
        require_exact_order=bool(frozen["require_exact_order"]),
    )
    evidence = ResponseHeaderSchemaEvidence(
        header_text=header_text,
        terminator=terminator,
        bytes_consumed=consumed,
        response_rows_opened=False,
        response_values_opened=False,
    )
    result = evaluate_response_header_schema(declaration, evidence)
    if not result.ready:
        raise RuntimeError(f"bounded physical header schema stopped: {result.status}")
    return {
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "transport": transport,
        "result": asdict(result),
    }


def estimability_gate(contract: dict) -> tuple[dict[str, object], object]:
    minima = contract["freezes"]["count_gate"]
    declaration = ProspectiveEstimabilityDeclaration(
        calibration_events=int(minima["calibration_events"]),
        calibration_non_events=int(minima["calibration_non_events"]),
        heldout_events=int(minima["heldout_events"]),
        heldout_non_events=int(minima["heldout_non_events"]),
        heldout_outer_units_with_both_classes=int(
            minima["heldout_outer_units_with_both_classes"]
        ),
    )
    published = contract["published_aggregate_evidence"]
    keys = (
        "calibration_events",
        "calibration_non_events",
        "heldout_events",
        "heldout_non_events",
        "heldout_outer_units_with_both_classes",
    )
    intervals = {
        key: AggregateCountInterval(
            lower=published["split_specific_intervals"][key]["lower"],
            upper=published["split_specific_intervals"][key]["upper"],
        )
        for key in keys
    }
    evidence = AggregateEstimabilityEvidence(
        source_label=published["source"],
        endpoint_definition_matches=bool(published["endpoint_definition_matches"]),
        response_rows_opened=False,
        intervals=intervals,
        note=published["note"],
    )
    result = evaluate_prospective_estimability(declaration, evidence)
    disposition = prospective_estimability_disposition(result)
    if result.status != "uncertain_pre_response":
        raise RuntimeError(f"expected uncertain published split counts, got {result.status}")
    if disposition != "continue_response_blind_exact_gate_required":
        raise RuntimeError(f"unexpected prospective disposition: {disposition}")
    return (
        {
            "declaration": asdict(declaration),
            "evidence": asdict(evidence),
            "result": asdict(result),
            "disposition": disposition,
        },
        result,
    )


def run(output: Path) -> dict[str, object]:
    contract_path = HERE / "source_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    audit: dict[str, object] = {
        "attempt_id": contract["attempt_id"],
        "stage": "response_blind_admission_geometry_header_and_authorization",
        "manifest_requests": 0,
        "manifest_file_identities": [],
        "ephemeral_urls_persisted": False,
        "nonresponse_download_requests": [],
        "opened_nonresponse_files": [],
        "response_header_range_requests": 0,
        "response_header_bytes_opened": 0,
        "response_download_requests": [],
        "response_payload_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        candidate = candidate_gate(contract)
        manifest = fetch_file_manifest(contract, audit)
        payloads = {
            name: download_nonresponse_member(name, contract, manifest, audit)
            for name in contract["nonresponse_files"]
        }
        readme = audit_readme(payloads["README.md"])
        node_ids, _, _, distance, active_days, camera = parse_camera_info(
            payloads["camerainfo.csv"], contract
        )
        worlds, structural = structural_gates(contract, node_ids, distance)
        closure = temporal_closure(node_ids, active_days, worlds)
        header = header_gate(contract, manifest, audit)
        estimability, prospective_result = estimability_gate(contract)

        freezes = contract["freezes"]
        if set(freezes) != set(REQUIRED_FREEZE_KEYS):
            raise RuntimeError(
                "freeze ledger keys differ from the required 16-key surface: "
                f"missing={sorted(set(REQUIRED_FREEZE_KEYS) - set(freezes))}, "
                f"extra={sorted(set(freezes) - set(REQUIRED_FREEZE_KEYS))}"
            )
        runner_path = ROOT / freezes["runtime_runner"]["path"]
        observed_runner_sha = file_sha256(runner_path)
        if observed_runner_sha != freezes["runtime_runner"]["sha256"]:
            raise RuntimeError("frozen empirical runner SHA-256 differs from contract")
        freeze_fingerprints = {
            key: canonical_sha256(freezes[key]) for key in REQUIRED_FREEZE_KEYS
        }
        access_contract = FrozenOutcomeAccessContract(
            attempt_id=contract["attempt_id"],
            freeze_fingerprints=freeze_fingerprints,
            response_rows_opened=False,
            exact_count_gate_first=True,
            zero_fit_on_count_failure=True,
            no_post_open_redesign=True,
            note=(
                "fresh Mont-Blanc mountain-hare paired complementarity; uncertain "
                "published split counts require the exact count gate first"
            ),
        )
        access = evaluate_outcome_access_gate(access_contract, prospective_result)
        if not access.authorized:
            raise RuntimeError(f"outcome access was not authorized: {access.status}")

        result: dict[str, object] = {
            **audit,
            "status": "authorized_once_only_exact_count_gate_required",
            "contract_sha256": file_sha256(contract_path),
            "runner_sha256": observed_runner_sha,
            "candidate_preflight": candidate,
            "readme_audit": readme,
            "camera_audit": camera,
            "structural_gates": structural,
            "temporal_source_closure": closure,
            "response_header_gate": header,
            "prospective_estimability": estimability,
            "freeze_fingerprints": freeze_fingerprints,
            "outcome_access_contract_fingerprint": access_contract.fingerprint,
            "outcome_access_gate": asdict(access),
        }
        result["fingerprint"] = canonical_sha256(result)
    except Exception as exc:
        result = {
            **audit,
            "status": "pre_response_stop",
            "stop_reason": repr(exc),
        }
        result["fingerprint"] = canonical_sha256(result)
        (output / "preflight.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise

    if result["response_download_requests"]:
        raise AssertionError("preflight attempted a full response download")
    if result["response_payload_bytes_opened"] != 0:
        raise AssertionError("preflight opened response data-row payload bytes")
    if result["response_rows_opened"] or result["response_values_opened"]:
        raise AssertionError("preflight opened a response row or value")
    if result["model_fits"] or result["heldout_scores"]:
        raise AssertionError("preflight fit a model or scored a heldout outcome")
    (output / "preflight.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    try:
        result = run(output)
    except Exception as exc:
        print(f"Mont-Blanc mountain-hare preflight stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "node_count": result["camera_audit"]["node_count"],
                "distinct_lcc_threshold_count": result["structural_gates"][
                    "distinct_threshold_count"
                ],
                "prospective_estimability": result["prospective_estimability"][
                    "result"
                ]["status"],
                "response_header_bytes_opened": result["response_header_bytes_opened"],
                "response_payload_bytes_opened": 0,
                "response_rows_opened": False,
                "outcome_access_gate_fingerprint": result["outcome_access_gate"][
                    "fingerprint"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
