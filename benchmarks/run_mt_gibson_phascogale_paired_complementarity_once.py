#!/usr/bin/env python3
"""Frozen once-only paired complementarity runner for Mt Gibson phascogales.

Smoke mode uses deterministic synthetic site-year observations and never requests
``Camera_survey_detection_data.csv``.  Outcome mode requires a marker bound to a green frozen parent,
downloads that response object exactly once, applies the exact count gate as the first
outcome-dependent analytical operation, and then (only on PASS) compares one strong
random forest with the identical forest plus unchanged EOG Layer B.
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
VALIDATION_DIR = ROOT / "validation/mt_gibson_phascogale_paired_complementarity"
sys.path.insert(0, str(VALIDATION_DIR))

from preflight import parse_deployments, parse_geometry  # noqa: E402
from transport import (  # noqa: E402
    download_nonresponse_member,
    download_response_once,
    fetch_file_manifest,
)


CONTRACT_PATH = VALIDATION_DIR / "source_contract.json"
EPS = 1e-6
CAMPAIGNS = tuple(range(2018, 2025))
ANALYSIS_YEARS = tuple(range(2020, 2025))
CALIBRATION_TRANSITIONS = ((2020, 2021), (2021, 2022))
HELDOUT_TRANSITIONS = ((2022, 2023), (2023, 2024))
ALL_TRANSITIONS = CALIBRATION_TRANSITIONS + HELDOUT_TRANSITIONS
WORLD_IDS = (
    "geo_lcc250",
    "geo_lcc500",
    "geo_lcc750",
    "geo_lcc900",
    "geo_exponential_full",
)

BASELINE_FEATURE_NAMES: tuple[str, ...] = (
    "target_year_index",
    "target_year_index_squared",
    "utm_easting_centered_km",
    "utm_northing_centered_km",
    "target_mean_distance_m",
    "target_nearest_other_site_m",
    "target_degree_lcc250",
    "target_degree_lcc500",
    "target_degree_lcc750",
    "target_degree_lcc900",
    "source_campaign_effort_days",
    "target_campaign_effort_days",
    "target_campaign_mid_day_index",
    "current_source_count",
    "log1p_current_source_detection_days",
    "nearest_current_source_distance_m",
    "source_count_lcc250",
    "source_count_lcc500",
    "source_count_lcc750",
    "source_count_lcc900",
    "source_exponential_exposure_lcc250",
    "source_exponential_exposure_lcc500",
    "source_exponential_exposure_lcc750",
    "source_exponential_exposure_lcc900",
    "source_exponential_exposure_full",
    "detection_day_weighted_exposure_lcc250",
    "detection_day_weighted_exposure_lcc500",
    "detection_day_weighted_exposure_lcc750",
    "detection_day_weighted_exposure_lcc900",
    "detection_day_weighted_exposure_full",
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


def exact_int(value: str, label: str) -> int:
    number = finite_optional(value, label)
    if number is None:
        raise RuntimeError(f"{label} is missing")
    integer = int(round(number))
    if abs(number - integer) > 1e-9:
        raise RuntimeError(f"{label} is not integer-valued")
    return integer


@dataclass(frozen=True)
class DetectionRecord:
    site_id: str
    detection_date: date


@dataclass(frozen=True)
class StaticInputs:
    node_ids: tuple[str, ...]
    coordinates: np.ndarray
    distance: np.ndarray
    deployment_intervals: dict[tuple[str, int], tuple[tuple[date, date], ...]]
    effort_days: np.ndarray
    campaign_mid_day: np.ndarray
    thresholds: np.ndarray
    kernel_scale: float


@dataclass(frozen=True)
class RiskRow:
    phase: str
    outer_unit_id: str
    source_year: int
    target_year: int
    node_index: int
    label: int
    baseline: tuple[float, ...]
    layer_b: tuple[float, ...]


def initial_audit(mode: str, contract: dict) -> dict:
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
    node_ids, coordinates, distance, geometry_audit = parse_geometry(
        payloads["Camera_survey_site_location_data.csv"], contract
    )
    intervals, effort_days, campaign_mid_day, deployment_audit = parse_deployments(
        payloads["Camera_survey_deployment_data.csv"], node_ids, contract
    )
    thresholds = np.asarray(
        contract["freezes"]["world_scale"]["thresholds_m"], dtype=float
    )
    if thresholds.shape != (4,) or not np.all(np.diff(thresholds) > 0):
        raise RuntimeError("frozen world thresholds are not four strictly increasing values")
    return (
        StaticInputs(
            node_ids=node_ids,
            coordinates=coordinates,
            distance=distance,
            deployment_intervals=intervals,
            effort_days=effort_days,
            campaign_mid_day=campaign_mid_day,
            thresholds=thresholds,
            kernel_scale=float(contract["freezes"]["world_scale"]["kernel_scale_m"]),
        ),
        {
            "geometry": geometry_audit,
            "deployments": deployment_audit,
            "readme_sha256": hashlib.sha256(payloads["README.md"]).hexdigest(),
        },
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
        raise RuntimeError("once-opened physical header length differs from frozen header")
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
) -> tuple[tuple[DetectionRecord, ...], dict[str, object]]:
    header_audit = validate_physical_header(content, contract)
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    except UnicodeDecodeError as exc:
        raise RuntimeError("once-opened response is not UTF-8") from exc
    expected = tuple(contract["response_header_firewall"]["expected_columns"])
    if header != expected:
        raise RuntimeError("once-opened parsed header order differs from frozen schema")
    records: list[DetectionRecord] = []
    node_set = set(static.node_ids)
    identities: set[tuple[str, date]] = set()
    for number, row in enumerate(rows, start=2):
        site = row["Camera Site"].strip()
        if site not in node_set:
            raise RuntimeError(f"unknown or non-exact Camera Site at response row {number}")
        token = row["Detection date"].strip()
        try:
            detected = datetime.strptime(token, "%d/%m/%Y").date()
        except ValueError as exc:
            raise RuntimeError(f"invalid Detection date at response row {number}") from exc
        identity = (site, detected)
        if identity in identities:
            raise RuntimeError(f"duplicate camera-site detection date at row {number}")
        identities.add(identity)
        records.append(DetectionRecord(site, detected))
    return tuple(records), {
        "physical_header": header_audit,
        "header": list(header),
        "row_count": len(rows),
        "unique_site_date_identity_count": len(identities),
        "outcome_counts_not_computed_during_schema_parse": True,
    }


def synthetic_response(static: StaticInputs) -> tuple[np.ndarray, np.ndarray]:
    state = np.zeros((len(static.node_ids), len(CAMPAIGNS)), dtype=int)
    detection_days = np.zeros_like(state, dtype=float)
    node_index = np.arange(len(static.node_ids))
    for year_index, _year in enumerate(CAMPAIGNS):
        occupied = ((5 * node_index + 7 * year_index) % 29) < 6
        state[:, year_index] = occupied.astype(int)
        detection_days[:, year_index] = occupied * (
            1 + ((3 * node_index + year_index) % 5)
        )
    return state, detection_days


def transition_endpoint_counts(
    state: np.ndarray,
    source_year: int,
    target_year: int,
) -> dict[str, int]:
    source = state[:, CAMPAIGNS.index(source_year)]
    target = state[:, CAMPAIGNS.index(target_year)]
    risk = source == 0
    return {
        "sources": int(np.sum(source == 1)),
        "events": int(np.sum(risk & (target == 1))),
        "non_events": int(np.sum(risk & (target == 0))),
    }


def materialize_response(
    records: tuple[DetectionRecord, ...],
    static: StaticInputs,
) -> tuple[np.ndarray, np.ndarray]:
    state = np.zeros((len(static.node_ids), len(CAMPAIGNS)), dtype=int)
    detection_days = np.zeros_like(state, dtype=float)
    node_index = {node: index for index, node in enumerate(static.node_ids)}
    for record in records:
        campaigns = {
            campaign
            for campaign in CAMPAIGNS
            for start, end in static.deployment_intervals[(record.site_id, campaign)]
            if end >= start and start <= record.detection_date <= end
        }
        if len(campaigns) != 1:
            raise RuntimeError(
                "detection date does not map to exactly one response-blind deployment campaign"
            )
        campaign = next(iter(campaigns))
        i = node_index[record.site_id]
        t = CAMPAIGNS.index(campaign)
        state[i, t] = 1
        detection_days[i, t] += 1.0
    return state, detection_days


def exact_count_gate(
    records: tuple[DetectionRecord, ...] | None,
    static: StaticInputs,
    contract: dict,
    *,
    synthetic: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[dict[str, object], np.ndarray, np.ndarray]:
    """First outcome-dependent analytical operation after schema/identity parsing."""

    if (records is None) == (synthetic is None):
        raise RuntimeError("exactly one real or synthetic response source is required")
    if synthetic is None:
        state, detection_days = materialize_response(records or (), static)
    else:
        state, detection_days = synthetic
    if state.shape != (len(static.node_ids), len(CAMPAIGNS)):
        raise RuntimeError("materialized state shape differs from frozen campaign registry")

    rows: list[dict[str, object]] = []
    for source_year, target_year in ALL_TRANSITIONS:
        counts = transition_endpoint_counts(state, source_year, target_year)
        rows.append(
            {
                "transition": [source_year, target_year],
                "phase": "calibration" if (source_year, target_year) in CALIBRATION_TRANSITIONS else "heldout",
                **counts,
            }
        )
    calibration = [row for row in rows if row["phase"] == "calibration"]
    heldout = [row for row in rows if row["phase"] == "heldout"]
    cal_events = sum(int(row["events"]) for row in calibration)
    cal_non_events = sum(int(row["non_events"]) for row in calibration)
    held_events = sum(int(row["events"]) for row in heldout)
    held_non_events = sum(int(row["non_events"]) for row in heldout)
    held_with_rows = sum(int(row["events"]) + int(row["non_events"]) > 0 for row in heldout)
    held_both = sum(int(row["events"]) > 0 and int(row["non_events"]) > 0 for row in heldout)
    all_sources = all(int(row["sources"]) > 0 for row in rows)
    minima = contract["freezes"]["count_gate"]
    passed = bool(
        cal_events >= int(minima["calibration_events"])
        and cal_non_events >= int(minima["calibration_non_events"])
        and held_events >= int(minima["heldout_events"])
        and held_non_events >= int(minima["heldout_non_events"])
        and held_both >= int(minima["heldout_outer_units_with_both_classes"])
        and held_with_rows == int(minima["heldout_outer_units_with_rows"])
        and all_sources
    )
    result = {
        "passed": passed,
        "executed_before_any_layer_a_update_or_model_fit": True,
        "transition_counts": rows,
        "calibration_events": cal_events,
        "calibration_non_events": cal_non_events,
        "heldout_events": held_events,
        "heldout_non_events": held_non_events,
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
    return result, state, detection_days


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
    for world_index, threshold in enumerate(static.thresholds):
        raw = exponential * (source_distance <= threshold + 1e-12)
        raw[np.arange(source_indices.size), source_indices] = 0.0
        denominator = loss + np.sum(raw, axis=1)
        supports[world_index] = (source_weight / denominator) @ raw
    raw = exponential.copy()
    raw[np.arange(source_indices.size), source_indices] = 0.0
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
    for index, keep in enumerate(surviving):
        if not bool(keep):
            continue
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


def baseline_features(
    static: StaticInputs,
    detection_days: np.ndarray,
    source_indices: np.ndarray,
    source_counts: np.ndarray,
    source_year: int,
    target_year: int,
) -> np.ndarray:
    n = len(static.node_ids)
    target_year_index = float(target_year - ANALYSIS_YEARS[0])
    centered = (static.coordinates - np.mean(static.coordinates, axis=0)) / 1000.0
    source_t = CAMPAIGNS.index(source_year)
    target_t = CAMPAIGNS.index(target_year)

    other = static.distance.copy()
    np.fill_diagonal(other, np.nan)
    mean_distance = np.nanmean(other, axis=1)
    nearest_other = np.nanmin(other, axis=1)
    target_degrees = [
        np.sum(static.distance <= threshold + 1e-12, axis=0) - 1
        for threshold in static.thresholds
    ]

    source_distance = static.distance[source_indices, :]
    exponential = np.exp(-source_distance / static.kernel_scale)
    source_within = [
        source_distance <= threshold + 1e-12 for threshold in static.thresholds
    ]
    source_counts_within = [np.sum(mask, axis=0) for mask in source_within]
    unweighted_exposure = [
        np.sum(exponential * mask, axis=0) for mask in source_within
    ]
    unweighted_full = np.sum(exponential, axis=0)
    weighted = source_counts[:, None] * exponential
    weighted_exposure = [np.sum(weighted * mask, axis=0) for mask in source_within]
    weighted_full = np.sum(weighted, axis=0)
    nearest_source = np.min(source_distance, axis=0)
    features = np.column_stack(
        [
            np.full(n, target_year_index),
            np.full(n, target_year_index**2),
            centered[:, 0],
            centered[:, 1],
            mean_distance,
            nearest_other,
            *target_degrees,
            static.effort_days[:, source_t],
            static.effort_days[:, target_t],
            static.campaign_mid_day[:, target_t],
            np.full(n, source_indices.size, dtype=float),
            np.full(n, math.log1p(float(np.sum(source_counts))), dtype=float),
            nearest_source,
            *source_counts_within,
            *unweighted_exposure,
            unweighted_full,
            *weighted_exposure,
            weighted_full,
        ]
    ).astype(float)
    if features.shape != (n, len(BASELINE_FEATURE_NAMES)):
        raise RuntimeError(
            f"baseline feature shape drift: {features.shape} != {(n, len(BASELINE_FEATURE_NAMES))}"
        )
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
    state: np.ndarray,
    detection_days: np.ndarray,
    static: StaticInputs,
    contract: dict,
) -> tuple[list[RiskRow], dict[str, object]]:
    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    risk_rows: list[RiskRow] = []
    history: list[dict[str, object]] = []
    tolerance = float(contract["freezes"]["world_scale"]["support_tolerance"])
    for source_year, target_year in ALL_TRANSITIONS:
        source_t = CAMPAIGNS.index(source_year)
        target_t = CAMPAIGNS.index(target_year)
        source_indices = np.flatnonzero(state[:, source_t] == 1)
        if source_indices.size == 0:
            raise RuntimeError(f"no current internal sources for {source_year}->{target_year}")
        source_counts = detection_days[source_indices, source_t].astype(float)
        supports = compute_world_supports(static, source_indices, contract)
        layer_b, layer_fingerprint = layer_b_summary(
            static,
            supports,
            surviving,
            f"{source_year}_to_{target_year}",
            contract,
        )
        baseline = baseline_features(
            static,
            detection_days,
            source_indices,
            source_counts,
            source_year,
            target_year,
        )
        phase = "calibration" if (source_year, target_year) in CALIBRATION_TRANSITIONS else "heldout"
        positives: list[int] = []
        transition_row_count = 0
        transition_events = 0
        transition_non_events = 0
        for index, _node in enumerate(static.node_ids):
            if state[index, source_t] != 0:
                continue
            label = int(state[index, target_t] == 1)
            if label:
                positives.append(index)
                transition_events += 1
            else:
                transition_non_events += 1
            transition_row_count += 1
            risk_rows.append(
                RiskRow(
                    phase=phase,
                    outer_unit_id=f"year_{target_year}",
                    source_year=source_year,
                    target_year=target_year,
                    node_index=index,
                    label=label,
                    baseline=tuple(float(value) for value in baseline[index]),
                    layer_b=tuple(float(value) for value in layer_b[index]),
                )
            )
        after, eliminated = update_worlds(
            supports,
            surviving,
            np.asarray(positives, dtype=int),
            tolerance,
        )
        history.append(
            {
                "transition": [source_year, target_year],
                "phase": phase,
                "current_internal_sources": int(source_indices.size),
                "risk_rows": transition_row_count,
                "events": transition_events,
                "non_events": transition_non_events,
                "surviving_before": [
                    world_id
                    for world_id, keep in zip(WORLD_IDS, surviving, strict=True)
                    if keep
                ],
                "eliminated_after_observation": list(eliminated),
                "surviving_after": [
                    world_id
                    for world_id, keep in zip(WORLD_IDS, after, strict=True)
                    if keep
                ],
                "layer_b_feature_fingerprint": layer_fingerprint,
            }
        )
        surviving = after
        if not np.any(surviving) and (source_year, target_year) != ALL_TRANSITIONS[-1]:
            raise RuntimeError(
                f"frozen world universe falsified after {source_year}->{target_year}"
            )
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


@dataclass(frozen=True)
class MedianImputer:
    medians: np.ndarray

    def transform(self, values: np.ndarray) -> np.ndarray:
        result = np.asarray(values, dtype=float).copy()
        if result.ndim != 2 or result.shape[1] != self.medians.size:
            raise RuntimeError("imputer input feature shape drift")
        locations = np.where(np.isnan(result))
        result[locations] = self.medians[locations[1]]
        if not np.isfinite(result).all():
            raise RuntimeError("nonfinite predictor remains after frozen median imputation")
        return result


def fit_imputer(values: np.ndarray) -> MedianImputer:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2:
        raise RuntimeError("calibration predictors are not a matrix")
    all_missing = np.all(np.isnan(matrix), axis=0)
    if np.any(all_missing):
        names = [BASELINE_FEATURE_NAMES[index] for index in np.flatnonzero(all_missing)]
        raise RuntimeError(f"all-missing calibration baseline features: {names}")
    medians = np.nanmedian(matrix, axis=0)
    if not np.isfinite(medians).all():
        raise RuntimeError("calibration median imputation produced a nonfinite value")
    return MedianImputer(medians=medians)


def layer_b_estimability(
    imputed_baseline: np.ndarray,
    layer_b: np.ndarray,
) -> dict[str, object]:
    baseline = np.asarray(imputed_baseline, dtype=float)
    layer = np.asarray(layer_b, dtype=float)
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
) -> tuple[dict[str, object], dict[str, object]]:
    calibration = [row for row in rows if row.phase == "calibration"]
    heldout = [row for row in rows if row.phase == "heldout"]
    x_cal_raw = np.asarray([row.baseline for row in calibration], dtype=float)
    layer_cal = np.asarray([row.layer_b for row in calibration], dtype=float)
    y_cal = np.asarray([row.label for row in calibration], dtype=int)
    imputer = fit_imputer(x_cal_raw)
    x_cal = imputer.transform(x_cal_raw)
    estimability = layer_b_estimability(x_cal, layer_cal)
    if not estimability["estimable"]:
        return {"estimability": estimability}, {"status": "layer_b_non_estimable"}

    baseline_model = learner(contract)
    augmented_model = learner(contract)
    baseline_model.fit(x_cal, y_cal)
    augmented_model.fit(np.column_stack((x_cal, layer_cal)), y_cal)

    x_held = imputer.transform(
        np.asarray([row.baseline for row in heldout], dtype=float)
    )
    layer_held = np.asarray([row.layer_b for row in heldout], dtype=float)
    y_held = np.asarray([row.label for row in heldout], dtype=int)
    p_base = baseline_model.predict_proba(x_held)[:, 1]
    p_augmented = augmented_model.predict_proba(
        np.column_stack((x_held, layer_held))
    )[:, 1]

    paired: list[PairedOuterUnitScore] = []
    outer_rows: list[dict[str, object]] = []
    outer_ids = sorted({row.outer_unit_id for row in heldout})
    for outer_id in outer_ids:
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
    result = {
        "models_fit": 2,
        "heldout_scores": 2 * len(paired),
        "imputer": {
            "fit_scope": "calibration rows only",
            "median_count": int(imputer.medians.size),
            "median_fingerprint": canonical_sha256(imputer.medians.tolist()),
        },
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
            "same_learner_hyperparameters_rows_labels_split_and_imputation": True,
        },
    }
    return result, {"status": "completed"}


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
        "outcome_access_gate_fingerprint": preflight["outcome_access_gate"][
            "fingerprint"
        ],
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
            "response_target": "observed_annual_camera_detection_reappearance",
            "response_boundary": (
                "standardized camera-site undetected->detected transition; not latent "
                "occupancy, physical immigration, parentage, or colonization history"
            ),
            "node_count": len(static.node_ids),
            "calibration_transition_count": len(CALIBRATION_TRANSITIONS),
            "heldout_transition_count": len(HELDOUT_TRANSITIONS),
            "static_input_audit": static_audit,
            "exact_site_id_supervised": False,
            "exact_world_id_supervised": False,
        }
    )

    if mode == "smoke":
        synthetic = synthetic_response(static)
        records = None
        response_provenance = {
            "source": "deterministic synthetic technical-control site-year table",
            "response_download_requests": 0,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": False,
            "site_year_cells": int(np.prod(synthetic[0].shape)),
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
        count_gate, state, detection_days = exact_count_gate(
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
        return stopped_result(
            base,
            "non_estimable_exact_count_gate_zero_fit",
            "one or more prospectively frozen exact count requirements failed",
            output,
        )

    try:
        risk_rows, row_audit = build_risk_rows(
            state, detection_days, static, contract
        )
        base["risk_table_audit"] = row_audit
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
        base["status"] = (
            "smoke_pass" if mode == "smoke" else "completed_frozen_paired_test"
        )
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
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
