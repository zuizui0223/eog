#!/usr/bin/env python3
"""Frozen once-only paired complementarity runner for Mont-Blanc mountain hares.

Smoke mode uses deterministic synthetic station-month observations and never opens
``taghare_1day.csv``. Outcome mode requires the frozen authorization marker, downloads
that response exactly once, and applies the exact count gate before any Layer-A update,
model fit, or heldout score.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import re
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
VALIDATION_DIR = ROOT / "validation/mont_blanc_mountain_hare_paired_complementarity"
sys.path.insert(0, str(VALIDATION_DIR))

from preflight import audit_readme, parse_camera_info  # noqa: E402
from transport import (  # noqa: E402
    download_nonresponse_member,
    download_response_once,
    fetch_file_manifest,
)


CONTRACT_PATH = VALIDATION_DIR / "source_contract.json"
EPS = 1e-6
EARTH_RADIUS_M = 6_371_008.8
ANALYSIS_MONTHS = tuple(
    (year, month)
    for year in range(2019, 2023)
    for month in range(1, 13)
    if (year, month) <= (2022, 6)
)
CALIBRATION_TRANSITIONS = tuple((index, index + 1) for index in range(23))
HELDOUT_TRANSITIONS = tuple((index, index + 1) for index in range(23, 41))
ALL_TRANSITIONS = CALIBRATION_TRANSITIONS + HELDOUT_TRANSITIONS
HELDOUT_OUTER_IDS = (
    "2021_Q1",
    "2021_Q2",
    "2021_Q3",
    "2021_Q4",
    "2022_Q1",
    "2022_Q2",
)
WORLD_IDS = (
    "geo_lcc250",
    "geo_lcc500",
    "geo_lcc750_900",
    "geo_exponential_full",
)

BASELINE_FEATURE_NAMES: tuple[str, ...] = (
    "target_month_index",
    "target_month_index_squared",
    "target_month_sin",
    "target_month_cos",
    "longitude_centered_km",
    "latitude_centered_km",
    "elevation_m",
    "slope_degrees",
    "aspect_sin",
    "aspect_cos",
    "habitat_forest",
    "habitat_shrubland",
    "habitat_grassland",
    "model_bushnell_natureview",
    "model_moultrie_40i",
    "model_reconyx_hf2x",
    "model_moultrie_50i",
    "model_moultrie_reconyx_mixed",
    "target_mean_distance_m",
    "target_nearest_other_site_m",
    "target_degree_lcc250",
    "target_degree_lcc500",
    "target_degree_lcc750_900",
    "source_month_active_days",
    "target_month_active_days",
    "current_source_count",
    "log1p_current_source_contact_days",
    "nearest_current_source_distance_m",
    "source_count_lcc250",
    "source_count_lcc500",
    "source_count_lcc750_900",
    "source_exponential_exposure_lcc250",
    "source_exponential_exposure_lcc500",
    "source_exponential_exposure_lcc750_900",
    "source_exponential_exposure_full",
    "contact_day_weighted_exposure_lcc250",
    "contact_day_weighted_exposure_lcc500",
    "contact_day_weighted_exposure_lcc750_900",
    "contact_day_weighted_exposure_full",
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


def month_text(index: int) -> str:
    year, month = ANALYSIS_MONTHS[index]
    return f"{year:04d}-{month:02d}"


def outer_id_for_target(target_index: int) -> str:
    year, month = ANALYSIS_MONTHS[target_index]
    value = f"{year}_Q{((month - 1) // 3) + 1}"
    if value not in HELDOUT_OUTER_IDS:
        raise RuntimeError(f"heldout target month maps outside frozen outer units: {value}")
    return value


@dataclass(frozen=True)
class ContactRecord:
    station_id: str
    contact_date: date


@dataclass(frozen=True)
class StaticInputs:
    node_ids: tuple[str, ...]
    attributes: dict[str, object]
    coordinates: np.ndarray
    distance: np.ndarray
    active_days: np.ndarray
    thresholds: np.ndarray
    kernel_scale: float


@dataclass(frozen=True)
class RiskRow:
    phase: str
    outer_unit_id: str
    source_index: int
    target_index: int
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
        "models_fit": 0,
        "heldout_scores": 0,
    }


def read_static_inputs(
    contract: dict,
    manifest: dict[str, str],
    audit: dict,
) -> tuple[StaticInputs, dict[str, object]]:
    payloads = {
        name: download_nonresponse_member(name, contract, manifest, audit)
        for name in contract["nonresponse_files"]
    }
    readme_audit = audit_readme(payloads["README.md"])
    node_ids, attributes, coordinates, distance, active_days, camera_audit = (
        parse_camera_info(payloads["camerainfo.csv"], contract)
    )
    thresholds = np.asarray(contract["freezes"]["world_scale"]["thresholds_m"], dtype=float)
    if thresholds.shape != (3,) or not np.all(np.diff(thresholds) > 0.0):
        raise RuntimeError("frozen world thresholds are not three strictly increasing values")
    return (
        StaticInputs(
            node_ids=node_ids,
            attributes=attributes,
            coordinates=coordinates,
            distance=distance,
            active_days=active_days,
            thresholds=thresholds,
            kernel_scale=float(contract["freezes"]["world_scale"]["kernel_scale_m"]),
        ),
        {"readme": readme_audit, "camera": camera_audit},
    )


def validate_physical_header(content: bytes, contract: dict) -> dict[str, object]:
    frozen = contract["response_header_firewall"]
    positions = [value for value in (content.find(b"\r"), content.find(b"\n")) if value >= 0]
    if not positions:
        raise RuntimeError("once-opened response has no first-record terminator")
    end = min(positions)
    terminator = "CR" if content[end : end + 1] == b"\r" else "LF"
    header_bytes = content[:end]
    try:
        header_text = header_bytes.decode("cp1252")
    except UnicodeDecodeError as exc:
        raise RuntimeError("once-opened response header is not cp1252") from exc
    if header_text != frozen["expected_header_text"]:
        raise RuntimeError("once-opened physical header text differs from frozen header")
    if hashlib.sha256(header_bytes).hexdigest() != frozen["expected_header_sha256"]:
        raise RuntimeError("once-opened physical header SHA-256 differs from frozen header")
    if terminator != frozen["expected_terminator"]:
        raise RuntimeError("once-opened physical header terminator differs from frozen header")
    if end + 1 != int(frozen["expected_bytes_consumed_including_terminator"]):
        raise RuntimeError("once-opened physical header length differs from frozen header")
    return {
        "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "terminator": terminator,
        "bytes_consumed_including_terminator": end + 1,
        "matches_pre_response_bounded_header": True,
    }


def _response_date(token: str, row_number: int) -> date:
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", token):
        pattern = "%d/%m/%Y"
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
        pattern = "%Y-%m-%d"
    else:
        raise RuntimeError(f"unfrozen Date representation at response row {row_number}")
    try:
        return datetime.strptime(token, pattern).date()
    except ValueError as exc:
        raise RuntimeError(f"invalid Date at response row {row_number}") from exc


def parse_response(
    content: bytes,
    static: StaticInputs,
    contract: dict,
) -> tuple[tuple[ContactRecord, ...], dict[str, object]]:
    """Perform frozen schema/identity validation without computing endpoint counts."""

    header_audit = validate_physical_header(content, contract)
    try:
        reader = csv.DictReader(io.StringIO(content.decode("cp1252"), newline=""), delimiter=";")
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("once-opened response is not cp1252") from exc
    expected = tuple(contract["response_header_firewall"]["expected_columns"])
    if header != expected:
        raise RuntimeError("once-opened parsed header order differs from frozen schema")

    node_index = {node: index for index, node in enumerate(static.node_ids)}
    setup_dates = static.attributes["setup_dates"]
    identities: set[tuple[str, date]] = set()
    duplicates = 0
    for row_number, row in enumerate(rows, start=2):
        if None in row or set(row) != set(expected):
            raise RuntimeError(f"response row width drift at row {row_number}")
        station = (row.get("Station") or "").strip()
        if station not in node_index:
            raise RuntimeError(f"unknown or non-exact Station at response row {row_number}")
        token = (row.get("Date") or "").strip()
        contacted = _response_date(token, row_number)
        if not date(2018, 1, 1) <= contacted <= date(2022, 6, 30):
            raise RuntimeError(f"Date outside frozen accepted range at response row {row_number}")
        if contacted < setup_dates[node_index[station]]:
            raise RuntimeError(f"Date precedes frozen station setup at response row {row_number}")
        identity = (station, contacted)
        if identity in identities:
            duplicates += 1
        identities.add(identity)
    records = tuple(ContactRecord(station, contacted) for station, contacted in sorted(identities))
    return records, {
        "physical_header": header_audit,
        "header": list(header),
        "raw_row_count": len(rows),
        "unique_station_date_identity_count": len(records),
        "exact_duplicate_rows_collapsed": duplicates,
        "outcome_counts_not_computed_during_schema_identity_parse": True,
    }


def synthetic_response(static: StaticInputs) -> tuple[np.ndarray, np.ndarray]:
    state = np.full((len(static.node_ids), len(ANALYSIS_MONTHS)), -1, dtype=int)
    contact_days = np.zeros(state.shape, dtype=float)
    node_index = np.arange(len(static.node_ids))
    for month_index in range(len(ANALYSIS_MONTHS)):
        observed = static.active_days[:, month_index] >= 20.0
        detected = ((5 * node_index + 7 * month_index) % 19) < 6
        state[observed, month_index] = detected[observed].astype(int)
        contact_days[:, month_index] = np.where(
            observed & detected,
            1 + ((3 * node_index + month_index) % 5),
            0,
        )
    return state, contact_days


def materialize_response(
    records: tuple[ContactRecord, ...],
    static: StaticInputs,
) -> tuple[np.ndarray, np.ndarray]:
    state = np.where(static.active_days >= 20.0, 0, -1).astype(int)
    contact_days = np.zeros(state.shape, dtype=float)
    node_index = {node: index for index, node in enumerate(static.node_ids)}
    month_index = {value: index for index, value in enumerate(ANALYSIS_MONTHS)}
    for record in records:
        key = (record.contact_date.year, record.contact_date.month)
        if key not in month_index:
            continue
        i = node_index[record.station_id]
        t = month_index[key]
        if state[i, t] < 0:
            continue
        state[i, t] = 1
        contact_days[i, t] += 1.0
    return state, contact_days


def transition_endpoint_counts(
    state: np.ndarray,
    source_index: int,
    target_index: int,
) -> dict[str, int]:
    source = state[:, source_index]
    target = state[:, target_index]
    risk = (source == 0) & (target >= 0)
    return {
        "sources": int(np.sum(source == 1)),
        "events": int(np.sum(risk & (target == 1))),
        "non_events": int(np.sum(risk & (target == 0))),
    }


def exact_count_gate(
    records: tuple[ContactRecord, ...] | None,
    static: StaticInputs,
    contract: dict,
    *,
    synthetic: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[dict[str, object], np.ndarray, np.ndarray]:
    """First outcome-dependent analytical operation after schema/identity validation."""

    if (records is None) == (synthetic is None):
        raise RuntimeError("exactly one real or synthetic response source is required")
    if synthetic is None:
        state, contact_days = materialize_response(records or (), static)
    else:
        state, contact_days = synthetic
    expected_shape = (len(static.node_ids), len(ANALYSIS_MONTHS))
    if state.shape != expected_shape or contact_days.shape != expected_shape:
        raise RuntimeError("materialized response shape differs from frozen station-month registry")
    if not np.isin(state, (-1, 0, 1)).all() or not np.isfinite(contact_days).all():
        raise RuntimeError("materialized response contains an invalid state or intensity")

    transition_rows: list[dict[str, object]] = []
    for source_index, target_index in ALL_TRANSITIONS:
        phase = (
            "calibration"
            if (source_index, target_index) in CALIBRATION_TRANSITIONS
            else "heldout"
        )
        counts = transition_endpoint_counts(state, source_index, target_index)
        transition_rows.append(
            {
                "transition": [month_text(source_index), month_text(target_index)],
                "phase": phase,
                "outer_unit_id": (
                    None if phase == "calibration" else outer_id_for_target(target_index)
                ),
                **counts,
            }
        )
    calibration = [row for row in transition_rows if row["phase"] == "calibration"]
    heldout = [row for row in transition_rows if row["phase"] == "heldout"]
    calibration_events = sum(int(row["events"]) for row in calibration)
    calibration_non_events = sum(int(row["non_events"]) for row in calibration)
    heldout_events = sum(int(row["events"]) for row in heldout)
    heldout_non_events = sum(int(row["non_events"]) for row in heldout)

    outer_rows: list[dict[str, object]] = []
    for outer_id in HELDOUT_OUTER_IDS:
        members = [row for row in heldout if row["outer_unit_id"] == outer_id]
        events = sum(int(row["events"]) for row in members)
        non_events = sum(int(row["non_events"]) for row in members)
        outer_rows.append(
            {
                "outer_unit_id": outer_id,
                "transition_count": len(members),
                "events": events,
                "non_events": non_events,
            }
        )
    held_with_rows = sum(int(row["events"]) + int(row["non_events"]) > 0 for row in outer_rows)
    held_both = sum(int(row["events"]) > 0 and int(row["non_events"]) > 0 for row in outer_rows)
    all_sources = all(int(row["sources"]) > 0 for row in transition_rows)
    minima = contract["freezes"]["count_gate"]
    passed = bool(
        calibration_events >= int(minima["calibration_events"])
        and calibration_non_events >= int(minima["calibration_non_events"])
        and heldout_events >= int(minima["heldout_events"])
        and heldout_non_events >= int(minima["heldout_non_events"])
        and held_both >= int(minima["heldout_outer_units_with_both_classes"])
        and held_with_rows == int(minima["heldout_outer_units_with_rows"])
        and all_sources
    )
    result = {
        "passed": passed,
        "executed_before_any_layer_a_update_or_model_fit": True,
        "transition_counts": transition_rows,
        "heldout_outer_unit_counts": outer_rows,
        "calibration_events": calibration_events,
        "calibration_non_events": calibration_non_events,
        "heldout_events": heldout_events,
        "heldout_non_events": heldout_non_events,
        "heldout_outer_units_with_rows": held_with_rows,
        "heldout_outer_units_with_both_classes": held_both,
        "all_transitions_have_current_internal_sources": all_sources,
        "minimums": {
            key: minima[key]
            for key in (
                "calibration_events",
                "calibration_non_events",
                "heldout_events",
                "heldout_non_events",
                "heldout_outer_units_with_both_classes",
                "heldout_outer_units_with_rows",
            )
        },
    }
    return result, state, contact_days


def compute_world_supports(
    static: StaticInputs,
    source_indices: np.ndarray,
    contract: dict,
) -> np.ndarray:
    if source_indices.size == 0:
        raise RuntimeError("current internal source set is empty")
    source_distance = static.distance[source_indices, :]
    exponential = np.exp(-source_distance / static.kernel_scale)
    supports = np.zeros((len(WORLD_IDS), len(static.node_ids)), dtype=float)
    source_weight = 1.0 / float(source_indices.size)
    loss = float(contract["freezes"]["world_scale"]["loss_support"])
    source_rows = np.arange(source_indices.size)
    for world_index, threshold in enumerate(static.thresholds):
        raw = exponential * (source_distance <= threshold + 1e-12)
        raw[source_rows, source_indices] = 0.0
        denominator = loss + np.sum(raw, axis=1)
        supports[world_index] = (source_weight / denominator) @ raw
    raw = exponential.copy()
    raw[source_rows, source_indices] = 0.0
    denominator = loss + np.sum(raw, axis=1)
    supports[-1] = (source_weight / denominator) @ raw
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
    surviving_ids = []
    for index, keep in enumerate(surviving):
        if not bool(keep):
            continue
        surviving_ids.append(WORLD_IDS[index])
        members.append(
            SimpleNamespace(
                cumulative_reachability=np.vstack(
                    (np.zeros(len(static.node_ids), dtype=float), supports[index])
                ),
                supported_state=np.vstack(
                    (
                        np.zeros(len(static.node_ids), dtype=bool),
                        supports[index] > tolerance,
                    )
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
            (world_id, canonical_sha256({"world_id": world_id}))
            for world_id in surviving_ids
        ),
        fingerprint=canonical_sha256(
            {
                "transition_id": transition_id,
                "surviving_world_ids": surviving_ids,
                "support_sha256": hashlib.sha256(
                    np.ascontiguousarray(supports[surviving], dtype=np.float64).tobytes()
                ).hexdigest(),
            }
        ),
    )
    summary = summarize_worldset_for_prediction(forecast, step=1)
    if summary.feature_names != PREDICTIVE_FEATURE_NAMES:
        raise RuntimeError("production Layer-B feature-name surface drift")
    return summary.feature_matrix, summary.feature_fingerprint


def baseline_features(
    static: StaticInputs,
    contact_days: np.ndarray,
    source_indices: np.ndarray,
    source_index: int,
    target_index: int,
    contract: dict,
) -> np.ndarray:
    n = len(static.node_ids)
    year, target_month = ANALYSIS_MONTHS[target_index]
    del year
    month_angle = 2.0 * math.pi * float(target_month - 1) / 12.0
    longitude = np.radians(static.coordinates[:, 0])
    latitude = np.radians(static.coordinates[:, 1])
    longitude_centered = (
        EARTH_RADIUS_M
        * math.cos(float(np.mean(latitude)))
        * (longitude - float(np.mean(longitude)))
        / 1000.0
    )
    latitude_centered = EARTH_RADIUS_M * (latitude - float(np.mean(latitude))) / 1000.0

    attributes = static.attributes
    elevation = np.asarray(attributes["elevation"], dtype=float)
    slope = np.asarray(attributes["slope"], dtype=float)
    preprocessing = contract["freezes"]["preprocessing_model_fit"]
    aspect_degrees = preprocessing["aspect_degrees_clockwise_from_north"]
    aspect_angle = np.radians(
        np.asarray([float(aspect_degrees[value]) for value in attributes["aspect"]])
    )
    habitat_map = preprocessing["habitat_mapping"]
    habitat = tuple(habitat_map[value] for value in attributes["habitat"])
    models = tuple(attributes["model"])
    model_tokens = tuple(preprocessing["model_tokens"])

    other_distance = static.distance.copy()
    np.fill_diagonal(other_distance, np.nan)
    mean_distance = np.nanmean(other_distance, axis=1)
    nearest_other = np.nanmin(other_distance, axis=1)
    degree = [
        np.sum(static.distance <= threshold + 1e-12, axis=0) - 1
        for threshold in static.thresholds
    ]

    source_distance = static.distance[source_indices, :]
    exponential = np.exp(-source_distance / static.kernel_scale)
    source_rows = np.arange(source_indices.size)
    masks = []
    for threshold in static.thresholds:
        mask = source_distance <= threshold + 1e-12
        mask[source_rows, source_indices] = False
        masks.append(mask)
    full_mask = np.ones(source_distance.shape, dtype=bool)
    full_mask[source_rows, source_indices] = False
    source_count_within = [np.sum(mask, axis=0) for mask in masks]
    unweighted = [np.sum(exponential * mask, axis=0) for mask in masks]
    unweighted_full = np.sum(exponential * full_mask, axis=0)
    source_weights = contact_days[source_indices, source_index]
    weighted = [np.sum(exponential * mask * source_weights[:, None], axis=0) for mask in masks]
    weighted_full = np.sum(exponential * full_mask * source_weights[:, None], axis=0)
    nearest_source = np.min(source_distance, axis=0)

    columns = (
        np.full(n, float(target_index)),
        np.full(n, float(target_index * target_index)),
        np.full(n, math.sin(month_angle)),
        np.full(n, math.cos(month_angle)),
        longitude_centered,
        latitude_centered,
        elevation,
        slope,
        np.sin(aspect_angle),
        np.cos(aspect_angle),
        np.asarray([value == "forest" for value in habitat], dtype=float),
        np.asarray([value == "shrubland" for value in habitat], dtype=float),
        np.asarray([value == "grassland" for value in habitat], dtype=float),
        *tuple(np.asarray([value == token for value in models], dtype=float) for token in model_tokens),
        mean_distance,
        nearest_other,
        *degree,
        static.active_days[:, source_index],
        static.active_days[:, target_index],
        np.full(n, float(source_indices.size)),
        np.full(n, math.log1p(float(np.sum(source_weights)))),
        nearest_source,
        *source_count_within,
        *unweighted,
        unweighted_full,
        *weighted,
        weighted_full,
    )
    matrix = np.column_stack(columns).astype(float)
    if matrix.shape != (n, len(BASELINE_FEATURE_NAMES)):
        raise RuntimeError(
            f"baseline feature shape drift: {matrix.shape} != {(n, len(BASELINE_FEATURE_NAMES))}"
        )
    if not np.isfinite(matrix).all():
        raise RuntimeError("nonfinite frozen baseline predictor")
    return matrix


def update_worlds(
    supports: np.ndarray,
    surviving: np.ndarray,
    positive_targets: np.ndarray,
    tolerance: float,
) -> tuple[np.ndarray, tuple[str, ...]]:
    result = surviving.copy()
    eliminated: list[str] = []
    if positive_targets.size:
        for index, world_id in enumerate(WORLD_IDS):
            if result[index] and np.any(supports[index, positive_targets] <= tolerance):
                result[index] = False
                eliminated.append(world_id)
    if np.any(result & ~surviving):
        raise AssertionError("eliminated frozen world returned")
    return result, tuple(eliminated)


def build_risk_rows(
    state: np.ndarray,
    contact_days: np.ndarray,
    static: StaticInputs,
    contract: dict,
) -> tuple[list[RiskRow], dict[str, object]]:
    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    tolerance = float(contract["freezes"]["world_scale"]["support_tolerance"])
    risk_rows: list[RiskRow] = []
    history: list[dict[str, object]] = []
    for source_index, target_index in ALL_TRANSITIONS:
        phase = (
            "calibration"
            if (source_index, target_index) in CALIBRATION_TRANSITIONS
            else "heldout"
        )
        source_indices = np.flatnonzero(state[:, source_index] == 1)
        if source_indices.size == 0:
            raise RuntimeError(f"no current internal source at {month_text(source_index)}")
        supports = compute_world_supports(static, source_indices, contract)
        transition_id = f"{month_text(source_index)}->{month_text(target_index)}"
        layer_b, layer_fingerprint = layer_b_summary(
            static, supports, surviving, transition_id, contract
        )
        baseline = baseline_features(
            static,
            contact_days,
            source_indices,
            source_index,
            target_index,
            contract,
        )
        risk = np.flatnonzero((state[:, source_index] == 0) & (state[:, target_index] >= 0))
        positives: list[int] = []
        transition_events = 0
        outer_id = "calibration" if phase == "calibration" else outer_id_for_target(target_index)
        for node in risk:
            node = int(node)
            label = int(state[node, target_index] == 1)
            transition_events += label
            if label:
                positives.append(node)
            risk_rows.append(
                RiskRow(
                    phase=phase,
                    outer_unit_id=outer_id,
                    source_index=source_index,
                    target_index=target_index,
                    node_index=node,
                    label=label,
                    baseline=tuple(float(value) for value in baseline[node]),
                    layer_b=tuple(float(value) for value in layer_b[node]),
                )
            )
        before_ids = [
            world_id for world_id, keep in zip(WORLD_IDS, surviving, strict=True) if keep
        ]
        after, eliminated = update_worlds(
            supports, surviving, np.asarray(positives, dtype=int), tolerance
        )
        after_ids = [
            world_id for world_id, keep in zip(WORLD_IDS, after, strict=True) if keep
        ]
        history.append(
            {
                "transition": [month_text(source_index), month_text(target_index)],
                "phase": phase,
                "outer_unit_id": outer_id,
                "current_internal_sources": int(source_indices.size),
                "risk_rows": int(risk.size),
                "events": transition_events,
                "non_events": int(risk.size) - transition_events,
                "surviving_before": before_ids,
                "eliminated_after_observation": list(eliminated),
                "surviving_after": after_ids,
                "layer_b_feature_fingerprint": layer_fingerprint,
            }
        )
        surviving = after
        if not np.any(surviving) and (source_index, target_index) != ALL_TRANSITIONS[-1]:
            raise RuntimeError(f"frozen world universe falsified after {transition_id}")
    return risk_rows, {
        "row_count": len(risk_rows),
        "calibration_rows": sum(row.phase == "calibration" for row in risk_rows),
        "heldout_rows": sum(row.phase == "heldout" for row in risk_rows),
        "rule_history": history,
        "final_surviving_world_ids": [
            world_id for world_id, keep in zip(WORLD_IDS, surviving, strict=True) if keep
        ],
        "exact_site_id_supervised": False,
        "exact_world_id_supervised": False,
    }


def layer_b_estimability(
    baseline: np.ndarray,
    layer_b: np.ndarray,
) -> dict[str, object]:
    baseline = np.asarray(baseline, dtype=float)
    layer = np.asarray(layer_b, dtype=float)
    if not np.isfinite(baseline).all() or not np.isfinite(layer).all():
        raise RuntimeError("Layer-B estimability input is nonfinite")
    sd = np.std(baseline, axis=0, ddof=0)
    keep = np.flatnonzero(sd > 1e-12)
    if keep.size:
        x = baseline[:, keep]
        x = (x - np.mean(x, axis=0)) / np.std(x, axis=0, ddof=0)
        design = np.column_stack((np.ones(len(x)), x))
    else:
        design = np.ones((len(baseline), 1), dtype=float)
    retained: list[int] = []
    residual_sd: list[float] = []
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
    params = dict(contract["freezes"]["preprocessing_model_fit"]["hyperparameters"])
    return RandomForestClassifier(**params)


def binary_log_loss(y: np.ndarray, probability: np.ndarray) -> float:
    truth = np.asarray(y, dtype=float)
    pred = np.clip(np.asarray(probability, dtype=float), EPS, 1.0 - EPS)
    return float(-np.mean(truth * np.log(pred) + (1.0 - truth) * np.log(1.0 - pred)))


def brier_score(y: np.ndarray, probability: np.ndarray) -> float:
    truth = np.asarray(y, dtype=float)
    return float(np.mean((np.asarray(probability, dtype=float) - truth) ** 2))


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
            {
                "feature_names": list(BASELINE_FEATURE_NAMES),
                "missing_value_policy": freezes["preprocessing_model_fit"][
                    "missing_value_policy"
                ],
            }
        ),
        eog_feature_fingerprint=canonical_sha256(freezes["layer_b_representation"]),
    )


def fit_and_score(
    rows: list[RiskRow],
    contract: dict,
    execution_audit: dict[str, object] | None = None,
) -> tuple[dict[str, object], dict[str, str]]:
    calibration = [row for row in rows if row.phase == "calibration"]
    heldout = [row for row in rows if row.phase == "heldout"]
    x_cal = np.asarray([row.baseline for row in calibration], dtype=float)
    layer_cal = np.asarray([row.layer_b for row in calibration], dtype=float)
    y_cal = np.asarray([row.label for row in calibration], dtype=int)
    x_held = np.asarray([row.baseline for row in heldout], dtype=float)
    layer_held = np.asarray([row.layer_b for row in heldout], dtype=float)
    y_held = np.asarray([row.label for row in heldout], dtype=int)
    for label, matrix in (
        ("calibration baseline", x_cal),
        ("calibration Layer B", layer_cal),
        ("heldout baseline", x_held),
        ("heldout Layer B", layer_held),
    ):
        if matrix.ndim != 2 or not np.isfinite(matrix).all():
            raise RuntimeError(f"{label} is nonfinite or not a matrix")
    estimability = layer_b_estimability(x_cal, layer_cal)
    if not estimability["estimable"]:
        return {"estimability": estimability}, {"status": "layer_b_non_estimable"}

    baseline_model = learner(contract)
    augmented_model = learner(contract)
    baseline_model.fit(x_cal, y_cal)
    if execution_audit is not None:
        execution_audit["models_fit"] = int(execution_audit.get("models_fit", 0)) + 1
    augmented_model.fit(np.column_stack((x_cal, layer_cal)), y_cal)
    if execution_audit is not None:
        execution_audit["models_fit"] = int(execution_audit.get("models_fit", 0)) + 1
    p_base = baseline_model.predict_proba(x_held)[:, 1]
    p_augmented = augmented_model.predict_proba(np.column_stack((x_held, layer_held)))[:, 1]

    paired: list[PairedOuterUnitScore] = []
    outer_rows: list[dict[str, object]] = []
    for outer_id in HELDOUT_OUTER_IDS:
        indices = np.asarray(
            [index for index, row in enumerate(heldout) if row.outer_unit_id == outer_id],
            dtype=int,
        )
        if indices.size == 0:
            raise RuntimeError(f"frozen heldout outer unit has no score rows: {outer_id}")
        truth = y_held[indices]
        base_loss = binary_log_loss(truth, p_base[indices])
        augmented_loss = binary_log_loss(truth, p_augmented[indices])
        if execution_audit is not None:
            execution_audit["heldout_scores"] = int(
                execution_audit.get("heldout_scores", 0)
            ) + 2
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
    return (
        {
            "models_fit": 2,
            "heldout_scores": 2 * len(paired),
            "missing_value_policy": "no imputation; all predictors verified finite",
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
                "augmented_feature_names": [
                    *BASELINE_FEATURE_NAMES,
                    *PREDICTIVE_FEATURE_NAMES,
                ],
                "exact_site_id_supervised": False,
                "exact_world_id_supervised": False,
                "only_augmented_difference": list(PREDICTIVE_FEATURE_NAMES),
                "same_learner_hyperparameters_rows_labels_split_and_preprocessing": True,
            },
        },
        {"status": "completed"},
    )


def verify_frozen_environment(contract: dict) -> None:
    freeze = contract["freezes"]["preprocessing_model_fit"]
    if ".".join(platform.python_version().split(".")[:2]) != freeze["python"]:
        raise RuntimeError("Python major/minor version differs from frozen environment")
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
        raise RuntimeError("preflight did not authorize the exact-count-first run")
    if preflight.get("response_rows_opened") is not False:
        raise RuntimeError("preflight claims a response row was opened")
    if marker.get("outcome_access_gate_fingerprint") != preflight[
        "outcome_access_gate"
    ]["fingerprint"]:
        raise RuntimeError("authorization marker outcome-gate fingerprint mismatch")
    if marker.get("preflight_fingerprint") != preflight.get("fingerprint"):
        raise RuntimeError("authorization marker preflight fingerprint mismatch")
    return {
        "authorized_parent_commit": marker.get("authorized_parent_commit"),
        "outcome_access_gate_fingerprint": preflight["outcome_access_gate"]["fingerprint"],
        "preflight_fingerprint": preflight["fingerprint"],
        "invocation_budget": 1,
    }


def write_result(path: Path, result: dict[str, object]) -> dict[str, object]:
    payload = dict(result)
    payload["fingerprint"] = canonical_sha256(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def stopped_result(
    base: dict[str, object],
    status: str,
    reason: str,
    output: Path,
) -> dict[str, object]:
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


def run(
    *,
    mode: str,
    output: Path,
    authorization_marker: Path | None = None,
    preflight_result: Path | None = None,
) -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    verify_frozen_environment(contract)
    base = initial_audit(mode, contract)
    if mode == "outcome":
        if authorization_marker is None or preflight_result is None:
            raise RuntimeError("outcome mode requires authorization marker and preflight result")
        base["authorization"] = verify_authorization(
            contract, authorization_marker, preflight_result
        )
    elif authorization_marker is not None or preflight_result is not None:
        raise RuntimeError("smoke mode must not receive outcome authorization inputs")

    manifest = fetch_file_manifest(contract, base)
    static, static_audit = read_static_inputs(contract, manifest, base)
    base.update(
        {
            "status": "pre_model",
            "response_target": "observed_monthly_camera_detection_reappearance",
            "response_boundary": (
                "adequately observed station-month zero-to-detected transition; not latent "
                "occupancy, abundance, physical immigration, parentage, or migration history"
            ),
            "node_count": len(static.node_ids),
            "analysis_month_count": len(ANALYSIS_MONTHS),
            "calibration_transition_count": len(CALIBRATION_TRANSITIONS),
            "heldout_transition_count": len(HELDOUT_TRANSITIONS),
            "heldout_outer_unit_count": len(HELDOUT_OUTER_IDS),
            "static_input_audit": static_audit,
            "exact_site_id_supervised": False,
            "exact_world_id_supervised": False,
        }
    )

    if mode == "smoke":
        synthetic = synthetic_response(static)
        records = None
        response_provenance = {
            "source": "deterministic synthetic technical-control station-month table",
            "response_download_requests": 0,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": False,
            "station_month_cells": int(np.prod(synthetic[0].shape)),
        }
    else:
        synthetic = None
        try:
            content = download_response_once(contract, manifest, base)
            records, schema = parse_response(content, static, contract)
            response_provenance = {
                "filename": contract["response_file"],
                "sha256_after_once_only_open": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "response_download_requests": 1,
                "response_rows_opened": True,
                "schema_identity_audit": schema,
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
        count_gate, state, contact_days = exact_count_gate(
            records, static, contract, synthetic=synthetic
        )
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
    if not count_gate["passed"]:
        if mode == "outcome":
            return stopped_result(
                base,
                "post_open_count_gate_stop_no_retry",
                "one or more prospectively frozen exact count requirements failed; zero fits and scores",
                output,
            )
        raise RuntimeError("synthetic technical control failed the exact count gate")

    try:
        risk_rows, row_audit = build_risk_rows(state, contact_days, static, contract)
        base["risk_table_audit"] = row_audit
        model_result, model_state = fit_and_score(risk_rows, contract, base)
        if model_state["status"] == "layer_b_non_estimable":
            base["layer_b_estimability"] = model_result["estimability"]
            status = (
                "post_open_layer_b_nonestimable_stop_no_retry"
                if mode == "outcome"
                else "layer_b_non_estimable_zero_fit"
            )
            return stopped_result(
                base,
                status,
                "unchanged Layer B has no calibration variation beyond the frozen baseline",
                output,
            )
        base.update(model_result)
        base["status"] = "smoke_pass" if mode == "smoke" else "completed_frozen_paired_test"
        return write_result(output, base)
    except Exception as exc:
        if mode == "outcome":
            return stopped_result(
                base,
                "post_open_execution_stop_no_retry",
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
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
