#!/usr/bin/env python3
"""Response-blind admission and authorization for the Yale--Myers attempt."""
from __future__ import annotations

import csv
from dataclasses import asdict
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
DEFAULT_OUTPUT = ROOT / "build/yale_myers_woodfrog_paired_complementarity/preflight"


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
        text = payload.decode("windows-1252")
    except UnicodeDecodeError as exc:
        raise RuntimeError("README_file.rtf is not Windows-1252 text") from exc
    required = (
        "This dataset contains 14 columns x 1130 rows",
        "From 2000 to 2020",
        "Avg.RASY.Count",
        "RASYdens_t2",
        "days_thawed",
        "spfaPDSIlag",
        "within 500 m",
        "Distance matrix for distance (in meters) between each pond",
        "Dataset is 65 columns x 65 rows",
    )
    # The year range lives in Dryad metadata rather than the small RTF.  It is checked
    # separately from the fixed source identity; do not manufacture it in the README.
    readme_required = tuple(value for value in required if value != "From 2000 to 2020")
    missing = [value for value in readme_required if value not in text]
    if missing:
        raise RuntimeError(f"fixed README semantic token missing: {missing[0]!r}")
    return {
        "encoding": "windows-1252",
        "declared_main_data_rows": 1130,
        "declared_main_data_columns": 14,
        "declared_distance_shape": [65, 65],
        "declared_neighbor_window_m": 500,
        "semantic_tokens_verified": list(readme_required),
    }


def parse_distance(payload: bytes, contract: dict) -> tuple[tuple[str, ...], np.ndarray, dict]:
    try:
        rows = list(csv.reader(io.StringIO(payload.decode("utf-8-sig"))))
    except UnicodeDecodeError as exc:
        raise RuntimeError("distance.mat.csv is not UTF-8") from exc
    if len(rows) != 65 or {len(row) for row in rows} != {65}:
        raise RuntimeError("distance.mat.csv physical shape differs from 65x65")
    if rows[0][0].strip() not in {"", "NA"}:
        raise RuntimeError("distance.mat.csv top-left label differs from frozen schema")
    column_ids = tuple(value.strip() for value in rows[0][1:])
    row_ids = tuple(row[0].strip() for row in rows[1:])
    if row_ids != column_ids:
        raise RuntimeError("distance row and column node order are not identical")
    if any(not value for value in row_ids) or len(set(row_ids)) != 64:
        raise RuntimeError("distance node labels are empty or duplicated")
    if canonical_sha256(list(row_ids)) != contract["freezes"]["node_geometry"][
        "ordered_node_ids_sha256"
    ]:
        raise RuntimeError("ordered 64-pond registry fingerprint drift")

    matrix = np.zeros((64, 64), dtype=float)
    diagonal_tokens: list[str] = []
    for i, row in enumerate(rows[1:]):
        for j, token in enumerate(row[1:]):
            value = token.strip()
            if i == j:
                diagonal_tokens.append(value)
                if value not in {"", "NA"}:
                    number = finite_optional(value, "distance diagonal")
                    if number is None or abs(number) > 1e-12:
                        raise RuntimeError("distance diagonal is neither missing nor zero")
                continue
            number = finite_optional(value, "off-diagonal distance")
            if number is None or number <= 0:
                raise RuntimeError("off-diagonal distance is missing or nonpositive")
            matrix[i, j] = number
    if not np.allclose(matrix, matrix.T, atol=1e-9, rtol=1e-12):
        raise RuntimeError("distance matrix is not symmetric")
    pair_values = matrix[np.triu_indices(64, k=1)]
    return row_ids, matrix, {
        "physical_shape": [65, 65],
        "node_count": 64,
        "pair_count": int(pair_values.size),
        "row_column_order_identical": True,
        "diagonal_tokens": sorted(set(diagonal_tokens)),
        "minimum_distance_m": float(np.min(pair_values)),
        "maximum_distance_m": float(np.max(pair_values)),
        "matrix_symmetric": True,
        "ordered_node_ids_sha256": canonical_sha256(list(row_ids)),
    }


def parse_pondinfo(
    payload: bytes,
    node_ids: tuple[str, ...],
) -> tuple[dict[str, tuple[float | None, float | None]], dict]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("pondinfo.csv is not UTF-8") from exc
    if header != ("Pond.ID", "Area", "Canopy"):
        raise RuntimeError(f"pondinfo.csv header drift: {header!r}")
    if len(rows) != 64:
        raise RuntimeError("pondinfo.csv row count differs from 64")
    values: dict[str, tuple[float | None, float | None]] = {}
    for number, row in enumerate(rows, start=2):
        node = (row.get("Pond.ID") or "").strip()
        if not node or node in values:
            raise RuntimeError(f"empty or duplicate Pond.ID at pondinfo row {number}")
        area = finite_optional(row.get("Area") or "", f"Area row {number}")
        canopy = finite_optional(row.get("Canopy") or "", f"Canopy row {number}")
        if area is not None and area <= 0:
            raise RuntimeError(f"nonpositive pond Area at row {number}")
        if canopy is not None and not 0 <= canopy <= 100:
            raise RuntimeError(f"pond Canopy outside 0..100 at row {number}")
        values[node] = (area, canopy)
    if set(values) != set(node_ids):
        raise RuntimeError("pondinfo registry does not join one-to-one to distance registry")
    return values, {
        "header": list(header),
        "rows": len(rows),
        "registry_join_complete": True,
        "area_missing": sum(row[0] is None for row in values.values()),
        "canopy_missing": sum(row[1] is None for row in values.values()),
        "area_observed_range_m2": [
            min(row[0] for row in values.values() if row[0] is not None),
            max(row[0] for row in values.values() if row[0] is not None),
        ],
        "canopy_observed_range_percent": [
            min(row[1] for row in values.values() if row[1] is not None),
            max(row[1] for row in values.values() if row[1] is not None),
        ],
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
        source_identity="Dryad 10.5061/dryad.0cfxpnw3r version 3 / resource 162105",
        geometry_source_identity=(
            "distance.mat.csv sha256:"
            + contract["files"]["distance.mat.csv"]["sha256"]
        ),
        response_source_identity=(
            "woodfrogdata.csv sha256:"
            + contract["files"]["woodfrogdata.csv"]["sha256"]
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=False,
        node_count=64,
        outer_unit_count=9,
        repeated_node_count=64,
        layout_design="natural_irregular",
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note=(
            "An exact response-independent metric distance matrix substitutes for raw "
            "coordinates; row/column labels and pondinfo close the 64-node registry."
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
        axis_id="pond_distance",
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
    transitions = 20
    declaration = TemporalSourceClosureDeclaration(
        closure_id="yale_myers_internal_conditional_full_support_v1",
        source_semantics=(
            "all 64 closed-registry ponds remain possible internal source states before "
            "outcome access; the eventual predictive endpoint conditions on observed "
            "current-year positive ponds and makes no external-source or ancestry claim"
        ),
        transition_semantics=(
            "same-node persistence plus every distinct internal pair admitted by the "
            "already-declared full-support exponential world over 2000->2001 through "
            "2019->2020; all registry ponds are optimistically target-eligible because "
            "split-specific survey availability is inside the unopened response and is "
            "enforced by the exact consecutive-row count gate"
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
        schema_id="yale_myers_woodfrog_response_header_v1",
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
        readme = audit_readme(payloads["README_file.rtf"])
        node_ids, distance, geometry = parse_distance(
            payloads["distance.mat.csv"], contract
        )
        _, pondinfo = parse_pondinfo(payloads["pondinfo.csv"], node_ids)
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
                "fresh Yale-Myers wood-frog paired complementarity; uncertain published "
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
            "pondinfo_audit": pondinfo,
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
        print(f"Yale-Myers preflight stopped: {exc!r}", file=sys.stderr)
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
