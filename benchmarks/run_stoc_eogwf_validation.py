#!/usr/bin/env python3
"""Run the prospectively frozen STOC EOG-WF validation once.

The scientific contract is frozen in:
  validation/stoc_eogwf/eligibility_and_preoutcome_contract.json
  validation/stoc_eogwf/preoutcome_amendment_v1_1.json
  validation/stoc_eogwf/preoutcome_amendment_v1_2.json

This runner must not be used to tune thresholds, species, worlds, horizons,
comparators, or decision rules after response access.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss


EXPECTED_BLOB_SHA = "4bfa2cd39a7e90340ad6a319e5c611e8646462c8"
EXPECTED_SIZE = 330891
EXPECTED_ROWS = 2006
EXPECTED_SITES = 1003
EXPECTED_SPECIES = 20
CALIBRATION_PERIOD = "2006-2011"
HELDOUT_PERIOD = "2012-2017"
ENV_COLUMNS = (
    "temp",
    "precip",
    "cover_agri",
    "cover_water",
    "cover_wet",
    "sdiv_hab",
)
META_COLUMNS = ("site", "period", "X_WGS84", "Y_WGS84", *ENV_COLUMNS)
QUANTILES = (("q25", 0.25), ("q50", 0.50), ("q75", 0.75), ("q90", 0.90))
MAX_STEPS = 8
N_ANCHORS = 10
EPS = 1e-6
SEED = 20260817
EARTH_RADIUS_KM = 6371.0088


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def haversine_matrix(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(lon_deg.astype(float))
    lat = np.radians(lat_deg.astype(float))
    dlon = lon[:, None] - lon[None, :]
    dlat = lat[:, None] - lat[None, :]
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def euclidean_matrix(x: np.ndarray) -> np.ndarray:
    sq = np.sum(x * x, axis=1)
    dist2 = sq[:, None] + sq[None, :] - 2.0 * (x @ x.T)
    return np.sqrt(np.maximum(dist2, 0.0))


def nearest_neighbor_values(matrix: np.ndarray) -> np.ndarray:
    work = matrix.copy()
    np.fill_diagonal(work, np.inf)
    result = np.min(work, axis=1)
    if not np.isfinite(result).all():
        raise ValueError("nearest-neighbour distances must be finite")
    return result


def quantile_map(values: np.ndarray) -> dict[str, float]:
    return {name: float(np.quantile(values, q, method="linear")) for name, q in QUANTILES}


def reachable_within(adjacency: np.ndarray, source_indices: Iterable[int], max_steps: int) -> np.ndarray:
    n = adjacency.shape[0]
    visited = np.zeros(n, dtype=bool)
    sources = np.asarray(sorted(set(int(i) for i in source_indices)), dtype=int)
    if sources.size == 0:
        raise ValueError("at least one source index is required")
    visited[sources] = True
    frontier = visited.copy()
    for _ in range(max_steps):
        active = np.flatnonzero(frontier)
        if active.size == 0:
            break
        neighbours = np.any(adjacency[active], axis=0)
        new = neighbours & ~visited
        if not np.any(new):
            break
        visited |= new
        frontier = new
    return visited


def farthest_first_anchors(positive_indices: np.ndarray, site_ids: np.ndarray, geo_dist: np.ndarray) -> np.ndarray:
    positives = [int(i) for i in positive_indices]
    if not positives:
        raise ValueError("positive pool is empty")
    ordered = sorted(positives, key=lambda i: str(site_ids[i]))
    selected = [ordered[0]]
    target_count = min(N_ANCHORS, len(ordered))
    remaining = set(ordered[1:])
    while len(selected) < target_count:
        best = None
        best_distance = -1.0
        for candidate in sorted(remaining, key=lambda i: str(site_ids[i])):
            distance = float(np.min(geo_dist[candidate, selected]))
            if distance > best_distance + 1e-12:
                best = candidate
                best_distance = distance
        assert best is not None
        selected.append(best)
        remaining.remove(best)
    return np.asarray(selected, dtype=int)


def build_world_adjacencies(
    geo_dist: np.ndarray,
    env_dist: np.ndarray,
    geo_thresholds: dict[str, float],
    env_thresholds: dict[str, float],
) -> dict[str, np.ndarray]:
    worlds: dict[str, np.ndarray] = {}
    for g_name, _ in QUANTILES:
        geo_mask = geo_dist <= geo_thresholds[g_name]
        np.fill_diagonal(geo_mask, False)
        worlds[f"geo_{g_name}"] = geo_mask
    for g_name, _ in QUANTILES:
        geo_mask = geo_dist <= geo_thresholds[g_name]
        for e_name, _ in QUANTILES:
            adjacency = geo_mask & (env_dist <= env_thresholds[e_name])
            np.fill_diagonal(adjacency, False)
            worlds[f"geo_{g_name}_env_{e_name}"] = adjacency
    if len(worlds) != 20:
        raise RuntimeError(f"expected 20 worlds, got {len(worlds)}")
    return worlds


def drop_constant_columns(train: np.ndarray, heldout: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[int]]:
    if train.ndim != 2:
        raise ValueError("feature matrix must be two-dimensional")
    if train.shape[1] == 0:
        return train, heldout, []
    keep = [i for i in range(train.shape[1]) if float(np.std(train[:, i])) > 1e-12]
    return train[:, keep], heldout[:, keep], keep


def fit_logistic_probabilities(train_x: np.ndarray, train_y: np.ndarray, heldout_x: np.ndarray) -> tuple[np.ndarray, list[int]]:
    train_x, heldout_x, keep = drop_constant_columns(train_x, heldout_x)
    prevalence = float(np.mean(train_y))
    if train_x.shape[1] == 0:
        return np.full(len(heldout_x), prevalence, dtype=float), keep
    model = LogisticRegression(
        C=1.0,
        penalty="l2",
        solver="lbfgs",
        max_iter=2000,
        class_weight=None,
        random_state=SEED,
    )
    model.fit(train_x, train_y)
    return model.predict_proba(heldout_x)[:, 1].astype(float), keep


def clipped_logloss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    return float(log_loss(np.asarray(y, dtype=int), p, labels=[0, 1]))


def class_positive_rates(y: np.ndarray, frequency: np.ndarray) -> dict[str, dict[str, float | int | None]]:
    classes = {
        "robustly_supported": frequency >= 1.0 - 1e-15,
        "contingent": (frequency > 0.0) & (frequency < 1.0),
        "excluded_in_all_worlds": frequency <= 0.0,
    }
    result: dict[str, dict[str, float | int | None]] = {}
    for name, mask in classes.items():
        n = int(np.sum(mask))
        result[name] = {
            "n": n,
            "positive_rate": None if n == 0 else float(np.mean(y[mask])),
        }
    return result


def collision_summary(y: np.ndarray, bits: np.ndarray) -> dict[str, object]:
    if bits.shape[1] == 0:
        return {"collision_levels": 0, "collision_sites": 0, "max_positive_rate_spread": None}
    counts = np.sum(bits, axis=1).astype(int)
    collision_levels = 0
    collision_sites = 0
    spreads: list[float] = []
    for count in sorted(set(counts.tolist())):
        idx = np.flatnonzero(counts == count)
        patterns: dict[tuple[int, ...], list[int]] = {}
        for i in idx:
            key = tuple(int(v) for v in bits[i].tolist())
            patterns.setdefault(key, []).append(int(i))
        if len(patterns) < 2:
            continue
        collision_levels += 1
        collision_sites += len(idx)
        rates = [float(np.mean(y[rows])) for rows in patterns.values() if rows]
        if len(rates) >= 2:
            spreads.append(max(rates) - min(rates))
    return {
        "collision_levels": collision_levels,
        "collision_sites": collision_sites,
        "max_positive_rate_spread": None if not spreads else float(max(spreads)),
    }


def load_and_gate(source_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, tuple[str, ...], dict[str, object]]:
    raw = source_path.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise ValueError(f"source size mismatch: {len(raw)} != {EXPECTED_SIZE}")
    blob_sha = git_blob_sha1(raw)
    if blob_sha != EXPECTED_BLOB_SHA:
        raise ValueError(f"source Git blob mismatch: {blob_sha} != {EXPECTED_BLOB_SHA}")
    source_sha256 = sha256_bytes(raw)

    df = pd.read_csv(source_path)
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(df)}")
    missing_cols = [col for col in META_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"missing required columns: {missing_cols}")
    species = tuple(col for col in df.columns if col not in META_COLUMNS)
    if len(species) != EXPECTED_SPECIES:
        raise ValueError(f"expected {EXPECTED_SPECIES} species columns, got {len(species)}")

    periods = set(df["period"].astype(str))
    if periods != {CALIBRATION_PERIOD, HELDOUT_PERIOD}:
        raise ValueError(f"unexpected periods: {sorted(periods)}")
    counts = df.groupby("site", dropna=False).size()
    if len(counts) != EXPECTED_SITES or not np.all(counts.to_numpy() == 2):
        raise ValueError("site pairing gate failed")

    calib = df[df["period"].astype(str) == CALIBRATION_PERIOD].copy()
    held = df[df["period"].astype(str) == HELDOUT_PERIOD].copy()
    calib["_site_key"] = calib["site"].astype(str)
    held["_site_key"] = held["site"].astype(str)
    calib = calib.sort_values("_site_key").reset_index(drop=True)
    held = held.sort_values("_site_key").reset_index(drop=True)
    if not np.array_equal(calib["_site_key"].to_numpy(), held["_site_key"].to_numpy()):
        raise ValueError("paired site IDs differ between periods")

    for column in ("X_WGS84", "Y_WGS84"):
        c = pd.to_numeric(calib[column], errors="coerce").to_numpy(float)
        h = pd.to_numeric(held[column], errors="coerce").to_numpy(float)
        if not np.isfinite(c).all() or not np.isfinite(h).all() or not np.allclose(c, h, atol=0.0, rtol=0.0):
            raise ValueError(f"coordinate gate failed for {column}")

    for frame_name, frame in (("calibration", calib), ("heldout", held)):
        values = frame.loc[:, ENV_COLUMNS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite environmental predictor in {frame_name}")

    audit = {
        "source_git_blob_sha": blob_sha,
        "source_sha256": source_sha256,
        "source_size": len(raw),
        "rows": len(df),
        "sites": len(calib),
        "species_columns": list(species),
    }
    return calib, held, species, audit


def run(source_path: Path) -> dict[str, object]:
    calib, held, species_columns, source_audit = load_and_gate(source_path)
    site_ids = calib["_site_key"].to_numpy(str)
    lon = pd.to_numeric(calib["X_WGS84"], errors="raise").to_numpy(float)
    lat = pd.to_numeric(calib["Y_WGS84"], errors="raise").to_numpy(float)
    geo_dist = haversine_matrix(lon, lat)
    geo_thresholds = quantile_map(nearest_neighbor_values(geo_dist))

    calib_env = calib.loc[:, ENV_COLUMNS].to_numpy(float)
    held_env = held.loc[:, ENV_COLUMNS].to_numpy(float)
    mean = np.mean(calib_env, axis=0)
    sd = np.std(calib_env, axis=0, ddof=0)
    if np.any(sd <= 1e-12):
        raise ValueError("non_estimable_pre_model_input_gate: zero-SD environmental predictor")
    calib_z = (calib_env - mean) / sd
    held_z = (held_env - mean) / sd
    calib_env_dist = euclidean_matrix(calib_z)
    held_env_dist = euclidean_matrix(held_z)
    env_thresholds = quantile_map(nearest_neighbor_values(calib_env_dist))

    calib_worlds = build_world_adjacencies(geo_dist, calib_env_dist, geo_thresholds, env_thresholds)
    held_worlds = build_world_adjacencies(geo_dist, held_env_dist, geo_thresholds, env_thresholds)
    world_ids = tuple(calib_worlds)
    if tuple(held_worlds) != world_ids:
        raise RuntimeError("world ID order differs across periods")

    spatial_blocks = KMeans(n_clusters=10, random_state=SEED, n_init=20).fit_predict(np.c_[lon, lat])

    species_results: list[dict[str, object]] = []
    for species in species_columns:
        y1_raw = pd.to_numeric(calib[species], errors="coerce").to_numpy(float)
        y2_raw = pd.to_numeric(held[species], errors="coerce").to_numpy(float)
        train_mask = np.isfinite(y1_raw)
        held_mask = np.isfinite(y2_raw)
        y1 = (y1_raw[train_mask] > 0.0).astype(int)
        y2 = (y2_raw[held_mask] > 0.0).astype(int)

        train_positive = int(np.sum(y1 == 1))
        train_zero = int(np.sum(y1 == 0))
        held_positive = int(np.sum(y2 == 1))
        held_zero = int(np.sum(y2 == 0))
        if train_positive < 30 or train_zero < 30 or held_positive < 10 or held_zero < 10:
            species_results.append({
                "species": species,
                "status": "excluded_non_estimable",
                "train_positive": train_positive,
                "train_zero": train_zero,
                "held_positive": held_positive,
                "held_zero": held_zero,
            })
            continue

        positive_indices = np.flatnonzero(np.isfinite(y1_raw) & (y1_raw > 0.0))
        anchors = farthest_first_anchors(positive_indices, site_ids, geo_dist)
        anchor_set = set(anchors.tolist())
        compatibility_targets = np.asarray([i for i in positive_indices if int(i) not in anchor_set], dtype=int)

        surviving: list[str] = []
        train_reach_by_world: dict[str, np.ndarray] = {}
        held_reach_by_world: dict[str, np.ndarray] = {}
        for world_id in world_ids:
            train_reach = reachable_within(calib_worlds[world_id], anchors, MAX_STEPS)
            if compatibility_targets.size and not np.all(train_reach[compatibility_targets]):
                continue
            surviving.append(world_id)
            train_reach_by_world[world_id] = train_reach
            held_reach_by_world[world_id] = reachable_within(held_worlds[world_id], anchors, MAX_STEPS)

        if not surviving:
            species_results.append({
                "species": species,
                "status": "declared_world_universe_falsified_on_calibration",
                "train_positive": train_positive,
                "train_zero": train_zero,
                "held_positive": held_positive,
                "held_zero": held_zero,
                "anchor_site_ids": [str(site_ids[i]) for i in anchors],
            })
            continue

        train_bits_all = np.column_stack([train_reach_by_world[w].astype(float) for w in surviving])
        held_bits_all = np.column_stack([held_reach_by_world[w].astype(float) for w in surviving])
        train_freq_all = np.mean(train_bits_all, axis=1)
        held_freq_all = np.mean(held_bits_all, axis=1)

        train_bits = train_bits_all[train_mask]
        held_bits = held_bits_all[held_mask]
        train_freq = train_freq_all[train_mask]
        held_freq = held_freq_all[held_mask]

        freq_prob, freq_keep = fit_logistic_probabilities(train_freq[:, None], y1, held_freq[:, None])
        identity_train = np.column_stack([train_freq, train_bits])
        identity_held = np.column_stack([held_freq, held_bits])
        identity_prob, identity_keep = fit_logistic_probabilities(identity_train, y1, identity_held)

        env_logit_prob, env_keep = fit_logistic_probabilities(calib_z[train_mask], y1, held_z[held_mask])
        rf = RandomForestClassifier(
            n_estimators=500,
            max_features="sqrt",
            min_samples_leaf=5,
            random_state=SEED,
            n_jobs=-1,
            class_weight=None,
        )
        rf.fit(calib_z[train_mask], y1)
        rf_prob = rf.predict_proba(held_z[held_mask])[:, 1].astype(float)
        ensemble_prob = 0.5 * (env_logit_prob + rf_prob)
        persistence_prob = np.clip((y1_raw[held_mask] > 0.0).astype(float), EPS, 1.0 - EPS)

        losses = {
            "frequency": clipped_logloss(y2, freq_prob),
            "identity": clipped_logloss(y2, identity_prob),
            "env_logistic": clipped_logloss(y2, env_logit_prob),
            "env_random_forest": clipped_logloss(y2, rf_prob),
            "external_ensemble": clipped_logloss(y2, ensemble_prob),
            "persistence": clipped_logloss(y2, persistence_prob),
            "raw_support_frequency": clipped_logloss(y2, held_freq),
        }
        id_minus_freq = losses["identity"] - losses["frequency"]
        id_minus_external = losses["identity"] - losses["external_ensemble"]
        id_minus_persistence = losses["identity"] - losses["persistence"]

        block_rows: list[dict[str, object]] = []
        held_block_ids = spatial_blocks[held_mask]
        for block in sorted(set(held_block_ids.tolist())):
            m = held_block_ids == block
            if np.sum(m) == 0 or len(np.unique(y2[m])) < 2:
                continue
            block_rows.append({
                "block": int(block),
                "n": int(np.sum(m)),
                "identity_minus_frequency_logloss": clipped_logloss(y2[m], identity_prob[m]) - clipped_logloss(y2[m], freq_prob[m]),
                "identity_minus_external_logloss": clipped_logloss(y2[m], identity_prob[m]) - clipped_logloss(y2[m], ensemble_prob[m]),
            })

        species_results.append({
            "species": species,
            "status": "estimable",
            "train_positive": train_positive,
            "train_zero": train_zero,
            "held_positive": held_positive,
            "held_zero": held_zero,
            "anchor_site_ids": [str(site_ids[i]) for i in anchors],
            "surviving_world_ids": surviving,
            "surviving_world_count": len(surviving),
            "losses": losses,
            "identity_minus_frequency_logloss": id_minus_freq,
            "identity_minus_external_logloss": id_minus_external,
            "identity_minus_persistence_logloss": id_minus_persistence,
            "identity_better_than_frequency": bool(id_minus_freq < 0.0),
            "identity_better_than_external": bool(id_minus_external < 0.0),
            "raw_class_positive_rates": class_positive_rates(y2, held_freq),
            "collision_summary": collision_summary(y2, held_bits.astype(int)),
            "frequency_retained_columns": freq_keep,
            "identity_retained_columns": identity_keep,
            "environment_retained_columns": env_keep,
            "spatial_block_effects": block_rows,
        })

    estimable = [row for row in species_results if row["status"] == "estimable"]
    n_estimable = len(estimable)
    summary: dict[str, object] = {
        "estimable_species": n_estimable,
        "excluded_non_estimable_species": sum(row["status"] == "excluded_non_estimable" for row in species_results),
        "calibration_falsified_species": sum(row["status"] == "declared_world_universe_falsified_on_calibration" for row in species_results),
    }
    if estimable:
        model_names = (
            "frequency",
            "identity",
            "env_logistic",
            "env_random_forest",
            "external_ensemble",
            "persistence",
            "raw_support_frequency",
        )
        macro_losses = {
            name: float(np.mean([row["losses"][name] for row in estimable]))
            for name in model_names
        }
        mean_id_freq = float(np.mean([row["identity_minus_frequency_logloss"] for row in estimable]))
        mean_id_external = float(np.mean([row["identity_minus_external_logloss"] for row in estimable]))
        mean_id_persistence = float(np.mean([row["identity_minus_persistence_logloss"] for row in estimable]))
        frac_id_freq = float(np.mean([row["identity_better_than_frequency"] for row in estimable]))
        frac_id_external = float(np.mean([row["identity_better_than_external"] for row in estimable]))
        identity_favourable = bool(n_estimable >= 10 and mean_id_freq < 0.0 and frac_id_freq >= 0.60)
        external_favourable = bool(
            n_estimable >= 10
            and mean_id_external < 0.0
            and mean_id_persistence <= 0.0
            and frac_id_external >= 0.60
        )
        summary.update({
            "species_macro_logloss": macro_losses,
            "species_macro_identity_minus_frequency_logloss": mean_id_freq,
            "species_macro_identity_minus_external_logloss": mean_id_external,
            "species_macro_identity_minus_persistence_logloss": mean_id_persistence,
            "fraction_species_identity_better_than_frequency": frac_id_freq,
            "fraction_species_identity_better_than_external": frac_id_external,
            "identity_predictive_value_status": "confirmed_identity_predictive_value" if identity_favourable else "no_confirmed_identity_predictive_value",
            "external_predictive_added_value_status": "confirmed_predictive_added_value" if external_favourable else "no_confirmed_predictive_added_value",
        })
    else:
        summary.update({
            "identity_predictive_value_status": "non_estimable",
            "external_predictive_added_value_status": "non_estimable",
        })

    payload: dict[str, object] = {
        "schema_version": "eog_stoc_eogwf_validation_result_v1",
        "source": source_audit,
        "periods": {"calibration": CALIBRATION_PERIOD, "heldout": HELDOUT_PERIOD},
        "world_universe": {
            "world_ids": list(world_ids),
            "geographic_thresholds_km": geo_thresholds,
            "environment_thresholds": env_thresholds,
            "max_steps": MAX_STEPS,
            "environment_mean": mean.tolist(),
            "environment_population_sd": sd.tolist(),
        },
        "summary": summary,
        "species_results": species_results,
    }
    payload["result_fingerprint"] = canonical_sha256(payload)
    return payload


def write_species_csv(payload: dict[str, object], path: Path) -> None:
    rows = payload["species_results"]
    fieldnames = [
        "species",
        "status",
        "train_positive",
        "train_zero",
        "held_positive",
        "held_zero",
        "surviving_world_count",
        "identity_minus_frequency_logloss",
        "identity_minus_external_logloss",
        "identity_minus_persistence_logloss",
        "identity_better_than_frequency",
        "identity_better_than_external",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = run(args.source)
    result_path = args.output / "stoc_eogwf_result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    write_species_csv(result, args.output / "stoc_eogwf_species_summary.csv")
    print(json.dumps({"summary": result["summary"], "result_fingerprint": result["result_fingerprint"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
