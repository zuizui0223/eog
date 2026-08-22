#!/usr/bin/env python3
"""Response-blind source, geometry, effort, closure and header gate for Portal DM."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import csv
from datetime import date
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

from transport import audit_fixed_tree, download_nonresponse, read_bounded_response_header


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "build/portal_dm_paired_complementarity/preflight"
COORDINATE_HEADER = (
    "gps_num", "plot", "type", "number", "east", "north", "elev",
    "hor_error", "vert_error", "flag", "notes",
)
EFFORT_HEADER = ("day", "month", "year", "period", "plot", "sampled", "effort", "qcflag")
MOON_HEADER = ("newmoonnumber", "newmoondate", "period", "censusdate")
PLOT_HEADER = ("year", "month", "plot", "treatment", "resourcetreatment", "anttreatment")
SPECIES_HEADER = (
    "speciescode", "scientificname", "taxa", "commonname", "censustarget",
    "unidentified", "rodent", "granivore", "minhfl", "meanhfl", "maxhfl",
    "minwgt", "meanwgt", "maxwgt", "juvwgt",
)


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def parse_csv(payload: bytes, expected_header: tuple[str, ...], label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not UTF-8") from exc
    if header != expected_header:
        raise RuntimeError(f"{label} header drift: {header!r}")
    if any(None in row for row in rows):
        raise RuntimeError(f"{label} contains a row wider than its header")
    return rows


def exact_int(value: str, label: str) -> int:
    try:
        number = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric") from exc
    if not math.isfinite(number) or abs(number - round(number)) > 1e-9:
        raise RuntimeError(f"{label} is not integer-valued")
    return int(round(number))


def finite_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"{label} is not finite")
    return number


def candidate_gate(contract: dict) -> dict[str, object]:
    frozen = contract["candidate_preflight"]
    response = contract["files"][contract["response_file"]]
    declaration = CandidatePreflightDeclaration(
        attempt_id=contract["attempt_id"],
        minimum_nodes=int(frozen["minimum_nodes"]),
        minimum_outer_units=int(frozen["minimum_outer_units"]),
        minimum_repeated_nodes=int(frozen["minimum_repeated_nodes"]),
        require_separate_geometry_and_response=True,
        require_coordinate_geometry=True,
        require_closed_analysis_registry=True,
    )
    evidence = CandidatePreflightEvidence(
        source_identity=(
            "weecology/PortalData@" + contract["publication"]["repository_commit"]
        ),
        geometry_source_identity=(
            "SiteandMethods/Portal_UTMCoords.csv blob "
            + contract["files"]["SiteandMethods/Portal_UTMCoords.csv"]["git_blob_sha1"]
        ),
        response_source_identity=(
            contract["response_file"] + " blob " + response["git_blob_sha1"]
        ),
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=int(frozen["known_node_count"]),
        outer_unit_count=int(frozen["known_outer_unit_count"]),
        repeated_node_count=int(frozen["known_repeated_node_count"]),
        layout_design=frozen["layout_design"],
        analysis_registry_closed=True,
        response_rows_opened=False,
        response_bytes_opened=False,
        note="24 plots closed by 49 released stake coordinates; eight frozen heldout years",
    )
    result = evaluate_candidate_preflight(declaration, evidence)
    if not result.ready:
        raise RuntimeError(f"candidate preflight stopped: {result.status}")
    return {"declaration": asdict(declaration), "evidence": asdict(evidence), "result": asdict(result)}


def audit_methods(payloads: dict[str, bytes]) -> dict[str, object]:
    methods = payloads["SiteandMethods/Methods.md"].decode("utf-8")
    rodent_readme = payloads["Rodents/README.md"].decode("utf-8")
    writer = payloads["DataCleaningScripts/new_rodent_data.r"].decode("utf-8")
    eml = payloads["EML/eml_portal_data.R"].decode("utf-8")
    required_methods = (
        "24 experimental plots",
        "49 permanent trapping stations",
        "7x7 grid",
        "plots were trapped around each new moon",
        "each plot is trapped for one night",
    )
    required_readme = (
        "All plots are trapped approximately monthly (1977 - present)",
        "differentiate real zeros from missing data",
        "Negative period codes indicate data collected outside of the normal census protocols",
    )
    for token in required_methods:
        if token not in methods:
            raise RuntimeError(f"Methods semantic token missing: {token!r}")
    for token in required_readme:
        if token not in rodent_readme:
            raise RuntimeError(f"Rodents README semantic token missing: {token!r}")
    for token in ("ws$pit_tag <- NA", "ws$id <- NA", "col.names = T"):
        if token not in writer:
            raise RuntimeError(f"current writer header token missing: {token!r}")
    if "prevlet" not in eml or "prevlt" not in methods:
        raise RuntimeError("official prevlet/prevlt header-candidate provenance drift")
    return {
        "methods_tokens": list(required_methods),
        "rodent_readme_tokens": list(required_readme),
        "finite_header_candidate_basis_confirmed": True,
    }


def geometry_gate(payload: bytes, contract: dict) -> tuple[tuple[str, ...], np.ndarray, np.ndarray, dict[str, object]]:
    rows = parse_csv(payload, COORDINATE_HEADER, "Portal_UTMCoords.csv")
    if len(rows) != int(contract["node_geometry"]["expected_coordinate_rows"]):
        raise RuntimeError("coordinate row count drift")
    expected_numbers = {10 * r + c for r in range(1, 8) for c in range(1, 8)}
    stakes: dict[int, list[tuple[int, int, float, float, int]]] = {
        plot: [] for plot in range(1, 25)
    }
    stake_gps_numbers: set[int] = set()
    flag_counts = {0: 0, 1: 0}
    for row in rows:
        if row["type"] != "stake":
            continue
        gps_number = exact_int(row["gps_num"], "coordinate gps_num")
        plot = exact_int(row["plot"], "coordinate plot")
        number = exact_int(row["number"], "coordinate stake number")
        flag = exact_int(row["flag"], "coordinate flag")
        if plot not in stakes or number not in expected_numbers or flag not in flag_counts:
            raise RuntimeError("stake row lies outside the frozen registry")
        if gps_number in stake_gps_numbers:
            raise RuntimeError(f"duplicate stake gps_num: {gps_number}")
        east = finite_float(row["east"], "stake east")
        north = finite_float(row["north"], "stake north")
        stakes[plot].append((gps_number, number, east, north, flag))
        stake_gps_numbers.add(gps_number)
        flag_counts[flag] += 1
    expected_rows_per_plot = int(contract["node_geometry"]["expected_stake_rows_per_plot"])
    if any(len(values) != expected_rows_per_plot for values in stakes.values()):
        raise RuntimeError("stake geometry does not have exactly 49 released rows per plot")

    number_anomalies: list[dict[str, object]] = []
    for plot, values in stakes.items():
        counts = Counter(value[1] for value in values)
        missing = sorted(expected_numbers - set(counts))
        duplicated = [
            {
                "number": number,
                "row_count": count,
                "gps_num": sorted(value[0] for value in values if value[1] == number),
            }
            for number, count in sorted(counts.items())
            if count > 1
        ]
        if missing or duplicated:
            number_anomalies.append(
                {
                    "plot": plot,
                    "missing_numbers": missing,
                    "duplicated_numbers": duplicated,
                }
            )
    if number_anomalies != contract["node_geometry"]["released_stake_number_anomalies"]:
        raise RuntimeError("released stake-number anomaly differs from the frozen contract")

    coordinate_pairs = [
        (value[2], value[3]) for values in stakes.values() for value in values
    ]
    if len(set(coordinate_pairs)) != 24 * expected_rows_per_plot:
        raise RuntimeError("released stake coordinate pairs are not unique")
    centers = np.asarray(
        [
            np.mean(
                np.asarray([(value[2], value[3]) for value in stakes[p]], dtype=float),
                axis=0,
            )
            for p in range(1, 25)
        ],
        dtype=float,
    )
    if len({tuple(row) for row in centers.tolist()}) != 24:
        raise RuntimeError("derived plot-center coordinates are not unique")
    delta = centers[:, None, :] - centers[None, :, :]
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    node_ids = tuple(f"plot_{plot:02d}" for plot in range(1, 25))
    if list(node_ids) != contract["node_geometry"]["analysis_node_ids"]:
        raise RuntimeError("closed node order differs from contract")
    pairs = distance[np.triu_indices(24, k=1)]
    audit = {
        "coordinate_rows": len(rows),
        "stake_rows": sum(len(value) for value in stakes.values()),
        "node_count": len(node_ids),
        "released_stake_rows_per_plot": expected_rows_per_plot,
        "released_stake_number_anomalies": number_anomalies,
        "unique_stake_gps_num_count": len(stake_gps_numbers),
        "unique_stake_coordinate_pair_count": len(set(coordinate_pairs)),
        "stake_flag_counts": flag_counts,
        "plot_centers": centers.tolist(),
        "minimum_pair_distance_m": float(np.min(pairs)),
        "maximum_pair_distance_m": float(np.max(pairs)),
        "pair_count": int(pairs.size),
        "distance_matrix_symmetric": bool(np.allclose(distance, distance.T)),
        "ordered_node_ids_fingerprint": canonical_sha256(list(node_ids)),
        "center_fingerprint": canonical_sha256(centers.tolist()),
    }
    return node_ids, centers, distance, audit


def structural_gate(contract: dict, node_ids: tuple[str, ...], distance: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    frozen = contract["world_scale"]
    declaration = StructuralScaleLadderDeclaration(
        axis_id=frozen["axis_id"],
        target_largest_component_fractions=tuple(frozen["target_largest_component_fractions"]),
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    if len(set(ladder.thresholds)) < int(frozen["minimum_distinct_threshold_count"]):
        raise RuntimeError("response-blind structural scale ladder collapsed")
    worlds = structural_scale_adjacencies(ladder, distance)
    full = np.ones((len(node_ids), len(node_ids)), dtype=bool)
    np.fill_diagonal(full, False)
    worlds["portal_plot_euclidean_full"] = full
    adequacy_frozen = contract["structural_adequacy"]
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(
            adequacy_frozen["min_largest_weak_component_fraction"]
        ),
        max_isolated_node_fraction=float(adequacy_frozen["max_isolated_node_fraction"]),
        require_at_least_one_world_pass=bool(
            adequacy_frozen["require_at_least_one_world_pass"]
        ),
    )
    audit = audit_world_universe_structure(
        node_ids, worlds, horizon=int(adequacy_frozen["horizon"])
    )
    gate = apply_structural_adequacy_gate(audit, adequacy)
    if not gate.passed:
        raise RuntimeError("response-blind structural adequacy gate stopped")
    return worlds, {
        "ladder_declaration": asdict(declaration),
        "ladder": asdict(ladder),
        "thresholds_m": list(ladder.thresholds),
        "distinct_threshold_count": len(set(ladder.thresholds)),
        "world_universe_audit": asdict(audit),
        "adequacy_declaration": asdict(adequacy),
        "adequacy_gate": asdict(gate),
    }


def effort_time_gate(
    effort_payload: bytes,
    moon_payload: bytes,
    plot_payload: bytes,
    worlds: dict[str, np.ndarray],
    node_ids: tuple[str, ...],
    contract: dict,
) -> dict[str, object]:
    effort_rows = parse_csv(effort_payload, EFFORT_HEADER, "Portal_rodent_trapping.csv")
    moon_rows = parse_csv(moon_payload, MOON_HEADER, "moon_dates.csv")
    plot_rows = parse_csv(plot_payload, PLOT_HEADER, "Portal_plots.csv")
    frozen = contract["effort_time_registry"]
    if len(effort_rows) != int(frozen["expected_effort_rows"]):
        raise RuntimeError("effort row count drift")
    if len(plot_rows) != int(frozen["expected_plot_treatment_rows"]):
        raise RuntimeError("plot-treatment row count drift")

    availability: dict[tuple[int, int], bool] = {}
    period_dates: dict[int, set[date]] = {}
    for row in effort_rows:
        period = exact_int(row["period"], "effort period")
        plot = exact_int(row["plot"], "effort plot")
        year = exact_int(row["year"], "effort year")
        month = exact_int(row["month"], "effort month")
        day = exact_int(row["day"], "effort day")
        sampled = exact_int(row["sampled"], "effort sampled")
        effort = exact_int(row["effort"], "effort traps")
        qcflag = exact_int(row["qcflag"], "effort qcflag")
        key = (period, plot)
        if period <= 0 or plot not in range(1, 25) or key in availability:
            raise RuntimeError("effort registry contains invalid or duplicate identity")
        availability[key] = sampled == 1 and effort >= 47 and qcflag == 1
        try:
            observed_date = date(year, month, day)
        except ValueError as exc:
            raise RuntimeError("effort row has an invalid calendar date") from exc
        period_dates.setdefault(period, set()).add(observed_date)
    if set(plot for _, plot in availability) != set(range(1, 25)):
        raise RuntimeError("effort registry does not cover all 24 plots")
    if len(period_dates) != int(frozen["expected_effort_period_count"]):
        raise RuntimeError("effort period count drift")

    moon_by_number: dict[int, tuple[int, date]] = {}
    moon_by_period: dict[int, tuple[int, date]] = {}
    missing_tokens = set(frozen["moon_missing_value_tokens"])
    for row in moon_rows:
        number = exact_int(row["newmoonnumber"], "newmoonnumber")
        if row["period"] in missing_tokens or row["censusdate"] in missing_tokens:
            continue
        period = exact_int(row["period"], "moon period")
        try:
            census = date.fromisoformat(row["censusdate"])
        except ValueError as exc:
            raise RuntimeError("moon censusdate is not strict ISO") from exc
        if number in moon_by_number or period in moon_by_period:
            raise RuntimeError("duplicate sampled newmoonnumber or period")
        moon_by_number[number] = (period, census)
        moon_by_period[period] = (number, census)
    if set(period_dates) != set(moon_by_period):
        raise RuntimeError("effort and moon registries do not contain the same periods")

    multi_calendar_year_periods = []
    for period, observed_dates in sorted(period_dates.items()):
        years = sorted({value.year for value in observed_dates})
        if len(years) <= 1:
            continue
        newmoonnumber, census = moon_by_period[period]
        multi_calendar_year_periods.append(
            {
                "period": period,
                "calendar_years": years,
                "trapping_dates": [value.isoformat() for value in sorted(observed_dates)],
                "newmoonnumber": newmoonnumber,
                "censusdate": census.isoformat(),
            }
        )
    if multi_calendar_year_periods != frozen["multi_calendar_year_effort_periods"]:
        raise RuntimeError("multi-calendar-year effort period differs from the contract")

    plot_months: set[tuple[int, int, int]] = set()
    categories = {"treatment": set(), "resourcetreatment": set(), "anttreatment": set()}
    for row in plot_rows:
        key = (
            exact_int(row["year"], "plot year"),
            exact_int(row["month"], "plot month"),
            exact_int(row["plot"], "plot ID"),
        )
        if key in plot_months:
            raise RuntimeError("duplicate plot treatment identity")
        plot_months.add(key)
        for name in categories:
            categories[name].add(row[name])

    transitions: list[dict[str, object]] = []
    for number in sorted(moon_by_number):
        if number + 1 not in moon_by_number:
            continue
        source_period, source_date = moon_by_number[number]
        target_period, target_date = moon_by_number[number + 1]
        if target_date.year > 2019:
            continue
        eligible = [
            plot
            for plot in range(1, 25)
            if availability.get((source_period, plot), False)
            and availability.get((target_period, plot), False)
        ]
        if not eligible:
            continue
        for plot in eligible:
            if (target_date.year, target_date.month, plot) not in plot_months:
                raise RuntimeError("eligible target lacks response-independent treatment row")
        transitions.append(
            {
                "newmoonnumber": number,
                "source_period": source_period,
                "target_period": target_period,
                "source_date": source_date.isoformat(),
                "target_date": target_date.isoformat(),
                "target_year": target_date.year,
                "eligible_plots": eligible,
            }
        )
    calibration = [row for row in transitions if int(row["target_year"]) <= 2011]
    heldout = [row for row in transitions if 2012 <= int(row["target_year"]) <= 2019]
    by_year = {
        str(year): {
            "transition_count": sum(int(row["target_year"]) == year for row in heldout),
            "potential_plot_rows": sum(
                len(row["eligible_plots"])
                for row in heldout
                if int(row["target_year"]) == year
            ),
        }
        for year in range(2012, 2020)
    }
    if len(calibration) != 374 or len(heldout) != 87:
        raise RuntimeError("response-independent transition count drift")
    if any(value["transition_count"] == 0 for value in by_year.values()):
        raise RuntimeError("a frozen heldout year has no response-independent transition")

    eligible_matrix = np.zeros((24, len(transitions)), dtype=bool)
    for column, row in enumerate(transitions):
        for plot in row["eligible_plots"]:
            eligible_matrix[plot - 1, column] = True
    declaration = TemporalSourceClosureDeclaration(
        closure_id="portal_dm_declared_score_transition_closure_v1",
        source_semantics="all response-blind possible internal plots at the first declared scored transition",
        transition_semantics=(
            "optimistic propagation across each declared consecutive-newmoon scored transition; "
            "target and persistence eligibility require the frozen effort rule"
        ),
    )
    result = evaluate_temporal_source_closure(
        declaration,
        node_ids,
        np.ones(24, dtype=bool),
        eligible_matrix,
        eligible_matrix,
        worlds["portal_plot_euclidean_full"],
    )
    if not result.passed:
        raise RuntimeError(f"temporal source closure stopped: {result.status}")
    return {
        "effort_rows": len(effort_rows),
        "effort_period_count": len(period_dates),
        "multi_calendar_year_effort_periods": multi_calendar_year_periods,
        "time_authority": frozen["time_authority"],
        "plot_treatment_rows": len(plot_rows),
        "treatment_categories": {key: sorted(value) for key, value in categories.items()},
        "declared_transition_count": len(transitions),
        "calibration_transition_count": len(calibration),
        "calibration_potential_plot_rows": sum(len(row["eligible_plots"]) for row in calibration),
        "heldout_transition_count": len(heldout),
        "heldout_potential_plot_rows": sum(len(row["eligible_plots"]) for row in heldout),
        "heldout_response_independent_counts": by_year,
        "closure_declaration": asdict(declaration),
        "closure_result": asdict(result),
    }


def species_gate(payload: bytes) -> dict[str, object]:
    rows = parse_csv(payload, SPECIES_HEADER, "Portal_rodent_species.csv")
    focal = [row for row in rows if row["speciescode"] == "DM"]
    if len(focal) != 1:
        raise RuntimeError("focal DM species identity is not unique")
    row = focal[0]
    if row["scientificname"] != "Dipodomys merriami" or row["censustarget"] != "1":
        raise RuntimeError("focal DM taxonomy or target status drift")
    return {
        "species_table_rows": len(rows),
        "focal_species": row,
        "response_rows_opened": False,
    }


def header_gate(contract: dict, audit: dict) -> dict[str, object]:
    header_text, terminator, consumed, transport = read_bounded_response_header(contract, audit)
    candidates = [tuple(value) for value in contract["response_header_firewall"]["candidate_columns"]]
    results = []
    for index, columns in enumerate(candidates, start=1):
        declaration = ResponseHeaderSchemaDeclaration(
            schema_id=f"portal_dm_response_header_candidate_{index}_v1",
            expected_columns=columns,
            delimiter=contract["response_header_firewall"]["delimiter"],
            require_exact_order=True,
        )
        evidence = ResponseHeaderSchemaEvidence(
            header_text=header_text,
            terminator=terminator,
            bytes_consumed=consumed,
            response_rows_opened=False,
            response_values_opened=False,
        )
        result = evaluate_response_header_schema(declaration, evidence)
        results.append((declaration, evidence, result))
    matches = [value for value in results if value[2].ready]
    if len(matches) != 1:
        raise RuntimeError(
            f"bounded physical header matched {len(matches)} prospectively declared candidates"
        )
    declaration, evidence, result = matches[0]
    return {
        "matched_candidate_index_one_based": results.index(matches[0]) + 1,
        "selected_exact_columns": list(result.observed_columns),
        "selected_header_text": header_text,
        "declaration": asdict(declaration),
        "evidence": asdict(evidence),
        "transport": transport,
        "result": asdict(result),
    }


def run(output: Path) -> dict[str, object]:
    contract_path = HERE / "source_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    audit: dict[str, object] = {
        "attempt_id": contract["attempt_id"],
        "stage": contract["stage_boundary"]["stage"],
        "tree_metadata_requests": 0,
        "tree_metadata_bytes": 0,
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
        "outcome_access_authorized": False,
    }
    try:
        candidate = candidate_gate(contract)
        tree = audit_fixed_tree(contract, audit)
        payloads = {
            path: download_nonresponse(path, contract, audit)
            for path, spec in contract["files"].items()
            if spec["role"] != "response"
        }
        methods = audit_methods(payloads)
        node_ids, _, distance, geometry = geometry_gate(
            payloads["SiteandMethods/Portal_UTMCoords.csv"], contract
        )
        worlds, structural = structural_gate(contract, node_ids, distance)
        effort_time = effort_time_gate(
            payloads["Rodents/Portal_rodent_trapping.csv"],
            payloads["Rodents/moon_dates.csv"],
            payloads["SiteandMethods/Portal_plots.csv"],
            worlds,
            node_ids,
            contract,
        )
        species = species_gate(payloads["Rodents/Portal_rodent_species.csv"])
        header = header_gate(contract, audit)
        result: dict[str, object] = {
            **audit,
            "status": "response_blind_candidate_header_ready_for_full_freeze",
            "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            "fixed_source_tree": tree,
            "candidate_preflight": candidate,
            "methods_audit": methods,
            "geometry_audit": geometry,
            "structural_gates": structural,
            "effort_time_audit": effort_time,
            "species_audit": species,
            "response_header_gate": header,
            "stage_boundary": contract["stage_boundary"],
        }
        result["fingerprint"] = canonical_sha256(result)
    except Exception as exc:
        result = {**audit, "status": "pre_response_stop", "stop_reason": repr(exc)}
        result["fingerprint"] = canonical_sha256(result)
        (output / "preflight.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        raise

    if result["response_download_requests"] or result["response_payload_bytes_opened"]:
        raise AssertionError("preflight crossed the row-level response firewall")
    if result["response_rows_opened"] or result["response_values_opened"]:
        raise AssertionError("preflight opened a response row or value")
    if result["model_fits"] or result["heldout_scores"]:
        raise AssertionError("preflight fit or scored a model")
    if result["outcome_access_authorized"]:
        raise AssertionError("stage-one preflight authorized outcome access")
    (output / "preflight.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    try:
        result = run(output)
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"Portal DM response-blind preflight stopped: {exc!r}", file=sys.stderr)
        raise SystemExit(3) from exc
    print(
        json.dumps(
            {
                "status": result["status"],
                "node_count": result["geometry_audit"]["node_count"],
                "distinct_threshold_count": result["structural_gates"]["distinct_threshold_count"],
                "heldout_outer_years": 8,
                "matched_header_candidate": result["response_header_gate"][
                    "matched_candidate_index_one_based"
                ],
                "response_header_bytes_opened": result["response_header_bytes_opened"],
                "response_payload_bytes_opened": 0,
                "response_rows_opened": False,
                "outcome_access_authorized": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
