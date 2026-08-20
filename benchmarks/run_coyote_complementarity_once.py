#!/usr/bin/env python3
"""Frozen paired-complementarity runner for the Chicago coyote candidate.

Smoke mode never opens coyote_detection_data.csv. Outcome mode is permitted only after
all response-blind contracts, runtime identity and the generic outcome-access gate are
frozen. The response target is recorded seasonal camera detection, not latent absence.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.request

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import summarize_worldset_for_prediction

COMMIT = "a068e2aba265551e3b29b1c3ec8c4b1f34eafcdb"
BASE_URL = f"https://raw.githubusercontent.com/mfidino/coyote-mange/{COMMIT}/data"
N = 113
SEASONS = (
    "SP10", "SU10", "FA10", "WI11",
    "SP11", "SU11", "FA11", "WI12",
    "SP12", "SU12", "FA12", "WI13",
    "SP13", "SU13", "FA13", "WI14",
)
TEMPERATURE_F = np.asarray([47, 70, 48, 18, 42, 72, 47, 23, 43, 74, 45, 20, 39, 73, 53, 16], dtype=float)
CALIBRATION_TRANSITIONS = tuple((SEASONS[i], SEASONS[i + 1]) for i in range(10))
HELDOUT_TRANSITIONS = tuple((SEASONS[i], SEASONS[i + 1]) for i in range(10, 15))
SEASON_INDEX = {season: i for i, season in enumerate(SEASONS)}
THRESHOLDS_M = np.asarray(
    [3078.2730548149884, 3618.619211798887, 4792.435393409076, 5230.133937099508],
    dtype=float,
)
LOCAL_SCALE_M = 3618.619211798887
WORLD_IDS = ("geo_lcc250", "geo_lcc500", "geo_lcc750", "geo_lcc900", "geo_exponential_full")
SUPPORT_TOLERANCE = 1e-15
LOSS_SUPPORT = 1.0
EPS = 1e-6
SEED = 20260820

MIN_CAL_EVENTS = 10
MIN_CAL_NON_EVENTS = 40
MIN_HELD_EVENTS = 10
MIN_HELD_NON_EVENTS = 40
MIN_HELD_BOTH = 4

MODEL_COVARIATES_BLOB = "e55380935ab1ea75e24a62d114fa70dd0e26aa59"
COORDINATES_BLOB = "391b6de221f3f827e94bf6d3f8a8050f279c6a8e"
RESPONSE_BLOB = "3ba6cfa50f5b74bdc6532676f7eb475ab0c46523"

ENDPOINT_FINGERPRINT = "48a5bbd1981d42aec28619cfe47af77b80365ef0d720b1365031d0b41b61a86e"
SPLIT_FINGERPRINT = "b6adca431b04f91ace2ceaa2a2df166ef7fe12e17f2cee1723941840c2b2d353"
EXTERNAL_FEATURE_FINGERPRINT = "43db6c215b63943a3f3639c08d86d0606a5fbfb973663b4fd8ea03370251adca"
LEARNER_FINGERPRINT = "b7787b2eedf85c2c1c1e55d6ee9202d4c9b120b94204c215bbf39026ed73d6f9"
EOG_FEATURE_FINGERPRINT = "8d10de705b2b357ee8d8cd587c1d64fb3fb5f48839aec3c131ffe44d56372a6d"

RF_ARGS = dict(
    n_estimators=500,
    max_features="sqrt",
    min_samples_leaf=5,
    class_weight=None,
    random_state=SEED,
    n_jobs=-1,
)


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def download(path: str) -> bytes:
    req = urllib.request.Request(f"{BASE_URL}/{path}", headers={"User-Agent": "eog-coyote-complementarity/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def read_nonresponse_inputs() -> tuple[tuple[str, ...], np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    cov_bytes = download("model_covariates.csv")
    coord_bytes = download("raw_site_coords.csv")
    if git_blob_sha(cov_bytes) != MODEL_COVARIATES_BLOB:
        raise ValueError("model_covariates.csv Git blob mismatch")
    if git_blob_sha(coord_bytes) != COORDINATES_BLOB:
        raise ValueError("raw_site_coords.csv Git blob mismatch")

    cov_reader = csv.DictReader(io.StringIO(cov_bytes.decode("utf-8-sig")))
    coord_reader = csv.DictReader(io.StringIO(coord_bytes.decode("utf-8-sig")))
    if not {"site", "house", "tree", "imp"}.issubset(set(cov_reader.fieldnames or ())):
        raise ValueError("model_covariates.csv schema mismatch")
    if not {"site", "utmEast", "utmNorth"}.issubset(set(coord_reader.fieldnames or ())):
        raise ValueError("raw_site_coords.csv schema mismatch")

    cov_rows = list(cov_reader)
    if len(cov_rows) != N:
        raise ValueError(f"expected {N} model-covariate rows, found {len(cov_rows)}")
    node_ids = tuple(str(row["site"]).strip() for row in cov_rows)
    if any(not value for value in node_ids) or len(set(node_ids)) != N:
        raise ValueError("model-covariate site IDs are empty or duplicated")
    conventional = np.asarray(
        [[float(row["house"]), float(row["tree"]), float(row["imp"])] for row in cov_rows],
        dtype=float,
    )
    if not np.isfinite(conventional).all():
        raise ValueError("model covariates contain non-finite values")

    coords_map: dict[str, tuple[float, float]] = {}
    for row in coord_reader:
        site = str(row["site"]).strip()
        if not site or site in coords_map:
            raise ValueError("coordinate site IDs are empty or duplicated")
        coords_map[site] = (float(row["utmEast"]), float(row["utmNorth"]))
    missing = [site for site in node_ids if site not in coords_map]
    if missing:
        raise ValueError(f"frozen coordinate registry missing node IDs: {missing}")
    coords = np.asarray([coords_map[site] for site in node_ids], dtype=float)
    if not np.isfinite(coords).all():
        raise ValueError("coordinate registry contains non-finite values")
    delta = coords[:, None, :] - coords[None, :, :]
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    np.fill_diagonal(distance, 0.0)
    provenance = {
        "source_commit": COMMIT,
        "model_covariates_git_blob": MODEL_COVARIATES_BLOB,
        "raw_site_coords_git_blob": COORDINATES_BLOB,
        "model_covariates_sha256": hashlib.sha256(cov_bytes).hexdigest(),
        "raw_site_coords_sha256": hashlib.sha256(coord_bytes).hexdigest(),
        "node_count": N,
    }
    return node_ids, conventional, coords, distance, provenance


def parse_coyote_value(text: object) -> int | None:
    value = str(text).strip()
    if not value or value.upper() in {"NA", "NAN"}:
        return None
    number = float(value)
    if number not in (0.0, 1.0):
        raise ValueError(f"Coyote value outside {{0,1,NA}}: {value!r}")
    return int(number)


def read_released_response(node_ids: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    content = download("coyote_detection_data.csv")
    if git_blob_sha(content) != RESPONSE_BLOB:
        raise ValueError("coyote_detection_data.csv Git blob mismatch")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {"Season", "Week", "Date", "SeasonWeek", "StationID", "SurveyID", "IDWeek", "Coyote"}
    if not required.issubset(set(reader.fieldnames or ())):
        raise ValueError(f"coyote response schema mismatch: {reader.fieldnames}")

    node_set = set(node_ids)
    weekly: dict[tuple[str, str, str], list[int | None]] = defaultdict(list)
    selected_rows = 0
    for row in reader:
        site = str(row["StationID"]).strip()
        if site not in node_set:
            continue
        season = str(row["Season"]).strip().upper()
        if season not in SEASON_INDEX:
            raise ValueError(f"unexpected season for frozen node universe: {season!r}")
        week = str(row["Week"]).strip().lower()
        if week not in {"week 1", "week 2", "week 3", "week 4"}:
            raise ValueError(f"unexpected Week value: {week!r}")
        weekly[(site, season, week)].append(parse_coyote_value(row["Coyote"]))
        selected_rows += 1

    node_index = {site: i for i, site in enumerate(node_ids)}
    state = np.full((N, len(SEASONS)), -1, dtype=int)
    effort = np.zeros((N, len(SEASONS)), dtype=int)
    known_week_values: dict[tuple[str, str], list[int]] = defaultdict(list)
    for (site, season, _week), values in weekly.items():
        finite = [value for value in values if value is not None]
        if finite:
            known_week_values[(site, season)].append(max(finite))
    for (site, season), values in known_week_values.items():
        i = node_index[site]
        t = SEASON_INDEX[season]
        effort[i, t] = len(values)
        if effort[i, t] > 4:
            raise ValueError(f"more than four active weeks for {site} {season}")
        state[i, t] = 1 if max(values) == 1 else 0

    return state, effort, {
        "response_git_blob": RESPONSE_BLOB,
        "response_sha256": hashlib.sha256(content).hexdigest(),
        "response_bytes_opened": True,
        "response_rows_opened": True,
        "selected_frozen_node_rows": selected_rows,
        "known_site_seasons": int(np.sum(state >= 0)),
        "missing_site_seasons": int(np.sum(state < 0)),
        "season_order": list(SEASONS),
    }


def synthetic_response(distance: np.ndarray, conventional: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    state = np.full((N, len(SEASONS)), -1, dtype=int)
    effort = rng.integers(2, 5, size=(N, len(SEASONS)), endpoint=False)
    state[:, 0] = (rng.random(N) < 0.42).astype(int)
    if int(np.sum(state[:, 0])) < 20:
        state[:20, 0] = 1
    urban = conventional[:, 0]
    urban = (urban - np.mean(urban)) / max(float(np.std(urban)), 1e-12)
    for t in range(len(SEASONS) - 1):
        current = state[:, t]
        sources = np.flatnonzero(current == 1)
        if sources.size == 0:
            state[0, t] = 1
            sources = np.asarray([0], dtype=int)
        source_distance = distance[sources, :]
        exposure = np.mean(np.exp(-source_distance / LOCAL_SCALE_M), axis=0)
        exposure /= max(float(np.max(exposure)), 1e-12)
        p = np.clip(0.14 + 0.32 * exposure + 0.04 * np.tanh(urban), 0.05, 0.75)
        persist = np.clip(0.62 + 0.16 * exposure, 0.45, 0.9)
        draw = rng.random(N)
        state[:, t + 1] = np.where(current == 1, draw < persist, draw < p).astype(int)
    return state, effort.astype(int)


def compute_world_supports(distance: np.ndarray, source_indices: np.ndarray) -> np.ndarray:
    if source_indices.size == 0:
        raise ValueError("current source set must not be empty")
    source_distance = distance[source_indices, :]
    source_weight = 1.0 / float(source_indices.size)
    exponential = np.exp(-source_distance / LOCAL_SCALE_M)
    supports = np.zeros((len(WORLD_IDS), N), dtype=float)
    for world_index, threshold in enumerate(THRESHOLDS_M):
        raw = exponential * (source_distance <= threshold + 1e-12)
        raw[np.arange(source_indices.size), source_indices] = 0.0
        denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
        supports[world_index, :] = (source_weight / denominator) @ raw
    raw = exponential.copy()
    raw[np.arange(source_indices.size), source_indices] = 0.0
    denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
    supports[-1, :] = (source_weight / denominator) @ raw
    return supports


def make_layer_b_summary(
    node_ids: tuple[str, ...], supports: np.ndarray, surviving: np.ndarray, transition_id: str
):
    members = []
    for index, world_id in enumerate(WORLD_IDS):
        if not bool(surviving[index]):
            continue
        cumulative = np.vstack((np.zeros(N, dtype=float), supports[index]))
        supported = np.vstack((np.zeros(N, dtype=bool), supports[index] > SUPPORT_TOLERANCE))
        members.append(SimpleNamespace(cumulative_reachability=cumulative, supported_state=supported))
    if not members:
        raise ValueError("no surviving worlds remain")
    forecast = SimpleNamespace(
        node_ids=node_ids,
        members=tuple(members),
        max_steps=1,
        gate_declaration=ForecastGateDeclaration(reachability_threshold=SUPPORT_TOLERANCE),
        world_fingerprints=tuple((world_id, f"frozen::{world_id}") for world_id in WORLD_IDS),
        fingerprint=canonical_sha256(
            {
                "transition_id": transition_id,
                "surviving_world_ids": [
                    world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag
                ],
            }
        ),
    )
    return summarize_worldset_for_prediction(forecast, step=1)


def shared_external_features(
    conventional: np.ndarray,
    coords: np.ndarray,
    distance: np.ndarray,
    effort: np.ndarray,
    source_indices: np.ndarray,
    source_t: int,
    target_t: int,
) -> np.ndarray:
    source_distance = distance[source_indices, :]
    exponential = np.exp(-source_distance / LOCAL_SCALE_M)
    counts = [np.sum(source_distance <= threshold + 1e-12, axis=0) for threshold in THRESHOLDS_M]
    exposures = [
        np.sum(exponential * (source_distance <= threshold + 1e-12), axis=0)
        for threshold in THRESHOLDS_M
    ]
    nearest = np.min(source_distance, axis=0)
    full_exposure = np.sum(exponential, axis=0)
    return np.column_stack(
        [
            np.full(N, source_t, dtype=float),
            np.full(N, TEMPERATURE_F[source_t], dtype=float),
            np.full(N, TEMPERATURE_F[target_t], dtype=float),
            conventional[:, 0],
            conventional[:, 1],
            conventional[:, 2],
            coords[:, 0],
            coords[:, 1],
            np.full(N, source_indices.size, dtype=float),
            nearest,
            *counts,
            *exposures,
            full_exposure,
            effort[:, source_t],
            effort[:, target_t],
        ]
    ).astype(float)


def update_rules(supports: np.ndarray, surviving: np.ndarray, positive_indices: np.ndarray):
    after = surviving.copy()
    eliminated: list[str] = []
    if positive_indices.size == 0:
        return after, ()
    for index, world_id in enumerate(WORLD_IDS):
        if after[index] and np.any(supports[index, positive_indices] <= SUPPORT_TOLERANCE):
            after[index] = False
            eliminated.append(world_id)
    return after, tuple(eliminated)


def transition_counts(state: np.ndarray, source_season: str, target_season: str) -> tuple[int, int, int]:
    s = state[:, SEASON_INDEX[source_season]]
    y = state[:, SEASON_INDEX[target_season]]
    sources = int(np.sum(s == 1))
    risk = (s == 0) & (y >= 0)
    events = int(np.sum(risk & (y == 1)))
    non_events = int(np.sum(risk & (y == 0)))
    return sources, events, non_events


def exact_count_gate(state: np.ndarray) -> dict[str, object]:
    cal = [transition_counts(state, *transition) for transition in CALIBRATION_TRANSITIONS]
    held = [transition_counts(state, *transition) for transition in HELDOUT_TRANSITIONS]
    all_sources = all(row[0] > 0 for row in cal + held)
    cal_events = sum(row[1] for row in cal)
    cal_non_events = sum(row[2] for row in cal)
    held_events = sum(row[1] for row in held)
    held_non_events = sum(row[2] for row in held)
    held_both = sum(int(row[1] > 0 and row[2] > 0) for row in held)
    passed = bool(
        all_sources
        and cal_events >= MIN_CAL_EVENTS
        and cal_non_events >= MIN_CAL_NON_EVENTS
        and held_events >= MIN_HELD_EVENTS
        and held_non_events >= MIN_HELD_NON_EVENTS
        and held_both >= MIN_HELD_BOTH
    )
    return {
        "passed": passed,
        "all_transitions_have_current_sources": all_sources,
        "calibration_events": cal_events,
        "calibration_non_events": cal_non_events,
        "heldout_events": held_events,
        "heldout_non_events": held_non_events,
        "heldout_outer_units_with_both_classes": held_both,
        "minimums": {
            "calibration_events": MIN_CAL_EVENTS,
            "calibration_non_events": MIN_CAL_NON_EVENTS,
            "heldout_events": MIN_HELD_EVENTS,
            "heldout_non_events": MIN_HELD_NON_EVENTS,
            "heldout_outer_units_with_both_classes": MIN_HELD_BOTH,
        },
    }


@dataclass
class TransitionDesign:
    source_season: str
    target_season: str
    risk_indices: np.ndarray
    y: np.ndarray
    baseline: np.ndarray
    layer_b: np.ndarray
    supports: np.ndarray
    source_count: int
    positive_count: int
    negative_count: int
    surviving_before: tuple[str, ...]
    layer_b_feature_fingerprint: str


def build_transition(
    node_ids: tuple[str, ...],
    conventional: np.ndarray,
    coords: np.ndarray,
    distance: np.ndarray,
    state: np.ndarray,
    effort: np.ndarray,
    surviving: np.ndarray,
    source_season: str,
    target_season: str,
) -> TransitionDesign:
    source_t = SEASON_INDEX[source_season]
    target_t = SEASON_INDEX[target_season]
    source_state = state[:, source_t]
    target_state = state[:, target_t]
    source_indices = np.flatnonzero(source_state == 1)
    if source_indices.size == 0:
        raise ValueError(f"no current sources for {source_season}->{target_season}")
    risk_indices = np.flatnonzero((source_state == 0) & (target_state >= 0))
    y = target_state[risk_indices].astype(int)
    supports = compute_world_supports(distance, source_indices)
    summary = make_layer_b_summary(
        node_ids, supports, surviving, f"{source_season}_to_{target_season}"
    )
    baseline_all = shared_external_features(
        conventional, coords, distance, effort, source_indices, source_t, target_t
    )
    return TransitionDesign(
        source_season=source_season,
        target_season=target_season,
        risk_indices=risk_indices,
        y=y,
        baseline=baseline_all[risk_indices],
        layer_b=summary.feature_matrix[risk_indices],
        supports=supports,
        source_count=int(source_indices.size),
        positive_count=int(np.sum(y == 1)),
        negative_count=int(np.sum(y == 0)),
        surviving_before=tuple(
            world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag
        ),
        layer_b_feature_fingerprint=summary.feature_fingerprint,
    )


def metrics(y: np.ndarray, probability: np.ndarray) -> dict[str, float | None]:
    truth = np.asarray(y, dtype=int)
    prob = np.clip(np.asarray(probability, dtype=float), EPS, 1.0 - EPS)
    result: dict[str, float | None] = {
        "logloss": float(log_loss(truth, prob, labels=[0, 1])),
        "brier": float(brier_score_loss(truth, prob)),
        "auc": None,
        "average_precision": None,
    }
    if len(np.unique(truth)) == 2:
        result["auc"] = float(roc_auc_score(truth, prob))
        result["average_precision"] = float(average_precision_score(truth, prob))
    return result


def write_result(path: Path, payload: dict[str, object]) -> None:
    payload["fingerprint"] = canonical_sha256(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_analysis(
    node_ids: tuple[str, ...],
    conventional: np.ndarray,
    coords: np.ndarray,
    distance: np.ndarray,
    state: np.ndarray,
    effort: np.ndarray,
    *,
    mode: str,
    nonresponse_provenance: dict[str, object],
    response_provenance: dict[str, object],
    output: Path,
) -> dict[str, object]:
    count_gate = exact_count_gate(state)
    base: dict[str, object] = {
        "execution_mode": mode,
        "status": "pre_model",
        "response_target": "recorded_seasonal_coyote_reappearance",
        "response_boundary": "recorded camera detection transition; not latent biological colonisation/absence",
        "node_count": N,
        "season_order": list(SEASONS),
        "calibration_transitions": [list(row) for row in CALIBRATION_TRANSITIONS],
        "heldout_transitions": [list(row) for row in HELDOUT_TRANSITIONS],
        "world_ids": list(WORLD_IDS),
        "thresholds_m": THRESHOLDS_M.tolist(),
        "local_scale_m": LOCAL_SCALE_M,
        "nonresponse_provenance": nonresponse_provenance,
        "response_provenance": response_provenance,
        "exact_count_gate": count_gate,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    if not count_gate["passed"]:
        base.update({"status": "non_estimable_response_balance", "complementarity_status": "non_estimable"})
        write_result(output, base)
        return base

    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    calibration: list[TransitionDesign] = []
    history: list[dict[str, object]] = []
    for source_season, target_season in CALIBRATION_TRANSITIONS:
        design = build_transition(
            node_ids, conventional, coords, distance, state, effort, surviving, source_season, target_season
        )
        calibration.append(design)
        after, eliminated = update_rules(
            design.supports, surviving, design.risk_indices[design.y == 1]
        )
        history.append(
            {
                "transition": [source_season, target_season],
                "phase": "calibration",
                "source_count": design.source_count,
                "events": design.positive_count,
                "non_events": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": [
                    world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag
                ],
                "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
            }
        )
        surviving = after
        if not np.any(surviving):
            base.update(
                {
                    "status": "universe_falsified_during_calibration",
                    "complementarity_status": "non_estimable",
                    "rule_history": history,
                }
            )
            write_result(output, base)
            return base

    cal_y = np.concatenate([row.y for row in calibration])
    cal_external = np.concatenate([row.baseline for row in calibration], axis=0)
    cal_layer_b = np.concatenate([row.layer_b for row in calibration], axis=0)
    baseline_rf = RandomForestClassifier(**RF_ARGS)
    augmented_rf = RandomForestClassifier(**RF_ARGS)
    baseline_rf.fit(cal_external, cal_y)
    augmented_rf.fit(np.column_stack([cal_external, cal_layer_b]), cal_y)
    base["models_fit"] = 2

    annual: list[dict[str, object]] = []
    paired: list[PairedOuterUnitScore] = []
    pooled_y: list[np.ndarray] = []
    pooled_baseline: list[np.ndarray] = []
    pooled_augmented: list[np.ndarray] = []

    for source_season, target_season in HELDOUT_TRANSITIONS:
        design = build_transition(
            node_ids, conventional, coords, distance, state, effort, surviving, source_season, target_season
        )
        baseline_prob = baseline_rf.predict_proba(design.baseline)[:, 1]
        augmented_prob = augmented_rf.predict_proba(
            np.column_stack([design.baseline, design.layer_b])
        )[:, 1]
        baseline_metrics = metrics(design.y, baseline_prob)
        augmented_metrics = metrics(design.y, augmented_prob)
        transition_id = f"{source_season}->{target_season}"
        paired.append(
            PairedOuterUnitScore(
                outer_unit_id=transition_id,
                baseline_score=float(baseline_metrics["logloss"]),
                augmented_score=float(augmented_metrics["logloss"]),
            )
        )
        base["heldout_scores"] = int(base["heldout_scores"]) + 2
        row: dict[str, object] = {
            "transition": [source_season, target_season],
            "source_count": design.source_count,
            "events": design.positive_count,
            "non_events": design.negative_count,
            "surviving_before": list(design.surviving_before),
            "baseline_rf": baseline_metrics,
            "augmented_rf_plus_layer_b": augmented_metrics,
            "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
        }
        pooled_y.append(design.y)
        pooled_baseline.append(baseline_prob)
        pooled_augmented.append(augmented_prob)

        after, eliminated = update_rules(
            design.supports, surviving, design.risk_indices[design.y == 1]
        )
        row["eliminated_after_observation"] = list(eliminated)
        row["surviving_after"] = [
            world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag
        ]
        history.append(
            {
                "transition": [source_season, target_season],
                "phase": "heldout",
                "source_count": design.source_count,
                "events": design.positive_count,
                "non_events": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": row["surviving_after"],
                "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
            }
        )
        annual.append(row)
        surviving = after
        if not np.any(surviving) and (source_season, target_season) != HELDOUT_TRANSITIONS[-1]:
            base.update(
                {
                    "status": "universe_falsified_during_heldout",
                    "complementarity_status": "non_estimable",
                    "rule_history": history,
                    "heldout_metrics": annual,
                }
            )
            write_result(output, base)
            return base

    declaration = PredictiveComplementarityDeclaration(
        metric_name="log_loss",
        lower_is_better=True,
        expected_outer_unit_count=5,
        favorable_min_augmented_wins=3,
        adverse_min_baseline_wins=3,
        learner_fit_fingerprint=LEARNER_FINGERPRINT,
        response_endpoint_fingerprint=ENDPOINT_FINGERPRINT,
        split_fingerprint=SPLIT_FINGERPRINT,
        external_feature_fingerprint=EXTERNAL_FEATURE_FINGERPRINT,
        eog_feature_fingerprint=EOG_FEATURE_FINGERPRINT,
    )
    complementarity = evaluate_predictive_complementarity(declaration, paired, tie_tolerance=0.0)
    all_y = np.concatenate(pooled_y)
    pooled = {
        "baseline_rf": metrics(all_y, np.concatenate(pooled_baseline)),
        "augmented_rf_plus_layer_b": metrics(all_y, np.concatenate(pooled_augmented)),
    }
    base.update(
        {
            "status": "smoke_pass" if mode == "smoke" else "completed_frozen_paired_complementarity_test",
            "rule_history": history,
            "heldout_metrics": annual,
            "pooled_metrics": pooled,
            "complementarity_status": complementarity.status,
            "complementarity": {
                "metric_name": complementarity.metric_name,
                "outer_unit_count": complementarity.outer_unit_count,
                "baseline_macro_score": complementarity.baseline_macro_score,
                "augmented_macro_score": complementarity.augmented_macro_score,
                "augmented_minus_baseline": complementarity.augmented_minus_baseline,
                "augmented_better_outer_units": complementarity.augmented_better_outer_units,
                "baseline_better_outer_units": complementarity.baseline_better_outer_units,
                "tied_outer_units": complementarity.tied_outer_units,
                "declaration_fingerprint": complementarity.declaration_fingerprint,
                "paired_score_fingerprint": complementarity.paired_score_fingerprint,
                "fingerprint": complementarity.fingerprint,
            },
            "final_surviving_world_ids": [
                world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag
            ],
        }
    )
    write_result(output, base)
    return base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "outcome"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, conventional, coords, distance, nonresponse = read_nonresponse_inputs()
    if args.mode == "smoke":
        state, effort = synthetic_response(distance, conventional)
        response = {
            "source": "deterministic synthetic technical-control state/effort matrices",
            "response_bytes_opened": False,
            "response_rows_opened": False,
        }
    else:
        state, effort, response = read_released_response(node_ids)

    result = run_analysis(
        node_ids,
        conventional,
        coords,
        distance,
        state,
        effort,
        mode=args.mode,
        nonresponse_provenance=nonresponse,
        response_provenance=response,
        output=args.output,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "models_fit": result.get("models_fit", 0),
                "heldout_scores": result.get("heldout_scores", 0),
                "complementarity_status": result.get("complementarity_status"),
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
