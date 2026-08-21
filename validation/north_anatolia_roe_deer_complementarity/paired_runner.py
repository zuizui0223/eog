from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)


ROOT = Path(__file__).resolve().parent


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def git_blob_sha1(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_and_verify(path: Path, *, expected_size: int, expected_blob: str) -> bytes:
    payload = path.read_bytes()
    if len(payload) != int(expected_size):
        raise RuntimeError(f"{path.name} byte size drift: {len(payload)} != {expected_size}")
    observed_blob = git_blob_sha1(payload)
    if observed_blob != expected_blob:
        raise RuntimeError(
            f"{path.name} Git blob drift: {observed_blob} != {expected_blob}"
        )
    return payload


def load_registry(
    stations_path: Path,
    variables_path: Path,
    source: dict,
    geometry_contract: dict,
) -> tuple[list[str], pd.DataFrame, np.ndarray, dict]:
    geometry_source = source["geometry"]
    stations_bytes = read_and_verify(
        stations_path,
        expected_size=geometry_source["stations_size_bytes"],
        expected_blob=geometry_source["stations_git_blob_sha1"],
    )
    variables_bytes = read_and_verify(
        variables_path,
        expected_size=geometry_source["variables_size_bytes"],
        expected_blob=geometry_source["variables_git_blob_sha1"],
    )

    station_reader = csv.DictReader(io.StringIO(stations_bytes.decode("utf-8-sig")))
    expected_station_columns = geometry_contract["geometry_schema"]["stations_columns_exact"]
    if list(station_reader.fieldnames or []) != expected_station_columns:
        raise RuntimeError("stations.csv physical schema drift")
    station_rows = list(station_reader)
    station_col = geometry_contract["geometry_schema"]["station_name_column"]
    raw_stations = [str(row[station_col]).strip() for row in station_rows]
    if len(raw_stations) != geometry_contract["analysis_registry"]["raw_station_count"]:
        raise RuntimeError("raw station count drift")
    if any(not value for value in raw_stations) or len(set(raw_stations)) != len(raw_stations):
        raise RuntimeError("raw station registry must be unique and non-empty")

    variables = pd.read_csv(
        io.BytesIO(variables_bytes),
        dtype=str,
        keep_default_na=False,
    )
    missing = [
        name
        for name in geometry_contract["geometry_schema"]["variable_required_columns"]
        if name not in variables.columns
    ]
    if missing:
        raise RuntimeError(f"variable_data.csv missing frozen fields: {missing}")
    if len(variables) != len(raw_stations):
        raise RuntimeError("variable_data.csv row count differs from raw station registry")
    if variables["Station"].duplicated().any() or (variables["Station"].str.strip() == "").any():
        raise RuntimeError("variable_data.csv Station values must be unique/non-empty")
    variables = variables.set_index("Station", drop=False)
    if set(variables.index) != set(raw_stations):
        raise RuntimeError("stations.csv and variable_data.csv do not define the same raw registry")

    excluded = set(geometry_contract["analysis_registry"]["excluded_station_names"])
    retained = [station for station in raw_stations if station not in excluded]
    if len(retained) != geometry_contract["analysis_registry"]["expected_analysis_node_count"]:
        raise RuntimeError("frozen analysis registry does not close at 171 nodes")
    variables = variables.loc[retained].copy()

    east = pd.to_numeric(variables["Easting"], errors="raise").to_numpy(float)
    north = pd.to_numeric(variables["Northing"], errors="raise").to_numpy(float)
    zones = pd.to_numeric(variables["Zone"], errors="raise").to_numpy(float)
    if not np.isfinite(east).all() or not np.isfinite(north).all() or not np.isfinite(zones).all():
        raise RuntimeError("retained coordinates/zone must be finite")
    if len(set(zones.tolist())) != 1:
        raise RuntimeError("retained nodes span multiple UTM zones")
    distance = np.hypot(east[:, None] - east[None, :], north[:, None] - north[None, :]) / 1000.0
    np.fill_diagonal(distance, 0.0)

    registry_payload = {
        "station_names": retained,
        "excluded_station_names": sorted(excluded),
        "common_utm_zone": float(zones[0]),
    }
    metadata = {
        "raw_station_names": raw_stations,
        "retained_station_names": retained,
        "registry_fingerprint": canonical_sha256(registry_payload),
        "stations_sha256": hashlib.sha256(stations_bytes).hexdigest(),
        "variables_sha256": hashlib.sha256(variables_bytes).hexdigest(),
    }
    return raw_stations, variables, distance, metadata


def load_effort(
    effort_path: Path,
    source: dict,
    contract: dict,
) -> np.ndarray:
    frozen = source["response_independent_predictors"]["camtrap_effort_Ndays.csv"]
    payload = read_and_verify(
        effort_path,
        expected_size=frozen["size_bytes"],
        expected_blob=frozen["git_blob_sha1"],
    )
    frame = pd.read_csv(io.BytesIO(payload), dtype=str, keep_default_na=False)
    required = {"ndays", "site", "pocc"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"effort file missing frozen fields: {sorted(required - set(frame.columns))}")
    if len(frame) != contract["effort_semantics"]["expected_rows"]:
        raise RuntimeError("effort row count drift")

    n_nodes = 171
    n_primary = 22
    effort = np.full((n_nodes, n_primary), np.nan, dtype=float)
    for row in frame.itertuples(index=False):
        site = int(getattr(row, "site"))
        pocc = int(getattr(row, "pocc"))
        ndays = float(getattr(row, "ndays"))
        if not (1 <= site <= n_nodes and 1 <= pocc <= n_primary):
            raise RuntimeError("effort site/pocc outside frozen range")
        if not math.isfinite(ndays) or ndays < 0:
            raise RuntimeError("effort ndays must be finite and non-negative")
        if math.isfinite(effort[site - 1, pocc - 1]):
            raise RuntimeError("duplicate effort site/pocc row")
        effort[site - 1, pocc - 1] = ndays
    if not np.isfinite(effort).all():
        raise RuntimeError("effort matrix is not complete over 171x22")
    return effort


def parse_response_counts(
    response_path: Path,
    source: dict,
    contract: dict,
    raw_stations: list[str],
    retained_stations: list[str],
) -> tuple[np.ndarray, dict]:
    response_frozen = source["response"]
    payload = read_and_verify(
        response_path,
        expected_size=response_frozen["size_bytes"],
        expected_blob=response_frozen["git_blob_sha1"],
    )
    frame = pd.read_csv(
        io.BytesIO(payload),
        dtype=str,
        keep_default_na=False,
        index_col=0,
    )
    observed_columns = [str(value).strip() for value in frame.columns]
    if observed_columns != raw_stations:
        raise RuntimeError("response physical station header differs from frozen raw registry")
    if len(frame) != contract["response_semantics"]["expected_month_rows"]:
        raise RuntimeError("response month-row count drift")
    expected_index = [str(value) for value in range(1, 111)]
    observed_index = [str(value).strip() for value in frame.index]
    if observed_index != expected_index:
        raise RuntimeError("response month index differs from frozen integers 1..110")

    counts = np.full(frame.shape, np.nan, dtype=float)
    allowed_missing = set(contract["response_semantics"]["allowed_missing_tokens_after_csv_parsing"])
    for row_index in range(frame.shape[0]):
        for column_index in range(frame.shape[1]):
            token = str(frame.iat[row_index, column_index]).strip()
            if token in allowed_missing:
                continue
            try:
                value = float(token)
            except ValueError as exc:
                raise RuntimeError(f"unexpected response token {token!r}") from exc
            if not math.isfinite(value) or value < 0 or not float(value).is_integer():
                raise RuntimeError(f"response count must be finite non-negative integer: {token!r}")
            counts[row_index, column_index] = value

    retained_indices = [raw_stations.index(station) for station in retained_stations]
    retained_counts = counts[:, retained_indices]
    if retained_counts.shape != (110, 171):
        raise RuntimeError("retained response matrix must be 110x171")
    season_detect = np.any(
        np.nan_to_num(retained_counts, nan=0.0).reshape(22, 5, 171) > 0,
        axis=1,
    ).T
    response_meta = {
        "size_bytes": len(payload),
        "git_blob_sha1": git_blob_sha1(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "raw_shape": list(counts.shape),
        "retained_shape": list(retained_counts.shape),
    }
    return season_detect.astype(bool), response_meta


def make_synthetic_response(
    effort: np.ndarray,
    distance: np.ndarray,
    broad_threshold_km: float,
) -> np.ndarray:
    """Create response-free deterministic smoke data that keeps the broad world feasible."""

    n_nodes, n_primary = effort.shape
    detected = np.zeros((n_nodes, n_primary), dtype=bool)
    initial_eligible = np.flatnonzero(effort[:, 0] > 0)
    detected[initial_eligible[::7], 0] = True
    if not detected[:, 0].any() and len(initial_eligible):
        detected[initial_eligible[0], 0] = True

    for t in range(n_primary - 1):
        source = detected[:, t] & (effort[:, t] > 0)
        if not source.any():
            eligible_source = np.flatnonzero(effort[:, t] > 0)
            if len(eligible_source):
                source[eligible_source[0]] = True
                detected[eligible_source[0], t] = True
        broad_reach = np.any(distance[:, source] <= broad_threshold_km, axis=1) if source.any() else np.zeros(n_nodes, dtype=bool)
        candidates = (~detected[:, t]) & (effort[:, t] > 0) & (effort[:, t + 1] > 0) & broad_reach
        candidate_ids = np.flatnonzero(candidates)
        selected = candidate_ids[((candidate_ids + 3 * t) % 4) == 0]
        if len(selected) < min(12, len(candidate_ids)):
            selected = candidate_ids[: min(max(12, len(selected)), len(candidate_ids))]
        detected[selected, t + 1] = True

    return detected


def static_baseline_matrix(
    variables: pd.DataFrame,
    retained_stations: list[str],
    contract: dict,
) -> tuple[np.ndarray, list[str], dict]:
    baseline = contract["strong_baseline"]
    numeric_names = list(baseline["static_numeric_features"])
    categorical_names = list(baseline["static_categorical_features"])

    numeric_columns: list[np.ndarray] = []
    feature_names: list[str] = []
    for name in numeric_names:
        if name not in variables.columns:
            raise RuntimeError(f"missing frozen static numeric predictor {name}")
        values = pd.to_numeric(variables[name], errors="raise").to_numpy(float)
        if not np.isfinite(values).all():
            raise RuntimeError(f"static numeric predictor {name} contains missing/non-finite values")
        numeric_columns.append(values)
        feature_names.append(name)

    categorical_values: dict[str, list[str]] = {}
    raw_categories: dict[str, list[str]] = {}
    prefix_values = [station[:3] for station in retained_stations]
    expected_prefixes = ["TAC", "TAR", "TBA", "TDA", "TEL", "TIL", "TKA", "TKG", "TTO", "TUL"]
    if sorted(set(prefix_values)) != expected_prefixes:
        raise RuntimeError("study-area prefix derivation no longer produces the frozen ten-area structure")
    categorical_values["study_area_prefix"] = prefix_values

    for name in categorical_names:
        if name == "study_area_prefix":
            values = prefix_values
        else:
            if name not in variables.columns:
                raise RuntimeError(f"missing frozen static categorical predictor {name}")
            values = [str(value).strip() for value in variables[name].tolist()]
            if any(value == "" for value in values):
                raise RuntimeError(f"static categorical predictor {name} contains empty values")
        categories = sorted(set(values))
        raw_categories[name] = categories
        categorical_values[name] = values

    onehot_columns: list[np.ndarray] = []
    for name in categorical_names:
        values = np.asarray(categorical_values[name], dtype=object)
        for category in raw_categories[name]:
            onehot_columns.append((values == category).astype(float))
            feature_names.append(f"{name}=={category}")

    static = np.column_stack([*numeric_columns, *onehot_columns]).astype(float)
    if not np.isfinite(static).all():
        raise RuntimeError("frozen static baseline matrix is not finite")
    meta = {
        "static_feature_names": feature_names,
        "categorical_levels": raw_categories,
        "feature_fingerprint": canonical_sha256(
            {
                "feature_names": feature_names,
                "categorical_levels": raw_categories,
                "registry": retained_stations,
            }
        ),
    }
    return static, feature_names, meta


def dynamic_baseline_features(
    candidate_indices: np.ndarray,
    transition_index: int,
    season_detect: np.ndarray,
    effort: np.ndarray,
    sentinel: int,
) -> np.ndarray:
    source_t = transition_index
    target_t = transition_index + 1
    primary_number = target_t + 1
    target_winter = 1.0 if primary_number % 2 == 1 else 0.0
    prior_count = season_detect[:, : source_t + 1].sum(axis=1).astype(float)
    since_last = np.full(season_detect.shape[0], float(sentinel), dtype=float)
    for node in range(season_detect.shape[0]):
        previous = np.flatnonzero(season_detect[node, : source_t + 1])
        if len(previous):
            since_last[node] = float(source_t - int(previous[-1]))
    return np.column_stack(
        [
            np.full(len(candidate_indices), target_winter, dtype=float),
            effort[candidate_indices, source_t],
            effort[candidate_indices, target_t],
            prior_count[candidate_indices],
            since_last[candidate_indices],
        ]
    )


def world_supports(
    distance: np.ndarray,
    source_mask: np.ndarray,
    worlds: list[dict],
) -> dict[str, np.ndarray]:
    supports: dict[str, np.ndarray] = {}
    source_indices = np.flatnonzero(source_mask)
    for world in worlds:
        if len(source_indices) == 0:
            support = np.zeros(distance.shape[0], dtype=float)
        else:
            support = np.mean(
                distance[:, source_indices] <= float(world["threshold_km"]),
                axis=1,
            ).astype(float)
        supports[world["world_id"]] = support
    return supports


def layer_b_matrix(
    node_ids: list[str],
    candidate_indices: np.ndarray,
    source_mask: np.ndarray,
    supports: dict[str, np.ndarray],
    worlds: list[dict],
    surviving_world_ids: list[str],
    transition_index: int,
    gate_fingerprint: str,
) -> np.ndarray:
    if not surviving_world_ids:
        raise RuntimeError("cannot summarize an empty surviving world set")
    world_fingerprints = tuple(canonical_sha256(world) for world in worlds)
    members = []
    for world_id in surviving_world_ids:
        support = supports[world_id]
        cumulative = np.stack([source_mask.astype(float), support], axis=0)
        supported = cumulative > 0.0
        members.append(
            SimpleNamespace(
                cumulative_reachability=cumulative,
                supported_state=supported,
            )
        )
    source_ids = [node_ids[index] for index in np.flatnonzero(source_mask)]
    forecast = SimpleNamespace(
        node_ids=tuple(node_ids),
        max_steps=1,
        members=tuple(members),
        world_fingerprints=world_fingerprints,
        gate_declaration=SimpleNamespace(fingerprint=gate_fingerprint),
        fingerprint=canonical_sha256(
            {
                "transition_index": transition_index,
                "surviving_world_ids": surviving_world_ids,
                "source_ids": source_ids,
            }
        ),
    )
    summary = summarize_worldset_for_prediction(forecast, step=1)
    matrix = summary.feature_matrix[candidate_indices, :]
    if matrix.shape[1] != len(PREDICTIVE_FEATURE_NAMES):
        raise RuntimeError("Layer-B production feature width drift")
    return matrix


def transition_rows(
    transition_index: int,
    season_detect: np.ndarray,
    effort: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    source_t = transition_index
    target_t = transition_index + 1
    source_mask = season_detect[:, source_t] & (effort[:, source_t] > 0)
    candidates = (
        (~season_detect[:, source_t])
        & (effort[:, source_t] > 0)
        & (effort[:, target_t] > 0)
    )
    candidate_indices = np.flatnonzero(candidates)
    y = season_detect[candidate_indices, target_t].astype(int)
    return source_mask, candidate_indices, y


def apply_world_update(
    surviving_world_ids: list[str],
    supports: dict[str, np.ndarray],
    candidate_indices: np.ndarray,
    y: np.ndarray,
) -> list[str]:
    positives = candidate_indices[y == 1]
    if len(positives) == 0:
        return list(surviving_world_ids)
    kept = []
    for world_id in surviving_world_ids:
        if np.all(supports[world_id][positives] > 0.0):
            kept.append(world_id)
    return kept


def count_gate(
    season_detect: np.ndarray,
    effort: np.ndarray,
    contract: dict,
) -> dict:
    split = contract["transition_split"]
    gate = contract["exact_count_gate"]
    by_transition = []
    for transition_index in range(21):
        _, candidates, y = transition_rows(transition_index, season_detect, effort)
        by_transition.append(
            {
                "transition_index": transition_index,
                "candidate_count": int(len(candidates)),
                "events": int(np.sum(y == 1)),
                "non_events": int(np.sum(y == 0)),
                "both_classes": bool(len(y) > 0 and np.any(y == 1) and np.any(y == 0)),
            }
        )
    calibration_ids = set(split["calibration_transition_indices_zero_based"])
    heldout_ids = set(split["heldout_transition_indices_zero_based"])
    cal = [row for row in by_transition if row["transition_index"] in calibration_ids]
    hold = [row for row in by_transition if row["transition_index"] in heldout_ids]
    totals = {
        "calibration_events": sum(row["events"] for row in cal),
        "calibration_non_events": sum(row["non_events"] for row in cal),
        "heldout_events": sum(row["events"] for row in hold),
        "heldout_non_events": sum(row["non_events"] for row in hold),
        "heldout_outer_units_with_both_classes": sum(row["both_classes"] for row in hold),
    }
    passed = (
        totals["calibration_events"] >= gate["minimum_calibration_events"]
        and totals["calibration_non_events"] >= gate["minimum_calibration_non_events"]
        and totals["heldout_events"] >= gate["minimum_heldout_events"]
        and totals["heldout_non_events"] >= gate["minimum_heldout_non_events"]
        and totals["heldout_outer_units_with_both_classes"]
        >= gate["minimum_heldout_outer_units_with_both_classes"]
    )
    return {
        "passed": bool(passed),
        "totals": totals,
        "by_transition": by_transition,
        "thresholds": gate,
    }


def fit_probability(model: RandomForestClassifier, matrix: np.ndarray) -> np.ndarray:
    probabilities = model.predict_proba(matrix)
    classes = list(model.classes_)
    if classes != [0, 1]:
        raise RuntimeError(f"fitted RF classes drifted from [0,1]: {classes}")
    return probabilities[:, 1]


def build_rf(contract: dict) -> RandomForestClassifier:
    b = contract["strong_baseline"]
    return RandomForestClassifier(
        n_estimators=int(b["n_estimators"]),
        max_features=b["max_features"],
        min_samples_leaf=int(b["min_samples_leaf"]),
        class_weight=b["class_weight"],
        random_state=int(b["random_state"]),
        n_jobs=int(b["n_jobs"]),
    )


def run(
    *,
    mode: str,
    stations_path: Path,
    variables_path: Path,
    effort_path: Path,
    response_path: Path | None,
) -> dict:
    contract = load_json(ROOT / "gate2_prediction_contract.json")
    source = load_json(ROOT / "source_freeze.json")
    geometry_contract = load_json(ROOT / "geometry_gate_contract.json")
    geometry_result = load_json(ROOT / "geometry_gate_result_freeze.json")

    if source["response_content_opened"] is not False or contract["response_content_opened"] is not False:
        raise RuntimeError("runner contract is not response-blind at freeze time")

    raw_stations, variables, distance, registry_meta = load_registry(
        stations_path, variables_path, source, geometry_contract
    )
    retained = registry_meta["retained_station_names"]
    if registry_meta["registry_fingerprint"] != geometry_result["analysis_registry_fingerprint"]:
        raise RuntimeError("analysis registry fingerprint differs from frozen passing geometry gate")

    effort = load_effort(effort_path, source, contract)
    worlds = list(contract["layer_a"]["declared_worlds"])
    broad_threshold = max(float(world["threshold_km"]) for world in worlds)

    response_meta = None
    if mode == "smoke":
        season_detect = make_synthetic_response(effort, distance, broad_threshold)
    elif mode == "actual":
        if response_path is None:
            raise RuntimeError("actual mode requires --response")
        season_detect, response_meta = parse_response_counts(
            response_path, source, contract, raw_stations, retained
        )
    else:
        raise ValueError(f"unsupported mode: {mode}")

    gate_result = count_gate(season_detect, effort, contract)
    result = {
        "mode": mode,
        "candidate": contract["candidate"],
        "response_opened": mode == "actual",
        "response_meta": response_meta,
        "count_gate": gate_result,
        "model_fit_count": 0,
        "heldout_score_count": 0,
        "status": "stop_exact_count_gate_failed" if not gate_result["passed"] else "count_gate_passed",
    }
    if not gate_result["passed"]:
        result["fingerprint"] = canonical_sha256(result)
        return result

    static, static_names, static_meta = static_baseline_matrix(
        variables, retained, contract
    )
    dynamic_names = list(contract["strong_baseline"]["dynamic_features_known_before_target_outcome"])
    base_feature_names = static_names + dynamic_names
    if len(base_feature_names) != static.shape[1] + 5:
        raise RuntimeError("baseline feature-name width drift")

    surviving = [world["world_id"] for world in worlds]
    calibration_base: list[np.ndarray] = []
    calibration_augmented: list[np.ndarray] = []
    calibration_y: list[np.ndarray] = []
    calibration_audit: list[dict] = []
    sentinel = int(contract["strong_baseline"]["never_detected_sentinel_for_seasons_since_last"])
    gate_fingerprint = geometry_result["level90_gate_fingerprint"]

    for transition_index in contract["transition_split"]["calibration_transition_indices_zero_based"]:
        source_mask, candidate_indices, y = transition_rows(transition_index, season_detect, effort)
        supports = world_supports(distance, source_mask, worlds)
        if not surviving:
            result["status"] = "stop_world_universe_falsified_during_calibration"
            result["calibration_audit"] = calibration_audit
            result["fingerprint"] = canonical_sha256(result)
            return result
        layer_b = layer_b_matrix(
            retained,
            candidate_indices,
            source_mask,
            supports,
            worlds,
            surviving,
            transition_index,
            gate_fingerprint,
        )
        dynamic = dynamic_baseline_features(
            candidate_indices, transition_index, season_detect, effort, sentinel
        )
        base = np.column_stack([static[candidate_indices, :], dynamic])
        calibration_base.append(base)
        calibration_augmented.append(np.column_stack([base, layer_b]))
        calibration_y.append(y)
        before = list(surviving)
        surviving = apply_world_update(surviving, supports, candidate_indices, y)
        calibration_audit.append(
            {
                "transition_index": transition_index,
                "candidate_count": int(len(candidate_indices)),
                "event_count": int(np.sum(y == 1)),
                "surviving_before": before,
                "surviving_after": list(surviving),
            }
        )

    if not surviving:
        result["status"] = "stop_world_universe_falsified_during_calibration"
        result["calibration_audit"] = calibration_audit
        result["fingerprint"] = canonical_sha256(result)
        return result

    x_base = np.vstack(calibration_base)
    x_aug = np.vstack(calibration_augmented)
    y_cal = np.concatenate(calibration_y)
    if set(np.unique(y_cal).tolist()) != {0, 1}:
        raise RuntimeError("count gate passed but pooled calibration response lacks both classes")

    baseline_model = build_rf(contract)
    augmented_model = build_rf(contract)
    baseline_model.fit(x_base, y_cal)
    augmented_model.fit(x_aug, y_cal)
    result["model_fit_count"] = 2

    paired_scores: list[PairedOuterUnitScore] = []
    heldout_audit: list[dict] = []
    for heldout_position, transition_index in enumerate(
        contract["transition_split"]["heldout_transition_indices_zero_based"]
    ):
        if not surviving:
            result["status"] = "stop_world_universe_falsified_mid_heldout"
            break
        source_mask, candidate_indices, y = transition_rows(transition_index, season_detect, effort)
        supports = world_supports(distance, source_mask, worlds)
        layer_b = layer_b_matrix(
            retained,
            candidate_indices,
            source_mask,
            supports,
            worlds,
            surviving,
            transition_index,
            gate_fingerprint,
        )
        dynamic = dynamic_baseline_features(
            candidate_indices, transition_index, season_detect, effort, sentinel
        )
        base = np.column_stack([static[candidate_indices, :], dynamic])
        aug = np.column_stack([base, layer_b])
        baseline_probability = fit_probability(baseline_model, base)
        augmented_probability = fit_probability(augmented_model, aug)
        baseline_score = float(
            log_loss(y, np.column_stack([1.0 - baseline_probability, baseline_probability]), labels=[0, 1])
        )
        augmented_score = float(
            log_loss(y, np.column_stack([1.0 - augmented_probability, augmented_probability]), labels=[0, 1])
        )
        outer_id = f"transition_{transition_index:02d}_state_{transition_index + 1:02d}_to_{transition_index + 2:02d}"
        paired_scores.append(
            PairedOuterUnitScore(
                outer_unit_id=outer_id,
                baseline_score=baseline_score,
                augmented_score=augmented_score,
            )
        )
        before = list(surviving)
        surviving = apply_world_update(surviving, supports, candidate_indices, y)
        heldout_audit.append(
            {
                "heldout_position": heldout_position,
                "transition_index": transition_index,
                "candidate_count": int(len(candidate_indices)),
                "events": int(np.sum(y == 1)),
                "non_events": int(np.sum(y == 0)),
                "baseline_logloss": baseline_score,
                "augmented_logloss": augmented_score,
                "surviving_before": before,
                "surviving_after": list(surviving),
            }
        )

    result["heldout_score_count"] = len(paired_scores) * 2
    result["calibration_audit"] = calibration_audit
    result["heldout_audit"] = heldout_audit
    result["surviving_world_ids_final"] = list(surviving)
    result["baseline_feature_names"] = base_feature_names
    result["baseline_feature_fingerprint"] = static_meta["feature_fingerprint"]
    result["layer_b_feature_names"] = list(PREDICTIVE_FEATURE_NAMES)

    if len(paired_scores) != contract["transition_split"]["heldout_outer_unit_count"]:
        result["status"] = "incomplete_paired_endpoint"
        result["fingerprint"] = canonical_sha256(result)
        return result

    declaration = PredictiveComplementarityDeclaration(
        metric_name=contract["metric_and_decision"]["primary_metric"],
        lower_is_better=True,
        expected_outer_unit_count=contract["transition_split"]["heldout_outer_unit_count"],
        favorable_min_augmented_wins=contract["metric_and_decision"]["favorable_minimum_augmented_outer_unit_wins"],
        adverse_min_baseline_wins=contract["metric_and_decision"]["adverse_minimum_baseline_outer_unit_wins"],
        learner_fit_fingerprint=canonical_sha256(contract["strong_baseline"]),
        response_endpoint_fingerprint=canonical_sha256(
            {
                "scientific_estimand": contract["scientific_estimand"],
                "response_semantics": contract["response_semantics"],
                "effort_semantics": contract["effort_semantics"],
            }
        ),
        split_fingerprint=canonical_sha256(
            {
                "transition_split": contract["transition_split"],
                "exact_count_gate": contract["exact_count_gate"],
            }
        ),
        external_feature_fingerprint=canonical_sha256(
            {
                "strong_baseline": contract["strong_baseline"],
                "static_feature_fingerprint": static_meta["feature_fingerprint"],
            }
        ),
        eog_feature_fingerprint=canonical_sha256(
            {
                "layer_a": contract["layer_a"],
                "layer_b": contract["layer_b"],
                "geometry_gate": geometry_result["scale_ladder_fingerprint"],
            }
        ),
    )
    complementarity = evaluate_predictive_complementarity(
        declaration,
        paired_scores,
        tie_tolerance=float(contract["metric_and_decision"]["tie_tolerance"]),
    )
    result["status"] = complementarity.status
    result["complementarity"] = asdict(complementarity)
    result["declaration_fingerprint"] = declaration.fingerprint
    result["paired_scores"] = [asdict(row) for row in paired_scores]
    result["fingerprint"] = canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "actual"), required=True)
    parser.add_argument("--stations", type=Path, required=True)
    parser.add_argument("--variables", type=Path, required=True)
    parser.add_argument("--effort", type=Path, required=True)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = run(
        mode=args.mode,
        stations_path=args.stations,
        variables_path=args.variables,
        effort_path=args.effort,
        response_path=args.response,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
