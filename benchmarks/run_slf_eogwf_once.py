#!/usr/bin/env python3
"""Once-only spotted-lanternfly validation under the frozen Gate 2 contract.

The scientific contract is frozen in validation/slf_two_layer before this runner is
allowed to inspect any row after the first response header. The response target is
first official county infestation designation, not latent biological absence.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)

from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)

WORLD_IDS = (
    "geo_lcc250",
    "geo_lcc500",
    "geo_lcc750",
    "geo_lcc900",
    "human_heavy_tail_full",
)
THRESHOLDS_KM = np.asarray(
    [35.828724722428895, 40.540163111516925, 49.44841925688052, 86.45483634210984],
    dtype=float,
)
LOCAL_SCALE_KM = 40.540163111516925
EARTH_RADIUS_KM = 6371.0088
SUPPORT_TOLERANCE = 1e-15
LOSS_SUPPORT = 1.0
SEED = 20260819
EPS = 1e-6

EXPECTED_CENSUS_SHA256 = "02ef546e4c4f9c032c19616eabb9526caa016f778f41ede3b8c9755dacce20ef"
EXPECTED_GEOMETRY_FINGERPRINT = "5b05192ae33e398c5381bdab37db048373e61e9cd84523fc4f48b7a2bc8dbb07"
EXPECTED_RESPONSE_BLOB = "e845dcc72080089d11c3f1078766cc14cdeb2340"
EXPECTED_RESPONSE_SHA256 = "9af3fba4e4a45b6bf8c0b11f869a82188297d34c76745535db00238d2020cb4c"
EXPECTED_COUNTS = {2014: 1, 2015: 3, 2016: 7, 2017: 17, 2018: 45, 2019: 57, 2020: 84, 2021: 130}
CALIBRATION_TRANSITIONS = ((2014, 2015), (2015, 2016), (2016, 2017), (2017, 2018))
HELDOUT_TRANSITIONS = ((2018, 2019), (2019, 2020), (2020, 2021))
EXCLUDED_USPS = {"AK", "HI", "PR"}

MIN_CAL_EVENTS = 10
MIN_CAL_NON_EVENTS = 40
MIN_HELD_EVENTS = 10
MIN_HELD_NON_EVENTS = 40
MIN_HELD_BOTH = 3


def canonical_sha256(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {str(k).strip(): str(v).strip() for k, v in row.items()}


def read_census_nodes(path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    if sha256_file(path) != EXPECTED_CENSUS_SHA256:
        raise ValueError("Census archive identity mismatch")
    with zipfile.ZipFile(path) as zf:
        names = [name for name in zf.namelist() if name.lower().endswith(".txt")]
        if len(names) != 1:
            raise ValueError("unexpected Census Gazetteer archive structure")
        text = zf.read(names[0]).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    fields = {str(v).strip() for v in (reader.fieldnames or ())}
    required = {"USPS", "GEOID", "INTPTLAT", "INTPTLONG"}
    if not required.issubset(fields):
        raise ValueError("Census schema mismatch")
    rows: list[tuple[str, float, float]] = []
    for raw in reader:
        row = normalize_row(raw)
        if row["USPS"] in EXCLUDED_USPS:
            continue
        rows.append((row["GEOID"], float(row["INTPTLAT"]), float(row["INTPTLONG"])))
    rows.sort(key=lambda value: value[0])
    node_ids = tuple(value[0] for value in rows)
    coords = np.asarray([[value[1], value[2]] for value in rows], dtype=float)
    if len(node_ids) != 3108 or len(set(node_ids)) != 3108:
        raise ValueError("Census node universe differs from Gate 0")
    geometry_fingerprint = canonical_sha256(
        [[node_id, float(lat), float(lon)] for node_id, (lat, lon) in zip(node_ids, coords, strict=True)]
    )
    if geometry_fingerprint != EXPECTED_GEOMETRY_FINGERPRINT:
        raise ValueError("Census geometry fingerprint differs from Gate 0")
    return node_ids, coords


def haversine_matrix(coords_deg: np.ndarray) -> np.ndarray:
    lat = np.deg2rad(coords_deg[:, 0])
    lon = np.deg2rad(coords_deg[:, 1])
    xyz = np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))
    cosine = np.clip(xyz @ xyz.T, -1.0, 1.0)
    matrix = EARTH_RADIUS_KM * np.arccos(cosine)
    matrix = (matrix + matrix.T) / 2.0
    np.fill_diagonal(matrix, 0.0)
    return matrix


def normalize_fips(value: object) -> str:
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if not text.isdigit():
        raise ValueError(f"invalid FIPS value {value!r}")
    return text.zfill(5)


def read_positive_registry(response_path: Path, node_set: set[str]) -> dict[int, set[str]]:
    if git_blob_sha1(response_path) != EXPECTED_RESPONSE_BLOB:
        raise ValueError("SLFS response Git blob mismatch")
    if sha256_file(response_path) != EXPECTED_RESPONSE_SHA256:
        raise ValueError("SLFS response SHA-256 mismatch")
    frame = pd.read_csv(response_path, dtype={"fips": str})
    required = {"fips", "year", "infested"}
    if not required.issubset(frame.columns):
        raise ValueError("SLFS response schema mismatch")
    frame = frame.loc[:, ["fips", "year", "infested"]].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["infested"] = pd.to_numeric(frame["infested"], errors="raise")
    frame["fips"] = [normalize_fips(value) for value in frame["fips"]]
    if not set(frame["fips"]).issubset(node_set):
        missing = sorted(set(frame["fips"]).difference(node_set))
        raise ValueError(f"response contains FIPS outside frozen Census universe: {missing[:10]}")
    if np.any(~np.isfinite(frame["infested"].to_numpy(float))) or np.any(frame["infested"].to_numpy(float) < 0):
        raise ValueError("invalid infestation response values")

    positives: dict[int, set[str]] = {}
    for year in EXPECTED_COUNTS:
        subset = frame[(frame["year"] == year) & (frame["infested"] > 0.5)]
        positives[year] = set(subset["fips"])
        if len(positives[year]) != EXPECTED_COUNTS[year]:
            raise ValueError(
                f"published cumulative count mismatch for {year}: {len(positives[year])} != {EXPECTED_COUNTS[year]}"
            )
    years = sorted(EXPECTED_COUNTS)
    for previous, current in zip(years, years[1:]):
        if not positives[previous].issubset(positives[current]):
            raise ValueError("official infestation registry is not cumulative across years")
    return positives


def compute_world_supports(distance: np.ndarray, source_indices: np.ndarray) -> np.ndarray:
    if source_indices.size == 0:
        raise ValueError("current source set must not be empty")
    source_distance = distance[source_indices, :]
    source_weight = 1.0 / float(source_indices.size)
    supports = np.zeros((len(WORLD_IDS), distance.shape[0]), dtype=float)

    exponential = np.exp(-source_distance / LOCAL_SCALE_KM)
    for world_index, threshold in enumerate(THRESHOLDS_KM):
        raw = exponential * (source_distance <= threshold + 1e-12)
        raw[np.arange(source_indices.size), source_indices] = 0.0
        denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
        supports[world_index, :] = (source_weight / denominator) @ raw

    raw = 1.0 / np.square(1.0 + source_distance / LOCAL_SCALE_KM)
    raw[np.arange(source_indices.size), source_indices] = 0.0
    denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
    supports[-1, :] = (source_weight / denominator) @ raw
    return supports


def make_layer_b_summary(
    node_ids: tuple[str, ...],
    supports: np.ndarray,
    surviving: np.ndarray,
    *,
    transition_id: str,
):
    members = []
    for index, world_id in enumerate(WORLD_IDS):
        if not bool(surviving[index]):
            continue
        cumulative = np.vstack((np.zeros(len(node_ids), dtype=float), supports[index]))
        supported = np.vstack((np.zeros(len(node_ids), dtype=bool), supports[index] > SUPPORT_TOLERANCE))
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
                "surviving_world_ids": [world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag],
            }
        ),
    )
    return summarize_worldset_for_prediction(forecast, step=1)


def shared_baseline(
    coords: np.ndarray,
    distance: np.ndarray,
    source_indices: np.ndarray,
    source_year: int,
) -> np.ndarray:
    source_distance = distance[source_indices, :]
    nearest = np.min(source_distance, axis=0)
    counts = [np.sum(source_distance <= threshold + 1e-12, axis=0) for threshold in THRESHOLDS_KM]
    heavy_exposure = np.sum(1.0 / np.square(1.0 + source_distance / LOCAL_SCALE_KM), axis=0)
    return np.column_stack(
        [
            np.full(len(coords), source_year - 2014, dtype=float),
            np.full(len(coords), len(source_indices), dtype=float),
            coords[:, 0],
            coords[:, 1],
            nearest,
            *counts,
            heavy_exposure,
        ]
    ).astype(float)


def update_rules(supports: np.ndarray, surviving: np.ndarray, positive_indices: np.ndarray) -> tuple[np.ndarray, tuple[str, ...]]:
    after = surviving.copy()
    eliminated: list[str] = []
    if positive_indices.size == 0:
        return after, ()
    for index, world_id in enumerate(WORLD_IDS):
        if after[index] and np.any(supports[index, positive_indices] <= SUPPORT_TOLERANCE):
            after[index] = False
            eliminated.append(world_id)
    return after, tuple(eliminated)


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
    coords: np.ndarray,
    distance: np.ndarray,
    node_index: dict[str, int],
    positives: dict[int, set[str]],
    surviving: np.ndarray,
    source_year: int,
    target_year: int,
) -> TransitionDesign:
    source_ids = positives[source_year]
    target_ids = positives[target_year]
    new_positive_ids = target_ids.difference(source_ids)
    source_indices = np.asarray(sorted(node_index[value] for value in source_ids), dtype=int)
    source_index_set = set(int(value) for value in source_indices)
    risk_indices = np.asarray([index for index in range(len(node_ids)) if index not in source_index_set], dtype=int)
    new_positive_index_set = {node_index[value] for value in new_positive_ids}
    y = np.asarray([1 if int(index) in new_positive_index_set else 0 for index in risk_indices], dtype=int)

    supports = compute_world_supports(distance, source_indices)
    summary = make_layer_b_summary(
        node_ids,
        supports,
        surviving,
        transition_id=f"{source_year}_to_{target_year}",
    )
    baseline_all = shared_baseline(coords, distance, source_indices, source_year)
    return TransitionDesign(
        source_year=source_year,
        target_year=target_year,
        risk_indices=risk_indices,
        y=y,
        baseline=baseline_all[risk_indices],
        layer_b=summary.feature_matrix[risk_indices],
        supports=supports,
        source_count=len(source_indices),
        positive_count=int(np.sum(y == 1)),
        negative_count=int(np.sum(y == 0)),
        surviving_before=tuple(world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag),
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census-zip", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, coords = read_census_nodes(args.census_zip)
    node_index = {node_id: index for index, node_id in enumerate(node_ids)}
    distance = haversine_matrix(coords)
    positives = read_positive_registry(args.response, set(node_ids))

    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    calibration: list[TransitionDesign] = []
    history: list[dict[str, object]] = []
    universe_falsified: list[int] | None = None

    for source_year, target_year in CALIBRATION_TRANSITIONS:
        design = build_transition(node_ids, coords, distance, node_index, positives, surviving, source_year, target_year)
        calibration.append(design)
        positive_indices = design.risk_indices[design.y == 1]
        after, eliminated = update_rules(design.supports, surviving, positive_indices)
        history.append({
            "transition": [source_year, target_year],
            "phase": "calibration",
            "source_count": design.source_count,
            "events": design.positive_count,
            "non_events": design.negative_count,
            "surviving_before": list(design.surviving_before),
            "eliminated_after_observation": list(eliminated),
            "surviving_after": [world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag],
            "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
        })
        surviving = after
        if not np.any(surviving):
            universe_falsified = [source_year, target_year]
            break

    cal_y = np.concatenate([row.y for row in calibration])
    cal_events = int(np.sum(cal_y == 1))
    cal_non_events = int(np.sum(cal_y == 0))
    base_result: dict[str, object] = {
        "status": "pre_model",
        "response_target": "first_official_county_infestation_designation",
        "response_boundary": "recorded designation status; not latent biological absence",
        "source_response_git_blob": EXPECTED_RESPONSE_BLOB,
        "source_response_sha256": EXPECTED_RESPONSE_SHA256,
        "census_sha256": EXPECTED_CENSUS_SHA256,
        "node_count": len(node_ids),
        "world_ids": list(WORLD_IDS),
        "thresholds_km": THRESHOLDS_KM.tolist(),
        "local_scale_km": LOCAL_SCALE_KM,
        "published_cumulative_counts_verified": {str(k): v for k, v in EXPECTED_COUNTS.items()},
        "calibration_events": cal_events,
        "calibration_non_events": cal_non_events,
        "rule_history": history,
        "universe_falsified_transition": universe_falsified,
    }

    if universe_falsified is not None:
        base_result.update({
            "status": "universe_falsified_during_calibration",
            "layer_b_predictive_status": "non_estimable",
            "external_predictive_status": "non_estimable",
        })
        write_result(args.output, base_result)
        print(json.dumps({"status": base_result["status"], "fingerprint": base_result["fingerprint"]}, indent=2))
        return

    if cal_events < MIN_CAL_EVENTS or cal_non_events < MIN_CAL_NON_EVENTS:
        base_result.update({
            "status": "non_estimable_response_balance",
            "layer_b_predictive_status": "non_estimable",
            "external_predictive_status": "non_estimable",
        })
        write_result(args.output, base_result)
        print(json.dumps({"status": base_result["status"], "fingerprint": base_result["fingerprint"]}, indent=2))
        return

    cal_baseline = np.concatenate([row.baseline for row in calibration], axis=0)
    cal_layer_b = np.concatenate([row.layer_b for row in calibration], axis=0)
    rep = layer_b_estimability(cal_baseline, cal_layer_b)
    base_result["layer_b_estimability"] = rep
    if not rep["estimable"]:
        base_result.update({
            "status": "layer_b_non_estimable_beyond_mean_only",
            "layer_b_predictive_status": "non_estimable",
            "external_predictive_status": "non_estimable",
        })
        write_result(args.output, base_result)
        print(json.dumps({"status": base_result["status"], "fingerprint": base_result["fingerprint"]}, indent=2))
        return

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

    annual: list[dict[str, object]] = []
    pooled_y: list[np.ndarray] = []
    pooled_predictions: dict[str, list[np.ndarray]] = {
        "geometry_process_logistic": [],
        "geometry_process_rf": [],
        "mean_only": [],
        "layer_b": [],
    }
    held_events = 0
    held_non_events = 0
    held_both = 0

    for source_year, target_year in HELDOUT_TRANSITIONS:
        design = build_transition(node_ids, coords, distance, node_index, positives, surviving, source_year, target_year)
        y = design.y
        held_events += design.positive_count
        held_non_events += design.negative_count
        held_both += int(design.positive_count > 0 and design.negative_count > 0)
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
            row[name] = metrics(y, prediction)
            pooled_predictions[name].append(prediction)
        pooled_y.append(y)

        after, eliminated = update_rules(design.supports, surviving, design.risk_indices[y == 1])
        row["eliminated_after_observation"] = list(eliminated)
        row["surviving_after"] = [world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag]
        history.append({
            "transition": [source_year, target_year],
            "phase": "heldout",
            "source_count": design.source_count,
            "events": design.positive_count,
            "non_events": design.negative_count,
            "surviving_before": list(design.surviving_before),
            "eliminated_after_observation": list(eliminated),
            "surviving_after": row["surviving_after"],
            "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
        })
        annual.append(row)
        surviving = after
        if not np.any(surviving) and (source_year, target_year) != HELDOUT_TRANSITIONS[-1]:
            universe_falsified = [source_year, target_year]
            break

    if universe_falsified is not None:
        base_result.update({
            "status": "universe_falsified_during_heldout",
            "rule_history": history,
            "annual_metrics": annual,
            "layer_b_predictive_status": "non_estimable",
            "external_predictive_status": "non_estimable",
        })
        write_result(args.output, base_result)
        print(json.dumps({"status": base_result["status"], "fingerprint": base_result["fingerprint"]}, indent=2))
        return

    if held_events < MIN_HELD_EVENTS or held_non_events < MIN_HELD_NON_EVENTS or held_both < MIN_HELD_BOTH:
        base_result.update({
            "status": "non_estimable_response_balance",
            "rule_history": history,
            "annual_metrics": annual,
            "heldout_events": held_events,
            "heldout_non_events": held_non_events,
            "heldout_outer_units_with_both_classes": held_both,
            "layer_b_predictive_status": "non_estimable",
            "external_predictive_status": "non_estimable",
        })
        write_result(args.output, base_result)
        print(json.dumps({"status": base_result["status"], "fingerprint": base_result["fingerprint"]}, indent=2))
        return

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
    layer_better_years = int(sum(float(row["layer_b"]["logloss"]) < float(row["mean_only"]["logloss"]) for row in annual))
    if layer_delta < 0.0 and layer_better_years >= 2:
        layer_status = "favorable_layer_b_predictive_value"
    elif layer_delta > 0.0 and layer_better_years <= 1:
        layer_status = "adverse_layer_b_predictive_value"
    else:
        layer_status = "no_confirmed_layer_b_predictive_value"

    external_better_years = int(
        sum(
            float(row["layer_b"]["logloss"])
            < min(
                float(row["geometry_process_logistic"]["logloss"]),
                float(row["geometry_process_rf"]["logloss"]),
            )
            for row in annual
        )
    )
    if (
        macro["layer_b"] < macro["geometry_process_logistic"]
        and macro["layer_b"] < macro["geometry_process_rf"]
        and external_better_years >= 2
    ):
        external_status = "favorable_external_predictive_added_value"
    elif macro["layer_b"] > min(macro["geometry_process_logistic"], macro["geometry_process_rf"]):
        external_status = "adverse_external_predictive_added_value"
    else:
        external_status = "no_confirmed_external_predictive_added_value"

    result = {
        **base_result,
        "status": "completed_independent_heldout_prediction",
        "rule_history": history,
        "surviving_world_ids_final": [world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag],
        "heldout_events": held_events,
        "heldout_non_events": held_non_events,
        "heldout_outer_units_with_both_classes": held_both,
        "annual_metrics": annual,
        "macro_transition_logloss": macro,
        "pooled_metrics": pooled,
        "layer_b_macro_delta_vs_mean_only": layer_delta,
        "layer_b_better_years_vs_mean_only": layer_better_years,
        "layer_b_predictive_status": layer_status,
        "layer_b_better_years_vs_best_external": external_better_years,
        "external_predictive_status": external_status,
        "feature_state": {
            "baseline_feature_count": int(x_external.shape[1]),
            "mean_only_feature_count": int(x_mean.shape[1]),
            "layer_b_feature_count": int(x_layer_b.shape[1]),
            "layer_b_names": list(PREDICTIVE_FEATURE_NAMES),
            "external_logistic_kept_columns": external_logistic.keep.tolist(),
            "mean_only_logistic_kept_columns": mean_fit.keep.tolist(),
            "layer_b_logistic_kept_columns": layer_b_fit.keep.tolist(),
        },
        "decision_boundary": "No post-response retuning of worlds, Layer B, baseline, split, models, metrics or decision rules.",
    }
    write_result(args.output, result)

    annual_path = args.output.with_name("slf_eogwf_annual_metrics.csv")
    model_names = ["geometry_process_logistic", "geometry_process_rf", "mean_only", "layer_b"]
    with annual_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["source_year", "target_year", "source_count", "events", "non_events", "surviving_before"]
            + [f"{name}_logloss" for name in model_names]
            + [f"{name}_brier" for name in model_names]
            + [f"{name}_auc" for name in model_names]
            + [f"{name}_average_precision" for name in model_names]
        )
        for row in annual:
            writer.writerow(
                [
                    row["transition"][0], row["transition"][1], row["source_count"], row["events"], row["non_events"],
                    ";".join(row["surviving_before"]),
                ]
                + [row[name]["logloss"] for name in model_names]
                + [row[name]["brier"] for name in model_names]
                + [row[name]["auc"] for name in model_names]
                + [row[name]["average_precision"] for name in model_names]
            )

    print(json.dumps({
        "status": result["status"],
        "calibration_events": cal_events,
        "heldout_events": held_events,
        "macro_transition_logloss": macro,
        "layer_b_predictive_status": layer_status,
        "external_predictive_status": external_status,
        "surviving_world_ids_final": result["surviving_world_ids_final"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
