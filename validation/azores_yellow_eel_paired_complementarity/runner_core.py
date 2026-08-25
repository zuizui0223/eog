from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from types import SimpleNamespace
from typing import Iterable, Mapping, Sequence

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
    "week_index",
    "week_index_squared",
    "week_sin",
    "week_cos",
    "longitude_centered_km",
    "latitude_centered_km",
    "active_days",
    "degree_geo1",
    "degree_geo2",
    "degree_geo3",
    "release_anchor_tag_count",
    "nearest_release_anchor_distance_km",
    "release_anchor_exposure_geo3",
    "previous_week_detected",
    "weeks_since_last_detection",
    "cumulative_prior_detected_weeks",
    "previous_week_detected_receiver_count",
    "previous_week_source_count_geo1",
    "previous_week_source_count_geo2",
    "previous_week_source_count_geo3",
    "previous_week_source_exposure_geo1",
    "previous_week_source_exposure_geo2",
    "previous_week_source_exposure_geo3",
    "cumulative_prior_global_detected_receiver_weeks",
)


class AllWorldsEliminated(RuntimeError):
    pass


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
    station: str
    week_index: int
    week_start: str
    conventional: tuple[float, ...]
    layer_b: tuple[float, ...]
    label: int


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


def haversine_km(a: tuple[float, float], b: tuple[float, float], radius: float = 6371.0088) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(h)))


def distance_matrix(stations: Sequence[str], coordinates: Mapping[str, tuple[float, float]]) -> np.ndarray:
    matrix = np.zeros((len(stations), len(stations)), dtype=float)
    for i, first in enumerate(stations):
        for j in range(i + 1, len(stations)):
            second = stations[j]
            value = haversine_km(coordinates[first], coordinates[second])
            matrix[i, j] = matrix[j, i] = value
    return matrix


def adjacency_matrices(distances: np.ndarray, thresholds: Sequence[float]) -> tuple[np.ndarray, ...]:
    result = []
    for threshold in thresholds:
        adjacency = np.asarray(distances <= float(threshold) + 1e-12, dtype=bool)
        np.fill_diagonal(adjacency, False)
        result.append(adjacency)
    return tuple(result)


def declared_world_ids() -> tuple[str, ...]:
    return tuple(
        f"geo{geometry_index}::{source_mode}"
        for geometry_index in (1, 2, 3)
        for source_mode in ("observed_only", "release_persistence")
    )


def _source_set(
    *,
    source_mode: str,
    week_index: int,
    release_anchor_stations: set[str],
    previous_positive_stations: set[str],
) -> set[str]:
    if week_index == 0:
        return set(release_anchor_stations)
    if source_mode == "observed_only":
        return set(previous_positive_stations)
    if source_mode == "release_persistence":
        return set(release_anchor_stations) | set(previous_positive_stations)
    raise ValueError(f"unsupported source mode: {source_mode}")


def world_supports(
    stations: Sequence[str],
    adjacencies: Sequence[np.ndarray],
    *,
    week_index: int,
    release_anchor_stations: set[str],
    previous_positive_stations: set[str],
    surviving_world_ids: Sequence[str],
) -> dict[str, np.ndarray]:
    station_index = {station: index for index, station in enumerate(stations)}
    supports: dict[str, np.ndarray] = {}
    for world_id in surviving_world_ids:
        geometry_token, source_mode = world_id.split("::", 1)
        geometry_index = int(geometry_token.removeprefix("geo")) - 1
        adjacency = np.asarray(adjacencies[geometry_index], dtype=bool)
        sources = _source_set(
            source_mode=source_mode,
            week_index=week_index,
            release_anchor_stations=release_anchor_stations,
            previous_positive_stations=previous_positive_stations,
        )
        support = np.zeros(len(stations), dtype=bool)
        for source in sorted(sources):
            if source not in station_index:
                raise ValueError(f"source station outside frozen registry: {source}")
            source_index = station_index[source]
            support[source_index] = True
            support |= adjacency[source_index]
        supports[world_id] = support
    return supports


def layer_b_summary(
    stations: Sequence[str],
    supports: Mapping[str, np.ndarray],
    *,
    structural_gate_fingerprint: str,
) -> dict[str, tuple[float, ...]]:
    if not supports:
        raise AllWorldsEliminated("no surviving world remains before current-week prediction")
    declared = declared_world_ids()
    members = []
    member_payload = []
    for world_id in sorted(supports):
        support = np.asarray(supports[world_id], dtype=bool)
        if support.shape != (len(stations),):
            raise ValueError("world support has incompatible station shape")
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
        node_ids=tuple(stations),
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
    stations: Sequence[str],
    positive_stations: set[str],
) -> tuple[str, ...]:
    station_index = {station: index for index, station in enumerate(stations)}
    positive_indices = [station_index[station] for station in sorted(positive_stations)]
    kept = []
    for world_id in surviving_world_ids:
        support = supports[world_id]
        if all(bool(support[index]) for index in positive_indices):
            kept.append(world_id)
    return tuple(kept)


def exact_count_gate(
    labels: Mapping[tuple[str, str], int],
    *,
    calibration_weeks: Sequence[str],
    heldout_weeks: Sequence[str],
    primary_outer_units: Sequence[Sequence[str]],
    minima: Mapping[str, int],
) -> CountGateResult:
    calibration_set = set(calibration_weeks)
    heldout_set = set(heldout_weeks)
    calibration_values = [int(value) for (week, _station), value in labels.items() if week in calibration_set]
    heldout_values = [int(value) for (week, _station), value in labels.items() if week in heldout_set]
    calibration_events = sum(calibration_values)
    heldout_events = sum(heldout_values)
    calibration_non_events = len(calibration_values) - calibration_events
    heldout_non_events = len(heldout_values) - heldout_events
    both_class_blocks = 0
    for block in primary_outer_units:
        block_set = set(block)
        values = [int(value) for (week, _station), value in labels.items() if week in block_set]
        if values and 0 in values and 1 in values:
            both_class_blocks += 1
    passed = (
        calibration_events >= int(minima["calibration_events_min"])
        and calibration_non_events >= int(minima["calibration_non_events_min"])
        and heldout_events >= int(minima["heldout_events_min"])
        and heldout_non_events >= int(minima["heldout_non_events_min"])
        and both_class_blocks >= int(minima["primary_outer_units_with_both_classes_min"])
    )
    return CountGateResult(
        passed=passed,
        calibration_events=calibration_events,
        calibration_non_events=calibration_non_events,
        heldout_events=heldout_events,
        heldout_non_events=heldout_non_events,
        primary_outer_units_with_both_classes=both_class_blocks,
    )


def _coordinate_features(
    stations: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    mean_lat = float(np.mean([coordinates[station][0] for station in stations]))
    mean_lon = float(np.mean([coordinates[station][1] for station in stations]))
    lon_scale = math.cos(math.radians(mean_lat)) * 111.32
    return {
        station: (
            (coordinates[station][1] - mean_lon) * lon_scale,
            (coordinates[station][0] - mean_lat) * 110.574,
        )
        for station in stations
    }


def build_prepared_rows(
    *,
    stations: Sequence[str],
    week_starts: Sequence[str],
    eligible_active_days: Mapping[tuple[str, str], int],
    labels: Mapping[tuple[str, str], int],
    coordinates: Mapping[str, tuple[float, float]],
    thresholds: Sequence[float],
    release_anchor_by_tag: Mapping[str, str],
    structural_gate_fingerprint: str,
) -> tuple[PreparedRow, ...]:
    distances = distance_matrix(stations, coordinates)
    adjacencies = adjacency_matrices(distances, thresholds)
    station_index = {station: index for index, station in enumerate(stations)}
    coordinate_features = _coordinate_features(stations, coordinates)
    release_anchor_stations = set(release_anchor_by_tag.values())
    release_anchor_counts = {
        station: sum(1 for anchor in release_anchor_by_tag.values() if anchor == station)
        for station in stations
    }
    geo3 = float(thresholds[2])
    release_exposure = {}
    nearest_release = {}
    for station in stations:
        index = station_index[station]
        release_exposure[station] = float(
            sum(
                math.exp(-distances[index, station_index[anchor]] / geo3)
                for anchor in release_anchor_by_tag.values()
            )
        )
        nearest_release[station] = float(
            min(distances[index, station_index[anchor]] for anchor in release_anchor_stations)
        )

    degrees = {
        station: tuple(float(np.sum(adjacency[station_index[station]])) for adjacency in adjacencies)
        for station in stations
    }
    positive_history: dict[str, list[int]] = {station: [] for station in stations}
    previous_positive: set[str] = set()
    cumulative_prior_global = 0
    surviving_world_ids = declared_world_ids()
    prepared: list[PreparedRow] = []

    for week_index, week_start in enumerate(week_starts):
        if not surviving_world_ids:
            raise AllWorldsEliminated(
                f"all worlds were eliminated before week {week_start}; no predictive rescue is allowed"
            )
        supports = world_supports(
            stations,
            adjacencies,
            week_index=week_index,
            release_anchor_stations=release_anchor_stations,
            previous_positive_stations=previous_positive,
            surviving_world_ids=surviving_world_ids,
        )
        layer_b = layer_b_summary(
            stations,
            supports,
            structural_gate_fingerprint=structural_gate_fingerprint,
        )

        for station in stations:
            key = (week_start, station)
            if key not in labels:
                continue
            active_days = int(eligible_active_days[key])
            prior = positive_history[station]
            previous_detected = 1.0 if (week_index > 0 and (week_starts[week_index - 1], station) in labels and labels[(week_starts[week_index - 1], station)] == 1) else 0.0
            weeks_since = float(week_index + 1 if not prior else week_index - prior[-1])
            previous_count = float(len(previous_positive))
            source_counts = []
            source_exposures = []
            focal_index = station_index[station]
            for threshold, adjacency in zip(thresholds, adjacencies, strict=True):
                count = 0
                exposure = 0.0
                for source in previous_positive:
                    source_index = station_index[source]
                    if source == station or adjacency[focal_index, source_index]:
                        count += 1
                    exposure += math.exp(-distances[focal_index, source_index] / float(threshold))
                source_counts.append(float(count))
                source_exposures.append(float(exposure))
            lon_centered, lat_centered = coordinate_features[station]
            conventional = (
                float(week_index),
                float(week_index * week_index),
                math.sin(2.0 * math.pi * week_index / 52.1775),
                math.cos(2.0 * math.pi * week_index / 52.1775),
                float(lon_centered),
                float(lat_centered),
                float(active_days),
                *degrees[station],
                float(release_anchor_counts[station]),
                nearest_release[station],
                release_exposure[station],
                previous_detected,
                weeks_since,
                float(len(prior)),
                previous_count,
                *source_counts,
                *source_exposures,
                float(cumulative_prior_global),
            )
            if len(conventional) != len(CONVENTIONAL_FEATURE_NAMES):
                raise RuntimeError("conventional feature count drift")
            prepared.append(
                PreparedRow(
                    station=station,
                    week_index=week_index,
                    week_start=week_start,
                    conventional=tuple(float(value) for value in conventional),
                    layer_b=layer_b[station],
                    label=int(labels[key]),
                )
            )

        positive_current = {
            station
            for station in stations
            if labels.get((week_start, station)) == 1
        }
        surviving_world_ids = update_surviving_worlds(
            surviving_world_ids,
            supports,
            stations,
            positive_current,
        )
        for station in positive_current:
            positive_history[station].append(week_index)
        cumulative_prior_global += len(positive_current)
        previous_positive = positive_current

    return tuple(prepared)


def binary_log_loss(y_true: Sequence[int], probabilities: Sequence[float], clip: float) -> float:
    if len(y_true) != len(probabilities) or not y_true:
        raise ValueError("log-loss inputs must have equal nonzero length")
    total = 0.0
    for target, probability in zip(y_true, probabilities, strict=True):
        p = min(1.0 - clip, max(clip, float(probability)))
        total += -(int(target) * math.log(p) + (1 - int(target)) * math.log(1.0 - p))
    return total / len(y_true)


def fit_and_score_paired(
    rows: Sequence[PreparedRow],
    *,
    calibration_week_count: int,
    primary_outer_units: Sequence[Sequence[str]],
    hyperparameters: Mapping[str, object],
    probability_clip: float,
    declaration: PredictiveComplementarityDeclaration,
):
    from sklearn.ensemble import RandomForestClassifier

    calibration = [row for row in rows if row.week_index < calibration_week_count]
    heldout = [row for row in rows if row.week_index >= calibration_week_count]
    y_train = np.asarray([row.label for row in calibration], dtype=int)
    if set(y_train.tolist()) != {0, 1}:
        raise ValueError("calibration data must contain both classes")
    x_base = np.asarray([row.conventional for row in calibration], dtype=float)
    x_aug = np.asarray([(*row.conventional, *row.layer_b) for row in calibration], dtype=float)
    base_model = RandomForestClassifier(**dict(hyperparameters))
    aug_model = RandomForestClassifier(**dict(hyperparameters))
    base_model.fit(x_base, y_train)
    aug_model.fit(x_aug, y_train)

    x_base_holdout = np.asarray([row.conventional for row in heldout], dtype=float)
    x_aug_holdout = np.asarray([(*row.conventional, *row.layer_b) for row in heldout], dtype=float)
    base_probability = base_model.predict_proba(x_base_holdout)[:, list(base_model.classes_).index(1)]
    aug_probability = aug_model.predict_proba(x_aug_holdout)[:, list(aug_model.classes_).index(1)]

    scores = []
    for block_index, block in enumerate(primary_outer_units, start=1):
        block_set = set(block)
        indices = [index for index, row in enumerate(heldout) if row.week_start in block_set]
        if not indices:
            raise ValueError(f"primary block {block_index} has zero heldout rows")
        targets = [heldout[index].label for index in indices]
        baseline = binary_log_loss(targets, [base_probability[index] for index in indices], probability_clip)
        augmented = binary_log_loss(targets, [aug_probability[index] for index in indices], probability_clip)
        scores.append(PairedOuterUnitScore(f"block_{block_index}", baseline, augmented))

    result = evaluate_predictive_complementarity(declaration, scores, tie_tolerance=0.0)
    supplementary = {
        "baseline_all_heldout_log_loss": binary_log_loss(
            [row.label for row in heldout], base_probability.tolist(), probability_clip
        ),
        "augmented_all_heldout_log_loss": binary_log_loss(
            [row.label for row in heldout], aug_probability.tolist(), probability_clip
        ),
    }
    return result, tuple(scores), supplementary
