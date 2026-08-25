from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math
from types import SimpleNamespace
from typing import Mapping, Sequence

import numpy as np

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)


CONVENTIONAL_FEATURE_NAMES: tuple[str, ...] = (
    "occasion_index",
    "occasion_index_squared",
    "day_of_year_sin",
    "day_of_year_cos",
    "longitude_centered_km",
    "latitude_centered_km",
    "precipitation",
    "min_air_temp",
    "marsh_Brackish",
    "marsh_Fresh",
    "marsh_Intermediate",
    "marsh_Salt",
    "habitat_Brackish_Salt_Marsh",
    "habitat_Fresh_Intermediate_Marsh",
    "degree_geo1",
    "degree_geo2",
    "degree_geo3",
    "previous_occasion_detected",
    "occasions_since_last_detection",
    "cumulative_prior_detected_occasions",
    "previous_occasion_detected_site_count",
    "previous_source_count_geo1",
    "previous_source_count_geo2",
    "previous_source_count_geo3",
    "previous_source_exposure_geo1",
    "previous_source_exposure_geo2",
    "previous_source_exposure_geo3",
    "cumulative_prior_global_detected_site_occasions",
    "historical_source_count_geo1",
    "historical_source_count_geo2",
    "historical_source_count_geo3",
    "historical_source_exposure_geo1",
    "historical_source_exposure_geo2",
    "historical_source_exposure_geo3",
)


@dataclass(frozen=True)
class CountGateResult:
    passed: bool
    calibration_events: int
    calibration_non_events: int
    heldout_events: int
    heldout_non_events: int
    primary_outer_units_with_both_classes: int


@dataclass(frozen=True)
class PreparedRow:
    site: str
    occasion_index: int
    sample_period: int
    date: str
    conventional: tuple[float, ...]
    layer_b: tuple[float, ...]
    label: int


@dataclass(frozen=True)
class FeatureBuildResult:
    rows: tuple[PreparedRow, ...]
    final_surviving_world_ids: tuple[str, ...]
    local_worlds_eliminated: tuple[str, ...]


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


def haversine_km(
    a: tuple[float, float],
    b: tuple[float, float],
    radius: float = 6371.0088,
) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(h)))


def distance_matrix(
    sites: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
) -> np.ndarray:
    matrix = np.zeros((len(sites), len(sites)), dtype=float)
    for i, first in enumerate(sites):
        for j in range(i + 1, len(sites)):
            second = sites[j]
            value = haversine_km(coordinates[first], coordinates[second])
            matrix[i, j] = matrix[j, i] = value
    return matrix


def adjacency_matrices(
    distances: np.ndarray,
    thresholds: Sequence[float],
) -> tuple[np.ndarray, ...]:
    result: list[np.ndarray] = []
    for threshold in thresholds:
        adjacency = np.asarray(distances <= float(threshold) + 1e-12, dtype=bool)
        np.fill_diagonal(adjacency, False)
        result.append(adjacency)
    return tuple(result)


def declared_world_ids() -> tuple[str, ...]:
    local = tuple(
        f"geo{geometry_index}::{source_mode}"
        for geometry_index in (1, 2, 3)
        for source_mode in (
            "immediate_previous_observed",
            "cumulative_observed_history",
        )
    )
    return (*local, "external_open")


def world_supports(
    sites: Sequence[str],
    adjacencies: Sequence[np.ndarray],
    *,
    previous_positive_sites: set[str],
    historical_positive_sites: set[str],
    surviving_world_ids: Sequence[str],
) -> dict[str, np.ndarray]:
    site_index = {site: index for index, site in enumerate(sites)}
    supports: dict[str, np.ndarray] = {}
    for world_id in surviving_world_ids:
        if world_id == "external_open":
            supports[world_id] = np.ones(len(sites), dtype=bool)
            continue
        geometry_token, source_mode = world_id.split("::", 1)
        geometry_index = int(geometry_token.removeprefix("geo")) - 1
        adjacency = np.asarray(adjacencies[geometry_index], dtype=bool)
        if source_mode == "immediate_previous_observed":
            sources = previous_positive_sites
        elif source_mode == "cumulative_observed_history":
            sources = historical_positive_sites
        else:
            raise ValueError(f"unknown source mode: {source_mode}")
        support = np.zeros(len(sites), dtype=bool)
        for source in sorted(sources):
            if source not in site_index:
                raise ValueError(f"source outside frozen site registry: {source}")
            source_index = site_index[source]
            support[source_index] = True
            support |= adjacency[source_index]
        supports[world_id] = support
    return supports


def layer_b_summary(
    sites: Sequence[str],
    supports: Mapping[str, np.ndarray],
    *,
    structural_gate_fingerprint: str,
) -> dict[str, tuple[float, ...]]:
    if not supports:
        raise RuntimeError("no surviving world exists")
    declared = declared_world_ids()
    members = []
    member_payload = []
    for world_id in sorted(supports):
        support = np.asarray(supports[world_id], dtype=bool)
        if support.shape != (len(sites),):
            raise ValueError("world support has incompatible site shape")
        cumulative = np.stack([support.astype(float), support.astype(float)], axis=0)
        supported = np.stack([support, support], axis=0)
        members.append(
            SimpleNamespace(
                cumulative_reachability=cumulative,
                supported_state=supported,
            )
        )
        member_payload.append([world_id, support.astype(int).tolist()])
    forecast = SimpleNamespace(
        node_ids=tuple(sites),
        max_steps=1,
        members=tuple(members),
        world_fingerprints=tuple(canonical_sha256(world_id) for world_id in declared),
        gate_declaration=SimpleNamespace(fingerprint=structural_gate_fingerprint),
        fingerprint=canonical_sha256(
            {
                "declared_world_ids": list(declared),
                "surviving_supports": member_payload,
                "gate": structural_gate_fingerprint,
            }
        ),
    )
    summary = summarize_worldset_for_prediction(forecast, step=1)
    if summary.feature_names != PREDICTIVE_FEATURE_NAMES:
        raise RuntimeError("package Layer-B feature identity drift")
    return {
        row.node_id: tuple(float(value) for value in row.feature_values)
        for row in summary.rows
    }


def update_surviving_worlds(
    surviving_world_ids: Sequence[str],
    supports: Mapping[str, np.ndarray],
    sites: Sequence[str],
    positive_sites: set[str],
) -> tuple[str, ...]:
    site_index = {site: index for index, site in enumerate(sites)}
    positive_indices = [site_index[site] for site in sorted(positive_sites)]
    kept = []
    for world_id in surviving_world_ids:
        support = np.asarray(supports[world_id], dtype=bool)
        if all(bool(support[index]) for index in positive_indices):
            kept.append(world_id)
    if "external_open" not in kept:
        raise RuntimeError("external-open world was unexpectedly eliminated")
    return tuple(kept)


def exact_count_gate(
    labels: Mapping[tuple[int, str], int],
    *,
    calibration_periods: Sequence[int],
    heldout_periods: Sequence[int],
    primary_outer_units: Sequence[int],
    minima: Mapping[str, int],
) -> CountGateResult:
    calibration_set = set(int(x) for x in calibration_periods)
    heldout_set = set(int(x) for x in heldout_periods)
    calibration_values = [
        int(value)
        for (period, _site), value in labels.items()
        if int(period) in calibration_set
    ]
    heldout_values = [
        int(value)
        for (period, _site), value in labels.items()
        if int(period) in heldout_set
    ]
    calibration_events = sum(calibration_values)
    heldout_events = sum(heldout_values)
    calibration_non_events = len(calibration_values) - calibration_events
    heldout_non_events = len(heldout_values) - heldout_events
    both_class = 0
    for period in primary_outer_units:
        values = [
            int(value)
            for (candidate_period, _site), value in labels.items()
            if int(candidate_period) == int(period)
        ]
        if values and 0 in values and 1 in values:
            both_class += 1
    passed = (
        calibration_events >= int(minima["calibration_events_min"])
        and calibration_non_events >= int(minima["calibration_non_events_min"])
        and heldout_events >= int(minima["heldout_events_min"])
        and heldout_non_events >= int(minima["heldout_non_events_min"])
        and both_class >= int(minima["primary_outer_units_with_both_classes_min"])
    )
    return CountGateResult(
        passed=passed,
        calibration_events=calibration_events,
        calibration_non_events=calibration_non_events,
        heldout_events=heldout_events,
        heldout_non_events=heldout_non_events,
        primary_outer_units_with_both_classes=both_class,
    )


def _coordinate_features(
    sites: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    mean_lat = float(np.mean([coordinates[site][0] for site in sites]))
    mean_lon = float(np.mean([coordinates[site][1] for site in sites]))
    lon_scale = math.cos(math.radians(mean_lat)) * 111.32
    return {
        site: (
            (coordinates[site][1] - mean_lon) * lon_scale,
            (coordinates[site][0] - mean_lat) * 110.574,
        )
        for site in sites
    }


def _day_features(date_text: str) -> tuple[float, float]:
    date = datetime.strptime(date_text, "%Y-%m-%d")
    day_of_year = int(date.strftime("%j"))
    phase = 2.0 * math.pi * (day_of_year - 1) / 365.2425
    return math.sin(phase), math.cos(phase)


def _source_features(
    *,
    focal_index: int,
    source_sites: set[str],
    site_index: Mapping[str, int],
    distances: np.ndarray,
    adjacencies: Sequence[np.ndarray],
    thresholds: Sequence[float],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    counts: list[float] = []
    exposures: list[float] = []
    for threshold, adjacency in zip(thresholds, adjacencies, strict=True):
        count = 0
        exposure = 0.0
        for source in source_sites:
            source_index = site_index[source]
            if source_index == focal_index or bool(adjacency[focal_index, source_index]):
                count += 1
            exposure += math.exp(-distances[focal_index, source_index] / float(threshold))
        counts.append(float(count))
        exposures.append(float(exposure))
    return tuple(counts), tuple(exposures)


def build_prepared_rows(
    *,
    sites: Sequence[str],
    site_coordinates: Mapping[str, tuple[float, float]],
    site_marsh: Mapping[str, str],
    site_habitat: Mapping[str, str],
    samples: Mapping[int, Mapping[str, object]],
    chronological_periods: Sequence[int],
    initialization_period: int,
    labels: Mapping[tuple[int, str], int],
    thresholds: Sequence[float],
    structural_gate_fingerprint: str,
) -> FeatureBuildResult:
    sites = tuple(sites)
    if len(sites) != 33 or len(set(sites)) != 33:
        raise ValueError("frozen site registry must contain 33 unique sites")
    if tuple(chronological_periods)[0] != int(initialization_period):
        raise ValueError("initialization period must be first chronological period")
    distances = distance_matrix(sites, site_coordinates)
    adjacencies = adjacency_matrices(distances, thresholds)
    site_index = {site: index for index, site in enumerate(sites)}
    coordinate_features = _coordinate_features(sites, site_coordinates)
    degrees = {
        site: tuple(
            float(np.sum(adjacency[site_index[site]]))
            for adjacency in adjacencies
        )
        for site in sites
    }

    allowed_marsh = ("Brackish", "Fresh", "Intermediate", "Salt")
    allowed_habitat = ("Brackish-Salt Marsh", "Fresh-Intermediate Marsh")
    if set(site_marsh.values()) - set(allowed_marsh):
        raise ValueError("unexpected Marsh category")
    if set(site_habitat.values()) - set(allowed_habitat):
        raise ValueError("unexpected Habitat category")

    full_periods = tuple(int(x) for x in chronological_periods)
    period_index = {period: index for index, period in enumerate(full_periods)}
    init = int(initialization_period)
    previous_positive = {
        site for site in sites if labels.get((init, site)) == 1
    }
    historical_positive = set(previous_positive)
    positive_history: dict[str, list[int]] = {site: [] for site in sites}
    for site in previous_positive:
        positive_history[site].append(0)
    cumulative_prior_global = len(previous_positive)
    surviving_world_ids = declared_world_ids()
    declared_local = {world for world in surviving_world_ids if world != "external_open"}
    prepared: list[PreparedRow] = []

    previous_period = init
    for period in full_periods[1:]:
        occasion_index = period_index[period]
        supports = world_supports(
            sites,
            adjacencies,
            previous_positive_sites=previous_positive,
            historical_positive_sites=historical_positive,
            surviving_world_ids=surviving_world_ids,
        )
        layer_b = layer_b_summary(
            sites,
            supports,
            structural_gate_fingerprint=structural_gate_fingerprint,
        )
        sample = samples[int(period)]
        date_text = str(sample["date"])
        precipitation = float(sample["precipitation"])
        min_air_temp = float(sample["min_air_temp"])
        day_sin, day_cos = _day_features(date_text)

        for site in sites:
            key = (period, site)
            if key not in labels:
                continue
            prior = positive_history[site]
            previous_detected = 1.0 if labels.get((previous_period, site)) == 1 else 0.0
            since_last = float(occasion_index + 1 if not prior else occasion_index - prior[-1])
            focal_index = site_index[site]
            previous_counts, previous_exposures = _source_features(
                focal_index=focal_index,
                source_sites=previous_positive,
                site_index=site_index,
                distances=distances,
                adjacencies=adjacencies,
                thresholds=thresholds,
            )
            historical_counts, historical_exposures = _source_features(
                focal_index=focal_index,
                source_sites=historical_positive,
                site_index=site_index,
                distances=distances,
                adjacencies=adjacencies,
                thresholds=thresholds,
            )
            lon_centered, lat_centered = coordinate_features[site]
            marsh = site_marsh[site]
            habitat = site_habitat[site]
            conventional = (
                float(occasion_index),
                float(occasion_index * occasion_index),
                float(day_sin),
                float(day_cos),
                float(lon_centered),
                float(lat_centered),
                precipitation,
                min_air_temp,
                float(marsh == "Brackish"),
                float(marsh == "Fresh"),
                float(marsh == "Intermediate"),
                float(marsh == "Salt"),
                float(habitat == "Brackish-Salt Marsh"),
                float(habitat == "Fresh-Intermediate Marsh"),
                *degrees[site],
                previous_detected,
                since_last,
                float(len(prior)),
                float(len(previous_positive)),
                *previous_counts,
                *previous_exposures,
                float(cumulative_prior_global),
                *historical_counts,
                *historical_exposures,
            )
            if len(conventional) != len(CONVENTIONAL_FEATURE_NAMES):
                raise RuntimeError("conventional feature count drift")
            if not np.isfinite(np.asarray(conventional, dtype=float)).all():
                raise RuntimeError("non-finite conventional feature")
            layer_values = layer_b[site]
            if len(layer_values) != len(PREDICTIVE_FEATURE_NAMES):
                raise RuntimeError("Layer-B feature count drift")
            if not np.isfinite(np.asarray(layer_values, dtype=float)).all():
                raise RuntimeError("non-finite Layer-B feature")
            prepared.append(
                PreparedRow(
                    site=site,
                    occasion_index=occasion_index,
                    sample_period=period,
                    date=date_text,
                    conventional=tuple(float(x) for x in conventional),
                    layer_b=tuple(float(x) for x in layer_values),
                    label=int(labels[key]),
                )
            )

        positive_current = {
            site for site in sites if labels.get((period, site)) == 1
        }
        surviving_world_ids = update_surviving_worlds(
            surviving_world_ids,
            supports,
            sites,
            positive_current,
        )
        for site in positive_current:
            positive_history[site].append(occasion_index)
        historical_positive |= positive_current
        previous_positive = positive_current
        cumulative_prior_global += len(positive_current)
        previous_period = period

    surviving_local = {world for world in surviving_world_ids if world != "external_open"}
    eliminated = tuple(sorted(declared_local - surviving_local))
    return FeatureBuildResult(
        rows=tuple(prepared),
        final_surviving_world_ids=tuple(surviving_world_ids),
        local_worlds_eliminated=eliminated,
    )


def binary_log_loss(labels: np.ndarray, probabilities: np.ndarray, clip: float) -> float:
    y = np.asarray(labels, dtype=int)
    p = np.clip(np.asarray(probabilities, dtype=float), float(clip), 1.0 - float(clip))
    if y.shape != p.shape or y.ndim != 1:
        raise ValueError("binary_log_loss requires matching one-dimensional arrays")
    if not np.isin(y, [0, 1]).all():
        raise ValueError("binary_log_loss labels must be 0/1")
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def fit_and_score(
    *,
    rows: Sequence[PreparedRow],
    calibration_periods: Sequence[int],
    heldout_periods: Sequence[int],
    rf_hyperparameters: Mapping[str, object],
    complementarity_declaration: PredictiveComplementarityDeclaration,
    probability_clip: float,
    tie_tolerance: float,
) -> dict:
    from sklearn.ensemble import RandomForestClassifier

    calibration_set = set(int(x) for x in calibration_periods)
    heldout_order = tuple(int(x) for x in heldout_periods)
    calibration_rows = [row for row in rows if row.sample_period in calibration_set]
    heldout_rows = [row for row in rows if row.sample_period in set(heldout_order)]
    if not calibration_rows or not heldout_rows:
        raise RuntimeError("calibration or heldout feature rows are empty")

    y_cal = np.asarray([row.label for row in calibration_rows], dtype=int)
    if len(set(y_cal.tolist())) < 2:
        raise RuntimeError("calibration response has fewer than two classes")
    x_base_cal = np.asarray([row.conventional for row in calibration_rows], dtype=float)
    x_aug_cal = np.asarray(
        [(*row.conventional, *row.layer_b) for row in calibration_rows],
        dtype=float,
    )
    x_base_hold = np.asarray([row.conventional for row in heldout_rows], dtype=float)
    x_aug_hold = np.asarray(
        [(*row.conventional, *row.layer_b) for row in heldout_rows],
        dtype=float,
    )

    params = dict(rf_hyperparameters)
    baseline = RandomForestClassifier(**params)
    augmented = RandomForestClassifier(**params)
    baseline.fit(x_base_cal, y_cal)
    augmented.fit(x_aug_cal, y_cal)
    p_base = baseline.predict_proba(x_base_hold)[:, list(baseline.classes_).index(1)]
    p_aug = augmented.predict_proba(x_aug_hold)[:, list(augmented.classes_).index(1)]

    scores: list[PairedOuterUnitScore] = []
    pooled_labels: list[int] = []
    pooled_base: list[float] = []
    pooled_aug: list[float] = []
    for period in heldout_order:
        indices = [index for index, row in enumerate(heldout_rows) if row.sample_period == period]
        if not indices:
            raise RuntimeError(f"heldout period {period} has zero eligible rows")
        labels_period = np.asarray([heldout_rows[index].label for index in indices], dtype=int)
        base_period = np.asarray([p_base[index] for index in indices], dtype=float)
        aug_period = np.asarray([p_aug[index] for index in indices], dtype=float)
        scores.append(
            PairedOuterUnitScore(
                outer_unit_id=f"period_{period}",
                baseline_score=binary_log_loss(labels_period, base_period, probability_clip),
                augmented_score=binary_log_loss(labels_period, aug_period, probability_clip),
            )
        )
        pooled_labels.extend(labels_period.tolist())
        pooled_base.extend(base_period.tolist())
        pooled_aug.extend(aug_period.tolist())

    result = evaluate_predictive_complementarity(
        complementarity_declaration,
        scores,
        tie_tolerance=float(tie_tolerance),
    )
    return {
        "status": result.status,
        "outer_unit_scores": [
            {
                "outer_unit_id": score.outer_unit_id,
                "baseline_log_loss": score.baseline_score,
                "augmented_log_loss": score.augmented_score,
                "augmented_minus_baseline": score.augmented_score - score.baseline_score,
            }
            for score in scores
        ],
        "baseline_macro_log_loss": result.baseline_macro_score,
        "augmented_macro_log_loss": result.augmented_macro_score,
        "augmented_minus_baseline_macro": result.augmented_minus_baseline,
        "augmented_better_outer_units": result.augmented_better_outer_units,
        "baseline_better_outer_units": result.baseline_better_outer_units,
        "tied_outer_units": result.tied_outer_units,
        "pooled_baseline_log_loss": binary_log_loss(
            np.asarray(pooled_labels), np.asarray(pooled_base), probability_clip
        ),
        "pooled_augmented_log_loss": binary_log_loss(
            np.asarray(pooled_labels), np.asarray(pooled_aug), probability_clip
        ),
        "predictive_complementarity_result_fingerprint": result.fingerprint,
        "model_fit_count": 2,
        "heldout_outer_units_scored": len(scores),
    }
