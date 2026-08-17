#!/usr/bin/env python3
"""Run the prospectively frozen Glanville EOG-WF annual colonisation validation once.

Scientific contracts were frozen before population response access in:

- validation/glanville_eogwf/gate0_source_process_contract.json
- validation/glanville_eogwf/gate1_scale_adequacy_declaration.json
- validation/glanville_eogwf/gate1_result.json
- validation/glanville_eogwf/gate2_temporal_prediction_contract.json
- validation/glanville_eogwf/gate2_amendment_v1_1.json
- validation/glanville_eogwf/gate2_temporal_metadata_result.json

The primary target is *survey-recorded annual colonisation*: a patch recorded as
unoccupied at t is positive when it is recorded occupied at t+1.  Survey zeros are not
promoted to latent biological absence.  No world, threshold, split, comparator or
decision rule may be retuned after this script opens ``population``.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score


ARCHIVE_MD5 = "69122a1d82b1fb970fb6638b02da3db4"
NODE_COUNT = 4656
WORLD_IDS = (
    "process_full_exp_alpha1",
    "struct_geo_lcc250",
    "struct_geo_lcc500",
    "struct_geo_lcc750",
    "struct_geo_lcc900",
)
THRESHOLDS_KM: tuple[float | None, ...] = (
    None,
    0.8412958233838802,
    1.1527935766506063,
    1.6079604357918804,
    6.418444554899734,
)
CALIBRATION_TRANSITIONS = tuple((year, year + 1) for year in range(1999, 2012))
HELDOUT_TRANSITIONS = tuple((year, year + 1) for year in range(2012, 2018))
ALL_TRANSITIONS = CALIBRATION_TRANSITIONS + HELDOUT_TRANSITIONS
SUPPORT_TOLERANCE = 1e-15
LOSS_SUPPORT = 1.0
ALPHA_PER_KM = 1.0
AREA_EXPONENT = 0.2
EPS = 1e-6
SEED = 20260817

MIN_CAL_POS = 100
MIN_CAL_NEG = 500
MIN_HELD_POS = 50
MIN_HELD_NEG = 200
MIN_HELD_YEARS_BOTH = 4


def canonical_sha256(payload: object) -> str:
    text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path, *, patch_as_string: bool = True) -> pd.DataFrame:
    dtype = {"patch": str} if patch_as_string else None
    return pd.read_csv(path, sep="\t", dtype=dtype)


def validate_inputs(
    patch_network_path: Path,
    patch_area_path: Path,
    survey_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    network = read_tsv(patch_network_path)
    area = read_tsv(patch_area_path)
    survey = read_tsv(survey_path)

    if tuple(network.columns) != ("patch", "x", "y", "area"):
        raise ValueError(f"patch_network schema mismatch: {tuple(network.columns)!r}")
    if tuple(area.columns) != ("patch", "year", "area"):
        raise ValueError(f"patch_area schema mismatch: {tuple(area.columns)!r}")
    expected_survey = (
        "year",
        "patch",
        "population",
        "plantago",
        "veronica",
        "plantago_low",
        "veronica_low",
        "plantago_dry",
        "veronica_dry",
        "grazing_presence",
        "grazing_intensity",
        "previous_population",
    )
    if tuple(survey.columns) != expected_survey:
        raise ValueError(f"survey_data schema mismatch: {tuple(survey.columns)!r}")

    network["patch"] = network["patch"].astype(str).str.strip()
    area["patch"] = area["patch"].astype(str).str.strip()
    survey["patch"] = survey["patch"].astype(str).str.strip()
    if len(network) != NODE_COUNT or network["patch"].nunique() != NODE_COUNT:
        raise ValueError("patch_network node count/uniqueness gate failed")

    node_set = set(network["patch"])
    unknown_area = sorted(set(area["patch"]).difference(node_set))
    unknown_survey = sorted(set(survey["patch"]).difference(node_set))
    if unknown_area:
        raise ValueError(f"patch_area contains nodes outside frozen network: {unknown_area[:10]}")
    if unknown_survey:
        raise ValueError(f"survey_data contains nodes outside frozen network: {unknown_survey[:10]}")

    for column in ("x", "y", "area"):
        values = pd.to_numeric(network[column], errors="coerce").to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite patch_network {column}")
    area["year"] = pd.to_numeric(area["year"], errors="raise").astype(int)
    area["area"] = pd.to_numeric(area["area"], errors="coerce")
    survey["year"] = pd.to_numeric(survey["year"], errors="raise").astype(int)
    survey["population"] = pd.to_numeric(survey["population"], errors="coerce")

    finite_population = survey["population"].dropna().to_numpy(float)
    if finite_population.size and np.any(finite_population < 0.0):
        raise ValueError("response_schema_invalid_negative_population")

    duplicated = survey.duplicated(subset=["year", "patch"], keep=False)
    if bool(duplicated.any()):
        raise ValueError("survey_data has duplicate year-patch rows")
    duplicated_area = area.duplicated(subset=["year", "patch"], keep=False)
    if bool(duplicated_area.any()):
        raise ValueError("patch_area has duplicate year-patch rows")

    survey_years = tuple(sorted(set(int(v) for v in survey["year"])))
    required_years = tuple(range(1999, 2019))
    if survey_years != required_years:
        raise ValueError(f"survey year freeze mismatch: {survey_years!r}")

    audit = {
        "network_rows": int(len(network)),
        "area_rows": int(len(area)),
        "survey_rows": int(len(survey)),
        "finite_population_rows": int(np.sum(np.isfinite(survey["population"].to_numpy(float)))),
        "missing_population_rows": int(np.sum(~np.isfinite(survey["population"].to_numpy(float)))),
        "survey_years": list(survey_years),
    }
    return network, area, survey, audit


def distance_and_kernel(network: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    coords = network.loc[:, ["x", "y"]].to_numpy(dtype=float)
    sq = np.sum(coords * coords, axis=1)
    dist2 = sq[:, None] + sq[None, :] - 2.0 * (coords @ coords.T)
    distance = np.sqrt(np.maximum(dist2, 0.0))
    np.fill_diagonal(distance, 0.0)
    kernel = np.exp(-ALPHA_PER_KM * distance)
    np.fill_diagonal(kernel, 0.0)
    return distance, kernel


def year_vector(
    frame: pd.DataFrame,
    year: int,
    node_index: dict[str, int],
    value_column: str,
) -> np.ndarray:
    result = np.full(len(node_index), np.nan, dtype=float)
    subset = frame[frame["year"] == int(year)]
    for patch, value in zip(subset["patch"], subset[value_column], strict=True):
        result[node_index[str(patch)]] = float(value) if pd.notna(value) else np.nan
    return result


def compute_world_supports(
    distance: np.ndarray,
    kernel: np.ndarray,
    active: np.ndarray,
    source_indices: np.ndarray,
) -> np.ndarray:
    """Return 5 × node exact one-step supports under the frozen Q semantics."""

    if source_indices.size == 0:
        raise ValueError("non_estimable_no_current_sources")
    source_distance = distance[source_indices, :]
    source_kernel = kernel[source_indices, :]
    active_row = active[None, :]
    source_weight = 1.0 / float(source_indices.size)
    supports = np.zeros((len(WORLD_IDS), distance.shape[0]), dtype=float)
    for world_index, threshold in enumerate(THRESHOLDS_KM):
        if threshold is None:
            raw = source_kernel * active_row
        else:
            raw = source_kernel * (source_distance <= threshold + 1e-12) * active_row
        denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
        supports[world_index, :] = (source_weight / denominator) @ raw
    return supports


def compressed_eog_features(
    supports: np.ndarray,
    surviving: np.ndarray,
) -> np.ndarray:
    if not np.any(surviving):
        raise ValueError("no surviving worlds for compression")
    values = supports[surviving, :]
    positive = values > SUPPORT_TOLERANCE
    mean = np.mean(values, axis=0)
    std = np.std(values, axis=0, ddof=0)
    min_value = np.min(values, axis=0)
    max_value = np.max(values, axis=0)
    q25 = np.quantile(values, 0.25, axis=0, method="linear")
    q50 = np.quantile(values, 0.50, axis=0, method="linear")
    q75 = np.quantile(values, 0.75, axis=0, method="linear")
    positive_fraction = np.mean(positive, axis=0)
    support_range = max_value - min_value
    surviving_fraction = np.full(values.shape[1], np.mean(surviving), dtype=float)
    return np.column_stack(
        [
            surviving_fraction,
            mean,
            std,
            min_value,
            max_value,
            q25,
            q50,
            q75,
            positive_fraction,
            support_range,
        ]
    )


def identity_eog_features(supports: np.ndarray, surviving: np.ndarray) -> np.ndarray:
    mask = surviving.astype(float)
    masked_support = supports.copy()
    masked_support[~surviving, :] = 0.0
    return np.column_stack(
        [
            np.repeat(mask[None, :], supports.shape[1], axis=0),
            masked_support.T,
        ]
    )


@dataclass
class TransitionDesign:
    source_year: int
    target_year: int
    candidate_indices: np.ndarray
    y: np.ndarray
    baseline: np.ndarray
    rf_features: np.ndarray
    identity_eog: np.ndarray
    compression_eog: np.ndarray
    supports_all_worlds: np.ndarray
    source_count: int
    candidate_count: int
    positive_count: int
    negative_count: int
    surviving_before: tuple[str, ...]


def build_transition_design(
    source_year: int,
    target_year: int,
    *,
    population_by_year: dict[int, np.ndarray],
    area_by_year: dict[int, np.ndarray],
    distance: np.ndarray,
    kernel: np.ndarray,
    surviving: np.ndarray,
) -> TransitionDesign:
    population_t = population_by_year[source_year]
    population_next = population_by_year[target_year]
    area_t = area_by_year[source_year]
    active = np.isfinite(area_t) & (area_t > 0.0)

    finite_t = np.isfinite(population_t)
    finite_next = np.isfinite(population_next)
    sources = np.flatnonzero(finite_t & (population_t > 0.0) & active)
    candidates = np.flatnonzero(
        finite_t & (population_t == 0.0) & finite_next & active
    )
    if sources.size == 0:
        raise ValueError(f"non_estimable_no_current_sources:{source_year}")
    if candidates.size == 0:
        raise ValueError(f"non_estimable_no_colonization_candidates:{source_year}")

    y = (population_next[candidates] > 0.0).astype(int)
    supports_all = compute_world_supports(distance, kernel, active, sources)

    source_area = np.power(area_t[sources], AREA_EXPONENT)
    ifm_all = source_area @ kernel[sources, :]
    target_area = np.power(area_t[candidates], AREA_EXPONENT)
    ifm = ifm_all[candidates]
    baseline = np.column_stack([target_area, ifm])

    source_distance = distance[sources, :]
    nearest = np.min(source_distance, axis=0)[candidates]
    count_1km = np.sum(source_distance <= 1.0 + 1e-12, axis=0)[candidates]
    count_2km = np.sum(source_distance <= 2.0 + 1e-12, axis=0)[candidates]
    rf_features = np.column_stack([target_area, ifm, nearest, count_1km, count_2km])

    candidate_supports = supports_all[:, candidates]
    identity = identity_eog_features(candidate_supports, surviving)
    compression = compressed_eog_features(candidate_supports, surviving)

    return TransitionDesign(
        source_year=source_year,
        target_year=target_year,
        candidate_indices=candidates,
        y=y,
        baseline=baseline,
        rf_features=rf_features,
        identity_eog=identity,
        compression_eog=compression,
        supports_all_worlds=supports_all,
        source_count=int(sources.size),
        candidate_count=int(candidates.size),
        positive_count=int(np.sum(y == 1)),
        negative_count=int(np.sum(y == 0)),
        surviving_before=tuple(world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag),
    )


def update_surviving_rules(
    design: TransitionDesign,
    surviving: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    result = surviving.copy()
    positive_nodes = design.candidate_indices[design.y == 1]
    eliminated: list[str] = []
    if positive_nodes.size == 0:
        return result, ()
    for world_index, world_id in enumerate(WORLD_IDS):
        if not result[world_index]:
            continue
        world_support = design.supports_all_worlds[world_index, positive_nodes]
        if np.any(world_support <= SUPPORT_TOLERANCE):
            result[world_index] = False
            eliminated.append(world_id)
    return result, tuple(eliminated)


def concatenate_designs(designs: list[TransitionDesign], attr: str) -> np.ndarray:
    return np.concatenate([np.asarray(getattr(design, attr)) for design in designs], axis=0)


@dataclass
class LogisticFit:
    model: LogisticRegression
    keep: np.ndarray
    mean: np.ndarray
    sd: np.ndarray

    def predict(self, x: np.ndarray) -> np.ndarray:
        values = np.asarray(x, dtype=float)[:, self.keep]
        z = (values - self.mean) / self.sd
        return self.model.predict_proba(z)[:, 1].astype(float)


def fit_logistic(x: np.ndarray, y: np.ndarray) -> LogisticFit:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=int)
    sd_full = np.std(x, axis=0, ddof=0)
    keep = np.flatnonzero(sd_full > 1e-12)
    if keep.size == 0:
        raise ValueError("all logistic features are constant")
    values = x[:, keep]
    mean = np.mean(values, axis=0)
    sd = np.std(values, axis=0, ddof=0)
    z = (values - mean) / sd
    model = LogisticRegression(
        C=1.0,
        penalty="l2",
        solver="lbfgs",
        max_iter=3000,
        class_weight=None,
        random_state=SEED,
    )
    model.fit(z, y)
    return LogisticFit(model=model, keep=keep, mean=mean, sd=sd)


def identity_estimability(identity: np.ndarray, compression: np.ndarray) -> dict[str, object]:
    identity = np.asarray(identity, dtype=float)
    compression = np.asarray(compression, dtype=float)
    id_sd = np.std(identity, axis=0, ddof=0)
    id_keep = np.flatnonzero(id_sd > 1e-12)
    comp_sd = np.std(compression, axis=0, ddof=0)
    comp_keep = np.flatnonzero(comp_sd > 1e-12)
    if id_keep.size == 0:
        return {
            "estimable": False,
            "retained_identity_columns": [],
            "retained_compression_columns": comp_keep.tolist(),
            "residual_sd_by_identity_column": [],
            "max_residual_sd": 0.0,
        }
    identity_z = (identity[:, id_keep] - np.mean(identity[:, id_keep], axis=0)) / id_sd[id_keep]
    if comp_keep.size:
        comp_values = compression[:, comp_keep]
        comp_z = (comp_values - np.mean(comp_values, axis=0)) / comp_sd[comp_keep]
        design = np.column_stack([np.ones(len(comp_z)), comp_z])
    else:
        design = np.ones((len(identity_z), 1), dtype=float)
    residual_sds: list[float] = []
    for column in range(identity_z.shape[1]):
        beta, *_ = np.linalg.lstsq(design, identity_z[:, column], rcond=None)
        residual = identity_z[:, column] - design @ beta
        residual_sds.append(float(np.std(residual, ddof=0)))
    max_residual = max(residual_sds, default=0.0)
    return {
        "estimable": bool(max_residual > 1e-8),
        "retained_identity_columns": id_keep.tolist(),
        "retained_compression_columns": comp_keep.tolist(),
        "residual_sd_by_identity_column": residual_sds,
        "max_residual_sd": max_residual,
    }


def probability_metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float | None]:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    result: dict[str, float | None] = {
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "auc": None,
    }
    if len(np.unique(y)) == 2:
        result["auc"] = float(roc_auc_score(y, p))
    return result


def annual_summary(rows: list[dict[str, object]], model: str) -> float:
    return float(np.mean([float(row[model]["logloss"]) for row in rows]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extract-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if md5_file(args.archive) != ARCHIVE_MD5:
        raise SystemExit("archive MD5 mismatch")
    archive_sha256 = sha256_file(args.archive)

    patch_network_path = args.extract_dir / "data" / "patch_network.tsv"
    patch_area_path = args.extract_dir / "data" / "patch_area.tsv"
    survey_path = args.extract_dir / "data" / "survey_data.tsv"
    network, area, survey, input_audit = validate_inputs(
        patch_network_path, patch_area_path, survey_path
    )

    node_ids = tuple(network["patch"].astype(str))
    node_index = {node_id: i for i, node_id in enumerate(node_ids)}
    distance, kernel = distance_and_kernel(network)

    population_by_year = {
        year: year_vector(survey, year, node_index, "population")
        for year in range(1999, 2019)
    }
    area_by_year = {
        year: year_vector(area, year, node_index, "area")
        for year in range(1999, 2019)
    }

    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    calibration_designs: list[TransitionDesign] = []
    rule_history: list[dict[str, object]] = []
    universe_falsified_transition: list[int] | None = None

    for source_year, target_year in CALIBRATION_TRANSITIONS:
        design = build_transition_design(
            source_year,
            target_year,
            population_by_year=population_by_year,
            area_by_year=area_by_year,
            distance=distance,
            kernel=kernel,
            surviving=surviving,
        )
        calibration_designs.append(design)
        after, eliminated = update_surviving_rules(design, surviving)
        rule_history.append(
            {
                "transition": [source_year, target_year],
                "phase": "calibration",
                "sources": design.source_count,
                "candidates": design.candidate_count,
                "positives": design.positive_count,
                "negatives": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": [
                    world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag
                ],
            }
        )
        surviving = after
        if not np.any(surviving):
            universe_falsified_transition = [source_year, target_year]
            break

    cal_y = concatenate_designs(calibration_designs, "y")
    cal_positive = int(np.sum(cal_y == 1))
    cal_negative = int(np.sum(cal_y == 0))

    base_payload: dict[str, object] = {
        "source_archive_md5": ARCHIVE_MD5,
        "source_archive_sha256": archive_sha256,
        "input_audit": input_audit,
        "world_ids": list(WORLD_IDS),
        "thresholds_km": [value for value in THRESHOLDS_KM],
        "calibration_transitions": [list(row) for row in CALIBRATION_TRANSITIONS],
        "heldout_transitions": [list(row) for row in HELDOUT_TRANSITIONS],
        "rule_history": rule_history,
        "calibration_positive": cal_positive,
        "calibration_negative": cal_negative,
        "response_target": "survey_recorded_annual_colonization_transition",
        "detection_boundary": "survey-recorded transition; zero is not asserted as latent biological absence",
    }

    if universe_falsified_transition is not None:
        base_payload.update(
            {
                "status": "universe_falsified_during_calibration",
                "universe_falsified_transition": universe_falsified_transition,
                "identity_predictive_value_status": "non_estimable",
                "external_predictive_added_value_status": "non_estimable",
            }
        )
        base_payload["fingerprint"] = canonical_sha256(base_payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(base_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": base_payload["status"],
            "universe_falsified_transition": universe_falsified_transition,
            "calibration_positive": cal_positive,
            "calibration_negative": cal_negative,
            "fingerprint": base_payload["fingerprint"],
        }, indent=2))
        return

    if cal_positive < MIN_CAL_POS or cal_negative < MIN_CAL_NEG:
        base_payload.update(
            {
                "status": "non_estimable_response_balance",
                "identity_predictive_value_status": "non_estimable",
                "external_predictive_added_value_status": "non_estimable",
            }
        )
        base_payload["fingerprint"] = canonical_sha256(base_payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(base_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": base_payload["status"], "fingerprint": base_payload["fingerprint"]}, indent=2))
        return

    cal_baseline = concatenate_designs(calibration_designs, "baseline")
    cal_rf = concatenate_designs(calibration_designs, "rf_features")
    cal_identity_eog = concatenate_designs(calibration_designs, "identity_eog")
    cal_compression_eog = concatenate_designs(calibration_designs, "compression_eog")
    cal_identity = np.column_stack([cal_baseline, cal_identity_eog])
    cal_compression = np.column_stack([cal_baseline, cal_compression_eog])

    id_estimability = identity_estimability(cal_identity_eog, cal_compression_eog)
    ifm_fit = fit_logistic(cal_baseline, cal_y)
    compression_fit = fit_logistic(cal_compression, cal_y)
    identity_fit = fit_logistic(cal_identity, cal_y) if bool(id_estimability["estimable"]) else None
    rf = RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        min_samples_leaf=5,
        class_weight=None,
        random_state=SEED,
        n_jobs=-1,
    )
    rf.fit(cal_rf, cal_y)

    heldout_rows: list[dict[str, object]] = []
    pooled_y: list[np.ndarray] = []
    pooled_predictions: dict[str, list[np.ndarray]] = {
        "compression": [],
        "ifm": [],
        "rf": [],
    }
    if identity_fit is not None:
        pooled_predictions["identity"] = []

    held_positive_total = 0
    held_negative_total = 0
    held_years_both = 0
    heldout_complete = True

    for source_year, target_year in HELDOUT_TRANSITIONS:
        if not np.any(surviving):
            heldout_complete = False
            break
        design = build_transition_design(
            source_year,
            target_year,
            population_by_year=population_by_year,
            area_by_year=area_by_year,
            distance=distance,
            kernel=kernel,
            surviving=surviving,
        )
        y = design.y
        held_positive_total += design.positive_count
        held_negative_total += design.negative_count
        if design.positive_count > 0 and design.negative_count > 0:
            held_years_both += 1

        x_compression = np.column_stack([design.baseline, design.compression_eog])
        predictions: dict[str, np.ndarray] = {
            "compression": compression_fit.predict(x_compression),
            "ifm": ifm_fit.predict(design.baseline),
            "rf": rf.predict_proba(design.rf_features)[:, 1].astype(float),
        }
        if identity_fit is not None:
            x_identity = np.column_stack([design.baseline, design.identity_eog])
            predictions["identity"] = identity_fit.predict(x_identity)

        metrics = {name: probability_metrics(y, pred) for name, pred in predictions.items()}
        row: dict[str, object] = {
            "transition": [source_year, target_year],
            "sources": design.source_count,
            "candidates": design.candidate_count,
            "positives": design.positive_count,
            "negatives": design.negative_count,
            "surviving_before": list(design.surviving_before),
            **metrics,
        }
        heldout_rows.append(row)
        pooled_y.append(y)
        for name, pred in predictions.items():
            pooled_predictions[name].append(pred)

        after, eliminated = update_surviving_rules(design, surviving)
        row["eliminated_after_observation"] = list(eliminated)
        row["surviving_after"] = [
            world_id for world_id, flag in zip(WORLD_IDS, after, strict=True) if flag
        ]
        rule_history.append(
            {
                "transition": [source_year, target_year],
                "phase": "heldout",
                "sources": design.source_count,
                "candidates": design.candidate_count,
                "positives": design.positive_count,
                "negatives": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": row["surviving_after"],
            }
        )
        surviving = after
        if not np.any(surviving) and (source_year, target_year) != HELDOUT_TRANSITIONS[-1]:
            heldout_complete = False
            universe_falsified_transition = [source_year, target_year]
            break

    response_estimable = (
        heldout_complete
        and len(heldout_rows) == len(HELDOUT_TRANSITIONS)
        and held_positive_total >= MIN_HELD_POS
        and held_negative_total >= MIN_HELD_NEG
        and held_years_both >= MIN_HELD_YEARS_BOTH
    )

    if not response_estimable:
        status = (
            "universe_falsified_during_holdout"
            if universe_falsified_transition is not None or not heldout_complete
            else "non_estimable_response_balance"
        )
        base_payload.update(
            {
                "status": status,
                "rule_history": rule_history,
                "identity_estimability": id_estimability,
                "heldout_rows": heldout_rows,
                "heldout_positive": held_positive_total,
                "heldout_negative": held_negative_total,
                "heldout_years_with_both_classes": held_years_both,
                "universe_falsified_transition": universe_falsified_transition,
                "identity_predictive_value_status": "non_estimable",
                "external_predictive_added_value_status": "non_estimable",
            }
        )
        base_payload["fingerprint"] = canonical_sha256(base_payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(base_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": status,
            "heldout_positive": held_positive_total,
            "heldout_negative": held_negative_total,
            "surviving_world_ids": [w for w, flag in zip(WORLD_IDS, surviving, strict=True) if flag],
            "fingerprint": base_payload["fingerprint"],
        }, indent=2))
        return

    pooled_y_array = np.concatenate(pooled_y)
    pooled_metrics = {
        name: probability_metrics(pooled_y_array, np.concatenate(parts))
        for name, parts in pooled_predictions.items()
    }
    macro_logloss = {
        name: annual_summary(heldout_rows, name)
        for name in pooled_predictions
    }

    identity_status = "identity_non_estimable_from_declared_compression"
    identity_delta = None
    identity_better_years = None
    if identity_fit is not None:
        identity_delta = float(macro_logloss["identity"] - macro_logloss["compression"])
        identity_better_years = int(
            sum(float(row["identity"]["logloss"]) < float(row["compression"]["logloss"]) for row in heldout_rows)
        )
        if identity_delta < 0.0 and identity_better_years >= 4:
            identity_status = "favorable_identity_predictive_value"
        elif identity_delta > 0.0:
            identity_status = "adverse_identity_predictive_value"
        else:
            identity_status = "no_confirmed_identity_predictive_value"

    external_status = "non_estimable"
    external_better_years = None
    if identity_fit is not None:
        better_external_macro = min(macro_logloss["ifm"], macro_logloss["rf"])
        external_better_years = int(
            sum(
                float(row["identity"]["logloss"])
                < min(float(row["ifm"]["logloss"]), float(row["rf"]["logloss"]))
                for row in heldout_rows
            )
        )
        if (
            macro_logloss["identity"] < macro_logloss["ifm"]
            and macro_logloss["identity"] < macro_logloss["rf"]
            and external_better_years >= 4
        ):
            external_status = "favorable_external_predictive_added_value"
        elif macro_logloss["identity"] > better_external_macro:
            external_status = "adverse_external_predictive_added_value"
        else:
            external_status = "no_confirmed_external_predictive_added_value"

    result = {
        **base_payload,
        "status": "completed_independent_heldout_prediction",
        "rule_history": rule_history,
        "surviving_world_ids_final": [
            world_id for world_id, flag in zip(WORLD_IDS, surviving, strict=True) if flag
        ],
        "identity_estimability": id_estimability,
        "calibration_rows": int(len(cal_y)),
        "heldout_rows_total": int(len(pooled_y_array)),
        "heldout_positive": held_positive_total,
        "heldout_negative": held_negative_total,
        "heldout_years_with_both_classes": held_years_both,
        "annual_metrics": heldout_rows,
        "macro_year_logloss": macro_logloss,
        "pooled_metrics": pooled_metrics,
        "identity_macro_delta_vs_compression": identity_delta,
        "identity_better_years_vs_compression": identity_better_years,
        "identity_predictive_value_status": identity_status,
        "identity_better_years_vs_best_external": external_better_years,
        "external_predictive_added_value_status": external_status,
        "model_feature_state": {
            "ifm_logistic_kept_columns": ifm_fit.keep.tolist(),
            "compression_logistic_kept_columns": compression_fit.keep.tolist(),
            "identity_logistic_kept_columns": None if identity_fit is None else identity_fit.keep.tolist(),
        },
        "decision_boundary": "No model/world/split/metric retuning after population response access.",
    }
    result["fingerprint"] = canonical_sha256(result)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    annual_csv = args.output.with_name("glanville_eogwf_annual_metrics.csv")
    model_names = ["compression", "ifm", "rf"] + (["identity"] if identity_fit is not None else [])
    with annual_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["source_year", "target_year", "sources", "candidates", "positives", "negatives", "surviving_before"]
            + [f"{model}_logloss" for model in model_names]
            + [f"{model}_brier" for model in model_names]
            + [f"{model}_auc" for model in model_names]
        )
        for row in heldout_rows:
            writer.writerow(
                [
                    row["transition"][0],
                    row["transition"][1],
                    row["sources"],
                    row["candidates"],
                    row["positives"],
                    row["negatives"],
                    ";".join(row["surviving_before"]),
                ]
                + [row[model]["logloss"] for model in model_names]
                + [row[model]["brier"] for model in model_names]
                + [row[model]["auc"] for model in model_names]
            )

    print(json.dumps(
        {
            "status": result["status"],
            "calibration_positive": cal_positive,
            "calibration_negative": cal_negative,
            "heldout_positive": held_positive_total,
            "heldout_negative": held_negative_total,
            "surviving_world_ids_final": result["surviving_world_ids_final"],
            "identity_estimable": id_estimability["estimable"],
            "macro_year_logloss": macro_logloss,
            "identity_predictive_value_status": identity_status,
            "external_predictive_added_value_status": external_status,
            "fingerprint": result["fingerprint"],
        },
        indent=2,
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
