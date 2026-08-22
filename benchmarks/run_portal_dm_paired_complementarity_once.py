#!/usr/bin/env python3
"""Frozen once-only Portal DM paired-complementarity runner.

Smoke mode generates a deterministic synthetic capture table and never requests the
released response. Outcome mode requires a marker bound to a green 16-key freeze,
downloads the pinned response blob once, applies the exact count gate as the first
outcome-dependent analytical operation, and only then compares one strong random
forest with the identical forest plus unchanged EOG Layer B.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import sys
from types import SimpleNamespace

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "validation/portal_dm_paired_complementarity"
sys.path.insert(0, str(VALIDATION_DIR))

from preflight import (  # noqa: E402
    EFFORT_HEADER,
    MOON_HEADER,
    PLOT_HEADER,
    audit_methods,
    effort_time_gate,
    exact_int,
    geometry_gate,
    parse_csv,
    species_gate,
    structural_gate,
)
from transport import (  # noqa: E402
    audit_fixed_tree,
    download_nonresponse,
    download_response_once,
)


CONTRACT_PATH = VALIDATION_DIR / "source_contract.json"
EPS = 1e-6
WORLD_IDS = (
    "portal_plot_euclidean_m_lcc250",
    "portal_plot_euclidean_m_lcc500",
    "portal_plot_euclidean_m_lcc750",
    "portal_plot_euclidean_full",
)
TREATMENT_CATEGORIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("treatment", ("control", "exclosure", "removal", "setup", "spectabs")),
    (
        "resourcetreatment",
        (
            "NA",
            "all_annuals",
            "biseas_annuals",
            "large_seeds",
            "mixed_pulse",
            "mixed_seeds",
            "none",
            "small_seeds",
            "summer_annuals",
            "winter_annuals",
        ),
    ),
    ("anttreatment", ("NA", "all_ants", "none", "rugosus")),
)
TREATMENT_FEATURE_NAMES = tuple(
    f"{field}_{category.lower()}" for field, values in TREATMENT_CATEGORIES for category in values
)
BASELINE_FEATURE_NAMES: tuple[str, ...] = (
    "target_newmoon_index_scaled",
    "target_newmoon_index_scaled_squared",
    "target_year_index",
    "target_month_sin",
    "target_month_cos",
    "observation_gap_days",
    "utm_easting_centered_km",
    "utm_northing_centered_km",
    "target_mean_distance_m",
    "target_nearest_other_plot_m",
    "target_degree_lcc250",
    "target_degree_lcc500",
    "target_degree_lcc750",
    "source_effort_traps",
    "target_effort_traps",
    *TREATMENT_FEATURE_NAMES,
    "current_source_count",
    "log1p_current_source_captures",
    "current_source_mean_positive_captures",
    "nearest_current_source_distance_m",
    "target_never_previously_positive",
    "target_newmoons_since_last_positive",
    "target_prior_positive_period_count",
    "log1p_target_cumulative_prior_captures",
    "source_count_lcc250",
    "source_count_lcc500",
    "source_count_lcc750",
    "source_exponential_exposure_lcc250",
    "source_exponential_exposure_lcc500",
    "source_exponential_exposure_lcc750",
    "source_exponential_exposure_full",
    "capture_weighted_exposure_lcc250",
    "capture_weighted_exposure_lcc500",
    "capture_weighted_exposure_lcc750",
    "capture_weighted_exposure_full",
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


def path_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class EffortCell:
    observed_date: date
    effort: int
    eligible: bool


@dataclass(frozen=True)
class Transition:
    newmoonnumber: int
    source_period: int
    target_period: int
    source_date: date
    target_date: date
    eligible_indices: tuple[int, ...]
    phase: str

    @property
    def outer_unit_id(self) -> str:
        return f"year_{self.target_date.year}"


@dataclass(frozen=True)
class StaticInputs:
    node_ids: tuple[str, ...]
    coordinates: np.ndarray
    distance: np.ndarray
    worlds: dict[str, np.ndarray]
    thresholds: np.ndarray
    kernel_scale: float
    effort: dict[tuple[int, int], EffortCell]
    moon_by_period: dict[int, tuple[int, date]]
    ordered_periods: tuple[int, ...]
    treatments: dict[tuple[int, int, int], tuple[str, str, str]]
    transitions: tuple[Transition, ...]


@dataclass(frozen=True)
class RiskRow:
    phase: str
    outer_unit_id: str
    newmoonnumber: int
    source_period: int
    target_period: int
    target_year: int
    node_index: int
    label: int
    baseline: tuple[float, ...]
    layer_b: tuple[float, ...]


def initial_audit(mode: str, contract: dict) -> dict[str, object]:
    return {
        "execution_mode": mode,
        "attempt_id": contract["attempt_id"],
        "contract_sha256": path_sha256(CONTRACT_PATH),
        "runner_sha256": path_sha256(Path(__file__).resolve()),
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
        "exact_count_gate_executed": False,
        "layer_a_updates": 0,
        "models_fit": 0,
        "heldout_scores": 0,
    }


def _parse_static_registries(
    payloads: dict[str, bytes],
    contract: dict,
) -> tuple[
    dict[tuple[int, int], EffortCell],
    dict[int, tuple[int, date]],
    tuple[int, ...],
    dict[tuple[int, int, int], tuple[str, str, str]],
]:
    effort_rows = parse_csv(
        payloads["Rodents/Portal_rodent_trapping.csv"],
        EFFORT_HEADER,
        "Portal_rodent_trapping.csv",
    )
    effort: dict[tuple[int, int], EffortCell] = {}
    for row in effort_rows:
        period = exact_int(row["period"], "effort period")
        plot = exact_int(row["plot"], "effort plot")
        observed = date(
            exact_int(row["year"], "effort year"),
            exact_int(row["month"], "effort month"),
            exact_int(row["day"], "effort day"),
        )
        traps = exact_int(row["effort"], "effort traps")
        eligible = (
            exact_int(row["sampled"], "sampled") == 1
            and traps >= 47
            and exact_int(row["qcflag"], "qcflag") == 1
        )
        key = (period, plot)
        if key in effort:
            raise RuntimeError(f"duplicate effort identity: {key}")
        effort[key] = EffortCell(observed, traps, eligible)

    missing = set(contract["effort_time_registry"]["moon_missing_value_tokens"])
    moon_rows = parse_csv(payloads["Rodents/moon_dates.csv"], MOON_HEADER, "moon_dates.csv")
    moon_by_period: dict[int, tuple[int, date]] = {}
    for row in moon_rows:
        if row["period"] in missing or row["censusdate"] in missing:
            continue
        period = exact_int(row["period"], "moon period")
        number = exact_int(row["newmoonnumber"], "newmoonnumber")
        census = date.fromisoformat(row["censusdate"])
        if period in moon_by_period:
            raise RuntimeError(f"duplicate moon period: {period}")
        moon_by_period[period] = (number, census)
    ordered_periods = tuple(
        period for period, _ in sorted(moon_by_period.items(), key=lambda item: item[1][0])
    )

    plot_rows = parse_csv(
        payloads["SiteandMethods/Portal_plots.csv"],
        PLOT_HEADER,
        "Portal_plots.csv",
    )
    treatments: dict[tuple[int, int, int], tuple[str, str, str]] = {}
    for row in plot_rows:
        key = (
            exact_int(row["year"], "plot year"),
            exact_int(row["month"], "plot month"),
            exact_int(row["plot"], "plot ID"),
        )
        values = (row["treatment"], row["resourcetreatment"], row["anttreatment"])
        if key in treatments:
            raise RuntimeError(f"duplicate treatment identity: {key}")
        treatments[key] = values
    return effort, moon_by_period, ordered_periods, treatments


def _build_transitions(
    effort: dict[tuple[int, int], EffortCell],
    moon_by_period: dict[int, tuple[int, date]],
    treatments: dict[tuple[int, int, int], tuple[str, str, str]],
    contract: dict,
) -> tuple[Transition, ...]:
    by_number = {number: (period, census) for period, (number, census) in moon_by_period.items()}
    transitions: list[Transition] = []
    for number in sorted(by_number):
        if number + 1 not in by_number:
            continue
        source_period, source_date = by_number[number]
        target_period, target_date = by_number[number + 1]
        if target_date.year > 2019:
            continue
        eligible = tuple(
            plot - 1
            for plot in range(1, 25)
            if effort[(source_period, plot)].eligible and effort[(target_period, plot)].eligible
        )
        if not eligible:
            continue
        for index in eligible:
            if (target_date.year, target_date.month, index + 1) not in treatments:
                raise RuntimeError("eligible target lacks treatment identity")
        transitions.append(
            Transition(
                newmoonnumber=number,
                source_period=source_period,
                target_period=target_period,
                source_date=source_date,
                target_date=target_date,
                eligible_indices=eligible,
                phase="calibration" if target_date.year <= 2011 else "heldout",
            )
        )
    frozen = contract["freezes"]["temporal_split"]
    if len(transitions) != int(frozen["declared_scored_transition_count"]):
        raise RuntimeError("runner transition registry count drift")
    if sum(value.phase == "calibration" for value in transitions) != int(
        frozen["calibration_transition_count"]
    ):
        raise RuntimeError("runner calibration transition count drift")
    if sum(value.phase == "heldout" for value in transitions) != int(
        frozen["heldout_transition_count"]
    ):
        raise RuntimeError("runner heldout transition count drift")
    return tuple(transitions)


def read_static_inputs(contract: dict, audit: dict) -> tuple[StaticInputs, dict[str, object]]:
    tree = audit_fixed_tree(contract, audit)
    payloads = {
        path: download_nonresponse(path, contract, audit)
        for path, spec in contract["files"].items()
        if spec["role"] != "response"
    }
    methods = audit_methods(payloads)
    node_ids, coordinates, distance, geometry = geometry_gate(
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
    effort, moon_by_period, ordered_periods, treatments = _parse_static_registries(
        payloads, contract
    )
    transitions = _build_transitions(effort, moon_by_period, treatments, contract)
    thresholds = np.asarray(contract["freezes"]["world_scale"]["thresholds_m"], dtype=float)
    if thresholds.shape != (3,) or not np.all(np.diff(thresholds) > 0):
        raise RuntimeError("frozen thresholds are not three strictly increasing values")
    if not np.allclose(
        thresholds,
        np.asarray(structural["thresholds_m"], dtype=float),
        atol=1e-12,
        rtol=0.0,
    ):
        raise RuntimeError("runner thresholds differ from response-blind geometry")
    observed_categories = {
        field: sorted({values[index] for values in treatments.values()})
        for index, (field, _) in enumerate(TREATMENT_CATEGORIES)
    }
    expected_categories = {
        field: list(values) for field, values in TREATMENT_CATEGORIES
    }
    if observed_categories != expected_categories:
        raise RuntimeError("treatment category registry differs from frozen tokens")
    static = StaticInputs(
        node_ids=node_ids,
        coordinates=coordinates,
        distance=distance,
        worlds=worlds,
        thresholds=thresholds,
        kernel_scale=float(contract["freezes"]["world_scale"]["kernel_scale_m"]),
        effort=effort,
        moon_by_period=moon_by_period,
        ordered_periods=ordered_periods,
        treatments=treatments,
        transitions=transitions,
    )
    return static, {
        "fixed_source_tree": tree,
        "methods": methods,
        "geometry": geometry,
        "structural": structural,
        "effort_time": effort_time,
        "species": species,
        "transition_count": len(transitions),
    }


def validate_physical_header(content: bytes, contract: dict) -> dict[str, object]:
    frozen = contract["response_header_firewall"]
    positions = [value for value in (content.find(b"\r"), content.find(b"\n")) if value >= 0]
    if not positions:
        raise RuntimeError("once-opened response has no first-record terminator")
    end = min(positions)
    terminator = "CR" if content[end : end + 1] == b"\r" else "LF"
    header_bytes = content[:end]
    try:
        header_text = header_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError("once-opened response header is not UTF-8") from exc
    if header_text != frozen["expected_header_text"]:
        raise RuntimeError("once-opened physical header text differs from frozen header")
    if hashlib.sha256(header_bytes).hexdigest() != frozen["expected_header_sha256"]:
        raise RuntimeError("once-opened physical header SHA-256 differs from frozen header")
    if terminator != frozen["expected_terminator"]:
        raise RuntimeError("once-opened physical header terminator differs from frozen header")
    if end + 1 != int(frozen["expected_bytes_consumed_including_terminator"]):
        raise RuntimeError("once-opened physical header byte count differs from frozen header")
    return {
        "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "terminator": terminator,
        "bytes_consumed_including_terminator": end + 1,
        "matches_pre_response_bounded_header": True,
    }


def parse_response(
    content: bytes,
    static: StaticInputs,
    contract: dict,
) -> tuple[dict[int, np.ndarray], dict[str, object]]:
    """Schema/identity parse only; endpoint counts are deliberately deferred."""

    header_audit = validate_physical_header(content, contract)
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
    except UnicodeDecodeError as exc:
        raise RuntimeError("once-opened response is not UTF-8") from exc
    expected = tuple(contract["response_header_firewall"]["expected_columns"])
    if header != expected:
        raise RuntimeError("once-opened parsed header order differs from frozen schema")
    counts = {period: np.zeros(24, dtype=int) for period in static.moon_by_period}
    record_ids: set[int] = set()
    row_count = 0
    focal_rows = 0
    excluded_special_focal_rows = 0
    for row_count, row in enumerate(reader, start=1):
        if None in row:
            raise RuntimeError(f"response row {row_count + 1} is wider than its header")
        record_id = exact_int(row["recordID"], f"recordID at response row {row_count + 1}")
        if record_id in record_ids:
            raise RuntimeError(f"duplicate recordID at response row {row_count + 1}")
        record_ids.add(record_id)
        species = row["species"]
        if not species:
            raise RuntimeError(f"empty species token at response row {row_count + 1}")
        if species != "DM":
            continue
        focal_rows += 1
        period = exact_int(row["period"], f"DM period at response row {row_count + 1}")
        if period <= 0:
            excluded_special_focal_rows += 1
            continue
        plot = exact_int(row["plot"], f"DM plot at response row {row_count + 1}")
        if period not in counts or plot not in range(1, 25):
            raise RuntimeError(
                f"normal-protocol DM identity lies outside the closed registry at row {row_count + 1}"
            )
        counts[period][plot - 1] += 1
    return counts, {
        "physical_header": header_audit,
        "header": list(header),
        "row_count": row_count,
        "unique_record_id_count": len(record_ids),
        "focal_capture_rows": focal_rows,
        "excluded_negative_period_focal_rows": excluded_special_focal_rows,
        "outcome_counts_not_computed_during_schema_identity_parse": True,
    }


def synthetic_response(static: StaticInputs, contract: dict) -> tuple[bytes, str]:
    output = io.StringIO()
    columns = tuple(contract["response_header_firewall"]["expected_columns"])
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
    )
    writer.writeheader()
    record_id = 1
    for period in static.ordered_periods:
        number, _ = static.moon_by_period[period]
        for plot in range(1, 25):
            if (plot + number) % 5 not in {0, 1}:
                continue
            captures = 1 + ((3 * plot + number) % 3)
            cell = static.effort[(period, plot)]
            for _ in range(captures):
                row = {name: "" for name in columns}
                row.update(
                    {
                        "recordID": str(record_id),
                        "month": str(cell.observed_date.month),
                        "day": str(cell.observed_date.day),
                        "year": str(cell.observed_date.year),
                        "period": str(period),
                        "plot": str(plot),
                        "stake": "11",
                        "species": "DM",
                        "id": str(record_id),
                    }
                )
                writer.writerow(row)
                record_id += 1
    content = output.getvalue().encode("utf-8")
    return content, hashlib.sha256(content).hexdigest()


def exact_count_gate(
    counts: dict[int, np.ndarray],
    static: StaticInputs,
    contract: dict,
) -> dict[str, object]:
    """First outcome-dependent analytical operation after schema/identity validation."""

    transition_rows: list[dict[str, object]] = []
    outer: dict[int, dict[str, int]] = {
        year: {"events": 0, "non_events": 0, "rows": 0} for year in range(2012, 2020)
    }
    for transition in static.transitions:
        source = counts[transition.source_period]
        target = counts[transition.target_period]
        source_eligible = np.asarray(
            [static.effort[(transition.source_period, plot)].eligible for plot in range(1, 25)],
            dtype=bool,
        )
        current_sources = int(np.sum(source_eligible & (source > 0)))
        eligible = np.zeros(24, dtype=bool)
        eligible[list(transition.eligible_indices)] = True
        risk = eligible & (source == 0)
        events = int(np.sum(risk & (target > 0)))
        non_events = int(np.sum(risk & (target == 0)))
        transition_rows.append(
            {
                "newmoonnumber": transition.newmoonnumber,
                "source_period": transition.source_period,
                "target_period": transition.target_period,
                "target_year": transition.target_date.year,
                "phase": transition.phase,
                "current_internal_sources": current_sources,
                "events": events,
                "non_events": non_events,
            }
        )
        if transition.phase == "heldout":
            values = outer[transition.target_date.year]
            values["events"] += events
            values["non_events"] += non_events
            values["rows"] += events + non_events

    calibration = [row for row in transition_rows if row["phase"] == "calibration"]
    heldout = [row for row in transition_rows if row["phase"] == "heldout"]
    observed = {
        "calibration_events": sum(int(row["events"]) for row in calibration),
        "calibration_non_events": sum(int(row["non_events"]) for row in calibration),
        "heldout_events": sum(int(row["events"]) for row in heldout),
        "heldout_non_events": sum(int(row["non_events"]) for row in heldout),
        "heldout_outer_units_with_both_classes": sum(
            values["events"] > 0 and values["non_events"] > 0 for values in outer.values()
        ),
        "heldout_outer_units_with_rows": sum(values["rows"] > 0 for values in outer.values()),
    }
    all_sources = all(int(row["current_internal_sources"]) > 0 for row in transition_rows)
    minima = contract["freezes"]["count_gate"]
    count_keys = (
        "calibration_events",
        "calibration_non_events",
        "heldout_events",
        "heldout_non_events",
        "heldout_outer_units_with_both_classes",
    )
    passed = all(observed[key] >= int(minima[key]) for key in count_keys)
    passed = bool(
        passed
        and observed["heldout_outer_units_with_rows"]
        == int(minima["heldout_outer_units_with_rows"])
        and all_sources
    )
    return {
        "passed": passed,
        "outcome_dependent_operation_index": 1,
        "executed_before_any_layer_a_update_or_model_fit": True,
        "transition_counts": transition_rows,
        "heldout_year_counts": {str(year): values for year, values in outer.items()},
        **observed,
        "all_scored_transitions_have_current_internal_sources": all_sources,
        "minimums": {key: minima[key] for key in (*count_keys, "heldout_outer_units_with_rows")},
    }


def compute_world_supports(
    static: StaticInputs,
    source_indices: np.ndarray,
    contract: dict,
) -> np.ndarray:
    if source_indices.size == 0:
        raise RuntimeError("current internal source set is empty")
    source_distance = static.distance[source_indices, :]
    exponential = np.exp(-source_distance / static.kernel_scale)
    exponential[np.arange(source_indices.size), source_indices] = 0.0
    supports = np.zeros((len(WORLD_IDS), len(static.node_ids)), dtype=float)
    source_weight = 1.0 / float(source_indices.size)
    loss = float(contract["freezes"]["world_scale"]["loss_support"])
    for world_index, threshold in enumerate(static.thresholds):
        raw = exponential * (source_distance <= threshold + 1e-12)
        denominator = loss + np.sum(raw, axis=1)
        supports[world_index] = (source_weight / denominator) @ raw
    denominator = loss + np.sum(exponential, axis=1)
    supports[-1] = (source_weight / denominator) @ exponential
    return supports


def layer_b_summary(
    static: StaticInputs,
    supports: np.ndarray,
    surviving: np.ndarray,
    transition_id: str,
    contract: dict,
) -> tuple[np.ndarray, str]:
    tolerance = float(contract["freezes"]["world_scale"]["support_tolerance"])
    members = []
    for index, keep in enumerate(surviving):
        if not bool(keep):
            continue
        members.append(
            SimpleNamespace(
                cumulative_reachability=np.vstack(
                    (np.zeros(len(static.node_ids), dtype=float), supports[index])
                ),
                supported_state=np.vstack(
                    (np.zeros(len(static.node_ids), dtype=bool), supports[index] > tolerance)
                ),
            )
        )
    if not members:
        raise RuntimeError("frozen world universe has no surviving member")
    forecast = SimpleNamespace(
        node_ids=static.node_ids,
        members=tuple(members),
        max_steps=1,
        gate_declaration=ForecastGateDeclaration(reachability_threshold=tolerance),
        world_fingerprints=tuple(
            (world_id, canonical_sha256({"world_id": world_id})) for world_id in WORLD_IDS
        ),
        fingerprint=canonical_sha256(
            {
                "transition_id": transition_id,
                "surviving_world_ids": [
                    world_id
                    for world_id, keep in zip(WORLD_IDS, surviving, strict=True)
                    if keep
                ],
                "support_sha256": hashlib.sha256(
                    np.ascontiguousarray(supports, dtype=np.float64).tobytes()
                ).hexdigest(),
            }
        ),
    )
    summary = summarize_worldset_for_prediction(forecast, step=1)
    if summary.feature_names != PREDICTIVE_FEATURE_NAMES:
        raise RuntimeError("production Layer-B feature-name surface drift")
    return summary.feature_matrix, summary.feature_fingerprint


def _history_by_period(
    counts: dict[int, np.ndarray],
    static: StaticInputs,
) -> dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    cumulative = np.zeros(24, dtype=float)
    positive_periods = np.zeros(24, dtype=float)
    last_positive = np.full(24, -1, dtype=int)
    result = {}
    for period in static.ordered_periods:
        number, _ = static.moon_by_period[period]
        values = counts[period]
        cumulative += values
        positive = values > 0
        positive_periods += positive
        last_positive[positive] = number
        result[period] = (cumulative.copy(), positive_periods.copy(), last_positive.copy())
    return result


def _treatment_matrix(static: StaticInputs, transition: Transition) -> np.ndarray:
    rows = []
    scored = set(transition.eligible_indices)
    for plot in range(1, 25):
        key = (transition.target_date.year, transition.target_date.month, plot)
        if key not in static.treatments:
            if plot - 1 in scored:
                raise RuntimeError("scored target lacks a frozen treatment identity")
            rows.append([0.0] * len(TREATMENT_FEATURE_NAMES))
            continue
        observed = static.treatments[key]
        values: list[float] = []
        for index, (_, categories) in enumerate(TREATMENT_CATEGORIES):
            if observed[index] not in categories:
                raise RuntimeError("target treatment token is outside the frozen categories")
            values.extend(float(observed[index] == category) for category in categories)
        rows.append(values)
    result = np.asarray(rows, dtype=float)
    if result.shape != (24, len(TREATMENT_FEATURE_NAMES)):
        raise RuntimeError("treatment feature shape drift")
    return result


def baseline_features(
    static: StaticInputs,
    transition: Transition,
    source_indices: np.ndarray,
    source_counts: np.ndarray,
    history: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    n = len(static.node_ids)
    centered = (static.coordinates - np.mean(static.coordinates, axis=0)) / 1000.0
    other = static.distance.copy()
    np.fill_diagonal(other, np.nan)
    mean_distance = np.nanmean(other, axis=1)
    nearest_other = np.nanmin(other, axis=1)
    degrees = [
        np.sum(static.distance <= threshold + 1e-12, axis=0) - 1
        for threshold in static.thresholds
    ]
    source_distance = static.distance[source_indices, :]
    exponential = np.exp(-source_distance / static.kernel_scale)
    exponential[np.arange(source_indices.size), source_indices] = 0.0
    masks = [source_distance <= threshold + 1e-12 for threshold in static.thresholds]
    source_counts_within = [np.sum(mask, axis=0) for mask in masks]
    unweighted = [np.sum(exponential * mask, axis=0) for mask in masks]
    unweighted.append(np.sum(exponential, axis=0))
    weighted_values = source_counts[:, None] * exponential
    weighted = [np.sum(weighted_values * mask, axis=0) for mask in masks]
    weighted.append(np.sum(weighted_values, axis=0))
    nearest_source = np.min(source_distance, axis=0)
    cumulative, prior_positive, last_positive = history
    never = last_positive < 0
    since_last = np.where(never, 0.0, transition.newmoonnumber - last_positive).astype(float)
    target_effort = np.asarray(
        [static.effort[(transition.target_period, plot)].effort for plot in range(1, 25)],
        dtype=float,
    )
    source_effort = np.asarray(
        [static.effort[(transition.source_period, plot)].effort for plot in range(1, 25)],
        dtype=float,
    )
    month_angle = 2.0 * math.pi * (transition.target_date.month - 1) / 12.0
    scaled_time = (transition.newmoonnumber + 1 - min(
        value[0] for value in static.moon_by_period.values()
    )) / 100.0
    treatment = _treatment_matrix(static, transition)
    features = np.column_stack(
        [
            np.full(n, scaled_time),
            np.full(n, scaled_time**2),
            np.full(n, transition.target_date.year - 1977, dtype=float),
            np.full(n, math.sin(month_angle)),
            np.full(n, math.cos(month_angle)),
            np.full(n, (transition.target_date - transition.source_date).days, dtype=float),
            centered[:, 0],
            centered[:, 1],
            mean_distance,
            nearest_other,
            *degrees,
            source_effort,
            target_effort,
            treatment,
            np.full(n, source_indices.size, dtype=float),
            np.full(n, math.log1p(float(np.sum(source_counts))), dtype=float),
            np.full(n, float(np.mean(source_counts)), dtype=float),
            nearest_source,
            never.astype(float),
            since_last,
            prior_positive,
            np.log1p(cumulative),
            *source_counts_within,
            *unweighted,
            *weighted,
        ]
    ).astype(float)
    if features.shape != (n, len(BASELINE_FEATURE_NAMES)):
        raise RuntimeError(
            f"baseline feature shape drift: {features.shape} != {(n, len(BASELINE_FEATURE_NAMES))}"
        )
    if not np.isfinite(features).all():
        raise RuntimeError("baseline contains a nonfinite predictor")
    return features


def update_worlds(
    supports: np.ndarray,
    surviving: np.ndarray,
    positive_indices: np.ndarray,
    tolerance: float,
) -> tuple[np.ndarray, tuple[str, ...]]:
    after = surviving.copy()
    eliminated: list[str] = []
    for index, world_id in enumerate(WORLD_IDS):
        if after[index] and positive_indices.size and np.any(
            supports[index, positive_indices] <= tolerance
        ):
            after[index] = False
            eliminated.append(world_id)
    return after, tuple(eliminated)


def build_risk_rows(
    counts: dict[int, np.ndarray],
    static: StaticInputs,
    contract: dict,
) -> tuple[list[RiskRow], dict[str, object]]:
    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    histories = _history_by_period(counts, static)
    tolerance = float(contract["freezes"]["world_scale"]["support_tolerance"])
    risk_rows: list[RiskRow] = []
    rule_history = []
    for transition in static.transitions:
        source = counts[transition.source_period]
        target = counts[transition.target_period]
        source_eligible = np.asarray(
            [static.effort[(transition.source_period, plot)].eligible for plot in range(1, 25)],
            dtype=bool,
        )
        source_indices = np.flatnonzero(source_eligible & (source > 0))
        if source_indices.size == 0:
            raise RuntimeError("count-passing transition unexpectedly has no current source")
        source_counts = source[source_indices].astype(float)
        supports = compute_world_supports(static, source_indices, contract)
        layer_b, layer_fingerprint = layer_b_summary(
            static,
            supports,
            surviving,
            f"newmoon_{transition.newmoonnumber}_to_{transition.newmoonnumber + 1}",
            contract,
        )
        baseline = baseline_features(
            static,
            transition,
            source_indices,
            source_counts,
            histories[transition.source_period],
        )
        positive_indices: list[int] = []
        events = 0
        non_events = 0
        for index in transition.eligible_indices:
            if source[index] != 0:
                continue
            label = int(target[index] > 0)
            if label:
                positive_indices.append(index)
                events += 1
            else:
                non_events += 1
            risk_rows.append(
                RiskRow(
                    phase=transition.phase,
                    outer_unit_id=transition.outer_unit_id,
                    newmoonnumber=transition.newmoonnumber,
                    source_period=transition.source_period,
                    target_period=transition.target_period,
                    target_year=transition.target_date.year,
                    node_index=index,
                    label=label,
                    baseline=tuple(float(value) for value in baseline[index]),
                    layer_b=tuple(float(value) for value in layer_b[index]),
                )
            )
        after, eliminated = update_worlds(
            supports,
            surviving,
            np.asarray(positive_indices, dtype=int),
            tolerance,
        )
        rule_history.append(
            {
                "newmoonnumber": transition.newmoonnumber,
                "phase": transition.phase,
                "current_internal_sources": int(source_indices.size),
                "risk_rows": events + non_events,
                "events": events,
                "non_events": non_events,
                "surviving_before": int(np.sum(surviving)),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": int(np.sum(after)),
                "layer_b_feature_fingerprint": layer_fingerprint,
            }
        )
        surviving = after
        if not np.any(surviving) and transition is not static.transitions[-1]:
            raise RuntimeError("frozen world universe was completely falsified")
    return risk_rows, {
        "row_count": len(risk_rows),
        "calibration_rows": sum(row.phase == "calibration" for row in risk_rows),
        "heldout_rows": sum(row.phase == "heldout" for row in risk_rows),
        "layer_a_update_count": len(rule_history),
        "rule_history": rule_history,
        "final_surviving_world_ids": [
            world_id for world_id, keep in zip(WORLD_IDS, surviving, strict=True) if keep
        ],
        "exact_plot_id_supervised": False,
        "exact_world_id_supervised": False,
    }


def layer_b_estimability(baseline: np.ndarray, layer_b: np.ndarray) -> dict[str, object]:
    external = np.asarray(baseline, dtype=float)
    layer = np.asarray(layer_b, dtype=float)
    sd = np.std(external, axis=0, ddof=0)
    keep = np.flatnonzero(sd > 1e-12)
    if keep.size:
        x = external[:, keep]
        x = (x - np.mean(x, axis=0)) / np.std(x, axis=0, ddof=0)
        design = np.column_stack((np.ones(len(x)), x))
    else:
        design = np.ones((len(external), 1), dtype=float)
    retained = []
    residual_sd = []
    for index in range(layer.shape[1]):
        values = layer[:, index]
        value_sd = float(np.std(values, ddof=0))
        if value_sd <= 1e-12:
            continue
        retained.append(index)
        z = (values - np.mean(values)) / value_sd
        coefficient, *_ = np.linalg.lstsq(design, z, rcond=None)
        residual_sd.append(float(np.std(z - design @ coefficient, ddof=0)))
    maximum = max(residual_sd, default=0.0)
    return {
        "estimable": bool(maximum > 1e-8),
        "retained_layer_b_columns": retained,
        "residual_sd_after_frozen_baseline": residual_sd,
        "maximum_residual_sd": maximum,
        "threshold": 1e-8,
    }


def learner(contract: dict) -> RandomForestClassifier:
    return RandomForestClassifier(
        **dict(contract["freezes"]["preprocessing_model_fit"]["hyperparameters"])
    )


def binary_log_loss(y: np.ndarray, probability: np.ndarray) -> float:
    truth = np.asarray(y, dtype=float)
    pred = np.clip(np.asarray(probability, dtype=float), EPS, 1.0 - EPS)
    return float(-np.mean(truth * np.log(pred) + (1.0 - truth) * np.log(1.0 - pred)))


def brier_score(y: np.ndarray, probability: np.ndarray) -> float:
    return float(np.mean((np.asarray(probability, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def paired_declaration(contract: dict) -> PredictiveComplementarityDeclaration:
    freezes = contract["freezes"]
    metrics = freezes["metrics_decision"]
    return PredictiveComplementarityDeclaration(
        metric_name=metrics["primary_metric"],
        lower_is_better=bool(metrics["lower_is_better"]),
        expected_outer_unit_count=int(metrics["expected_outer_unit_count"]),
        favorable_min_augmented_wins=int(metrics["favorable_min_augmented_wins"]),
        adverse_min_baseline_wins=int(metrics["adverse_min_baseline_wins"]),
        learner_fit_fingerprint=canonical_sha256(freezes["preprocessing_model_fit"]),
        response_endpoint_fingerprint=canonical_sha256(freezes["response_semantics"]),
        split_fingerprint=canonical_sha256(freezes["temporal_split"]),
        external_feature_fingerprint=canonical_sha256(
            {"feature_names": list(BASELINE_FEATURE_NAMES), "missing_value_policy": "fail_closed"}
        ),
        eog_feature_fingerprint=canonical_sha256(freezes["layer_b_representation"]),
    )


def fit_and_score(
    rows: list[RiskRow],
    contract: dict,
) -> tuple[dict[str, object], dict[str, object]]:
    calibration = [row for row in rows if row.phase == "calibration"]
    heldout = [row for row in rows if row.phase == "heldout"]
    x_cal = np.asarray([row.baseline for row in calibration], dtype=float)
    layer_cal = np.asarray([row.layer_b for row in calibration], dtype=float)
    y_cal = np.asarray([row.label for row in calibration], dtype=int)
    if not np.isfinite(x_cal).all() or not np.isfinite(layer_cal).all():
        raise RuntimeError("calibration predictors are nonfinite")
    estimability = layer_b_estimability(x_cal, layer_cal)
    if not estimability["estimable"]:
        return {"estimability": estimability}, {"status": "layer_b_non_estimable"}

    baseline_model = learner(contract)
    augmented_model = learner(contract)
    baseline_model.fit(x_cal, y_cal)
    augmented_model.fit(np.column_stack((x_cal, layer_cal)), y_cal)

    x_held = np.asarray([row.baseline for row in heldout], dtype=float)
    layer_held = np.asarray([row.layer_b for row in heldout], dtype=float)
    y_held = np.asarray([row.label for row in heldout], dtype=int)
    if not np.isfinite(x_held).all() or not np.isfinite(layer_held).all():
        raise RuntimeError("heldout predictors are nonfinite")
    p_base = baseline_model.predict_proba(x_held)[:, 1]
    p_augmented = augmented_model.predict_proba(
        np.column_stack((x_held, layer_held))
    )[:, 1]

    paired = []
    outer_rows = []
    for outer_id in sorted({row.outer_unit_id for row in heldout}):
        indices = np.asarray(
            [index for index, row in enumerate(heldout) if row.outer_unit_id == outer_id],
            dtype=int,
        )
        truth = y_held[indices]
        base_loss = binary_log_loss(truth, p_base[indices])
        augmented_loss = binary_log_loss(truth, p_augmented[indices])
        paired.append(PairedOuterUnitScore(outer_id, base_loss, augmented_loss))
        outer_rows.append(
            {
                "outer_unit_id": outer_id,
                "row_count": int(indices.size),
                "events": int(np.sum(truth == 1)),
                "non_events": int(np.sum(truth == 0)),
                "baseline_log_loss": base_loss,
                "augmented_log_loss": augmented_loss,
                "augmented_minus_baseline": augmented_loss - base_loss,
            }
        )
    declaration = paired_declaration(contract)
    decision = evaluate_predictive_complementarity(
        declaration,
        paired,
        tie_tolerance=float(contract["freezes"]["metrics_decision"]["tie_tolerance"]),
    )
    return {
        "models_fit": 2,
        "heldout_scores": 2 * len(paired),
        "layer_b_estimability": estimability,
        "paired_declaration_fingerprint": declaration.fingerprint,
        "paired_complementarity": asdict(decision),
        "paired_outer_unit_scores": outer_rows,
        "pooled_metrics": {
            "baseline_log_loss": binary_log_loss(y_held, p_base),
            "augmented_log_loss": binary_log_loss(y_held, p_augmented),
            "baseline_brier": brier_score(y_held, p_base),
            "augmented_brier": brier_score(y_held, p_augmented),
        },
        "model_feature_audit": {
            "baseline_feature_names": list(BASELINE_FEATURE_NAMES),
            "augmented_feature_names": [*BASELINE_FEATURE_NAMES, *PREDICTIVE_FEATURE_NAMES],
            "exact_plot_id_supervised": False,
            "exact_world_id_supervised": False,
            "only_augmented_difference": list(PREDICTIVE_FEATURE_NAMES),
            "same_learner_hyperparameters_rows_labels_split_and_preprocessing": True,
        },
    }, {"status": "completed"}


def verify_frozen_environment(contract: dict) -> None:
    freeze = contract["freezes"]["preprocessing_model_fit"]
    if ".".join(platform.python_version().split(".")[:2]) != freeze["python"]:
        raise RuntimeError("Python major/minor differs from frozen environment")
    if np.__version__ != freeze["numpy"]:
        raise RuntimeError(f"NumPy version drift: {np.__version__} != {freeze['numpy']}")
    if sklearn.__version__ != freeze["scikit_learn"]:
        raise RuntimeError(
            f"scikit-learn version drift: {sklearn.__version__} != {freeze['scikit_learn']}"
        )
    if tuple(freeze["baseline_feature_names"]) != BASELINE_FEATURE_NAMES:
        raise RuntimeError("baseline feature-name contract drift")
    if tuple(contract["freezes"]["layer_b_representation"]["feature_names"]) != tuple(
        PREDICTIVE_FEATURE_NAMES
    ):
        raise RuntimeError("Layer-B feature-name contract drift")
    if tuple(contract["freezes"]["world_scale"]["world_ids"]) != WORLD_IDS:
        raise RuntimeError("world ID contract drift")
    if path_sha256(Path(__file__).resolve()) != contract["freezes"]["runtime_runner"][
        "sha256"
    ]:
        raise RuntimeError("runner self-hash differs from frozen contract")


def verify_authorization(
    contract: dict,
    marker_path: Path,
    preflight_path: Path,
) -> dict[str, object]:
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if marker.get("attempt_id") != contract["attempt_id"]:
        raise RuntimeError("authorization marker attempt ID mismatch")
    if marker.get("invocation_budget") != 1 or marker.get("response_rows_opened") is not False:
        raise RuntimeError("authorization marker does not preserve unopened once-only state")
    if marker.get("no_retry") is not True or marker.get("no_post_open_redesign") is not True:
        raise RuntimeError("authorization marker does not freeze no-retry/no-redesign")
    if marker.get("contract_sha256") != path_sha256(CONTRACT_PATH):
        raise RuntimeError("authorization marker contract SHA-256 mismatch")
    if marker.get("runner_sha256") != path_sha256(Path(__file__).resolve()):
        raise RuntimeError("authorization marker runner SHA-256 mismatch")
    if preflight.get("status") != "authorized_once_only_exact_count_gate_required":
        raise RuntimeError("full freeze gate did not authorize the exact-count-first run")
    if preflight.get("response_rows_opened") is not False:
        raise RuntimeError("full freeze gate claims a response row was opened")
    if marker.get("outcome_access_gate_fingerprint") != preflight[
        "outcome_access_gate"
    ]["fingerprint"]:
        raise RuntimeError("authorization marker outcome-gate fingerprint mismatch")
    if marker.get("preflight_fingerprint") != preflight.get("fingerprint"):
        raise RuntimeError("authorization marker preflight fingerprint mismatch")
    if contract["freezes"]["runtime_runner"].get("synthetic_smoke_core_fingerprint") is None:
        raise RuntimeError("outcome mode is blocked while the smoke fingerprint is pending")
    return {
        "authorized_parent_commit": marker.get("authorized_parent_commit"),
        "outcome_access_gate_fingerprint": preflight["outcome_access_gate"]["fingerprint"],
        "preflight_fingerprint": preflight["fingerprint"],
        "invocation_budget": 1,
    }


def write_result(path: Path, result: dict) -> dict:
    payload = dict(result)
    payload["fingerprint"] = canonical_sha256(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def stopped_result(base: dict, status: str, reason: str, output: Path) -> dict:
    return write_result(
        output,
        {
            **base,
            "status": status,
            "stop_reason": reason,
            "models_fit": int(base.get("models_fit", 0)),
            "heldout_scores": int(base.get("heldout_scores", 0)),
        },
    )


def _smoke_core(result: dict) -> dict[str, object]:
    return {
        "synthetic_fixture_fingerprint": result["response_provenance"][
            "synthetic_fixture_fingerprint"
        ],
        "exact_count_gate": result["exact_count_gate"],
        "risk_table_audit": result["risk_table_audit"],
        "layer_b_estimability": result["layer_b_estimability"],
        "paired_declaration_fingerprint": result["paired_declaration_fingerprint"],
        "paired_complementarity": result["paired_complementarity"],
        "paired_outer_unit_scores": result["paired_outer_unit_scores"],
        "pooled_metrics": result["pooled_metrics"],
        "model_feature_audit": result["model_feature_audit"],
    }


def run(
    *,
    mode: str,
    output: Path,
    authorization_marker: Path | None = None,
    preflight_result: Path | None = None,
) -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    verify_frozen_environment(contract)
    base = initial_audit(mode, contract)
    if mode == "outcome":
        if authorization_marker is None or preflight_result is None:
            raise RuntimeError("outcome mode requires authorization marker and full freeze result")
        base["authorization"] = verify_authorization(
            contract, authorization_marker, preflight_result
        )
    elif authorization_marker is not None or preflight_result is not None:
        raise RuntimeError("smoke mode must not receive outcome authorization inputs")

    static, static_audit = read_static_inputs(contract, base)
    base.update(
        {
            "status": "pre_model",
            "response_target": "observed_monthly_plot_capture_reappearance",
            "response_boundary": (
                "effort-eligible plot zero-to-positive capture transition conditional on "
                "current internal captured plots; not latent occupancy, immigration, ancestry, "
                "or individual movement"
            ),
            "node_count": len(static.node_ids),
            "calibration_transition_count": sum(
                value.phase == "calibration" for value in static.transitions
            ),
            "heldout_transition_count": sum(
                value.phase == "heldout" for value in static.transitions
            ),
            "static_input_audit": static_audit,
            "exact_plot_id_supervised": False,
            "exact_world_id_supervised": False,
        }
    )

    if mode == "smoke":
        content, fixture_fingerprint = synthetic_response(static, contract)
        counts, schema = parse_response(content, static, contract)
        response_provenance = {
            "source": "deterministic synthetic technical-control capture table",
            "synthetic_fixture_fingerprint": fixture_fingerprint,
            "response_download_requests": 0,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": False,
            "schema": schema,
        }
    else:
        try:
            content = download_response_once(contract, base)
            counts, schema = parse_response(content, static, contract)
            response_provenance = {
                "filename": contract["response_file"],
                "git_blob_sha1_after_once_only_open": contract["files"][
                    contract["response_file"]
                ]["git_blob_sha1"],
                "bytes": len(content),
                "response_download_requests": 1,
                "response_rows_opened": True,
                "schema": schema,
            }
        except Exception as exc:
            return stopped_result(
                base,
                "post_open_schema_or_identity_stop_no_retry",
                repr(exc),
                output,
            )
    base["response_provenance"] = response_provenance

    try:
        count_gate = exact_count_gate(counts, static, contract)
    except Exception as exc:
        if mode == "outcome":
            return stopped_result(
                base,
                "post_open_count_gate_stop_no_retry",
                repr(exc),
                output,
            )
        raise
    base["exact_count_gate"] = count_gate
    base["exact_count_gate_executed"] = True
    if not count_gate["passed"]:
        return stopped_result(
            base,
            "non_estimable_exact_count_gate_zero_fit",
            "one or more prospectively frozen exact count requirements failed",
            output,
        )

    try:
        risk_rows, row_audit = build_risk_rows(counts, static, contract)
        expected_rows = (
            int(count_gate["calibration_events"])
            + int(count_gate["calibration_non_events"])
            + int(count_gate["heldout_events"])
            + int(count_gate["heldout_non_events"])
        )
        if len(risk_rows) != expected_rows:
            raise RuntimeError("feature risk-row count differs from exact count gate")
        base["risk_table_audit"] = row_audit
        base["layer_a_updates"] = int(row_audit["layer_a_update_count"])
        model_result, state = fit_and_score(risk_rows, contract)
        if state["status"] == "layer_b_non_estimable":
            base["layer_b_estimability"] = model_result["estimability"]
            return stopped_result(
                base,
                "layer_b_non_estimable_zero_fit",
                "unchanged Layer B has no calibration variation beyond the frozen baseline",
                output,
            )
        base.update(model_result)
        base["status"] = "smoke_pass" if mode == "smoke" else "completed_frozen_paired_test"
        if mode == "smoke":
            core = _smoke_core(base)
            base["smoke_core_fingerprint"] = canonical_sha256(core)
            expected = contract["freezes"]["runtime_runner"].get(
                "synthetic_smoke_core_fingerprint"
            )
            if expected is not None and base["smoke_core_fingerprint"] != expected:
                raise RuntimeError("synthetic smoke core fingerprint differs from freeze")
        return write_result(output, base)
    except Exception as exc:
        if mode == "outcome":
            return stopped_result(
                base,
                "post_open_execution_failure_no_retry",
                repr(exc),
                output,
            )
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "outcome"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorization-marker", type=Path)
    parser.add_argument("--preflight-result", type=Path)
    args = parser.parse_args()
    result = run(
        mode=args.mode,
        output=args.output,
        authorization_marker=args.authorization_marker,
        preflight_result=args.preflight_result,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "paired_status": result.get("paired_complementarity", {}).get("status"),
                "models_fit": result.get("models_fit", 0),
                "heldout_scores": result.get("heldout_scores", 0),
                "response_download_requests": len(result["response_download_requests"]),
                "response_payload_bytes_opened": result["response_payload_bytes_opened"],
                "smoke_core_fingerprint": result.get("smoke_core_fingerprint"),
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
