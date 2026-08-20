#!/usr/bin/env python3
"""Frozen two-layer EOG-WF runner for the Tvärminne Daphnia candidate.

Smoke mode never downloads data_M.csv. Outcome mode is intended for one authorized
execution only, after the response-blind freeze ledger is complete. The prediction
target is the released annual D. magna occupancy code, not latent biological absence.
"""
from __future__ import annotations

import argparse
import binascii
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import urllib.request
import zlib

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)

from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import summarize_worldset_for_prediction

ZIP_URL = "https://ndownloader.figshare.com/files/36330951"
ZIP_MD5 = "012431094673144b28f056210a516f63"
UA = "eog-daphnia-frozen-runner/1.0"
N = 546
YEARS = tuple(range(1982, 2018))
CALIBRATION_TRANSITIONS = tuple((year, year + 1) for year in range(1982, 2006))
HELDOUT_TRANSITIONS = tuple((year, year + 1) for year in range(2006, 2017))
THRESHOLDS = np.asarray(
    [0.22151186379051, 0.274502525748238, 0.284129344781106, 0.364920914083473],
    dtype=float,
)
LOCAL_SCALE = 0.274502525748238
WORLD_IDS = (
    "geo_lcc250",
    "geo_lcc500",
    "geo_lcc750",
    "geo_lcc900",
    "geo_exponential_full",
)
SUPPORT_TOLERANCE = 1e-15
LOSS_SUPPORT = 1.0
SEED = 20260820
EPS = 1e-6

MIN_CAL_EVENTS = 10
MIN_CAL_NON_EVENTS = 40
MIN_HELD_EVENTS = 10
MIN_HELD_NON_EVENTS = 40
MIN_HELD_BOTH = 8

MEMBERS = {
    "A": {
        "name": "code_SpatialCoex/Bayesian model fitting/A.csv",
        "offset": 70,
        "compressed_size": 2603,
        "uncompressed_size": 6669,
        "crc32": "08470def",
        "sha256": "3134ec64abc5a285069a27752a8aae7a7d881144d94d7e003d66d99005abf8b0",
    },
    "distance": {
        "name": "code_SpatialCoex/Bayesian model fitting/distance.csv",
        "offset": 9093,
        "compressed_size": 2362738,
        "uncompressed_size": 5235396,
        "crc32": "f5f840c0",
        "sha256": "4ffb62d36b808b18fb999aa1f585e1987d0df76e289543ef43941f2e3037b750",
    },
    "temperature": {
        "name": "code_SpatialCoex/Bayesian model fitting/tem.csv",
        "offset": 2374199,
        "compressed_size": 196,
        "uncompressed_size": 454,
        "crc32": "6b1484de",
        "sha256": None,
    },
    "response": {
        "name": "code_SpatialCoex/Bayesian model fitting/data_M.csv",
        "offset": 5084,
        "compressed_size": 2523,
        "uncompressed_size": 40111,
        "crc32": "aa2c0d97",
        "sha256": None,
    },
}


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def range_get(start: int, end: int) -> bytes:
    req = urllib.request.Request(
        ZIP_URL,
        headers={"User-Agent": UA, "Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        status = getattr(response, "status", None) or response.getcode()
        if status != 206:
            raise RuntimeError(f"range request returned HTTP {status}, expected 206")
        body = response.read()
    if len(body) != end - start + 1:
        raise RuntimeError("range response length mismatch")
    return body


def extract_member(spec: dict[str, object]) -> bytes:
    offset = int(spec["offset"])
    fixed = range_get(offset, offset + 29)
    fields = struct.unpack("<4s5H3I2H", fixed)
    if fields[0] != b"PK\x03\x04":
        raise RuntimeError(f"invalid local ZIP header for {spec['name']}")
    method = fields[3]
    name_len, extra_len = fields[9], fields[10]
    raw_name = range_get(offset + 30, offset + 30 + name_len - 1)
    name = raw_name.decode("utf-8", errors="replace")
    if name != spec["name"]:
        raise RuntimeError(f"member name mismatch: {name!r} != {spec['name']!r}")
    data_start = offset + 30 + name_len + extra_len
    compressed_size = int(spec["compressed_size"])
    compressed = range_get(data_start, data_start + compressed_size - 1)
    if method == 8:
        content = zlib.decompress(compressed, -15)
    elif method == 0:
        content = compressed
    else:
        raise RuntimeError(f"unsupported ZIP compression method {method} for {name}")
    if len(content) != int(spec["uncompressed_size"]):
        raise RuntimeError(f"uncompressed-size mismatch for {name}")
    crc = f"{binascii.crc32(content) & 0xffffffff:08x}"
    if crc != spec["crc32"]:
        raise RuntimeError(f"CRC mismatch for {name}: {crc} != {spec['crc32']}")
    sha = hashlib.sha256(content).hexdigest()
    expected_sha = spec.get("sha256")
    if expected_sha and sha != expected_sha:
        raise RuntimeError(f"SHA-256 mismatch for {name}: {sha} != {expected_sha}")
    return content


def numeric_csv(content: bytes) -> tuple[np.ndarray, tuple[int, ...]]:
    raw = np.genfromtxt(io.StringIO(content.decode("utf-8-sig")), delimiter=",", dtype=float)
    raw = np.asarray(raw, dtype=float)
    if raw.ndim == 0:
        raw = raw.reshape(1, 1)
    elif raw.ndim == 1:
        raw = raw.reshape(-1, 1)
    original_shape = tuple(int(value) for value in raw.shape)
    keep_rows = ~np.all(~np.isfinite(raw), axis=1)
    keep_cols = ~np.all(~np.isfinite(raw), axis=0)
    return raw[keep_rows][:, keep_cols], original_shape


def sequential_labels(values: np.ndarray, start: int) -> bool:
    expected = np.arange(start, start + len(values), dtype=float)
    return bool(np.isfinite(values).all() and np.allclose(values, expected, atol=1e-9, rtol=0.0))


def read_nonresponse_inputs() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, object]]:
    a_bytes = extract_member(MEMBERS["A"])
    d_bytes = extract_member(MEMBERS["distance"])
    t_bytes = extract_member(MEMBERS["temperature"])

    a_raw, a_shape = numeric_csv(a_bytes)
    if a_raw.shape == (N, 1):
        patch_size = a_raw[:, 0]
    elif a_raw.shape == (N, 2) and sequential_labels(a_raw[:, 0], 1):
        patch_size = a_raw[:, 1]
    else:
        raise RuntimeError(f"A.csv schema mismatch after header removal: {a_raw.shape}")
    if not np.isfinite(patch_size).all() or np.any(patch_size <= 0):
        raise RuntimeError("A.csv contains non-finite or non-positive patch sizes")

    distance, d_shape = numeric_csv(d_bytes)
    if distance.shape == (N, N + 1) and sequential_labels(distance[:, 0], 1):
        distance = distance[:, 1:]
    elif distance.shape == (N + 1, N) and sequential_labels(distance[0, :], 1):
        distance = distance[1:, :]
    elif distance.shape == (N + 1, N + 1):
        if sequential_labels(distance[1:, 0], 1) and sequential_labels(distance[0, 1:], 1):
            distance = distance[1:, 1:]
    if distance.shape != (N, N):
        raise RuntimeError(f"distance.csv schema mismatch after header removal: {distance.shape}")
    if not np.isfinite(distance).all() or np.any(distance < -1e-12):
        raise RuntimeError("distance.csv contains invalid values")
    if not np.allclose(distance, distance.T, atol=1e-9, rtol=1e-9):
        raise RuntimeError("distance.csv is not symmetric")
    if not np.allclose(np.diag(distance), 0.0, atol=1e-9, rtol=0.0):
        raise RuntimeError("distance.csv diagonal is not zero")

    temp_raw, t_shape = numeric_csv(t_bytes)
    if temp_raw.shape == (len(YEARS), 1):
        temperature = temp_raw[:, 0]
    elif temp_raw.shape == (1, len(YEARS)):
        temperature = temp_raw[0, :]
    elif temp_raw.shape == (len(YEARS), 2) and sequential_labels(temp_raw[:, 0], YEARS[0]):
        temperature = temp_raw[:, 1]
    else:
        raise RuntimeError(f"tem.csv schema mismatch after header removal: {temp_raw.shape}")
    if not np.isfinite(temperature).all():
        raise RuntimeError("tem.csv contains non-finite values")

    provenance = {
        "zip_md5": ZIP_MD5,
        "A_sha256": hashlib.sha256(a_bytes).hexdigest(),
        "distance_sha256": hashlib.sha256(d_bytes).hexdigest(),
        "temperature_sha256": hashlib.sha256(t_bytes).hexdigest(),
        "A_raw_numeric_shape": list(a_shape),
        "distance_raw_numeric_shape": list(d_shape),
        "temperature_raw_numeric_shape": list(t_shape),
    }
    return patch_size.astype(float), distance.astype(float), temperature.astype(float), provenance


def read_released_response() -> tuple[np.ndarray, dict[str, object]]:
    content = extract_member(MEMBERS["response"])
    values, raw_shape = numeric_csv(content)
    if values.shape == (N, len(YEARS) + 1) and sequential_labels(values[:, 0], 1):
        values = values[:, 1:]
    if values.shape != (N, len(YEARS)):
        raise RuntimeError(
            f"data_M.csv must resolve to {N}x{len(YEARS)}, got {values.shape} from raw {raw_shape}"
        )
    finite = values[np.isfinite(values)]
    if finite.size == 0 or np.any((finite != 0.0) & (finite != 1.0)):
        raise RuntimeError("data_M.csv contains values outside {0,1,missing}")
    missing_count = int(np.sum(~np.isfinite(values)))
    released = np.nan_to_num(values, nan=0.0).astype(int)
    return released, {
        "response_sha256": hashlib.sha256(content).hexdigest(),
        "response_crc32": MEMBERS["response"]["crc32"],
        "raw_numeric_shape": list(raw_shape),
        "normalized_shape": list(released.shape),
        "explicit_missing_values_zero_imputed_per_paper": missing_count,
        "response_member_bytes_downloaded": True,
    }


def synthetic_response(distance: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    occupancy = np.zeros((N, len(YEARS)), dtype=int)
    occupancy[:, 0] = (rng.random(N) < 0.12).astype(int)
    if int(np.sum(occupancy[:, 0])) < 20:
        occupancy[:20, 0] = 1
    for step in range(len(YEARS) - 1):
        current = occupancy[:, step]
        sources = np.flatnonzero(current == 1)
        if sources.size == 0:
            sources = np.asarray([0], dtype=int)
            current[0] = 1
        source_distance = distance[sources, :]
        exposure = np.mean(np.exp(-source_distance / LOCAL_SCALE), axis=0)
        scale = exposure / max(float(np.max(exposure)), 1e-12)
        colon_prob = np.clip(0.04 + 0.22 * scale, 0.04, 0.28)
        persist_prob = np.clip(0.86 - 0.05 * step / (len(YEARS) - 1), 0.75, 0.9)
        draw = rng.random(N)
        occupancy[:, step + 1] = np.where(
            current == 1,
            draw < persist_prob,
            draw < colon_prob,
        ).astype(int)
    return occupancy


def compute_world_supports(distance: np.ndarray, source_indices: np.ndarray) -> np.ndarray:
    if source_indices.size == 0:
        raise ValueError("current source set must not be empty")
    source_distance = distance[source_indices, :]
    source_weight = 1.0 / float(source_indices.size)
    exponential = np.exp(-source_distance / LOCAL_SCALE)
    supports = np.zeros((len(WORLD_IDS), N), dtype=float)
    for world_index, threshold in enumerate(THRESHOLDS):
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
    node_ids: tuple[str, ...],
    supports: np.ndarray,
    surviving: np.ndarray,
    transition_id: str,
):
    members = []
    for index, world_id in enumerate(WORLD_IDS):
        if not bool(surviving[index]):
            continue
        cumulative = np.vstack((np.zeros(N, dtype=float), supports[index]))
        supported = np.vstack((np.zeros(N, dtype=bool), supports[index] > SUPPORT_TOLERANCE))
        members.append(SimpleNamespace(cumulative_reachability=cumulative, supported_state=supported))
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


def shared_baseline(
    patch_size: np.ndarray,
    distance: np.ndarray,
    temperature: np.ndarray,
    source_indices: np.ndarray,
    source_year: int,
) -> np.ndarray:
    source_distance = distance[source_indices, :]
    source_area = patch_size[source_indices, None]
    exponential = np.exp(-source_distance / LOCAL_SCALE)
    counts = [np.sum(source_distance <= threshold + 1e-12, axis=0) for threshold in THRESHOLDS]
    exposures = [
        np.sum(source_area * exponential * (source_distance <= threshold + 1e-12), axis=0)
        for threshold in THRESHOLDS
    ]
    full_exposure = np.sum(source_area * exponential, axis=0)
    nearest = np.min(source_distance, axis=0)
    year_index = source_year - YEARS[0]
    return np.column_stack(
        [
            np.full(N, year_index, dtype=float),
            np.full(N, temperature[year_index], dtype=float),
            np.log(patch_size),
            np.full(N, source_indices.size, dtype=float),
            nearest,
            *counts,
            *exposures,
            full_exposure,
        ]
    ).astype(float)


def update_rules(
    supports: np.ndarray,
    surviving: np.ndarray,
    positive_indices: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    after = surviving.copy()
    eliminated: list[str] = []
    if positive_indices.size == 0:
        return after, ()
    for index, world_id in enumerate(WORLD_IDS):
        if after[index] and np.any(supports[index, positive_indices] <= SUPPORT_TOLERANCE):
            after[index] = False
            eliminated.append(world_id)
    return after, tuple(eliminated)


def transition_counts(occupancy: np.ndarray, source_year: int, target_year: int) -> tuple[int, int, int]:
    s = occupancy[:, source_year - YEARS[0]]
    y = occupancy[:, target_year - YEARS[0]]
    sources = int(np.sum(s == 1))
    risk = s == 0
    events = int(np.sum(risk & (y == 1)))
    non_events = int(np.sum(risk & (y == 0)))
    return sources, events, non_events


def exact_count_gate(occupancy: np.ndarray) -> dict[str, object]:
    calibration_rows = [transition_counts(occupancy, *transition) for transition in CALIBRATION_TRANSITIONS]
    heldout_rows = [transition_counts(occupancy, *transition) for transition in HELDOUT_TRANSITIONS]
    all_sources_positive = all(row[0] > 0 for row in calibration_rows + heldout_rows)
    cal_events = sum(row[1] for row in calibration_rows)
    cal_non_events = sum(row[2] for row in calibration_rows)
    held_events = sum(row[1] for row in heldout_rows)
    held_non_events = sum(row[2] for row in heldout_rows)
    held_both = sum(int(row[1] > 0 and row[2] > 0) for row in heldout_rows)
    passed = bool(
        all_sources_positive
        and cal_events >= MIN_CAL_EVENTS
        and cal_non_events >= MIN_CAL_NON_EVENTS
        and held_events >= MIN_HELD_EVENTS
        and held_non_events >= MIN_HELD_NON_EVENTS
        and held_both >= MIN_HELD_BOTH
    )
    return {
        "passed": passed,
        "all_transitions_have_current_sources": all_sources_positive,
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
    source_year: int
    target_year: int
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
    patch_size: np.ndarray,
    distance: np.ndarray,
    temperature: np.ndarray,
    occupancy: np.ndarray,
    surviving: np.ndarray,
    source_year: int,
    target_year: int,
) -> TransitionDesign:
    source_state = occupancy[:, source_year - YEARS[0]]
    target_state = occupancy[:, target_year - YEARS[0]]
    source_indices = np.flatnonzero(source_state == 1)
    if source_indices.size == 0:
        raise ValueError(f"no current sources for {source_year}->{target_year}")
    risk_indices = np.flatnonzero(source_state == 0)
    y = target_state[risk_indices].astype(int)
    supports = compute_world_supports(distance, source_indices)
    summary = make_layer_b_summary(
        node_ids,
        supports,
        surviving,
        transition_id=f"{source_year}_to_{target_year}",
    )
    baseline_all = shared_baseline(patch_size, distance, temperature, source_indices, source_year)
    return TransitionDesign(
        source_year=source_year,
        target_year=target_year,
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


@dataclass
class LogisticFit:
    model: LogisticRegression
    keep: np.ndarray
    mean: np.ndarray
    sd: np.ndarray

    def predict(self, values: np.ndarray) -> np.ndarray:
        x = np.asarray(values, dtype=float)[:, self.keep]
        z = (x - self.mean) / self.sd
        return self.model.predict_proba(z)[:, 1]


def fit_logistic(x: np.ndarray, y: np.ndarray) -> LogisticFit:
    values = np.asarray(x, dtype=float)
    sd_full = np.std(values, axis=0, ddof=0)
    keep = np.flatnonzero(sd_full > 1e-12)
    if keep.size == 0:
        raise ValueError("all logistic features are constant")
    kept = values[:, keep]
    mean = np.mean(kept, axis=0)
    sd = np.std(kept, axis=0, ddof=0)
    model = LogisticRegression(
        C=1.0,
        penalty="l2",
        solver="lbfgs",
        max_iter=3000,
        class_weight=None,
        random_state=SEED,
    )
    model.fit((kept - mean) / sd, np.asarray(y, dtype=int))
    return LogisticFit(model=model, keep=keep, mean=mean, sd=sd)


def layer_b_estimability(baseline: np.ndarray, layer_b: np.ndarray) -> dict[str, object]:
    base = np.column_stack([baseline, layer_b[:, :2]])
    base_sd = np.std(base, axis=0, ddof=0)
    base_keep = np.flatnonzero(base_sd > 1e-12)
    if base_keep.size:
        x = base[:, base_keep]
        x = (x - np.mean(x, axis=0)) / np.std(x, axis=0, ddof=0)
        design = np.column_stack([np.ones(len(x)), x])
    else:
        design = np.ones((len(base), 1), dtype=float)
    residuals: list[float] = []
    retained: list[int] = []
    for index in range(2, layer_b.shape[1]):
        values = layer_b[:, index]
        sd = float(np.std(values, ddof=0))
        if sd <= 1e-12:
            continue
        retained.append(index)
        z = (values - np.mean(values)) / sd
        beta, *_ = np.linalg.lstsq(design, z, rcond=None)
        residuals.append(float(np.std(z - design @ beta, ddof=0)))
    maximum = max(residuals, default=0.0)
    return {
        "estimable": bool(maximum > 1e-8),
        "retained_extra_layer_b_columns": retained,
        "residual_sd": residuals,
        "max_residual_sd": maximum,
    }


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float | None]:
    truth = np.asarray(y, dtype=int)
    prob = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
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


def write_result(output: Path, payload: dict[str, object]) -> None:
    payload["fingerprint"] = canonical_sha256(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_analysis(
    occupancy: np.ndarray,
    patch_size: np.ndarray,
    distance: np.ndarray,
    temperature: np.ndarray,
    *,
    mode: str,
    provenance: dict[str, object],
    response_provenance: dict[str, object],
    output: Path,
) -> dict[str, object]:
    count_gate = exact_count_gate(occupancy)
    base_result: dict[str, object] = {
        "execution_mode": mode,
        "status": "pre_model",
        "response_target": "released_annual_daphnia_magna_recolonisation",
        "response_boundary": "released annual 0/1 endpoint; zero is not latent biological absence",
        "node_count": N,
        "years": [YEARS[0], YEARS[-1]],
        "calibration_transition_count": len(CALIBRATION_TRANSITIONS),
        "heldout_transition_count": len(HELDOUT_TRANSITIONS),
        "world_ids": list(WORLD_IDS),
        "thresholds_released_units": THRESHOLDS.tolist(),
        "local_scale_released_units": LOCAL_SCALE,
        "nonresponse_provenance": provenance,
        "response_provenance": response_provenance,
        "exact_count_gate": count_gate,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    if not count_gate["passed"]:
        base_result.update(
            {
                "status": "non_estimable_response_balance",
                "layer_b_predictive_status": "non_estimable",
                "external_predictive_status": "non_estimable",
            }
        )
        write_result(output, base_result)
        return base_result

    node_ids = tuple(f"pool_{i+1:03d}" for i in range(N))
    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    calibration: list[TransitionDesign] = []
    history: list[dict[str, object]] = []

    for source_year, target_year in CALIBRATION_TRANSITIONS:
        design = build_transition(
            node_ids,
            patch_size,
            distance,
            temperature,
            occupancy,
            surviving,
            source_year,
            target_year,
        )
        calibration.append(design)
        positive_indices = design.risk_indices[design.y == 1]
        after, eliminated = update_rules(design.supports, surviving, positive_indices)
        history.append(
            {
                "transition": [source_year, target_year],
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
            base_result.update(
                {
                    "status": "universe_falsified_during_calibration",
                    "rule_history": history,
                    "layer_b_predictive_status": "non_estimable",
                    "external_predictive_status": "non_estimable",
                }
            )
            write_result(output, base_result)
            return base_result

    cal_y = np.concatenate([row.y for row in calibration])
    cal_baseline = np.concatenate([row.baseline for row in calibration], axis=0)
    cal_layer_b = np.concatenate([row.layer_b for row in calibration], axis=0)
    rep = layer_b_estimability(cal_baseline, cal_layer_b)
    base_result["layer_b_estimability"] = rep
    base_result["rule_history"] = history
    if not rep["estimable"]:
        base_result.update(
            {
                "status": "layer_b_non_estimable_beyond_mean_only",
                "layer_b_predictive_status": "non_estimable",
                "external_predictive_status": "non_estimable",
            }
        )
        write_result(output, base_result)
        return base_result

    x_external = cal_baseline
    x_mean = np.column_stack([cal_baseline, cal_layer_b[:, :2]])
    x_layer_b = np.column_stack([cal_baseline, cal_layer_b])
    external_logistic = fit_logistic(x_external, cal_y)
    mean_fit = fit_logistic(x_mean, cal_y)
    layer_b_fit = fit_logistic(x_layer_b, cal_y)
    rf = RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        min_samples_leaf=5,
        class_weight=None,
        random_state=SEED,
        n_jobs=-1,
    )
    rf.fit(x_external, cal_y)
    base_result["models_fit"] = 4

    annual: list[dict[str, object]] = []
    pooled_y: list[np.ndarray] = []
    pooled_predictions: dict[str, list[np.ndarray]] = {
        "geometry_process_logistic": [],
        "geometry_process_rf": [],
        "mean_only": [],
        "layer_b": [],
    }

    for source_year, target_year in HELDOUT_TRANSITIONS:
        design = build_transition(
            node_ids,
            patch_size,
            distance,
            temperature,
            occupancy,
            surviving,
            source_year,
            target_year,
        )
        x_mean_year = np.column_stack([design.baseline, design.layer_b[:, :2]])
        x_layer_year = np.column_stack([design.baseline, design.layer_b])
        predictions = {
            "geometry_process_logistic": external_logistic.predict(design.baseline),
            "geometry_process_rf": rf.predict_proba(design.baseline)[:, 1],
            "mean_only": mean_fit.predict(x_mean_year),
            "layer_b": layer_b_fit.predict(x_layer_year),
        }
        row: dict[str, object] = {
            "transition": [source_year, target_year],
            "source_count": design.source_count,
            "events": design.positive_count,
            "non_events": design.negative_count,
            "surviving_before": list(design.surviving_before),
            "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
        }
        for name, prediction in predictions.items():
            row[name] = metrics(design.y, prediction)
            pooled_predictions[name].append(prediction)
        pooled_y.append(design.y)
        base_result["heldout_scores"] = int(base_result["heldout_scores"]) + len(predictions)

        after, eliminated = update_rules(
            design.supports,
            surviving,
            design.risk_indices[design.y == 1],
        )
        row["eliminated_after_observation"] = list(eliminated)
        row["surviving_after"] = [
            world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag
        ]
        history.append(
            {
                "transition": [source_year, target_year],
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
        if not np.any(surviving) and (source_year, target_year) != HELDOUT_TRANSITIONS[-1]:
            base_result.update(
                {
                    "status": "universe_falsified_during_heldout",
                    "rule_history": history,
                    "annual_metrics": annual,
                    "layer_b_predictive_status": "non_estimable",
                    "external_predictive_status": "non_estimable",
                }
            )
            write_result(output, base_result)
            return base_result

    all_y = np.concatenate(pooled_y)
    pooled = {
        name: metrics(all_y, np.concatenate(parts))
        for name, parts in pooled_predictions.items()
    }
    macro = {
        name: float(np.mean([float(row[name]["logloss"]) for row in annual]))
        for name in pooled_predictions
    }
    layer_delta = float(macro["layer_b"] - macro["mean_only"])
    layer_better = int(
        sum(float(row["layer_b"]["logloss"]) < float(row["mean_only"]["logloss"]) for row in annual)
    )
    if layer_delta < 0.0 and layer_better >= 6:
        layer_status = "favorable_layer_b_predictive_value"
    elif layer_delta > 0.0 and layer_better <= 5:
        layer_status = "adverse_layer_b_predictive_value"
    else:
        layer_status = "no_confirmed_layer_b_predictive_value"

    better_external_name = min(
        ("geometry_process_logistic", "geometry_process_rf"),
        key=lambda name: macro[name],
    )
    external_better = int(
        sum(
            float(row["layer_b"]["logloss"]) < float(row[better_external_name]["logloss"])
            for row in annual
        )
    )
    if (
        macro["layer_b"] < macro["geometry_process_logistic"]
        and macro["layer_b"] < macro["geometry_process_rf"]
        and external_better >= 6
    ):
        external_status = "favorable_external_predictive_added_value"
    elif (
        macro["layer_b"] > min(macro["geometry_process_logistic"], macro["geometry_process_rf"])
        and external_better <= 5
    ):
        external_status = "adverse_external_predictive_added_value"
    else:
        external_status = "no_confirmed_external_predictive_added_value"

    base_result.update(
        {
            "status": "smoke_pass" if mode == "smoke" else "completed_frozen_heldout_test",
            "rule_history": history,
            "annual_metrics": annual,
            "pooled_metrics": pooled,
            "macro_logloss": macro,
            "layer_b_minus_mean_only_macro_logloss": layer_delta,
            "layer_b_better_heldout_transitions": layer_better,
            "better_external_baseline": better_external_name,
            "layer_b_better_than_better_external_transitions": external_better,
            "layer_b_predictive_status": layer_status,
            "external_predictive_status": external_status,
            "final_surviving_world_ids": [
                world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag
            ],
        }
    )
    write_result(output, base_result)
    return base_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "outcome"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    patch_size, distance, temperature, provenance = read_nonresponse_inputs()
    if args.mode == "smoke":
        occupancy = synthetic_response(distance)
        response_provenance = {
            "source": "deterministic synthetic technical-control matrix",
            "response_member_bytes_downloaded": False,
            "response_rows_opened": False,
        }
    else:
        occupancy, response_provenance = read_released_response()
        response_provenance["response_rows_opened"] = True

    result = run_analysis(
        occupancy,
        patch_size,
        distance,
        temperature,
        mode=args.mode,
        provenance=provenance,
        response_provenance=response_provenance,
        output=args.output,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "models_fit": result.get("models_fit", 0),
                "heldout_scores": result.get("heldout_scores", 0),
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
