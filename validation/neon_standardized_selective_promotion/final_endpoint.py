from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, log_loss

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "final_endpoint_contract.json"
SCHEMA_CONTRACT = HERE / "response_schema_contract.json"
DEPLOYMENT_CONTRACT = HERE / "stage1_response_blind_contract.json"
OUTPUT = ROOT / "build/neon_standardized_selective_promotion/final_endpoint_result.json"
BASE = "https://zenodo.org/api/records/20826511/files/{name}/content"
EPS = 1e-6
EARTH_KM = 6371.0088


def fetch_exact(name: str, expected_md5: str, expected_size: int, user_agent: str) -> bytes:
    req = Request(BASE.format(name=name), headers={"User-Agent": user_agent})
    with urlopen(req, timeout=60) as response:
        raw = response.read()
    if len(raw) != expected_size:
        raise RuntimeError(f"size mismatch for {name}: {len(raw)} != {expected_size}")
    got = hashlib.md5(raw).hexdigest()
    if got != expected_md5:
        raise RuntimeError(f"md5 mismatch for {name}: {got}")
    return raw


def parse_csv(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    return list(reader.fieldnames or []), list(reader)


def parse_date(value: str) -> datetime:
    return datetime.strptime(value.strip()[:10], "%Y-%m-%d")


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, (a[0], a[1]))
    lat2, lon2 = map(math.radians, (b[0], b[1]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_KM * math.asin(min(1.0, math.sqrt(h)))


def frozen_thresholds(deployments: list[dict[str, str]]) -> list[float]:
    coords = sorted({(float(row["latitude"]), float(row["longitude"])) for row in deployments})
    if len(coords) < 5:
        raise RuntimeError("fewer than five distinct deployment coordinates")
    nearest = []
    for i, source in enumerate(coords):
        distances = [haversine(source, target) for j, target in enumerate(coords) if i != j]
        positive = [distance for distance in distances if distance > 0]
        if positive:
            nearest.append(min(positive))
    if len(nearest) < 5:
        raise RuntimeError("insufficient positive nearest-neighbour distances")
    return [float(np.quantile(nearest, q, method="linear")) for q in (0.25, 0.50, 0.75, 0.90)]


def support_summary(
    target: tuple[float, float],
    source_coords: set[tuple[float, float]],
    surviving: list[int],
    thresholds: list[float],
) -> np.ndarray:
    values = []
    for index in surviving:
        threshold = thresholds[index]
        values.append(1.0 if any(haversine(source, target) <= threshold for source in source_coords) else 0.0)
    values.append(1.0)  # external_open
    array = np.asarray(values, dtype=float)
    return np.asarray(
        [
            len(values) / 5.0,
            float(np.mean(array)),
            float(np.std(array)),
            float(np.min(array)),
            float(np.max(array)),
            float(np.quantile(array, 0.25, method="linear")),
            float(np.quantile(array, 0.50, method="linear")),
            float(np.quantile(array, 0.75, method="linear")),
            float(np.mean(array > 0.0)),
            float(np.max(array) - np.min(array)),
        ]
    )


def update_worlds(
    new_positive_coord: tuple[float, float],
    source_coords: set[tuple[float, float]],
    surviving: list[int],
    thresholds: list[float],
) -> tuple[set[tuple[float, float]], list[int]]:
    keep = list(surviving)
    if source_coords:
        keep = [
            index
            for index in surviving
            if any(haversine(source, new_positive_coord) <= thresholds[index] for source in source_coords)
        ]
    return source_coords | {new_positive_coord}, keep


def resolve_header(header: list[str], aliases: list[str], required: bool = True) -> str | None:
    for alias in aliases:
        if header.count(alias) == 1:
            return alias
    if required:
        raise RuntimeError(f"required response semantic missing; accepted={aliases}; observed={header}")
    return None


def match_focal_deployments(
    sequence_rows: list[dict[str, str]],
    valid_ids: set[str],
    deployment_id_col: str,
    scientific_name_col: str,
    common_name_col: str | None,
    focal_scientific: str,
    focal_common: set[str],
) -> tuple[set[str], int, int]:
    exact_rows = []
    for row in sequence_rows:
        deployment_id = (row.get(deployment_id_col) or "").strip()
        scientific = (row.get(scientific_name_col) or "").strip().casefold()
        if deployment_id in valid_ids and scientific == focal_scientific:
            exact_rows.append(row)

    common_rows = []
    if not exact_rows and common_name_col:
        for row in sequence_rows:
            deployment_id = (row.get(deployment_id_col) or "").strip()
            common = (row.get(common_name_col) or "").strip().casefold()
            if deployment_id in valid_ids and common in focal_common:
                common_rows.append(row)

    matched_rows = exact_rows if exact_rows else common_rows
    positives = {(row.get(deployment_id_col) or "").strip() for row in matched_rows}
    return positives, len(exact_rows), len(common_rows)


def macro_loss(y: np.ndarray, p: np.ndarray, groups: list[str]) -> float:
    scores = []
    for group in sorted(set(groups)):
        mask = np.asarray([value == group for value in groups], dtype=bool)
        scores.append(float(log_loss(y[mask], p[mask], labels=[0, 1])))
    return float(np.mean(scores))


def macro_brier(y: np.ndarray, p: np.ndarray, groups: list[str]) -> float:
    scores = []
    for group in sorted(set(groups)):
        mask = np.asarray([value == group for value in groups], dtype=bool)
        scores.append(float(brier_score_loss(y[mask], p[mask])))
    return float(np.mean(scores))


def fit_model(hyperparameters: dict, x: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=int(hyperparameters["n_estimators"]),
        max_features=str(hyperparameters["max_features"]),
        min_samples_leaf=int(hyperparameters["min_samples_leaf"]),
        class_weight=None,
        random_state=int(hyperparameters["random_state"]),
        n_jobs=int(hyperparameters["n_jobs"]),
    )
    model.fit(x, y)
    if list(model.classes_) != [0, 1]:
        raise RuntimeError(f"unexpected model classes {model.classes_}")
    return model


def predict_positive(model: RandomForestClassifier, x: np.ndarray) -> np.ndarray:
    return np.clip(model.predict_proba(x)[:, 1], EPS, 1 - EPS)


def write_result(result: dict) -> dict:
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def run() -> dict:
    contract = json.loads(CONTRACT.read_text())
    schema_contract = json.loads(SCHEMA_CONTRACT.read_text())
    deployment_contract = json.loads(DEPLOYMENT_CONTRACT.read_text())
    base = {
        "schema": "eog.neon_standardized_selective_promotion.final_endpoint_result.v1",
        "attempt_id": contract["attempt_id"],
        "response_gets": 0,
        "response_consumed": False,
        "counts_as_fresh_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }

    deployment_spec = deployment_contract["authorized_payloads"]["camera_trap_deployments.csv"]
    deployment_raw = fetch_exact(
        "camera_trap_deployments.csv",
        deployment_spec["md5"],
        deployment_spec["size"],
        "eog-neon-final/1",
    )
    deployment_header, deployment_rows = parse_csv(deployment_raw)
    required_deployment = {
        "deployment_id",
        "longitude",
        "latitude",
        "start_date",
        "end_date",
        "subproject_name",
    }
    if not required_deployment.issubset(deployment_header):
        raise RuntimeError(f"frozen deployment schema drift: {deployment_header}")
    if len(deployment_rows) != 820 or len({row["deployment_id"] for row in deployment_rows}) != 820:
        raise RuntimeError("frozen deployment row/id count drift")

    ordered = sorted(
        deployment_rows,
        key=lambda row: (parse_date(row["start_date"]), row["deployment_id"]),
    )
    n = len(ordered)
    cut1, cut2 = math.floor(0.60 * n), math.floor(0.80 * n)
    split = np.asarray([0] * cut1 + [1] * (cut2 - cut1) + [2] * (n - cut2), dtype=int)
    thresholds = frozen_thresholds(ordered)

    response = contract["authoritative_response"]
    try:
        response_raw = fetch_exact(
            response["file"], response["md5"], response["size"], "eog-neon-final/1"
        )
        base["response_gets"] = 1
        base["response_consumed"] = True
        response_header, sequence_rows = parse_csv(response_raw)
        deployment_id_col = resolve_header(
            response_header,
            schema_contract["required_semantics"]["deployment_id"]["accepted_exact_headers"],
        )
        scientific_name_col = resolve_header(
            response_header,
            schema_contract["required_semantics"]["scientific_name"]["accepted_exact_headers"],
        )
        common_name_col = resolve_header(
            response_header,
            schema_contract["required_semantics"]["common_name_optional"]["accepted_exact_headers"],
            required=False,
        )
    except Exception as exc:
        return write_result(
            {**base, "terminal_class": "stop_response_schema_or_identity", "reason": str(exc)}
        )

    valid_ids = {row["deployment_id"] for row in ordered}
    positives, exact_scientific_matches, common_fallback_matches = match_focal_deployments(
        sequence_rows,
        valid_ids,
        deployment_id_col,
        scientific_name_col,
        common_name_col,
        schema_contract["focal_matching"]["scientific_exact_after_strip_casefold"],
        set(schema_contract["focal_matching"]["common_exact_after_strip_casefold_optional"]),
    )
    y = np.asarray([int(row["deployment_id"] in positives) for row in ordered], dtype=int)

    minima = contract["estimability_minima"]
    counts = {
        "inner_train_positive": int(np.sum(y[split == 0] == 1)),
        "inner_train_negative": int(np.sum(y[split == 0] == 0)),
        "inner_validation_positive": int(np.sum(y[split == 1] == 1)),
        "inner_validation_negative": int(np.sum(y[split == 1] == 0)),
        "outer_positive": int(np.sum(y[split == 2] == 1)),
        "outer_negative": int(np.sum(y[split == 2] == 0)),
        "inner_validation_subprojects": len(
            {ordered[i]["subproject_name"] for i in range(n) if split[i] == 1}
        ),
        "outer_subprojects": len(
            {ordered[i]["subproject_name"] for i in range(n) if split[i] == 2}
        ),
    }
    estimable = (
        counts["inner_train_positive"] >= minima["inner_train_each_class"]
        and counts["inner_train_negative"] >= minima["inner_train_each_class"]
        and counts["inner_validation_positive"] >= minima["inner_validation_each_class"]
        and counts["inner_validation_negative"] >= minima["inner_validation_each_class"]
        and counts["outer_positive"] >= minima["outer_each_class"]
        and counts["outer_negative"] >= minima["outer_each_class"]
        and counts["inner_validation_subprojects"] >= minima["inner_validation_subprojects"]
        and counts["outer_subprojects"] >= minima["outer_subprojects"]
    )
    if not estimable:
        return write_result(
            {
                **base,
                "terminal_class": "stop_response_estimability",
                "response_rows": len(sequence_rows),
                "focal_sequence_matches": exact_scientific_matches + common_fallback_matches,
                "deployment_class_counts": counts,
                "minima": minima,
            }
        )

    categories = sorted({row["subproject_name"] for row in ordered})
    category_map = {value: index for index, value in enumerate(categories)}
    baseline_rows = []
    for row in ordered:
        start = parse_date(row["start_date"])
        end = parse_date(row["end_date"])
        phase = 2 * math.pi * (start.month - 1) / 12
        vector = [
            float(row["longitude"]),
            float(row["latitude"]),
            float((end - start).days),
            math.sin(phase),
            math.cos(phase),
        ]
        onehot = [0.0] * len(categories)
        onehot[category_map[row["subproject_name"]]] = 1.0
        vector.extend(onehot)
        baseline_rows.append(vector)
    x_base = np.asarray(baseline_rows, dtype=float)

    events = sorted(
        [
            (parse_date(row["end_date"]), row["deployment_id"], index)
            for index, row in enumerate(ordered)
        ],
        key=lambda value: (value[0], value[1]),
    )
    event_position = 0
    sources: set[tuple[float, float]] = set()
    surviving = [0, 1, 2, 3]
    contraction_events = []
    layer_rows = []
    for row in ordered:
        start = parse_date(row["start_date"])
        while event_position < len(events) and events[event_position][0] < start:
            end_time, deployment_id, index = events[event_position]
            if y[index] == 1:
                coord = (
                    float(ordered[index]["latitude"]),
                    float(ordered[index]["longitude"]),
                )
                before = list(surviving)
                sources, surviving = update_worlds(coord, sources, surviving, thresholds)
                if before != surviving:
                    contraction_events.append(
                        {
                            "positive_deployment_id": deployment_id,
                            "available_after": end_time.strftime("%Y-%m-%d"),
                            "before": before,
                            "after": list(surviving),
                        }
                    )
            event_position += 1
        target = (float(row["latitude"]), float(row["longitude"]))
        layer_rows.append(support_summary(target, sources, surviving, thresholds))

    x_layer = np.asarray(layer_rows, dtype=float)
    x_augmented = np.hstack([x_base, x_layer])
    train = split == 0
    validation = split == 1
    outer = split == 2
    calibration = split < 2
    hyperparameters = contract["baseline"]["hyperparameters"]

    baseline_inner_model = fit_model(hyperparameters, x_base[train], y[train])
    augmented_inner_model = fit_model(hyperparameters, x_augmented[train], y[train])
    p_base_validation = predict_positive(baseline_inner_model, x_base[validation])
    p_aug_validation = predict_positive(augmented_inner_model, x_augmented[validation])
    validation_groups = [
        ordered[index]["subproject_name"] for index in range(n) if validation[index]
    ]
    inner_base = macro_loss(y[validation], p_base_validation, validation_groups)
    inner_augmented = macro_loss(y[validation], p_aug_validation, validation_groups)
    promoted = inner_augmented < inner_base

    baseline_final_model = fit_model(hyperparameters, x_base[calibration], y[calibration])
    augmented_final_model = fit_model(
        hyperparameters, x_augmented[calibration], y[calibration]
    )
    p_base_outer = predict_positive(baseline_final_model, x_base[outer])
    p_aug_outer = predict_positive(augmented_final_model, x_augmented[outer])
    outer_groups = [ordered[index]["subproject_name"] for index in range(n) if outer[index]]
    outer_base = macro_loss(y[outer], p_base_outer, outer_groups)
    outer_augmented = macro_loss(y[outer], p_aug_outer, outer_groups)
    selected_predictions = p_aug_outer if promoted else p_base_outer
    selected = outer_augmented if promoted else outer_base
    delta = selected - outer_base
    terminal = (
        "favorable_selective_added_value"
        if delta < 0
        else "adverse_selective_added_value"
        if delta > 0
        else "null_selective_added_value"
    )
    baseline_brier = macro_brier(y[outer], p_base_outer, outer_groups)
    augmented_brier = macro_brier(y[outer], p_aug_outer, outer_groups)
    selected_brier = macro_brier(y[outer], selected_predictions, outer_groups)

    return write_result(
        {
            **base,
            "terminal_class": terminal,
            "counts_as_fresh_predictive_evidence": True,
            "response_rows": len(sequence_rows),
            "resolved_headers": {
                "deployment_id": deployment_id_col,
                "scientific_name": scientific_name_col,
                "common_name_optional": common_name_col,
            },
            "focal_sequence_matches": {
                "scientific": exact_scientific_matches,
                "common_fallback": common_fallback_matches,
                "positive_deployments": len(positives),
            },
            "deployment_class_counts": counts,
            "split_sizes": {
                "inner_train": int(np.sum(train)),
                "inner_validation": int(np.sum(validation)),
                "outer": int(np.sum(outer)),
            },
            "layer_b": {
                "threshold_km": thresholds,
                "contraction_events": contraction_events,
                "surviving_local_worlds_final": surviving,
            },
            "inner_validation": {
                "baseline_macro_log_loss": inner_base,
                "augmented_macro_log_loss": inner_augmented,
                "augmented_minus_baseline": inner_augmented - inner_base,
                "promoted": bool(promoted),
            },
            "outer": {
                "baseline_macro_log_loss": outer_base,
                "always_augmented_macro_log_loss": outer_augmented,
                "selected_macro_log_loss": selected,
                "selected_minus_baseline": delta,
                "selected_minus_always_augmented": selected - outer_augmented,
                "selected_oracle_regret": selected - min(outer_base, outer_augmented),
                "baseline_macro_brier": baseline_brier,
                "always_augmented_macro_brier": augmented_brier,
                "selected_macro_brier": selected_brier,
                "selected_minus_baseline_brier": selected_brier - baseline_brier,
            },
        }
    )


if __name__ == "__main__":
    run()
