#!/usr/bin/env python3
"""Audit the frozen Chiricahua Layer-B design without reading detection response.

Allowed inputs: coordinates, hydroperiod, temperature and wind. The response file
``y.wide.dryad.csv`` is forbidden. This runner builds the five frozen founder worlds,
projects them through the merged label-invariant Layer-B interface, and checks that
the full summary contains response-free variation beyond its declared mean-only
compression before any outcome is opened.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.world_forecast import ForecastGateDeclaration, WorldForecastMember
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)

YEARS = tuple(range(2003, 2018))
RESPONSE_YEARS = tuple(range(2007, 2018))
CALIBRATION_YEARS = tuple(range(2007, 2013))
HELDOUT_YEARS = tuple(range(2013, 2018))
N_NODES = 274
N_SAMPLED = 47
N_VISITS = 3
FOUNDER_INDICES_1_BASED = (15, 33, 274)
DESTROYED_INDICES_1_BASED = (10, 19, 31)
DESTROYED_FROM_YEAR = 2010
SIGMA_KM = 3.312102655413929
SUPPORT_TOLERANCE = 1e-15
WORLD_SPECS: tuple[tuple[str, float | None], ...] = (
    ("full_gaussian_lcc900_scale", None),
    ("truncated_geo_lcc250", 2.5750036893177453),
    ("truncated_geo_lcc500", 2.596906043737432),
    ("truncated_geo_lcc750", 3.0378047995221813),
    ("truncated_geo_lcc900", 3.312102655413929),
)
HYDRO_CLASSES = ("Intermittent", "Semi-permanent", "Permanent")


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_number(value: str) -> float:
    text = str(value).strip()
    if text == "" or text.upper() in {"NA", "NAN", "NULL"}:
        return float("nan")
    return float(text)


def read_coords(path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    ids: list[str] = []
    values: list[tuple[float, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        if tuple(next(reader)) != ("", "x", "y"):
            raise ValueError("unexpected coords.dryad.csv header")
        for row in reader:
            if len(row) != 3:
                raise ValueError("coordinate row width mismatch")
            ids.append(str(row[0]).strip())
            values.append((float(row[1]), float(row[2])))
    node_ids = tuple(ids)
    if len(node_ids) != N_NODES or len(set(node_ids)) != N_NODES:
        raise ValueError("coordinate node universe mismatch")
    coords = np.asarray(values, dtype=float)
    if not np.isfinite(coords).all():
        raise ValueError("coordinates must be finite")
    return node_ids, coords


def read_hydroperiod(path: Path, node_ids: tuple[str, ...]) -> tuple[str, ...]:
    ids: list[str] = []
    values: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        if tuple(next(reader)) != ("", "x"):
            raise ValueError("unexpected water.dryad.csv header")
        for row in reader:
            if len(row) != 2:
                raise ValueError("hydroperiod row width mismatch")
            ids.append(str(row[0]).strip())
            values.append(str(row[1]).strip())
    if tuple(ids) != node_ids:
        raise ValueError("hydroperiod IDs/order differ from coordinates")
    unknown = sorted(set(values).difference(HYDRO_CLASSES))
    if unknown:
        raise ValueError(f"unknown hydroperiod classes: {unknown}")
    return tuple(values)


def read_wide_covariate(
    path: Path,
    sampled_ids: tuple[str, ...],
) -> np.ndarray:
    expected_header = ("", *(f"V{index}" for index in range(1, 46)))
    ids: list[str] = []
    rows: list[list[float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader))
        if header != expected_header:
            raise ValueError(f"unexpected wide covariate header in {path.name}")
        for row in reader:
            if len(row) != 46:
                raise ValueError(f"wide covariate row width mismatch in {path.name}")
            ids.append(str(row[0]).strip())
            rows.append([parse_number(value) for value in row[1:]])
    if tuple(ids) != sampled_ids or len(rows) != N_SAMPLED:
        raise ValueError(f"sampled IDs/order mismatch in {path.name}")
    matrix = np.asarray(rows, dtype=float)
    if matrix.shape != (N_SAMPLED, N_VISITS * len(YEARS)):
        raise ValueError(f"wide covariate shape mismatch in {path.name}")
    return matrix.reshape(N_SAMPLED, len(YEARS), N_VISITS)


def distance_km(coords_m: np.ndarray) -> np.ndarray:
    sq = np.sum(coords_m * coords_m, axis=1)
    dist2 = sq[:, None] + sq[None, :] - 2.0 * (coords_m @ coords_m.T)
    result = np.sqrt(np.maximum(dist2, 0.0)) / 1000.0
    np.fill_diagonal(result, 0.0)
    return result


def build_operator(node_ids: tuple[str, ...], distance: np.ndarray, threshold: float | None):
    edges: list[DynamicReachabilityEdge] = []
    for source in range(len(node_ids)):
        for target in range(len(node_ids)):
            if source == target:
                continue
            dist = float(distance[source, target])
            if threshold is not None and dist > threshold + 1e-12:
                continue
            support = float(np.exp(-(dist * dist) / (2.0 * SIGMA_KM * SIGMA_KM)))
            edges.append(
                DynamicReachabilityEdge(
                    source=source,
                    target=target,
                    geographic_support=support,
                )
            )
    return build_dynamic_transition_operator(node_ids, edges, loss_support=1.0)


def cumulative_first_passage_all(
    transition: np.ndarray,
    source_indices: np.ndarray,
    max_steps: int,
) -> np.ndarray:
    """Vectorized exact target-wise first-passage support for one frozen operator."""

    n = transition.shape[0]
    source_mass = np.zeros(n, dtype=float)
    source_mass[source_indices] = 1.0 / len(source_indices)
    active = np.repeat(source_mass[None, :], n, axis=0)
    diagonal = np.arange(n)
    active[diagonal, diagonal] = 0.0
    hits = np.zeros((max_steps + 1, n), dtype=float)
    hits[0, source_indices] = source_mass[source_indices]
    for step in range(1, max_steps + 1):
        hits[step] = np.einsum("tn,nt->t", active, transition, optimize=True)
        active = active @ transition
        active[diagonal, diagonal] = 0.0
    cumulative = np.cumsum(hits, axis=0)
    cumulative[:, source_indices] = 1.0
    if np.any(np.diff(cumulative, axis=0) < -1e-12):
        raise RuntimeError("first-passage support is not horizon-monotone")
    return cumulative


def make_summary_forecast(
    node_ids: tuple[str, ...],
    world_rows: list[tuple[str, str, np.ndarray]],
    max_steps: int,
):
    declaration = ForecastGateDeclaration(reachability_threshold=SUPPORT_TOLERANCE)
    members: list[WorldForecastMember] = []
    for world_id, operator_fingerprint, cumulative in world_rows:
        supported = cumulative > SUPPORT_TOLERANCE
        payload = {
            "world_id": world_id,
            "operator_fingerprint": operator_fingerprint,
            "cumulative": cumulative.tolist(),
            "supported": supported.astype(int).tolist(),
            "gate_fingerprint": declaration.fingerprint,
        }
        members.append(
            WorldForecastMember(
                world_id=world_id,
                cumulative_reachability=cumulative,
                supported_state=supported,
                world_fingerprint=operator_fingerprint,
                state_layer_fingerprint=None,
                fingerprint=canonical_sha256(payload),
            )
        )
    forecast_payload = {
        "node_ids": list(node_ids),
        "worlds": [[world_id, fingerprint] for world_id, fingerprint, _ in world_rows],
        "members": [member.fingerprint for member in members],
        "max_steps": max_steps,
        "gate_fingerprint": declaration.fingerprint,
    }
    return SimpleNamespace(
        node_ids=node_ids,
        members=tuple(members),
        max_steps=max_steps,
        gate_declaration=declaration,
        world_fingerprints=tuple(
            (world_id, fingerprint) for world_id, fingerprint, _ in world_rows
        ),
        fingerprint=canonical_sha256(forecast_payload),
    )


def residual_variation(
    layer_b: np.ndarray,
    shared: np.ndarray,
) -> dict[str, object]:
    scalar = layer_b[:, [0, 1]]
    design_raw = np.column_stack([shared, scalar])
    design_sd = np.std(design_raw, axis=0, ddof=0)
    design_keep = np.flatnonzero(design_sd > 1e-12)
    if design_keep.size:
        values = design_raw[:, design_keep]
        values = (values - np.mean(values, axis=0)) / np.std(values, axis=0, ddof=0)
        design = np.column_stack([np.ones(len(values)), values])
    else:
        design = np.ones((len(layer_b), 1), dtype=float)

    rows: list[dict[str, object]] = []
    for index, name in enumerate(PREDICTIVE_FEATURE_NAMES):
        if index in {0, 1}:
            continue
        values = layer_b[:, index]
        sd = float(np.std(values, ddof=0))
        if sd <= 1e-12:
            residual_sd = 0.0
        else:
            standardized = (values - float(np.mean(values))) / sd
            beta, *_ = np.linalg.lstsq(design, standardized, rcond=None)
            residual_sd = float(np.std(standardized - design @ beta, ddof=0))
        rows.append({"feature": name, "raw_sd": sd, "residual_sd": residual_sd})
    maximum = max((float(row["residual_sd"]) for row in rows), default=0.0)
    return {
        "estimable": bool(maximum > 1e-8),
        "max_residual_sd": maximum,
        "rows": rows,
        "shared_plus_scalar_kept_columns": design_keep.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coords", type=Path, required=True)
    parser.add_argument("--hydroperiod", type=Path, required=True)
    parser.add_argument("--temperature", type=Path, required=True)
    parser.add_argument("--wind", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    node_ids, coords = read_coords(args.coords)
    hydroperiod = read_hydroperiod(args.hydroperiod, node_ids)
    sampled_ids = node_ids[:N_SAMPLED]
    temperature = read_wide_covariate(args.temperature, sampled_ids)
    wind = read_wide_covariate(args.wind, sampled_ids)
    distance = distance_km(coords)
    founder_indices = np.asarray([index - 1 for index in FOUNDER_INDICES_1_BASED], dtype=int)

    world_rows: list[tuple[str, str, np.ndarray]] = []
    for world_id, threshold in WORLD_SPECS:
        operator = build_operator(node_ids, distance, threshold)
        cumulative = cumulative_first_passage_all(
            operator.transition,
            founder_indices,
            max_steps=max(YEARS) - min(YEARS),
        )
        world_rows.append((world_id, operator.fingerprint, cumulative))

    forecast = make_summary_forecast(
        node_ids,
        world_rows,
        max_steps=max(YEARS) - min(YEARS),
    )
    summaries = {
        year: summarize_worldset_for_prediction(forecast, step=year - 2003)
        for year in RESPONSE_YEARS
    }

    nearest_founder = np.min(distance[:, founder_indices], axis=1)
    hydro_index = {value: index for index, value in enumerate(HYDRO_CLASSES)}
    destroyed = {index - 1 for index in DESTROYED_INDICES_1_BASED}
    founder_set = set(founder_indices.tolist())
    rows_by_year: dict[str, int] = {}
    calibration_shared: list[np.ndarray] = []
    calibration_layer_b: list[np.ndarray] = []
    covariate_rows: list[list[object]] = []

    for year in RESPONSE_YEARS:
        year_index = YEARS.index(year)
        valid_visits = np.isfinite(temperature[:, year_index, :]) & np.isfinite(
            wind[:, year_index, :]
        )
        count = np.sum(valid_visits, axis=1)
        safe_count = np.maximum(count, 1)
        mean_temp = np.nansum(np.where(valid_visits, temperature[:, year_index, :], np.nan), axis=1) / safe_count
        mean_wind = np.nansum(np.where(valid_visits, wind[:, year_index, :], np.nan), axis=1) / safe_count
        summary = summaries[year]
        by_id = {row.node_id: np.asarray(row.feature_values, dtype=float) for row in summary.rows}
        year_rows = 0
        for site_index, node_id in enumerate(sampled_ids):
            if site_index in founder_set or count[site_index] == 0:
                continue
            if site_index in destroyed and year >= DESTROYED_FROM_YEAR:
                continue
            one_hot = np.zeros(len(HYDRO_CLASSES), dtype=float)
            one_hot[hydro_index[hydroperiod[site_index]]] = 1.0
            shared = np.concatenate(
                [
                    one_hot,
                    np.asarray(
                        [
                            np.log1p(nearest_founder[site_index]),
                            float(year - 2003),
                            float(count[site_index]),
                            float(mean_wind[site_index]),
                            float(mean_temp[site_index]),
                        ]
                    ),
                ]
            )
            layer_b = by_id[node_id]
            if not np.isfinite(shared).all() or not np.isfinite(layer_b).all():
                raise ValueError("non-finite response-free design feature")
            year_rows += 1
            covariate_rows.append([year, node_id, *shared.tolist(), *layer_b.tolist()])
            if year in CALIBRATION_YEARS:
                calibration_shared.append(shared)
                calibration_layer_b.append(layer_b)
        rows_by_year[str(year)] = year_rows

    if not calibration_shared:
        raise RuntimeError("no response-free calibration design rows")
    shared_matrix = np.vstack(calibration_shared)
    layer_b_matrix = np.vstack(calibration_layer_b)
    variation = residual_variation(layer_b_matrix, shared_matrix)
    response_years_complete = all(rows_by_year[str(year)] > 0 for year in RESPONSE_YEARS)
    final_pass = bool(response_years_complete and variation["estimable"])

    payload = {
        "status": (
            "gate2_nonresponse_implementation_pass"
            if final_pass
            else "gate2_stop_nonresponse_implementation_or_layer_b_nonestimable"
        ),
        "response_file_read": False,
        "response_rows_opened": False,
        "node_count": N_NODES,
        "sampled_site_count": N_SAMPLED,
        "years": list(YEARS),
        "calibration_years": list(CALIBRATION_YEARS),
        "heldout_years": list(HELDOUT_YEARS),
        "rows_by_response_year": rows_by_year,
        "temperature_fingerprint": canonical_sha256(
            np.where(np.isfinite(temperature), temperature, None).tolist()
        ),
        "wind_fingerprint": canonical_sha256(
            np.where(np.isfinite(wind), wind, None).tolist()
        ),
        "world_operator_fingerprints": [
            [world_id, fingerprint] for world_id, fingerprint, _ in world_rows
        ],
        "forecast_fingerprint": forecast.fingerprint,
        "layer_b_feature_names": list(PREDICTIVE_FEATURE_NAMES),
        "layer_b_feature_fingerprints_by_year": {
            str(year): summaries[year].feature_fingerprint for year in RESPONSE_YEARS
        },
        "calibration_response_free_row_count": len(calibration_shared),
        "layer_b_variation_beyond_shared_plus_mean_only": variation,
        "response_years_complete": response_years_complete,
        "final_gate_pass": final_pass,
        "design_fingerprint": canonical_sha256(covariate_rows),
        "scientific_boundary": "This gate certifies only response-free implementation and representation variation. It is not a predictive result.",
        "stop_rule": "If final_gate_pass is false, do not open y.wide.dryad.csv.",
    }
    payload["fingerprint"] = canonical_sha256(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if not final_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
