#!/usr/bin/env python3
"""Run the frozen once-only Chiricahua two-layer EOG-WF outcome analysis.

The runner has two modes:

* ``--synthetic-smoke`` exercises the complete response-processing, sequential
  world-contraction, supervised-comparator, repeated-detection HMM, metric and
  decision machinery using deterministic synthetic detections.  It never accepts or
  reads ``y.wide.dryad.csv``.
* outcome mode reads the exact frozen detection-history file once and applies the
  already frozen Gate-2 contracts without retuning.

The scientific target is first *survey-recorded* detection from the fixed 2003
founders.  It is not latent colonisation probability or historical-route recovery.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import scipy
import sklearn
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

# Running ``python benchmarks/run_...py`` places benchmarks/ on sys.path.
import run_chiricahua_gate2_nonresponse as base
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)


YEARS = base.YEARS
RESPONSE_YEARS = base.RESPONSE_YEARS
CALIBRATION_YEARS = base.CALIBRATION_YEARS
HELDOUT_YEARS = base.HELDOUT_YEARS
N_NODES = base.N_NODES
N_SAMPLED = base.N_SAMPLED
N_VISITS = base.N_VISITS
FOUNDER_INDICES_1_BASED = base.FOUNDER_INDICES_1_BASED
DESTROYED_INDICES_1_BASED = base.DESTROYED_INDICES_1_BASED
DESTROYED_FROM_YEAR = base.DESTROYED_FROM_YEAR
SIGMA_KM = base.SIGMA_KM
SUPPORT_TOLERANCE = base.SUPPORT_TOLERANCE
WORLD_SPECS = base.WORLD_SPECS
HYDRO_CLASSES = base.HYDRO_CLASSES

MODEL_EOG = "eog_summary_logistic"
MODEL_MEAN = "same_world_mean_only_logistic"
MODEL_FOUNDER = "founder_connectivity_logistic"
MODEL_HMM = "dynamic_occupancy_hmm"
MODEL_RF = "flexible_random_forest"
MODEL_NAMES = (MODEL_EOG, MODEL_MEAN, MODEL_FOUNDER, MODEL_HMM, MODEL_RF)

MIN_CAL_POS = 10
MIN_CAL_NEG = 40
MIN_HELD_POS = 5
MIN_HELD_NEG = 20
MIN_HELD_BOTH_YEARS = 3
RANDOM_STATE = 20260818
PROBABILITY_EPSILON = 1e-15


class UniverseFalsified(RuntimeError):
    """All frozen Layer-A rules were eliminated by positive evidence."""


@dataclass(frozen=True)
class FrozenStandardizer:
    means: np.ndarray
    scales: np.ndarray
    keep_indices: np.ndarray

    @classmethod
    def fit(cls, values: np.ndarray) -> "FrozenStandardizer":
        matrix = np.asarray(values, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("standardizer requires a non-empty 2D calibration matrix")
        if not np.isfinite(matrix).all():
            raise ValueError("standardizer calibration matrix must be finite")
        means = np.mean(matrix, axis=0)
        scales = np.std(matrix, axis=0, ddof=0)
        keep = np.flatnonzero(scales > 1e-12)
        if keep.size == 0:
            raise ValueError("all declared supervised features have zero calibration SD")
        return cls(means=means, scales=scales, keep_indices=keep)

    def transform(self, values: np.ndarray) -> np.ndarray:
        matrix = np.asarray(values, dtype=float)
        if matrix.ndim != 2 or matrix.shape[1] != self.means.size:
            raise ValueError("feature width differs from frozen standardizer")
        if not np.isfinite(matrix).all():
            raise ValueError("prediction features must be finite")
        kept = self.keep_indices
        return (matrix[:, kept] - self.means[kept]) / self.scales[kept]

    def to_dict(self) -> dict[str, object]:
        return {
            "means": self.means.tolist(),
            "scales": self.scales.tolist(),
            "keep_indices": self.keep_indices.tolist(),
        }


@dataclass
class FrozenLogisticModel:
    name: str
    standardizer: FrozenStandardizer
    estimator: LogisticRegression

    @classmethod
    def fit(cls, name: str, values: np.ndarray, labels: np.ndarray) -> "FrozenLogisticModel":
        standardizer = FrozenStandardizer.fit(values)
        transformed = standardizer.transform(values)
        estimator = LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=3000,
            class_weight=None,
        )
        estimator.fit(transformed, labels)
        if int(estimator.n_iter_[0]) >= 3000:
            raise RuntimeError(f"{name} did not converge before max_iter")
        return cls(name=name, standardizer=standardizer, estimator=estimator)

    def predict(self, values: np.ndarray) -> np.ndarray:
        probabilities = self.estimator.predict_proba(self.standardizer.transform(values))[:, 1]
        return np.asarray(probabilities, dtype=float)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "standardizer": self.standardizer.to_dict(),
            "intercept": self.estimator.intercept_.tolist(),
            "coefficients": self.estimator.coef_.tolist(),
            "iterations": self.estimator.n_iter_.tolist(),
        }


@dataclass(frozen=True)
class RiskRow:
    year: int
    site_index: int
    node_id: str
    label: int
    visit_count: int
    shared: np.ndarray
    layer_b: np.ndarray
    eog_features: np.ndarray
    mean_features: np.ndarray
    founder_features: np.ndarray
    rf_features: np.ndarray
    surviving_world_count: int
    summary_fingerprint: str


@dataclass(frozen=True)
class HMMFit:
    estimable: bool
    parameters: np.ndarray | None
    negative_log_likelihood: float | None
    starts: tuple[dict[str, object], ...]
    scaling: dict[str, float]
    message: str


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_response_number(value: str) -> float:
    text = str(value).strip()
    if text == "" or text.upper() in {"NA", "NAN", "NULL"}:
        return float("nan")
    result = float(text)
    if result not in (0.0, 1.0):
        raise ValueError(f"finite response value must be 0 or 1, found {result!r}")
    return result


def read_response(path: Path, sampled_ids: tuple[str, ...]) -> np.ndarray:
    expected_header = ("", *(f"V{index}" for index in range(1, 46)))
    ids: list[str] = []
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader))
        if header != expected_header:
            raise ValueError("unexpected y.wide.dryad.csv header")
        for row_number, row in enumerate(reader, start=2):
            if len(row) != 46:
                raise ValueError(f"response row {row_number} has {len(row)} fields")
            ids.append(str(row[0]).strip())
            rows.append([parse_response_number(value) for value in row[1:]])
    if tuple(ids) != sampled_ids or len(rows) != N_SAMPLED:
        raise ValueError("response sampled IDs/order differ from the frozen 47-site universe")
    matrix = np.asarray(rows, dtype=float)
    expected_shape = (N_SAMPLED, N_VISITS * len(YEARS))
    if matrix.shape != expected_shape:
        raise ValueError(f"response matrix must have shape {expected_shape}")
    response = matrix.reshape(N_SAMPLED, len(YEARS), N_VISITS)
    destroyed = [index - 1 for index in DESTROYED_INDICES_1_BASED]
    for site_index in destroyed:
        for year in YEARS:
            if year < DESTROYED_FROM_YEAR:
                continue
            values = response[site_index, YEARS.index(year)]
            if np.any(values[np.isfinite(values)] == 1.0):
                raise ValueError("positive detection occurs after source-declared site destruction")
    return response


def response_status(visits: np.ndarray) -> tuple[bool, int | None, int]:
    values = np.asarray(visits, dtype=float)
    observed = np.isfinite(values)
    count = int(np.sum(observed))
    if count == 0:
        return False, None, 0
    finite = values[observed]
    if np.any((finite != 0.0) & (finite != 1.0)):
        raise ValueError("finite response visits must be binary")
    return True, int(np.any(finite == 1.0)), count


def distance_founder_features(
    distance: np.ndarray,
    founder_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    founder_distances = distance[:, founder_indices]
    kernel = np.exp(-(founder_distances * founder_distances) / (2.0 * SIGMA_KM * SIGMA_KM))
    founder_connectivity = 1.0 - np.prod(1.0 - kernel, axis=1)
    founder_connectivity = np.clip(founder_connectivity, 0.0, 1.0)
    thresholds = np.asarray([value for _, value in WORLD_SPECS if value is not None], dtype=float)
    founder_counts = np.column_stack(
        [np.sum(founder_distances <= threshold + 1e-12, axis=1) for threshold in thresholds]
    ).astype(float)
    nearest = np.min(founder_distances, axis=1)
    return founder_distances, founder_connectivity, founder_counts


def response_free_medians(temperature: np.ndarray, wind: np.ndarray) -> tuple[float, float]:
    calibration_indices = [YEARS.index(year) for year in CALIBRATION_YEARS]
    temp_values = temperature[:, calibration_indices, :]
    wind_values = wind[:, calibration_indices, :]
    finite_temp = temp_values[np.isfinite(temp_values)]
    finite_wind = wind_values[np.isfinite(wind_values)]
    if finite_temp.size == 0 or finite_wind.size == 0:
        raise ValueError("calibration-period response-free covariates have no finite values")
    return float(np.median(finite_temp)), float(np.median(finite_wind))


def surveyed_covariate_mean(
    response_visits: np.ndarray,
    covariate_visits: np.ndarray,
    fallback: float,
) -> float:
    surveyed = np.isfinite(response_visits)
    usable = surveyed & np.isfinite(covariate_visits)
    if np.any(usable):
        return float(np.mean(covariate_visits[usable]))
    return float(fallback)


# ---------------------------------------------------------------------------
# Frozen world universe and Layer-B summaries
# ---------------------------------------------------------------------------


def build_world_rows(
    node_ids: tuple[str, ...],
    distance: np.ndarray,
    founder_indices: np.ndarray,
) -> list[tuple[str, str, np.ndarray]]:
    rows: list[tuple[str, str, np.ndarray]] = []
    for world_id, threshold in WORLD_SPECS:
        operator = base.build_operator(node_ids, distance, threshold)
        cumulative = base.cumulative_first_passage_all(
            operator.transition,
            founder_indices,
            max_steps=max(YEARS) - min(YEARS),
        )
        rows.append((world_id, operator.fingerprint, cumulative))
    return rows


def summarize_surviving_worlds(
    node_ids: tuple[str, ...],
    world_rows: Sequence[tuple[str, str, np.ndarray]],
    surviving_world_ids: Sequence[str],
    year: int,
) -> tuple[dict[str, np.ndarray], str, int]:
    survivor_set = set(surviving_world_ids)
    selected = [row for row in world_rows if row[0] in survivor_set]
    if not selected:
        raise UniverseFalsified("no frozen world survives before the requested year")
    forecast = base.make_summary_forecast(
        node_ids,
        selected,
        max_steps=max(YEARS) - min(YEARS),
    )
    # Keep the declared five-world universe in the Layer-B denominator while members
    # contain only the exact rules surviving before this year's response.
    forecast.world_fingerprints = tuple((world_id, fingerprint) for world_id, fingerprint, _ in world_rows)
    forecast.fingerprint = canonical_sha256(
        {
            "declared_worlds": list(forecast.world_fingerprints),
            "surviving_worlds": [[world_id, fingerprint] for world_id, fingerprint, _ in selected],
            "member_fingerprints": [member.fingerprint for member in forecast.members],
            "max_steps": forecast.max_steps,
            "gate_fingerprint": forecast.gate_declaration.fingerprint,
        }
    )
    summary = summarize_worldset_for_prediction(forecast, step=year - 2003)
    mapping = {
        row.node_id: np.asarray(row.feature_values, dtype=float)
        for row in summary.rows
    }
    return mapping, summary.feature_fingerprint, summary.surviving_world_count


def eliminate_incompatible_worlds(
    surviving_world_ids: Sequence[str],
    positive_site_indices: Iterable[int],
    year: int,
    world_lookup: Mapping[str, tuple[str, np.ndarray]],
) -> tuple[list[str], list[str]]:
    positives = tuple(sorted(set(int(value) for value in positive_site_indices)))
    if not positives:
        return list(surviving_world_ids), []
    horizon = year - 2003
    retained: list[str] = []
    eliminated: list[str] = []
    for world_id in surviving_world_ids:
        _, cumulative = world_lookup[world_id]
        compatible = all(
            float(cumulative[horizon, site_index]) > SUPPORT_TOLERANCE
            for site_index in positives
        )
        if compatible:
            retained.append(world_id)
        else:
            eliminated.append(world_id)
    return retained, eliminated


# ---------------------------------------------------------------------------
# Risk-set construction
# ---------------------------------------------------------------------------


def initial_first_detection_state(response: np.ndarray) -> set[int]:
    pre_indices = [YEARS.index(year) for year in YEARS if year < min(RESPONSE_YEARS)]
    detected: set[int] = set()
    for site_index in range(N_SAMPLED):
        values = response[site_index, pre_indices, :]
        if np.any(values[np.isfinite(values)] == 1.0):
            detected.add(site_index)
    return detected


def build_risk_rows_for_year(
    *,
    year: int,
    response: np.ndarray,
    ever_detected: set[int],
    surviving_world_ids: Sequence[str],
    node_ids: tuple[str, ...],
    coords: np.ndarray,
    hydroperiod: tuple[str, ...],
    temperature: np.ndarray,
    wind: np.ndarray,
    distance: np.ndarray,
    founder_indices: np.ndarray,
    founder_distances: np.ndarray,
    founder_connectivity: np.ndarray,
    founder_counts: np.ndarray,
    world_rows: Sequence[tuple[str, str, np.ndarray]],
    temp_fallback: float,
    wind_fallback: float,
) -> tuple[list[RiskRow], list[int], str]:
    summary_by_id, summary_fingerprint, surviving_count = summarize_surviving_worlds(
        node_ids,
        world_rows,
        surviving_world_ids,
        year,
    )
    sampled_ids = node_ids[:N_SAMPLED]
    hydro_index = {value: index for index, value in enumerate(HYDRO_CLASSES)}
    founder_set = set(int(value) for value in founder_indices)
    destroyed_set = {index - 1 for index in DESTROYED_INDICES_1_BASED}
    year_index = YEARS.index(year)
    rows: list[RiskRow] = []
    positives: list[int] = []

    for site_index, node_id in enumerate(sampled_ids):
        if site_index in founder_set or site_index in ever_detected:
            continue
        if site_index in destroyed_set and year >= DESTROYED_FROM_YEAR:
            continue
        surveyed, label, visit_count = response_status(response[site_index, year_index, :])
        if not surveyed or label is None:
            continue
        mean_temp = surveyed_covariate_mean(
            response[site_index, year_index, :],
            temperature[site_index, year_index, :],
            temp_fallback,
        )
        mean_wind = surveyed_covariate_mean(
            response[site_index, year_index, :],
            wind[site_index, year_index, :],
            wind_fallback,
        )
        one_hot = np.zeros(len(HYDRO_CLASSES), dtype=float)
        one_hot[hydro_index[hydroperiod[site_index]]] = 1.0
        shared = np.concatenate(
            [
                one_hot,
                np.asarray(
                    [
                        np.log1p(np.min(founder_distances[site_index])),
                        float(year - 2003),
                        float(visit_count),
                        mean_wind,
                        mean_temp,
                    ],
                    dtype=float,
                ),
            ]
        )
        layer_b = summary_by_id[node_id]
        eog_features = np.concatenate([shared, layer_b])
        mean_features = np.concatenate([shared, layer_b[[0, 1]]])
        founder_features = np.concatenate(
            [shared, np.asarray([founder_connectivity[site_index]], dtype=float)]
        )
        rf_features = np.concatenate(
            [
                shared,
                coords[site_index],
                founder_distances[site_index],
                founder_counts[site_index],
                np.asarray([founder_connectivity[site_index]], dtype=float),
            ]
        )
        for values in (shared, layer_b, eog_features, mean_features, founder_features, rf_features):
            if not np.isfinite(values).all():
                raise ValueError("risk-row feature construction produced non-finite values")
        rows.append(
            RiskRow(
                year=year,
                site_index=site_index,
                node_id=node_id,
                label=int(label),
                visit_count=visit_count,
                shared=shared,
                layer_b=layer_b,
                eog_features=eog_features,
                mean_features=mean_features,
                founder_features=founder_features,
                rf_features=rf_features,
                surviving_world_count=surviving_count,
                summary_fingerprint=summary_fingerprint,
            )
        )
        if label == 1:
            positives.append(site_index)
    return rows, positives, summary_fingerprint


def matrix_from_rows(rows: Sequence[RiskRow], attribute: str) -> np.ndarray:
    if not rows:
        raise ValueError("cannot construct a model matrix from zero rows")
    return np.vstack([np.asarray(getattr(row, attribute), dtype=float) for row in rows])


# ---------------------------------------------------------------------------
# Frozen repeated-detection HMM
# ---------------------------------------------------------------------------


def safe_center_scale(values: np.ndarray) -> tuple[float, float]:
    finite = np.asarray(values, dtype=float)
    if not np.isfinite(finite).all() or finite.size == 0:
        raise ValueError("HMM scaling values must be finite and non-empty")
    mean = float(np.mean(finite))
    sd = float(np.std(finite, ddof=0))
    return mean, sd if sd > 1e-12 else 1.0


def prepare_hmm_arrays(
    response: np.ndarray,
    temperature: np.ndarray,
    wind: np.ndarray,
    hydroperiod: tuple[str, ...],
    founder_connectivity: np.ndarray,
    temp_fallback: float,
    wind_fallback: float,
) -> dict[str, Any]:
    sampled_hydro = hydroperiod[:N_SAMPLED]
    semi = np.asarray([value == "Semi-permanent" for value in sampled_hydro], dtype=float)
    permanent = np.asarray([value == "Permanent" for value in sampled_hydro], dtype=float)
    conn = np.asarray(founder_connectivity[:N_SAMPLED], dtype=float)
    conn_mean, conn_sd = safe_center_scale(conn)
    conn_z = (conn - conn_mean) / conn_sd

    cal_year_indices = [YEARS.index(year) for year in CALIBRATION_YEARS]
    cal_temp = temperature[:, cal_year_indices, :]
    cal_wind = wind[:, cal_year_indices, :]
    imputed_temp = np.where(np.isfinite(cal_temp), cal_temp, temp_fallback)
    imputed_wind = np.where(np.isfinite(cal_wind), cal_wind, wind_fallback)
    temp_mean, temp_sd = safe_center_scale(imputed_temp.ravel())
    wind_mean, wind_sd = safe_center_scale(imputed_wind.ravel())

    cal_horizons = np.asarray([year - 2003 for year in CALIBRATION_YEARS[1:]], dtype=float)
    horizon_mean, horizon_sd = safe_center_scale(cal_horizons)

    return {
        "semi": semi,
        "permanent": permanent,
        "conn_z": conn_z,
        "conn_mean": conn_mean,
        "conn_sd": conn_sd,
        "temp_mean": temp_mean,
        "temp_sd": temp_sd,
        "wind_mean": wind_mean,
        "wind_sd": wind_sd,
        "horizon_mean": horizon_mean,
        "horizon_sd": horizon_sd,
        "response": response,
        "temperature": temperature,
        "wind": wind,
        "temp_fallback": temp_fallback,
        "wind_fallback": wind_fallback,
    }


def hmm_parameter_slices() -> dict[str, slice]:
    return {
        "initial": slice(0, 4),
        "colonization": slice(4, 9),
        "persistence": slice(9, 12),
        "detection": slice(12, 15),
    }


def hmm_emissions(
    response_visits: np.ndarray,
    detection_probability: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(response_visits, dtype=float)
    p = np.clip(np.asarray(detection_probability, dtype=float), PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    observed = np.isfinite(y)
    positive = np.any(observed & (y == 1.0), axis=1)
    e0 = (~positive).astype(float)
    log_e1 = np.sum(
        np.where(
            observed,
            np.where(y == 1.0, np.log(p), np.log1p(-p)),
            0.0,
        ),
        axis=1,
    )
    e1 = np.exp(log_e1)
    return e0, e1


def hmm_probabilities_for_year(
    parameters: np.ndarray,
    arrays: Mapping[str, Any],
    year: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    slices = hmm_parameter_slices()
    semi = arrays["semi"]
    permanent = arrays["permanent"]
    conn_z = arrays["conn_z"]
    year_index = YEARS.index(year)
    temp = np.where(
        np.isfinite(arrays["temperature"][:, year_index, :]),
        arrays["temperature"][:, year_index, :],
        arrays["temp_fallback"],
    )
    wind = np.where(
        np.isfinite(arrays["wind"][:, year_index, :]),
        arrays["wind"][:, year_index, :],
        arrays["wind_fallback"],
    )
    temp_z = (temp - arrays["temp_mean"]) / arrays["temp_sd"]
    wind_z = (wind - arrays["wind_mean"]) / arrays["wind_sd"]

    b_init = parameters[slices["initial"]]
    b_colon = parameters[slices["colonization"]]
    b_persist = parameters[slices["persistence"]]
    b_detect = parameters[slices["detection"]]

    initial = expit(b_init[0] + b_init[1] * semi + b_init[2] * permanent + b_init[3] * conn_z)
    horizon_z = ((year - 2003) - arrays["horizon_mean"]) / arrays["horizon_sd"]
    colonization = expit(
        b_colon[0]
        + b_colon[1] * semi
        + b_colon[2] * permanent
        + b_colon[3] * conn_z
        + b_colon[4] * horizon_z
    )
    persistence = expit(b_persist[0] + b_persist[1] * semi + b_persist[2] * permanent)
    detection = expit(b_detect[0] + b_detect[1] * wind_z + b_detect[2] * temp_z)
    return initial, colonization, persistence, detection


def hmm_negative_log_likelihood(parameters: np.ndarray, arrays: Mapping[str, Any]) -> float:
    response = arrays["response"]
    posterior_occupied: np.ndarray | None = None
    log_likelihood = 0.0
    destroyed = {index - 1 for index in DESTROYED_INDICES_1_BASED}

    for year in CALIBRATION_YEARS:
        initial, colonization, persistence, detection = hmm_probabilities_for_year(parameters, arrays, year)
        if posterior_occupied is None:
            prior_occupied = initial
        else:
            prior_occupied = posterior_occupied * persistence + (1.0 - posterior_occupied) * colonization
        if year >= DESTROYED_FROM_YEAR:
            for site_index in destroyed:
                prior_occupied[site_index] = 0.0
        year_index = YEARS.index(year)
        e0, e1 = hmm_emissions(response[:, year_index, :], detection)
        alpha0 = (1.0 - prior_occupied) * e0
        alpha1 = prior_occupied * e1
        scale = alpha0 + alpha1
        if not np.isfinite(scale).all() or np.any(scale <= 0.0):
            return 1e100
        log_likelihood += float(np.sum(np.log(scale)))
        posterior_occupied = alpha1 / scale
    return -log_likelihood if np.isfinite(log_likelihood) else 1e100


def fit_dynamic_hmm(arrays: Mapping[str, Any]) -> HMMFit:
    rng = np.random.default_rng(RANDOM_STATE)
    starts = [np.zeros(15, dtype=float)]
    starts.extend(rng.normal(0.0, 0.5, size=(4, 15)))
    records: list[dict[str, object]] = []
    candidates: list[tuple[float, np.ndarray]] = []
    bounds = [(-8.0, 8.0)] * 15
    for start_index, start in enumerate(starts):
        result = minimize(
            hmm_negative_log_likelihood,
            np.asarray(start, dtype=float),
            args=(arrays,),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 3000, "ftol": 1e-12, "gtol": 1e-7},
        )
        record = {
            "start_index": start_index,
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "iterations": int(getattr(result, "nit", -1)),
            "function_evaluations": int(getattr(result, "nfev", -1)),
            "negative_log_likelihood": float(result.fun) if np.isfinite(result.fun) else None,
        }
        records.append(record)
        if result.success and np.isfinite(result.fun) and np.isfinite(result.x).all():
            candidates.append((float(result.fun), np.asarray(result.x, dtype=float)))
    scaling = {
        key: float(arrays[key])
        for key in (
            "conn_mean",
            "conn_sd",
            "temp_mean",
            "temp_sd",
            "wind_mean",
            "wind_sd",
            "horizon_mean",
            "horizon_sd",
        )
    }
    if not candidates:
        return HMMFit(
            estimable=False,
            parameters=None,
            negative_log_likelihood=None,
            starts=tuple(records),
            scaling=scaling,
            message="no converged finite bounded L-BFGS-B solution",
        )
    candidates.sort(key=lambda item: item[0])
    best_nll, best_parameters = candidates[0]
    return HMMFit(
        estimable=True,
        parameters=best_parameters,
        negative_log_likelihood=best_nll,
        starts=tuple(records),
        scaling=scaling,
        message="converged finite solution selected by minimum calibration NLL",
    )


def hmm_detection_predictions(
    fit: HMMFit,
    arrays: Mapping[str, Any],
) -> dict[tuple[int, int], float]:
    if not fit.estimable or fit.parameters is None:
        return {}
    parameters = fit.parameters
    response = arrays["response"]
    posterior_occupied: np.ndarray | None = None
    destroyed = {index - 1 for index in DESTROYED_INDICES_1_BASED}
    predictions: dict[tuple[int, int], float] = {}

    for year in RESPONSE_YEARS:
        initial, colonization, persistence, detection = hmm_probabilities_for_year(parameters, arrays, year)
        if posterior_occupied is None:
            prior_occupied = initial
        else:
            prior_occupied = posterior_occupied * persistence + (1.0 - posterior_occupied) * colonization
        if year >= DESTROYED_FROM_YEAR:
            for site_index in destroyed:
                prior_occupied[site_index] = 0.0
        year_index = YEARS.index(year)
        observed = np.isfinite(response[:, year_index, :])
        no_detection_if_occupied = np.prod(
            np.where(observed, 1.0 - detection, 1.0),
            axis=1,
        )
        any_detection_if_occupied = 1.0 - no_detection_if_occupied
        predicted_detection = np.clip(
            prior_occupied * any_detection_if_occupied,
            PROBABILITY_EPSILON,
            1.0 - PROBABILITY_EPSILON,
        )
        for site_index in range(N_SAMPLED):
            predictions[(year, site_index)] = float(predicted_detection[site_index])

        e0, e1 = hmm_emissions(response[:, year_index, :], detection)
        alpha0 = (1.0 - prior_occupied) * e0
        alpha1 = prior_occupied * e1
        scale = alpha0 + alpha1
        if np.any(scale <= 0.0) or not np.isfinite(scale).all():
            raise RuntimeError("HMM filtering became non-finite after fitting")
        posterior_occupied = alpha1 / scale
    return predictions


# ---------------------------------------------------------------------------
# Metrics and decisions
# ---------------------------------------------------------------------------


def binary_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, object]:
    y = np.asarray(labels, dtype=int)
    p = np.clip(np.asarray(probabilities, dtype=float), PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    if y.ndim != 1 or p.shape != y.shape or y.size == 0:
        raise ValueError("binary metrics require aligned non-empty vectors")
    result: dict[str, object] = {
        "n": int(y.size),
        "positives": int(np.sum(y == 1)),
        "negatives": int(np.sum(y == 0)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "roc_auc": None,
    }
    if len(np.unique(y)) == 2:
        result["roc_auc"] = float(roc_auc_score(y, p))
    return result


def aggregate_model_metrics(
    prediction_rows: Sequence[dict[str, object]],
) -> tuple[dict[str, dict[str, object]], list[dict[str, object]]]:
    model_summary: dict[str, dict[str, object]] = {}
    annual_rows: list[dict[str, object]] = []
    for model_name in MODEL_NAMES:
        available = [row for row in prediction_rows if row.get(model_name) is not None]
        if not available:
            model_summary[model_name] = {"estimable": False}
            continue
        annual: dict[str, dict[str, object]] = {}
        for year in HELDOUT_YEARS:
            year_rows = [row for row in available if int(row["year"]) == year]
            if not year_rows:
                continue
            labels = np.asarray([int(row["label"]) for row in year_rows], dtype=int)
            probabilities = np.asarray([float(row[model_name]) for row in year_rows], dtype=float)
            metrics = binary_metrics(labels, probabilities)
            annual[str(year)] = metrics
            annual_rows.append({"year": year, "model": model_name, **metrics})
        labels = np.asarray([int(row["label"]) for row in available], dtype=int)
        probabilities = np.asarray([float(row[model_name]) for row in available], dtype=float)
        pooled = binary_metrics(labels, probabilities)
        macro_years = [annual[str(year)] for year in HELDOUT_YEARS if str(year) in annual]
        model_summary[model_name] = {
            "estimable": len(macro_years) == len(HELDOUT_YEARS),
            "annual": annual,
            "macro_year_log_loss": (
                float(np.mean([float(row["log_loss"]) for row in macro_years]))
                if macro_years
                else None
            ),
            "macro_year_brier": (
                float(np.mean([float(row["brier"]) for row in macro_years]))
                if macro_years
                else None
            ),
            "macro_year_auc": (
                float(np.mean([float(row["roc_auc"]) for row in macro_years if row["roc_auc"] is not None]))
                if any(row["roc_auc"] is not None for row in macro_years)
                else None
            ),
            "pooled": pooled,
        }
    annual_rows.sort(key=lambda row: (int(row["year"]), str(row["model"])))
    return model_summary, annual_rows


def count_year_wins(
    model_summary: Mapping[str, Mapping[str, object]],
    left: str,
    right: str,
) -> int:
    wins = 0
    for year in HELDOUT_YEARS:
        left_row = model_summary[left]["annual"].get(str(year))  # type: ignore[index]
        right_row = model_summary[right]["annual"].get(str(year))  # type: ignore[index]
        if left_row is not None and right_row is not None:
            if float(left_row["log_loss"]) < float(right_row["log_loss"]):
                wins += 1
    return wins


def classify_layer_b_status(
    model_summary: Mapping[str, Mapping[str, object]],
    endpoint_estimable: bool,
) -> dict[str, object]:
    if not endpoint_estimable:
        return {
            "status": "non_estimable_response_or_representation",
            "macro_log_loss_difference_eog_minus_mean": None,
            "eog_year_wins": 0,
        }
    eog = float(model_summary[MODEL_EOG]["macro_year_log_loss"])
    mean = float(model_summary[MODEL_MEAN]["macro_year_log_loss"])
    difference = eog - mean
    wins = count_year_wins(model_summary, MODEL_EOG, MODEL_MEAN)
    if difference < 0.0 and wins >= 4:
        status = "favorable_layer_b_predictive_value"
    elif difference > 0.0 and wins <= 1:
        status = "adverse_layer_b_predictive_value"
    else:
        status = "no_confirmed_layer_b_predictive_value"
    return {
        "status": status,
        "macro_log_loss_difference_eog_minus_mean": difference,
        "eog_year_wins": wins,
    }


def classify_external_status(
    model_summary: Mapping[str, Mapping[str, object]],
    endpoint_estimable: bool,
    hmm_estimable: bool,
) -> dict[str, object]:
    external_names = (MODEL_FOUNDER, MODEL_HMM, MODEL_RF)
    if not endpoint_estimable or not hmm_estimable:
        return {
            "status": "non_estimable_external_predictive_added_value",
            "best_external_model": None,
            "macro_log_loss_difference_eog_minus_best_external": None,
            "eog_year_wins_against_best_available_each_year": 0,
        }
    eog_macro = float(model_summary[MODEL_EOG]["macro_year_log_loss"])
    best_external = min(
        external_names,
        key=lambda name: float(model_summary[name]["macro_year_log_loss"]),
    )
    best_macro = float(model_summary[best_external]["macro_year_log_loss"])
    year_wins = 0
    for year in HELDOUT_YEARS:
        eog_row = model_summary[MODEL_EOG]["annual"][str(year)]  # type: ignore[index]
        best_year_loss = min(
            float(model_summary[name]["annual"][str(year)]["log_loss"])  # type: ignore[index]
            for name in external_names
        )
        if float(eog_row["log_loss"]) < best_year_loss:
            year_wins += 1
    difference = eog_macro - best_macro
    lower_than_all = all(
        eog_macro < float(model_summary[name]["macro_year_log_loss"])
        for name in external_names
    )
    if lower_than_all and year_wins >= 4:
        status = "favorable_external_predictive_added_value"
    elif difference > 0.0 and year_wins <= 1:
        status = "adverse_external_predictive_added_value"
    else:
        status = "no_confirmed_external_predictive_added_value"
    return {
        "status": status,
        "best_external_model": best_external,
        "macro_log_loss_difference_eog_minus_best_external": difference,
        "eog_year_wins_against_best_available_each_year": year_wins,
    }


# ---------------------------------------------------------------------------
# Synthetic smoke response
# ---------------------------------------------------------------------------


def make_synthetic_response(
    world_rows: Sequence[tuple[str, str, np.ndarray]],
    sampled_ids: tuple[str, ...],
) -> np.ndarray:
    response = np.full((N_SAMPLED, len(YEARS), N_VISITS), np.nan, dtype=float)
    founder_sampled = {index - 1 for index in FOUNDER_INDICES_1_BASED if index <= N_SAMPLED}
    destroyed = {index - 1 for index in DESTROYED_INDICES_1_BASED}

    # A complete deterministic survey design for the smoke test.
    for year in RESPONSE_YEARS:
        year_index = YEARS.index(year)
        for site_index in range(N_SAMPLED):
            if site_index in destroyed and year >= DESTROYED_FROM_YEAR:
                continue
            response[site_index, year_index, :] = 0.0
    for site_index in founder_sampled:
        for year in RESPONSE_YEARS:
            response[site_index, YEARS.index(year), 0] = 1.0

    available = [
        index
        for index in range(N_SAMPLED)
        if index not in founder_sampled and index not in destroyed
    ]
    chosen: set[int] = set()
    positives_per_year = {year: (2 if year in CALIBRATION_YEARS else 1) for year in RESPONSE_YEARS}
    for year in RESPONSE_YEARS:
        horizon = year - 2003
        eligible = [
            index
            for index in available
            if index not in chosen
            and all(float(cumulative[horizon, index]) > SUPPORT_TOLERANCE for _, _, cumulative in world_rows)
        ]
        required = positives_per_year[year]
        if len(eligible) < required:
            raise RuntimeError("synthetic smoke could not find enough all-world-supported sites")
        selected = eligible[:required]
        for site_index in selected:
            chosen.add(site_index)
            year_index = YEARS.index(year)
            response[site_index, year_index, 0] = 1.0
            # Preserve detectable persistence after first detection for HMM smoke.
            for later_year in RESPONSE_YEARS:
                if later_year <= year:
                    continue
                later_index = YEARS.index(later_year)
                if np.isfinite(response[site_index, later_index, 0]):
                    response[site_index, later_index, 0] = 1.0
    if len(sampled_ids) != N_SAMPLED:
        raise RuntimeError("synthetic response sampled universe mismatch")
    return response


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------


def run_analysis(
    *,
    node_ids: tuple[str, ...],
    coords: np.ndarray,
    hydroperiod: tuple[str, ...],
    temperature: np.ndarray,
    wind: np.ndarray,
    response: np.ndarray,
    response_source: str,
    response_fingerprint: str | None,
) -> dict[str, object]:
    sampled_ids = node_ids[:N_SAMPLED]
    distance = base.distance_km(coords)
    founder_indices = np.asarray([index - 1 for index in FOUNDER_INDICES_1_BASED], dtype=int)
    founder_distances, founder_connectivity, founder_counts = distance_founder_features(
        distance,
        founder_indices,
    )
    temp_fallback, wind_fallback = response_free_medians(temperature, wind)
    world_rows = build_world_rows(node_ids, distance, founder_indices)
    world_lookup = {
        world_id: (fingerprint, cumulative)
        for world_id, fingerprint, cumulative in world_rows
    }
    declared_world_ids = [world_id for world_id, _, _ in world_rows]
    surviving_world_ids = list(declared_world_ids)
    ever_detected = initial_first_detection_state(response)
    calibration_rows: list[RiskRow] = []
    contraction_history: list[dict[str, object]] = []
    universe_falsified_year: int | None = None

    # Pre-2007 detections only define the first-detection risk set. Frozen Layer-A
    # updates begin with the declared response/calibration period in 2007.
    for year in CALIBRATION_YEARS:
        try:
            rows, positives, summary_fingerprint = build_risk_rows_for_year(
                year=year,
                response=response,
                ever_detected=ever_detected,
                surviving_world_ids=surviving_world_ids,
                node_ids=node_ids,
                coords=coords,
                hydroperiod=hydroperiod,
                temperature=temperature,
                wind=wind,
                distance=distance,
                founder_indices=founder_indices,
                founder_distances=founder_distances,
                founder_connectivity=founder_connectivity,
                founder_counts=founder_counts,
                world_rows=world_rows,
                temp_fallback=temp_fallback,
                wind_fallback=wind_fallback,
            )
        except UniverseFalsified:
            universe_falsified_year = year
            break
        calibration_rows.extend(rows)
        before = list(surviving_world_ids)
        surviving_world_ids, eliminated = eliminate_incompatible_worlds(
            surviving_world_ids,
            positives,
            year,
            world_lookup,
        )
        contraction_history.append(
            {
                "year": year,
                "phase": "calibration",
                "risk_rows": len(rows),
                "positive_first_detections": len(positives),
                "surviving_before": before,
                "eliminated": eliminated,
                "surviving_after": list(surviving_world_ids),
                "summary_fingerprint": summary_fingerprint,
            }
        )
        ever_detected.update(positives)
        if not surviving_world_ids:
            universe_falsified_year = year
            break

    cal_labels = np.asarray([row.label for row in calibration_rows], dtype=int)
    calibration_positive = int(np.sum(cal_labels == 1)) if cal_labels.size else 0
    calibration_negative = int(np.sum(cal_labels == 0)) if cal_labels.size else 0
    response_gate_calibration = (
        calibration_positive >= MIN_CAL_POS and calibration_negative >= MIN_CAL_NEG
    )

    variation: dict[str, object]
    if calibration_rows:
        variation = base.residual_variation(
            matrix_from_rows(calibration_rows, "layer_b"),
            matrix_from_rows(calibration_rows, "shared"),
        )
    else:
        variation = {"estimable": False, "max_residual_sd": 0.0, "rows": []}

    model_fits: dict[str, object] = {}
    logistic_models: dict[str, FrozenLogisticModel] = {}
    rf_model: RandomForestClassifier | None = None
    hmm_fit = HMMFit(
        estimable=False,
        parameters=None,
        negative_log_likelihood=None,
        starts=(),
        scaling={},
        message="not attempted",
    )
    hmm_predictions: dict[tuple[int, int], float] = {}

    can_fit_supervised = (
        universe_falsified_year is None
        and response_gate_calibration
        and bool(variation.get("estimable", False))
        and len(np.unique(cal_labels)) == 2
    )
    if can_fit_supervised:
        logistic_models[MODEL_EOG] = FrozenLogisticModel.fit(
            MODEL_EOG,
            matrix_from_rows(calibration_rows, "eog_features"),
            cal_labels,
        )
        logistic_models[MODEL_MEAN] = FrozenLogisticModel.fit(
            MODEL_MEAN,
            matrix_from_rows(calibration_rows, "mean_features"),
            cal_labels,
        )
        logistic_models[MODEL_FOUNDER] = FrozenLogisticModel.fit(
            MODEL_FOUNDER,
            matrix_from_rows(calibration_rows, "founder_features"),
            cal_labels,
        )
        for name, model in logistic_models.items():
            model_fits[name] = model.to_dict()

        rf_model = RandomForestClassifier(
            n_estimators=500,
            max_features="sqrt",
            min_samples_leaf=5,
            class_weight=None,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        rf_model.fit(matrix_from_rows(calibration_rows, "rf_features"), cal_labels)
        model_fits[MODEL_RF] = {
            "n_estimators": 500,
            "max_features": "sqrt",
            "min_samples_leaf": 5,
            "random_state": RANDOM_STATE,
            "feature_importances": rf_model.feature_importances_.tolist(),
        }

        hmm_arrays = prepare_hmm_arrays(
            response,
            temperature,
            wind,
            hydroperiod,
            founder_connectivity,
            temp_fallback,
            wind_fallback,
        )
        hmm_fit = fit_dynamic_hmm(hmm_arrays)
        model_fits[MODEL_HMM] = {
            "estimable": hmm_fit.estimable,
            "negative_log_likelihood": hmm_fit.negative_log_likelihood,
            "parameters": None if hmm_fit.parameters is None else hmm_fit.parameters.tolist(),
            "parameter_slices": {
                key: [value.start, value.stop]
                for key, value in hmm_parameter_slices().items()
            },
            "starts": list(hmm_fit.starts),
            "scaling": hmm_fit.scaling,
            "message": hmm_fit.message,
        }
        if hmm_fit.estimable:
            hmm_predictions = hmm_detection_predictions(hmm_fit, hmm_arrays)

    prediction_rows: list[dict[str, object]] = []
    heldout_risk_rows: list[RiskRow] = []
    if can_fit_supervised:
        assert rf_model is not None
        for year in HELDOUT_YEARS:
            try:
                rows, positives, summary_fingerprint = build_risk_rows_for_year(
                    year=year,
                    response=response,
                    ever_detected=ever_detected,
                    surviving_world_ids=surviving_world_ids,
                    node_ids=node_ids,
                    coords=coords,
                    hydroperiod=hydroperiod,
                    temperature=temperature,
                    wind=wind,
                    distance=distance,
                    founder_indices=founder_indices,
                    founder_distances=founder_distances,
                    founder_connectivity=founder_connectivity,
                    founder_counts=founder_counts,
                    world_rows=world_rows,
                    temp_fallback=temp_fallback,
                    wind_fallback=wind_fallback,
                )
            except UniverseFalsified:
                universe_falsified_year = year
                break
            heldout_risk_rows.extend(rows)
            if rows:
                eog_prob = logistic_models[MODEL_EOG].predict(matrix_from_rows(rows, "eog_features"))
                mean_prob = logistic_models[MODEL_MEAN].predict(matrix_from_rows(rows, "mean_features"))
                founder_prob = logistic_models[MODEL_FOUNDER].predict(matrix_from_rows(rows, "founder_features"))
                rf_prob = rf_model.predict_proba(matrix_from_rows(rows, "rf_features"))[:, 1]
                for index, row in enumerate(rows):
                    prediction_rows.append(
                        {
                            "year": row.year,
                            "node_id": row.node_id,
                            "site_index_1_based": row.site_index + 1,
                            "label": row.label,
                            "visit_count": row.visit_count,
                            "surviving_world_count": row.surviving_world_count,
                            "summary_fingerprint": row.summary_fingerprint,
                            MODEL_EOG: float(eog_prob[index]),
                            MODEL_MEAN: float(mean_prob[index]),
                            MODEL_FOUNDER: float(founder_prob[index]),
                            MODEL_RF: float(rf_prob[index]),
                            MODEL_HMM: (
                                float(hmm_predictions[(year, row.site_index)])
                                if hmm_fit.estimable
                                else None
                            ),
                        }
                    )
            before = list(surviving_world_ids)
            surviving_world_ids, eliminated = eliminate_incompatible_worlds(
                surviving_world_ids,
                positives,
                year,
                world_lookup,
            )
            contraction_history.append(
                {
                    "year": year,
                    "phase": "heldout",
                    "risk_rows": len(rows),
                    "positive_first_detections": len(positives),
                    "surviving_before": before,
                    "eliminated": eliminated,
                    "surviving_after": list(surviving_world_ids),
                    "summary_fingerprint": summary_fingerprint,
                }
            )
            ever_detected.update(positives)
            if not surviving_world_ids:
                universe_falsified_year = year
                if year != HELDOUT_YEARS[-1]:
                    break

    heldout_labels = np.asarray([row.label for row in heldout_risk_rows], dtype=int)
    heldout_positive = int(np.sum(heldout_labels == 1)) if heldout_labels.size else 0
    heldout_negative = int(np.sum(heldout_labels == 0)) if heldout_labels.size else 0
    heldout_years_with_both = sum(
        len({row.label for row in heldout_risk_rows if row.year == year}) == 2
        for year in HELDOUT_YEARS
    )
    response_gate_heldout = (
        heldout_positive >= MIN_HELD_POS
        and heldout_negative >= MIN_HELD_NEG
        and heldout_years_with_both >= MIN_HELD_BOTH_YEARS
        and all(any(row.year == year for row in heldout_risk_rows) for year in HELDOUT_YEARS)
    )
    scored_heldout_years = {
        int(row["year"])
        for row in contraction_history
        if row.get("phase") == "heldout"
    }
    heldout_scoring_complete = scored_heldout_years == set(HELDOUT_YEARS)
    falsified_before_completion = bool(
        universe_falsified_year is not None and not heldout_scoring_complete
    )
    endpoint_estimable = bool(
        can_fit_supervised
        and response_gate_heldout
        and not falsified_before_completion
        and heldout_scoring_complete
        and len(prediction_rows) == len(heldout_risk_rows)
    )

    if prediction_rows:
        model_summary, annual_metric_rows = aggregate_model_metrics(prediction_rows)
    else:
        model_summary = {name: {"estimable": False} for name in MODEL_NAMES}
        annual_metric_rows = []

    layer_b_decision = classify_layer_b_status(model_summary, endpoint_estimable)
    external_decision = classify_external_status(
        model_summary,
        endpoint_estimable,
        hmm_fit.estimable,
    )

    if falsified_before_completion:
        overall_status = "universe_falsified_before_complete_scoring"
    elif universe_falsified_year is not None and heldout_scoring_complete:
        overall_status = "completed_universe_falsified_after_final_scoring"
    elif not endpoint_estimable:
        overall_status = "non_estimable_response_or_representation"
    elif layer_b_decision["status"] == "favorable_layer_b_predictive_value":
        overall_status = "completed_favorable_layer_b"
    elif layer_b_decision["status"] == "adverse_layer_b_predictive_value":
        overall_status = "completed_adverse_layer_b"
    else:
        overall_status = "completed_no_confirmed_layer_b_added_value"

    payload: dict[str, object] = {
        "status": overall_status,
        "response_source": response_source,
        "response_file_read": response_source == "frozen_y_wide_dryad_csv",
        "response_rows_opened": response_source == "frozen_y_wide_dryad_csv",
        "response_sha256": response_fingerprint,
        "scientific_target": "first survey-recorded detection from fixed 2003 founders",
        "node_count": N_NODES,
        "sampled_site_count": N_SAMPLED,
        "calibration_years": list(CALIBRATION_YEARS),
        "heldout_years": list(HELDOUT_YEARS),
        "calibration_risk_rows": len(calibration_rows),
        "calibration_positive_first_detections": calibration_positive,
        "calibration_negative_candidate_rows": calibration_negative,
        "heldout_risk_rows": len(heldout_risk_rows),
        "heldout_positive_first_detections": heldout_positive,
        "heldout_negative_candidate_rows": heldout_negative,
        "heldout_years_with_both_classes": heldout_years_with_both,
        "response_estimability": {
            "calibration_gate_pass": response_gate_calibration,
            "heldout_gate_pass": response_gate_heldout,
            "layer_b_variation": variation,
            "endpoint_estimable": endpoint_estimable,
        },
        "declared_world_ids": declared_world_ids,
        "world_operator_fingerprints": [
            [world_id, fingerprint] for world_id, fingerprint, _ in world_rows
        ],
        "contraction_history": contraction_history,
        "surviving_world_ids_final": list(surviving_world_ids),
        "universe_falsified_year": universe_falsified_year,
        "heldout_scoring_complete": heldout_scoring_complete,
        "falsified_before_completion": falsified_before_completion,
        "model_fits": model_fits,
        "model_metrics": model_summary,
        "layer_b_decision": layer_b_decision,
        "external_added_value_decision": external_decision,
        "annual_metric_rows": annual_metric_rows,
        "prediction_rows": prediction_rows,
        "runtime": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "scientific_boundaries": [
            "survey-recorded detection is not latent biological colonization probability",
            "fixed founders are not replaced by inferred unsurveyed current sources",
            "structural scales are analyst-choice scales rather than frog dispersal estimates",
            "exact world identities remain Layer-A update/falsification state and are not supervised columns",
            "no actual colonization route is inferred",
        ],
    }
    payload["prediction_fingerprint"] = canonical_sha256(prediction_rows)
    payload["annual_metrics_fingerprint"] = canonical_sha256(annual_metric_rows)
    payload["result_fingerprint"] = canonical_sha256(payload)
    return payload


def write_annual_metrics(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["year", "model", "n", "positives", "negatives", "log_loss", "brier", "roc_auc"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def write_predictions(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "year",
        "node_id",
        "site_index_1_based",
        "label",
        "visit_count",
        "surviving_world_count",
        "summary_fingerprint",
        *MODEL_NAMES,
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coords", type=Path, required=True)
    parser.add_argument("--hydroperiod", type=Path, required=True)
    parser.add_argument("--temperature", type=Path, required=True)
    parser.add_argument("--wind", type=Path, required=True)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--synthetic-smoke", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--annual-output", type=Path, required=True)
    parser.add_argument("--prediction-output", type=Path, required=True)
    args = parser.parse_args()

    if args.synthetic_smoke and args.response is not None:
        raise ValueError("synthetic smoke must not receive a response file")
    if not args.synthetic_smoke and args.response is None:
        raise ValueError("outcome mode requires --response")

    node_ids, coords = base.read_coords(args.coords)
    hydroperiod = base.read_hydroperiod(args.hydroperiod, node_ids)
    sampled_ids = node_ids[:N_SAMPLED]
    temperature = base.read_wide_covariate(args.temperature, sampled_ids)
    wind = base.read_wide_covariate(args.wind, sampled_ids)

    if args.synthetic_smoke:
        distance = base.distance_km(coords)
        founder_indices = np.asarray([index - 1 for index in FOUNDER_INDICES_1_BASED], dtype=int)
        world_rows = build_world_rows(node_ids, distance, founder_indices)
        response = make_synthetic_response(world_rows, sampled_ids)
        response_source = "deterministic_synthetic_smoke"
        response_fingerprint = canonical_sha256(np.where(np.isfinite(response), response, -1.0).tolist())
    else:
        assert args.response is not None
        response = read_response(args.response, sampled_ids)
        response_source = "frozen_y_wide_dryad_csv"
        response_fingerprint = file_sha256(args.response)

    result = run_analysis(
        node_ids=node_ids,
        coords=coords,
        hydroperiod=hydroperiod,
        temperature=temperature,
        wind=wind,
        response=response,
        response_source=response_source,
        response_fingerprint=response_fingerprint,
    )

    if args.synthetic_smoke:
        allowed = {
            "completed_favorable_layer_b",
            "completed_adverse_layer_b",
            "completed_no_confirmed_layer_b_added_value",
        }
        if result["status"] not in allowed:
            raise RuntimeError(f"synthetic smoke did not reach complete scoring: {result['status']}")
        hmm_fit = result["model_fits"].get(MODEL_HMM, {})  # type: ignore[index]
        if not bool(hmm_fit.get("estimable", False)):
            raise RuntimeError("synthetic smoke did not obtain a converged HMM")
        if len(result["prediction_rows"]) == 0:  # type: ignore[arg-type]
            raise RuntimeError("synthetic smoke produced no heldout predictions")
        result["status"] = "gate2_outcome_runner_synthetic_smoke_pass"
        result["scientific_interpretation"] = (
            "Technical smoke only: all frozen response, model, HMM, metric and decision "
            "paths completed on deterministic synthetic detections; no empirical response was read."
        )
        result["result_fingerprint"] = canonical_sha256(
            {key: value for key, value in result.items() if key != "result_fingerprint"}
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_annual_metrics(args.annual_output, result["annual_metric_rows"])  # type: ignore[arg-type]
    write_predictions(args.prediction_output, result["prediction_rows"])  # type: ignore[arg-type]
    print(
        json.dumps(
            {
                "status": result["status"],
                "result_fingerprint": result["result_fingerprint"],
                "layer_b_decision": result["layer_b_decision"],
                "external_added_value_decision": result["external_added_value_decision"],
                "calibration_positive_first_detections": result["calibration_positive_first_detections"],
                "heldout_positive_first_detections": result["heldout_positive_first_detections"],
                "universe_falsified_year": result["universe_falsified_year"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
