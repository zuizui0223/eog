#!/usr/bin/env python3
"""Frozen once-only paired complementarity runner for the springtail experiment.

Smoke mode uses a deterministic synthetic population table and never requests the
released response file. Outcome mode requires an authorization marker plus the
matching response-blind preflight result, downloads the fixed response blob exactly
once, and executes the exact count gate before either paired model is fit.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import shlex
from types import SimpleNamespace
from typing import Iterable
import urllib.request

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/springtail_paired_complementarity/source_contract.json"
USER_AGENT = "EOG-springtail-frozen-once-only-runner/1.0"
EPS = 1e-6

BASELINE_FEATURE_NAMES: tuple[str, ...] = (
    "target_day",
    "log1p_target_day",
    "observation_gap_days",
    "dist_to_source_mm",
    "node_degree",
    "config_lattice",
    "config_partially_random",
    "config_random",
    "algebraic_connectivity_binary",
    "log_algebraic_connectivity_weighted",
    "network_diameter_binary",
    "network_diameter_weighted_mm",
    "mean_kernel_support",
    "current_observed_fraction",
    "ever_colonized_fraction",
    "log1p_current_total_abundance",
    "log1p_current_source_abundance",
    "log1p_current_mean_positive_abundance",
    "current_observed_front_mm",
    "ever_colonized_front_mm",
)


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


def path_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()


def bounded_download(url: str, expected_size: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read(expected_size + 1)
        status = getattr(response, "status", None) or response.getcode()
    if status != 200:
        raise RuntimeError(f"download returned HTTP {status}: {url}")
    if len(content) != expected_size:
        raise RuntimeError(
            f"downloaded size mismatch for {url}: {len(content)} != {expected_size}"
        )
    return content


def verified_nonresponse_download(spec: dict, audit: dict) -> bytes:
    audit["nonresponse_download_requests"].append(spec["raw_url"])
    content = bounded_download(spec["raw_url"], int(spec["size"]))
    if hashlib.sha256(content).hexdigest() != spec["sha256"]:
        raise RuntimeError(f"nonresponse SHA-256 mismatch: {spec['path']}")
    if git_blob_sha1(content) != spec["git_blob_sha1"]:
        raise RuntimeError(f"nonresponse Git blob mismatch: {spec['path']}")
    return content


def response_download_once(spec: dict, audit: dict) -> bytes:
    if audit["response_download_requests"]:
        raise RuntimeError("response download budget already exhausted")
    audit["response_download_requests"].append(spec["raw_url"])
    content = bounded_download(spec["raw_url"], int(spec["size"]))
    audit["response_payload_bytes_opened"] = len(content)
    audit["response_rows_opened"] = True
    if git_blob_sha1(content) != spec["git_blob_sha1"]:
        raise RuntimeError("once-opened response Git blob mismatch")
    return content


def parse_whitespace_table(content: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        lines = content.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise RuntimeError("released table is not UTF-8") from exc
    token_rows = [shlex.split(line, comments=False, posix=True) for line in lines if line.strip()]
    if len(token_rows) < 2:
        raise RuntimeError("released table contains no data rows")
    header = tuple(token_rows[0])
    if not header or len(set(header)) != len(header):
        raise RuntimeError("released table header is empty or duplicated")
    rows: list[dict[str, str]] = []
    for line_number, values in enumerate(token_rows[1:], start=2):
        if len(values) != len(header):
            raise RuntimeError(
                f"released table line {line_number} has {len(values)} fields, "
                f"expected {len(header)}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    return header, rows


def finite_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric: {value!r}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"{label} is not finite")
    return number


def exact_int(value: str, label: str) -> int:
    number = finite_float(value, label)
    integer = int(round(number))
    if abs(number - integer) > 1e-9:
        raise RuntimeError(f"{label} is not integer-valued: {value!r}")
    return integer


@dataclass(frozen=True)
class NodeCovariate:
    config: int
    rep: int
    node: int
    distance: float
    degree: float


@dataclass(frozen=True)
class NetworkCovariate:
    config: int
    rep: int
    algebraic_binary: float
    algebraic_weighted: float
    diameter_binary: float
    diameter_weighted: float


@dataclass(frozen=True)
class Observation:
    config: int
    rep: int
    day: int
    counts: tuple[float, ...]


@dataclass(frozen=True)
class LayerBLandscape:
    features: np.ndarray
    mean_kernel_support: np.ndarray
    feature_fingerprint: str


@dataclass(frozen=True)
class RiskRow:
    outer_unit_id: str
    config: int
    rep: int
    target_day: int
    node: int
    phase: str
    label: int
    baseline: tuple[float, ...]
    layer_b: tuple[float, ...]


def landscape_id(config: int, rep: int) -> str:
    return f"config_{config}_rep_{rep}"


def read_static_inputs(contract: dict, audit: dict) -> tuple[
    dict[tuple[int, int, int], NodeCovariate],
    dict[tuple[int, int], NetworkCovariate],
    dict[str, str],
]:
    contents = {
        name: verified_nonresponse_download(spec, audit)
        for name, spec in contract["nonresponse_files"].items()
    }
    readme_sha = hashlib.sha256(contents["readme"]).hexdigest()

    node_header, node_rows = parse_whitespace_table(contents["node_geometry"])
    if node_header != ("Config", "Rep", "node", "distToSource", "degree"):
        raise RuntimeError(f"node geometry header drift: {node_header!r}")
    node_covariates: dict[tuple[int, int, int], NodeCovariate] = {}
    for row in node_rows:
        config = exact_int(row["Config"], "node Config")
        rep = exact_int(row["Rep"], "node Rep")
        node = exact_int(row["node"], "node")
        if rep < 2:
            continue
        distance = finite_float(row["distToSource"], "distToSource")
        degree = finite_float(row["degree"], "degree")
        key = (config, rep, node)
        if key in node_covariates:
            raise RuntimeError(f"duplicate node geometry row: {key}")
        node_covariates[key] = NodeCovariate(config, rep, node, distance, degree)

    expected_nodes = {
        (config, rep, node)
        for config in (1, 2, 3)
        for rep in range(2, 10)
        for node in range(1, 11)
    }
    if set(node_covariates) != expected_nodes:
        raise RuntimeError("node geometry does not exactly cover the closed 24x10 registry")
    for key, row in node_covariates.items():
        if (row.node == 5) != (abs(row.distance) <= 1e-12):
            raise RuntimeError(f"source-distance boundary failed: {key}")
        if row.distance < 0 or row.degree <= 0:
            raise RuntimeError(f"invalid node covariate: {key}")

    network_header, network_rows = parse_whitespace_table(contents["network_geometry"])
    expected_header = (
        "Config",
        "Rep",
        "AlgebraicConnectivity_Binary",
        "AlgebraicConnectivity_Weighted",
        "NetworkDiameter_Binary",
        "NetworkDiameter_Weighted",
    )
    if network_header != expected_header:
        raise RuntimeError(f"network geometry header drift: {network_header!r}")
    networks: dict[tuple[int, int], NetworkCovariate] = {}
    for row in network_rows:
        config = exact_int(row["Config"], "network Config")
        rep = exact_int(row["Rep"], "network Rep")
        values = tuple(finite_float(row[name], name) for name in expected_header[2:])
        if any(value <= 0 for value in values):
            raise RuntimeError(f"nonpositive network metric: {(config, rep)}")
        key = (config, rep)
        if key in networks:
            raise RuntimeError(f"duplicate network geometry row: {key}")
        networks[key] = NetworkCovariate(config, rep, *values)
    expected_networks = {(config, rep) for config in (1, 2, 3) for rep in range(2, 10)}
    if set(networks) != expected_networks:
        raise RuntimeError("network geometry does not exactly cover the closed registry")

    provenance = {
        "readme_sha256": readme_sha,
        "node_geometry_sha256": hashlib.sha256(contents["node_geometry"]).hexdigest(),
        "network_geometry_sha256": hashlib.sha256(contents["network_geometry"]).hexdigest(),
    }
    return node_covariates, networks, provenance


def kernel_supports(distances: np.ndarray, contract: dict) -> tuple[np.ndarray, np.ndarray]:
    scale = contract["freezes"]["world_scale"]
    a = float(scale["kernel_a"])
    b_worlds = np.asarray(scale["kernel_b_worlds"], dtype=float)
    loss = float(scale["loss_support"])
    source_index = int(contract["freezes"]["node_geometry"]["inoculation_source_node"]) - 1
    supports = np.zeros((len(b_worlds), len(distances)), dtype=float)
    for world_index, b_value in enumerate(b_worlds):
        raw = a * np.exp(b_value * distances)
        raw[source_index] = 0.0
        supports[world_index] = raw / (loss + float(np.sum(raw)))
    mean_index = int(np.flatnonzero(np.isclose(b_worlds, -0.043, atol=1e-12))[0])
    return supports, supports[mean_index].copy()


def build_layer_b_landscapes(
    contract: dict,
    nodes: dict[tuple[int, int, int], NodeCovariate],
) -> dict[tuple[int, int], LayerBLandscape]:
    world_scale = contract["freezes"]["world_scale"]
    b_worlds = tuple(float(value) for value in world_scale["kernel_b_worlds"])
    tolerance = float(world_scale["support_tolerance"])
    results: dict[tuple[int, int], LayerBLandscape] = {}
    for config in (1, 2, 3):
        for rep in range(2, 10):
            node_ids = tuple(f"node_{node}" for node in range(1, 11))
            distances = np.asarray(
                [nodes[(config, rep, node)].distance for node in range(1, 11)], dtype=float
            )
            supports, mean_support = kernel_supports(distances, contract)
            members = []
            world_fingerprints = []
            for index, b_value in enumerate(b_worlds):
                cumulative = np.vstack((np.zeros(10, dtype=float), supports[index]))
                supported = np.vstack(
                    (np.zeros(10, dtype=bool), supports[index] > tolerance)
                )
                members.append(
                    SimpleNamespace(
                        cumulative_reachability=cumulative,
                        supported_state=supported,
                    )
                )
                world_fingerprints.append(
                    (f"kernel_world_{index+1}", canonical_sha256({"b": b_value}))
                )
            forecast = SimpleNamespace(
                node_ids=node_ids,
                members=tuple(members),
                max_steps=1,
                gate_declaration=ForecastGateDeclaration(reachability_threshold=tolerance),
                world_fingerprints=tuple(world_fingerprints),
                fingerprint=canonical_sha256(
                    {
                        "config": config,
                        "rep": rep,
                        "distance": distances.tolist(),
                        "supports": supports.tolist(),
                        "declared_worlds": list(b_worlds),
                    }
                ),
            )
            summary = summarize_worldset_for_prediction(forecast, step=1)
            if summary.feature_names != PREDICTIVE_FEATURE_NAMES:
                raise RuntimeError("Layer-B implementation feature-name drift")
            if summary.feature_matrix.shape != (10, 10):
                raise RuntimeError("Layer-B landscape matrix shape drift")
            results[(config, rep)] = LayerBLandscape(
                features=summary.feature_matrix,
                mean_kernel_support=mean_support,
                feature_fingerprint=summary.feature_fingerprint,
            )
    return results


def parse_response(content: bytes, contract: dict) -> tuple[list[Observation], dict]:
    header, rows = parse_whitespace_table(content)
    response_freeze = contract["freezes"]["response_identity"]
    required = set(response_freeze["required_columns"])
    observed = set(header)
    optional = response_freeze["only_optional_column"]
    if not required.issubset(observed):
        raise RuntimeError(f"response is missing required columns: {sorted(required-observed)}")
    if observed - required not in (set(), {optional}):
        raise RuntimeError(f"response has undeclared columns: {sorted(observed-required)}")

    observations: list[Observation] = []
    seen: set[tuple[int, int, int]] = set()
    for row_number, row in enumerate(rows, start=2):
        config = exact_int(row["Config"], f"response Config at line {row_number}")
        rep = exact_int(row["Rep"], f"response Rep at line {row_number}")
        day = exact_int(row["Day"], f"response Day at line {row_number}")
        if config not in (1, 2, 3) or rep not in range(2, 10) or day not in range(1, 183):
            raise RuntimeError(f"response row outside closed registry/day range: line {row_number}")
        counts: list[float] = []
        for node in range(1, 11):
            value = finite_float(row[f"Node{node}"], f"Node{node} at line {row_number}")
            if value < 0 or abs(value - round(value)) > 1e-9:
                raise RuntimeError(f"released node count is negative or noninteger at line {row_number}")
            counts.append(value)
        key = (config, rep, day)
        if key in seen:
            raise RuntimeError(f"duplicate response Config/Rep/Day row: {key}")
        seen.add(key)
        observations.append(Observation(config, rep, day, tuple(counts)))

    expected_landscapes = {(config, rep) for config in (1, 2, 3) for rep in range(2, 10)}
    observed_landscapes = {(row.config, row.rep) for row in observations}
    if observed_landscapes != expected_landscapes:
        raise RuntimeError("response does not exactly cover the closed 24-landscape registry")
    by_landscape = group_observations(observations)
    gaps: list[int] = []
    for key, values in by_landscape.items():
        if len(values) < 2:
            raise RuntimeError(f"response landscape has fewer than two observations: {key}")
        previous = 0
        for row in values:
            gap = row.day - previous
            if gap <= 0:
                raise RuntimeError(f"response days are not strictly increasing: {key}")
            gaps.append(gap)
            previous = row.day
        if max(gaps[-len(values) :]) > 5:
            raise RuntimeError(f"response photography gap exceeds published maximum: {key}")
    return observations, {
        "header": list(header),
        "row_count": len(observations),
        "landscape_count": len(by_landscape),
        "minimum_day": min(row.day for row in observations),
        "maximum_day": max(row.day for row in observations),
        "maximum_observation_gap_days": max(gaps),
    }


def synthetic_observations(
    nodes: dict[tuple[int, int, int], NodeCovariate],
) -> list[Observation]:
    observations: list[Observation] = []
    for config in (1, 2, 3):
        for rep in range(2, 10):
            colonization: dict[int, int] = {}
            for node in range(1, 11):
                if node == 5:
                    colonization[node] = 0
                    continue
                distance = nodes[(config, rep, node)].distance
                latent = 2 + int(distance // 60) + 2 * (config - 1) + ((rep + node) % 5)
                colonization[node] = min(max(latent, 2), 28)
            for day in range(1, 61, 2):
                counts = []
                for node in range(1, 11):
                    if day < colonization[node]:
                        counts.append(0.0)
                    else:
                        counts.append(float(8 + node + day + config + rep))
                observations.append(Observation(config, rep, day, tuple(counts)))
    return observations


def group_observations(
    observations: Iterable[Observation],
) -> dict[tuple[int, int], list[Observation]]:
    grouped: dict[tuple[int, int], list[Observation]] = {}
    for row in observations:
        grouped.setdefault((row.config, row.rep), []).append(row)
    for values in grouped.values():
        values.sort(key=lambda row: row.day)
    return grouped


def baseline_features(
    *,
    target_day: int,
    gap: int,
    node: NodeCovariate,
    network: NetworkCovariate,
    previous_counts: np.ndarray,
    ever_colonized: set[int],
    distance_by_node: np.ndarray,
    mean_kernel_support: float,
) -> tuple[float, ...]:
    observed = previous_counts > 0
    positive = previous_counts[observed]
    current_front = float(np.max(distance_by_node[observed])) if np.any(observed) else 0.0
    ever_indices = np.asarray([member - 1 for member in sorted(ever_colonized)], dtype=int)
    ever_front = float(np.max(distance_by_node[ever_indices])) if ever_indices.size else 0.0
    mean_positive = float(np.mean(positive)) if positive.size else 0.0
    values = (
        float(target_day),
        float(math.log1p(target_day)),
        float(gap),
        float(node.distance),
        float(node.degree),
        float(node.config == 1),
        float(node.config == 2),
        float(node.config == 3),
        float(network.algebraic_binary),
        float(math.log(network.algebraic_weighted)),
        float(network.diameter_binary),
        float(network.diameter_weighted),
        float(mean_kernel_support),
        float(np.mean(observed)),
        float(len(ever_colonized) / 10.0),
        float(math.log1p(float(np.sum(previous_counts)))),
        float(math.log1p(float(previous_counts[4]))),
        float(math.log1p(mean_positive)),
        current_front,
        ever_front,
    )
    if len(values) != len(BASELINE_FEATURE_NAMES) or not np.isfinite(values).all():
        raise RuntimeError("baseline feature construction drift or nonfinite value")
    return values


def build_risk_rows(
    observations: list[Observation],
    nodes: dict[tuple[int, int, int], NodeCovariate],
    networks: dict[tuple[int, int], NetworkCovariate],
    layer_b: dict[tuple[int, int], LayerBLandscape],
    split_day: int,
) -> tuple[list[RiskRow], dict]:
    rows: list[RiskRow] = []
    by_landscape = group_observations(observations)
    expected = {(config, rep) for config in (1, 2, 3) for rep in range(2, 10)}
    if set(by_landscape) != expected:
        raise RuntimeError("risk-row source does not exactly match the closed registry")
    eventually_positive = 0
    feature_fingerprints: dict[str, str] = {}
    for config, rep in sorted(by_landscape):
        key = (config, rep)
        current_counts = np.zeros(10, dtype=float)
        current_counts[4] = 10.0
        ever: set[int] = {5}
        previous_day = 0
        distances = np.asarray(
            [nodes[(config, rep, node)].distance for node in range(1, 11)], dtype=float
        )
        feature_fingerprints[landscape_id(config, rep)] = layer_b[key].feature_fingerprint
        for target in by_landscape[key]:
            gap = target.day - previous_day
            if gap <= 0:
                raise RuntimeError(f"nonpositive observation gap for {key}")
            target_counts = np.asarray(target.counts, dtype=float)
            for node_id in range(1, 11):
                if node_id == 5 or node_id in ever:
                    continue
                node_row = nodes[(config, rep, node_id)]
                label = int(target_counts[node_id - 1] > 0)
                rows.append(
                    RiskRow(
                        outer_unit_id=landscape_id(config, rep),
                        config=config,
                        rep=rep,
                        target_day=target.day,
                        node=node_id,
                        phase="calibration" if target.day <= split_day else "heldout",
                        label=label,
                        baseline=baseline_features(
                            target_day=target.day,
                            gap=gap,
                            node=node_row,
                            network=networks[key],
                            previous_counts=current_counts,
                            ever_colonized=ever,
                            distance_by_node=distances,
                            mean_kernel_support=float(
                                layer_b[key].mean_kernel_support[node_id - 1]
                            ),
                        ),
                        layer_b=tuple(
                            float(value) for value in layer_b[key].features[node_id - 1]
                        ),
                    )
                )
            newly_positive = {
                node_id
                for node_id in range(1, 11)
                if target_counts[node_id - 1] > 0
            }
            ever.update(newly_positive)
            current_counts = target_counts
            previous_day = target.day
        eventually_positive += len(ever - {5})
    return rows, {
        "risk_row_count": len(rows),
        "eventually_positive_non_source_nodes": eventually_positive,
        "layer_b_feature_fingerprints": feature_fingerprints,
    }


def exact_count_gate(rows: list[RiskRow], build_audit: dict, contract: dict) -> dict:
    minima = contract["freezes"]["count_gate"]
    calibration = [row for row in rows if row.phase == "calibration"]
    heldout = [row for row in rows if row.phase == "heldout"]
    cal_events = sum(row.label == 1 for row in calibration)
    cal_non_events = sum(row.label == 0 for row in calibration)
    held_events = sum(row.label == 1 for row in heldout)
    held_non_events = sum(row.label == 0 for row in heldout)
    expected_ids = {
        landscape_id(config, rep) for config in (1, 2, 3) for rep in range(2, 10)
    }
    by_outer: dict[str, list[int]] = {}
    for row in heldout:
        by_outer.setdefault(row.outer_unit_id, []).append(row.label)
    with_rows = len(by_outer)
    with_both = sum(len(set(labels)) == 2 for labels in by_outer.values())
    all_eventually_positive = (
        build_audit["eventually_positive_non_source_nodes"] == 24 * 9
    )
    passed = bool(
        cal_events >= int(minima["calibration_events"])
        and cal_non_events >= int(minima["calibration_non_events"])
        and held_events >= int(minima["heldout_events"])
        and held_non_events >= int(minima["heldout_non_events"])
        and with_both >= int(minima["heldout_outer_units_with_both_classes"])
        and with_rows == int(minima["heldout_outer_units_with_rows"])
        and set(by_outer) == expected_ids
        and all_eventually_positive
    )
    return {
        "passed": passed,
        "calibration_rows": len(calibration),
        "calibration_events": cal_events,
        "calibration_non_events": cal_non_events,
        "heldout_rows": len(heldout),
        "heldout_events": held_events,
        "heldout_non_events": held_non_events,
        "heldout_outer_units_with_rows": with_rows,
        "heldout_outer_units_with_both_classes": with_both,
        "all_216_non_source_nodes_eventually_observed_positive": all_eventually_positive,
        "minimums": {
            key: minima[key]
            for key in (
                "calibration_events",
                "calibration_non_events",
                "heldout_events",
                "heldout_non_events",
                "heldout_outer_units_with_both_classes",
                "heldout_outer_units_with_rows",
            )
        },
    }


def layer_b_estimability(calibration: list[RiskRow]) -> dict:
    baseline = np.asarray([row.baseline for row in calibration], dtype=float)
    layer_b = np.asarray([row.layer_b for row in calibration], dtype=float)
    base = np.column_stack((baseline, layer_b[:, :2]))
    sd = np.std(base, axis=0, ddof=0)
    keep = np.flatnonzero(sd > 1e-12)
    if keep.size:
        design_values = base[:, keep]
        design_values = (design_values - np.mean(design_values, axis=0)) / np.std(
            design_values, axis=0, ddof=0
        )
        design = np.column_stack((np.ones(len(base)), design_values))
    else:
        design = np.ones((len(base), 1), dtype=float)
    residual_sd: list[float] = []
    retained: list[int] = []
    for index in range(2, layer_b.shape[1]):
        values = layer_b[:, index]
        values_sd = float(np.std(values, ddof=0))
        if values_sd <= 1e-12:
            continue
        retained.append(index)
        standardized = (values - np.mean(values)) / values_sd
        coefficient, *_ = np.linalg.lstsq(design, standardized, rcond=None)
        residual_sd.append(float(np.std(standardized - design @ coefficient, ddof=0)))
    maximum = max(residual_sd, default=0.0)
    return {
        "estimable": bool(maximum > 1e-8),
        "retained_extra_layer_b_columns": retained,
        "residual_sd": residual_sd,
        "maximum_residual_sd": maximum,
    }


def binary_log_loss(y: np.ndarray, probability: np.ndarray) -> float:
    truth = np.asarray(y, dtype=float)
    pred = np.clip(np.asarray(probability, dtype=float), EPS, 1.0 - EPS)
    return float(-np.mean(truth * np.log(pred) + (1.0 - truth) * np.log(1.0 - pred)))


def brier_score(y: np.ndarray, probability: np.ndarray) -> float:
    return float(np.mean((np.asarray(probability, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def learner(contract: dict) -> RandomForestClassifier:
    params = dict(contract["freezes"]["preprocessing_model_fit"]["hyperparameters"])
    return RandomForestClassifier(**params)


def paired_declaration(contract: dict) -> PredictiveComplementarityDeclaration:
    freezes = contract["freezes"]
    metrics = freezes["metrics_decision"]
    return PredictiveComplementarityDeclaration(
        metric_name=metrics["primary_metric"],
        lower_is_better=bool(metrics["lower_is_better"]),
        expected_outer_unit_count=int(metrics["expected_outer_unit_count"]),
        favorable_min_augmented_wins=int(metrics["favorable_min_augmented_wins"]),
        adverse_min_baseline_wins=int(metrics["adverse_min_baseline_wins"]),
        learner_fit_fingerprint=canonical_sha256(freezes["preprocessing_model_fit"]),
        response_endpoint_fingerprint=canonical_sha256(freezes["response_semantics"]),
        split_fingerprint=canonical_sha256(freezes["temporal_split"]),
        external_feature_fingerprint=canonical_sha256(
            {
                "feature_names": list(BASELINE_FEATURE_NAMES),
                "missing_value_policy": freezes["preprocessing_model_fit"][
                    "missing_value_policy"
                ],
            }
        ),
        eog_feature_fingerprint=canonical_sha256(freezes["layer_b_representation"]),
    )


def fit_and_score(rows: list[RiskRow], contract: dict) -> dict:
    calibration = [row for row in rows if row.phase == "calibration"]
    heldout = [row for row in rows if row.phase == "heldout"]
    x_base = np.asarray([row.baseline for row in calibration], dtype=float)
    x_augmented = np.column_stack(
        (x_base, np.asarray([row.layer_b for row in calibration], dtype=float))
    )
    y_cal = np.asarray([row.label for row in calibration], dtype=int)
    baseline_model = learner(contract)
    augmented_model = learner(contract)
    baseline_model.fit(x_base, y_cal)
    augmented_model.fit(x_augmented, y_cal)

    x_held_base = np.asarray([row.baseline for row in heldout], dtype=float)
    x_held_augmented = np.column_stack(
        (x_held_base, np.asarray([row.layer_b for row in heldout], dtype=float))
    )
    y_held = np.asarray([row.label for row in heldout], dtype=int)
    p_base = baseline_model.predict_proba(x_held_base)[:, 1]
    p_augmented = augmented_model.predict_proba(x_held_augmented)[:, 1]

    paired: list[PairedOuterUnitScore] = []
    outer_rows: list[dict] = []
    for outer_id in sorted({row.outer_unit_id for row in heldout}):
        indices = np.asarray(
            [index for index, row in enumerate(heldout) if row.outer_unit_id == outer_id],
            dtype=int,
        )
        truth = y_held[indices]
        baseline_loss = binary_log_loss(truth, p_base[indices])
        augmented_loss = binary_log_loss(truth, p_augmented[indices])
        paired.append(PairedOuterUnitScore(outer_id, baseline_loss, augmented_loss))
        outer_rows.append(
            {
                "outer_unit_id": outer_id,
                "row_count": int(indices.size),
                "events": int(np.sum(truth == 1)),
                "non_events": int(np.sum(truth == 0)),
                "baseline_log_loss": baseline_loss,
                "augmented_log_loss": augmented_loss,
                "augmented_minus_baseline": augmented_loss - baseline_loss,
            }
        )
    declaration = paired_declaration(contract)
    decision = evaluate_predictive_complementarity(
        declaration,
        paired,
        tie_tolerance=float(contract["freezes"]["metrics_decision"]["tie_tolerance"]),
    )
    return {
        "models_fit": 2,
        "heldout_scores": 2 * len(paired),
        "paired_declaration_fingerprint": declaration.fingerprint,
        "paired_complementarity": asdict(decision),
        "paired_outer_unit_scores": outer_rows,
        "pooled_metrics": {
            "baseline_log_loss": binary_log_loss(y_held, p_base),
            "augmented_log_loss": binary_log_loss(y_held, p_augmented),
            "baseline_brier": brier_score(y_held, p_base),
            "augmented_brier": brier_score(y_held, p_augmented),
        },
        "model_feature_audit": {
            "baseline_feature_names": list(BASELINE_FEATURE_NAMES),
            "augmented_feature_names": [*BASELINE_FEATURE_NAMES, *PREDICTIVE_FEATURE_NAMES],
            "exact_landscape_id_supervised": False,
            "exact_world_id_supervised": False,
            "only_augmented_difference": list(PREDICTIVE_FEATURE_NAMES),
        },
    }


def verify_frozen_environment(contract: dict) -> None:
    freeze = contract["freezes"]["preprocessing_model_fit"]
    if np.__version__ != freeze["numpy"]:
        raise RuntimeError(f"NumPy version drift: {np.__version__} != {freeze['numpy']}")
    if sklearn.__version__ != freeze["scikit_learn"]:
        raise RuntimeError(
            f"scikit-learn version drift: {sklearn.__version__} != {freeze['scikit_learn']}"
        )
    if tuple(freeze["baseline_feature_names"]) != BASELINE_FEATURE_NAMES:
        raise RuntimeError("baseline feature-name contract drift")
    if tuple(contract["freezes"]["layer_b_representation"]["feature_names"]) != tuple(
        PREDICTIVE_FEATURE_NAMES
    ):
        raise RuntimeError("Layer-B feature-name contract drift")
    runner_spec = contract["freezes"]["runtime_runner"]
    if path_sha256(Path(__file__).resolve()) != runner_spec["sha256"]:
        raise RuntimeError("runner self-hash differs from frozen contract")


def verify_authorization(
    contract: dict,
    marker_path: Path,
    preflight_path: Path,
) -> dict:
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if marker.get("attempt_id") != contract["attempt_id"]:
        raise RuntimeError("authorization marker attempt ID mismatch")
    if marker.get("invocation_budget") != 1 or marker.get("response_rows_opened") is not False:
        raise RuntimeError("authorization marker does not preserve the once-only unopened state")
    if marker.get("contract_sha256") != path_sha256(CONTRACT_PATH):
        raise RuntimeError("authorization marker contract hash mismatch")
    if marker.get("runner_sha256") != path_sha256(Path(__file__).resolve()):
        raise RuntimeError("authorization marker runner hash mismatch")
    if preflight.get("status") != "authorized_once_only_exact_count_gate_required":
        raise RuntimeError("preflight did not authorize the once-only exact count gate")
    if preflight.get("response_rows_opened") is not False:
        raise RuntimeError("preflight claims response rows were opened")
    gate_fingerprint = preflight["outcome_access_gate"]["fingerprint"]
    if marker.get("outcome_access_gate_fingerprint") != gate_fingerprint:
        raise RuntimeError("authorization marker outcome-gate fingerprint mismatch")
    if marker.get("preflight_fingerprint") != preflight.get("fingerprint"):
        raise RuntimeError("authorization marker preflight fingerprint mismatch")
    return {
        "authorized_parent_commit": marker.get("authorized_parent_commit"),
        "outcome_access_gate_fingerprint": gate_fingerprint,
        "preflight_fingerprint": preflight["fingerprint"],
        "invocation_budget": 1,
    }


def write_result(path: Path, result: dict) -> None:
    payload = dict(result)
    payload["fingerprint"] = canonical_sha256(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stopped_result(base: dict, status: str, reason: str, output: Path) -> dict:
    result = {
        **base,
        "status": status,
        "stop_reason": reason,
        "models_fit": int(base.get("models_fit", 0)),
        "heldout_scores": int(base.get("heldout_scores", 0)),
    }
    write_result(output, result)
    return result


def run(
    *,
    mode: str,
    output: Path,
    authorization_marker: Path | None = None,
    preflight_result: Path | None = None,
) -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    verify_frozen_environment(contract)
    audit = {
        "execution_mode": mode,
        "attempt_id": contract["attempt_id"],
        "contract_sha256": path_sha256(CONTRACT_PATH),
        "runner_sha256": path_sha256(Path(__file__).resolve()),
        "nonresponse_download_requests": [],
        "response_download_requests": [],
        "response_payload_bytes_opened": 0,
        "response_rows_opened": False,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    authorization: dict | None = None
    if mode == "outcome":
        if authorization_marker is None or preflight_result is None:
            raise RuntimeError("outcome mode requires authorization marker and preflight result")
        authorization = verify_authorization(contract, authorization_marker, preflight_result)
        audit["authorization"] = authorization
    elif authorization_marker is not None or preflight_result is not None:
        raise RuntimeError("smoke mode must not receive outcome authorization inputs")

    nodes, networks, nonresponse_provenance = read_static_inputs(contract, audit)
    layer_b = build_layer_b_landscapes(contract, nodes)
    base = {
        **audit,
        "status": "pre_model",
        "response_target": "released_first_observed_node_colonization",
        "response_boundary": "released automated photographic N>0 versus N==0; not latent biological absence",
        "closed_registry_landscapes": 24,
        "closed_registry_non_source_nodes": 216,
        "temporal_split_day": int(
            contract["freezes"]["temporal_split"]["calibration_rule"].split("<=")[-1]
        ),
        "nonresponse_provenance": nonresponse_provenance,
        "physical_landscape_id_supervised": False,
        "exact_world_id_supervised": False,
    }
    split_day = 7
    if mode == "smoke":
        observations = synthetic_observations(nodes)
        response_provenance = {
            "source": "deterministic synthetic technical-control observations",
            "response_download_requests": 0,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": False,
            "row_count": len(observations),
        }
    else:
        response_spec = contract["response_file"]
        try:
            response_content = response_download_once(response_spec, audit)
            base.update(
                {
                    "response_download_requests": audit["response_download_requests"],
                    "response_payload_bytes_opened": audit["response_payload_bytes_opened"],
                    "response_rows_opened": audit["response_rows_opened"],
                }
            )
            observations, schema = parse_response(response_content, contract)
            response_provenance = {
                "path": response_spec["path"],
                "git_blob_sha1": response_spec["git_blob_sha1"],
                "sha256_after_once_only_open": hashlib.sha256(response_content).hexdigest(),
                "bytes": len(response_content),
                "response_download_requests": 1,
                "response_rows_opened": True,
                "schema": schema,
            }
        except Exception as exc:
            base.update(
                {
                    "response_download_requests": audit["response_download_requests"],
                    "response_payload_bytes_opened": audit["response_payload_bytes_opened"],
                    "response_rows_opened": audit["response_rows_opened"],
                }
            )
            return stopped_result(
                base,
                "post_open_schema_or_identity_stop_no_retry",
                repr(exc),
                output,
            )

    try:
        risk_rows, row_audit = build_risk_rows(
            observations, nodes, networks, layer_b, split_day
        )
        count_gate = exact_count_gate(risk_rows, row_audit, contract)
    except Exception as exc:
        if mode == "outcome":
            base.update({"response_provenance": response_provenance})
            return stopped_result(
                base,
                "post_open_risk_table_stop_no_retry",
                repr(exc),
                output,
            )
        raise

    base.update(
        {
            "response_provenance": response_provenance,
            "risk_table_audit": row_audit,
            "exact_count_gate": count_gate,
        }
    )
    if not count_gate["passed"]:
        return stopped_result(
            base,
            "non_estimable_exact_count_gate_zero_fit",
            "one or more prospectively frozen exact count requirements failed",
            output,
        )

    calibration = [row for row in risk_rows if row.phase == "calibration"]
    estimability = layer_b_estimability(calibration)
    base["layer_b_estimability"] = estimability
    if not estimability["estimable"]:
        return stopped_result(
            base,
            "layer_b_non_estimable_zero_fit",
            "unchanged Layer B has no retained variation beyond the frozen conventional block",
            output,
        )

    try:
        scores = fit_and_score(risk_rows, contract)
    except Exception as exc:
        if mode == "outcome":
            return stopped_result(
                base,
                "post_open_execution_failure_no_retry",
                repr(exc),
                output,
            )
        raise
    result = {
        **base,
        **scores,
        "status": "smoke_pass" if mode == "smoke" else "completed_frozen_paired_test",
    }
    write_result(output, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "outcome"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authorization-marker", type=Path)
    parser.add_argument("--preflight-result", type=Path)
    args = parser.parse_args()
    result = run(
        mode=args.mode,
        output=args.output,
        authorization_marker=args.authorization_marker,
        preflight_result=args.preflight_result,
    )
    summary = {
        "status": result["status"],
        "execution_mode": result["execution_mode"],
        "response_download_requests": len(result["response_download_requests"]),
        "response_payload_bytes_opened": result["response_payload_bytes_opened"],
        "response_rows_opened": result["response_rows_opened"],
        "models_fit": result["models_fit"],
        "heldout_scores": result["heldout_scores"],
        "exact_count_gate_passed": result.get("exact_count_gate", {}).get("passed"),
        "paired_status": result.get("paired_complementarity", {}).get("status"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
