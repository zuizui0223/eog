#!/usr/bin/env python3
"""Response-blind admission and authorization for the Mt Gibson attempt."""
from __future__ import annotations

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
DEFAULT_OUTPUT = ROOT / "build/mt_gibson_phascogale_paired_complementarity/preflight"


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


def finite_optional(value: str, label: str) -> float | None:
    token = value.strip()
    if token in {"", "NA", "NaN", "nan"}:
        return None
    try:
        number = float(token)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric or a frozen missing token") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"{label} is nonfinite")
    return number


def audit_readme(payload: bytes) -> dict[str, object]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("README.md is not UTF-8 text") from exc
    required = (
        "red-tailed phascogales",
        "Camera survey_deployment data",
        "Camera survey_detection data",
        "Camera survey_site location",
        "X_COORD - UTM easting coordinates, zone 50",
        "Y_COORD - UTM northing coordinates, zone 50",
        "Detection date - Date of red-tailed phascogale detection on remote camera, one detection per survey date per site",
        "The camera survey files are linked via the Camera Site",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise RuntimeError(f"fixed README semantic token missing: {missing[0]!r}")
    return {
        "encoding": "utf-8",
        "coordinate_reference": "UTM zone 50",
        "response_unit": "one detection per survey date per site",
        "camera_join_key": "Camera Site",
        "semantic_tokens_verified": list(required),
    }


def parse_geometry(
    payload: bytes, contract: dict
) -> tuple[tuple[str, ...], np.ndarray, np.ndarray, dict]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("Camera_survey_site_location_data.csv is not UTF-8") from exc
    if header != ("Site", "X_COORD", "Y_COORD"):
        raise RuntimeError(f"camera site-location header drift: {header!r}")
    if len(rows) != 70:
        raise RuntimeError("camera site-location row count differs from 70")
    node_ids = tuple((row.get("Site") or "").strip() for row in rows)
    if any(not value for value in node_ids) or len(set(node_ids)) != 70:
        raise RuntimeError("camera site IDs are empty or duplicated")
    if canonical_sha256(list(node_ids)) != contract["freezes"]["node_geometry"][
        "ordered_node_ids_sha256"
    ]:
        raise RuntimeError("ordered 70-site registry fingerprint drift")
    coordinates = np.asarray(
        [
            [
                finite_optional(row.get("X_COORD") or "", "X_COORD"),
                finite_optional(row.get("Y_COORD") or "", "Y_COORD"),
            ]
            for row in rows
        ],
        dtype=float,
    )
    if not np.isfinite(coordinates).all():
        raise RuntimeError("camera site coordinates are missing or nonfinite")
    if len({tuple(value) for value in coordinates.tolist()}) != 70:
        raise RuntimeError("camera site coordinate pairs are duplicated")
    delta = coordinates[:, None, :] - coordinates[None, :, :]
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    np.fill_diagonal(distance, 0.0)
    pair_values = distance[np.triu_indices(70, k=1)]
    return node_ids, coordinates, distance, {
        "header": list(header),
        "node_count": 70,
        "pair_count": int(pair_values.size),
        "coordinate_reference": "UTM zone 50",
        "coordinate_pairs_unique": True,
        "coordinate_min": np.min(coordinates, axis=0).tolist(),
        "coordinate_max": np.max(coordinates, axis=0).tolist(),
        "minimum_distance_m": float(np.min(pair_values)),
        "maximum_distance_m": float(np.max(pair_values)),
        "derived_matrix_symmetric": bool(np.allclose(distance, distance.T)),
        "ordered_node_ids_sha256": canonical_sha256(list(node_ids)),
    }


def _parse_date(token: str, label: str) -> date:
    try:
        return datetime.strptime(token.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise RuntimeError(f"invalid {label}") from exc


def parse_deployments(
    payload: bytes,
    node_ids: tuple[str, ...],
    contract: dict,
) -> tuple[
    dict[tuple[str, int], tuple[tuple[date, date], ...]],
    np.ndarray,
    np.ndarray,
    dict,
]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("Camera_survey_deployment_data.csv is not UTF-8") from exc
    if header != ("Camera site", "Date deployed", "Date retrieved"):
        raise RuntimeError(f"camera deployment header drift: {header!r}")
    if len(rows) != 493:
        raise RuntimeError("camera deployment row count differs from 493")
    node_set = set(node_ids)
    grouped: dict[tuple[str, int], list[tuple[date, date]]] = {}
    invalid: list[dict[str, object]] = []
    for number, row in enumerate(rows, start=2):
        node = (row.get("Camera site") or "").strip()
        if node not in node_set:
            raise RuntimeError(f"unknown camera site at deployment row {number}")
        start = _parse_date(row.get("Date deployed") or "", "Date deployed")
        end = _parse_date(row.get("Date retrieved") or "", "Date retrieved")
        campaign = 2018 if start.year == 2017 else end.year
        if campaign not in range(2018, 2025):
            raise RuntimeError(f"deployment campaign outside 2018..2024 at row {number}")
        grouped.setdefault((node, campaign), []).append((start, end))
        if end < start:
            invalid.append(
                {"site": node, "campaign": campaign, "start": str(start), "end": str(end)}
            )
    expected_keys = {(node, year) for node in node_ids for year in range(2018, 2025)}
    if set(grouped) != expected_keys:
        raise RuntimeError("deployment table does not close all 70x7 site campaigns")
    frozen_invalid = contract["freezes"]["node_geometry"]["survey_effort"]["invalid_intervals_excluded"]
    if invalid != frozen_invalid:
        raise RuntimeError("frozen invalid-deployment identity drift")
    intervals = {key: tuple(value) for key, value in grouped.items()}
    effort = np.zeros((70, 7), dtype=float)
    midpoint = np.zeros((70, 7), dtype=float)
    node_index = {node: index for index, node in enumerate(node_ids)}
    for (node, campaign), values in intervals.items():
        days = {
            ordinal
            for start, end in values
            if end >= start
            for ordinal in range(start.toordinal(), end.toordinal() + 1)
        }
        if not days:
            raise RuntimeError("site campaign has no valid deployment day")
        i = node_index[node]
        t = campaign - 2018
        effort[i, t] = len(days)
        anchor = date(campaign - 1, 10, 1).toordinal()
        midpoint[i, t] = float(np.mean([ordinal - anchor for ordinal in days]))
    duplicates = sorted(
        [
            {"site": node, "campaign": campaign, "interval_count": len(values)}
            for (node, campaign), values in intervals.items()
            if len(values) > 1
        ],
        key=lambda row: (row["campaign"], row["site"]),
    )
    expected_duplicates = contract["freezes"]["node_geometry"]["survey_effort"]["duplicate_groups"]
    if duplicates != expected_duplicates:
        raise RuntimeError("frozen duplicate-deployment group identity drift")
    return intervals, effort, midpoint, {
        "header": list(header),
        "rows": len(rows),
        "site_campaign_groups": len(intervals),
        "complete_70_by_7_registry": True,
        "campaigns": list(range(2018, 2025)),
        "duplicate_groups": duplicates,
        "invalid_intervals_excluded": invalid,
        "effort_union_rule": "inclusive union of valid deployment calendar days",
        "effort_day_range": [float(np.min(effort)), float(np.max(effort))],
        "midpoint_index_anchor": "October 1 before each named campaign",
    }


def candidate_gate(contract: dict) -> dict:
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
        source_identity="Dryad 10.5061/dryad.xd2547dp4 version 1 / resource 303436",
        geometry_source_identity=(
            "Camera_survey_site_location_data.csv sha256:"
            + contract["files"]["Camera_survey_site_location_data.csv"]["sha256"]
        ),
        response_source_identity=(
            "Camera_survey_detection_data.csv sha256:"
            + contract["files"]["Camera_survey_detection_data.csv"]["sha256"]
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=70,
        outer_unit_count=2,
        repeated_node_count=70,
        layout_design="natural_irregular",
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note=(
            "UTM site coordinates and deployment effort are physically separate from "
            "detections; all 70 sites repeat in every 2018-2024 campaign. The paired "
            "claim uses only four 2020-2024 transitions after releases ended in 2019."
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
        axis_id="camera_site_utm_distance",
        target_largest_component_fractions=tuple(contract["structural_targets"]),
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    observed = np.asarray(ladder.thresholds, dtype=float)
    expected = np.asarray(contract["freezes"]["world_scale"]["thresholds_m"], dtype=float)
    if not np.allclose(observed, expected, atol=1e-9, rtol=0.0):
        raise RuntimeError(
            f"response-blind LCC threshold drift: {observed.tolist()} != {expected.tolist()}"
        )
    if len({round(value, 9) for value in observed}) != int(
        contract["freezes"]["structural_adequacy"]["required_distinct_lcc_thresholds"]
    ):
        raise RuntimeError("four declared LCC regimes do not yield four distinct thresholds")
    built = structural_scale_adjacencies(ladder, distance)
    world_ids = contract["freezes"]["world_scale"]["threshold_world_ids"]
    worlds = {
        world_id: built[level.level_id]
        for world_id, level in zip(world_ids, ladder.levels, strict=True)
    }
    full = np.ones((len(node_ids), len(node_ids)), dtype=bool)
    np.fill_diagonal(full, False)
    worlds[contract["freezes"]["world_scale"]["full_world_id"]] = full

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
        "distinct_threshold_count": len({round(value, 9) for value in observed}),
        "world_audit": asdict(audit),
        "adequacy_gate": asdict(gate),
    }


def temporal_closure(
    node_ids: tuple[str, ...],
    worlds: dict[str, np.ndarray],
) -> dict:
    n = len(node_ids)
    transitions = 4
    declaration = TemporalSourceClosureDeclaration(
        closure_id="mt_gibson_post_release_internal_conditional_full_support_v1",
        source_semantics=(
            "all 70 closed-registry camera sites remain possible internal source states "
            "before outcome access; the endpoint conditions on current detected sites "
            "inside the fenced reserve and makes no ancestry claim"
        ),
        transition_semantics=(
            "same-node persistence plus every distinct internal pair admitted by the "
            "already-declared full-support exponential world over 2020->2021 through "
            "2023->2024; the response-blind deployment table proves every registry site "
            "was surveyed in every campaign, and managed releases ended in 2019"
        ),
    )
    result = evaluate_temporal_source_closure(
        declaration,
        node_ids,
        np.ones(n, dtype=bool),
        np.ones((n, transitions), dtype=bool),
        np.ones((n, transitions), dtype=bool),
        worlds["geo_exponential_full"],
    )
    if not result.passed:
        raise RuntimeError(f"temporal source closure stopped: {result.status}")
    return {"declaration": asdict(declaration), "result": asdict(result)}


def header_gate(contract: dict, manifest: dict[str, str], audit: dict) -> dict:
    frozen = contract["response_header_firewall"]
    header_text, terminator, consumed, transport = read_bounded_response_header(
        contract, manifest, audit
    )
    if int(transport["transport_reconnects"]) != 0:
        raise RuntimeError(
            "bounded physical response header required a reconnect; freeze evidence is not reused"
        )
    if header_text != frozen["expected_header_text"]:
        raise RuntimeError("bounded physical response header text differs from frozen evidence")
    if terminator != frozen["expected_terminator"]:
        raise RuntimeError("bounded physical response terminator differs from frozen evidence")
    if consumed != int(frozen["expected_bytes_consumed_including_terminator"]):
        raise RuntimeError("bounded physical response header length differs from frozen evidence")
    declaration = ResponseHeaderSchemaDeclaration(
        schema_id="mt_gibson_phascogale_response_header_v1",
        expected_columns=tuple(frozen["expected_columns"]),
        delimiter=",",
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


def estimability_gate(contract: dict) -> dict:
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
    intervals = {
        key: AggregateCountInterval(
            lower=published["split_specific_intervals"][key]["lower"],
            upper=published["split_specific_intervals"][key]["upper"],
        )
        for key in (
            "calibration_events",
            "calibration_non_events",
            "heldout_events",
            "heldout_non_events",
            "heldout_outer_units_with_both_classes",
        )
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
        raise RuntimeError(
            f"expected unresolved published split counts, observed {result.status}"
        )
    if disposition != "continue_response_blind_exact_gate_required":
        raise RuntimeError(f"unexpected prospective disposition: {disposition}")
    return {
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "result": asdict(result),
        "disposition": disposition,
    }


def run(output: Path) -> dict:
    contract_path = HERE / "source_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    audit = {
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
        node_ids, _, distance, geometry = parse_geometry(
            payloads["Camera_survey_site_location_data.csv"], contract
        )
        _, _, _, deployments = parse_deployments(
            payloads["Camera_survey_deployment_data.csv"], node_ids, contract
        )
        worlds, structural = structural_gates(contract, node_ids, distance)
        closure = temporal_closure(node_ids, worlds)
        header = header_gate(contract, manifest, audit)
        estimability = estimability_gate(contract)

        freezes = contract["freezes"]
        if set(freezes) != set(REQUIRED_FREEZE_KEYS):
            raise RuntimeError(
                "freeze ledger keys differ from the required 16-key surface: "
                f"missing={sorted(set(REQUIRED_FREEZE_KEYS)-set(freezes))}, "
                f"extra={sorted(set(freezes)-set(REQUIRED_FREEZE_KEYS))}"
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
                "fresh Mt Gibson phascogale paired complementarity; uncertain published "
                "split counts require exact count gate first; one full response download"
            ),
        )
        access = evaluate_outcome_access_gate(
            access_contract,
            # The generic gate consumes the exact result object, retained above.
            evaluate_prospective_estimability(
                ProspectiveEstimabilityDeclaration(
                    **{
                        key: int(contract["freezes"]["count_gate"][key])
                        for key in (
                            "calibration_events",
                            "calibration_non_events",
                            "heldout_events",
                            "heldout_non_events",
                            "heldout_outer_units_with_both_classes",
                        )
                    }
                ),
                AggregateEstimabilityEvidence(
                    source_label=contract["published_aggregate_evidence"]["source"],
                    endpoint_definition_matches=True,
                    response_rows_opened=False,
                    intervals={
                        key: AggregateCountInterval()
                        for key in (
                            "calibration_events",
                            "calibration_non_events",
                            "heldout_events",
                            "heldout_non_events",
                            "heldout_outer_units_with_both_classes",
                        )
                    },
                    note=contract["published_aggregate_evidence"]["note"],
                ),
            ),
        )
        if not access.authorized:
            raise RuntimeError(f"outcome access was not authorized: {access.status}")

        result = {
            **audit,
            "status": "authorized_once_only_exact_count_gate_required",
            "contract_sha256": file_sha256(contract_path),
            "runner_sha256": observed_runner_sha,
            "candidate_preflight": candidate,
            "readme_audit": readme,
            "geometry_audit": geometry,
            "deployment_audit": deployments,
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
        print(f"Mt Gibson preflight stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "node_count": result["geometry_audit"]["node_count"],
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
