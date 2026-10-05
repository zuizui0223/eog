#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

import numpy as np

from eog.history_retention import (
    partial_r2_nested_distance,
    partial_r2_nested_scalar,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_grassland_above_below_history_retention_v30/protocol_v30.json"


def _git_blob_sha(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()


def _download(repo: str, commit: str, path: str, expected_blob: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-v30-grassland-history-retention/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    actual = _git_blob_sha(payload)
    if actual != expected_blob:
        raise RuntimeError(
            f"source blob mismatch for {path}: expected {expected_blob}, got {actual}"
        )
    return payload


def _read_tsv(payload: bytes) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def _float(value: str, label: str) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"non-numeric {label}: {value!r}") from error
    if not np.isfinite(output):
        raise RuntimeError(f"non-finite {label}: {value!r}")
    return output


def _bray_curtis(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    output = np.zeros((n, n), dtype=float)
    for i in range(n):
        numerator = np.abs(matrix[i + 1 :] - matrix[i]).sum(axis=1)
        denominator = (matrix[i + 1 :] + matrix[i]).sum(axis=1)
        if np.any(denominator <= 0):
            raise RuntimeError("Bray-Curtis denominator is zero")
        values = numerator / denominator
        output[i, i + 1 :] = values
        output[i + 1 :, i] = values
    return output


def _levels(values: np.ndarray) -> list[object]:
    return sorted(set(values.tolist()), key=lambda value: str(value))


def _dummy(values: np.ndarray) -> np.ndarray:
    levels = _levels(values)
    if len(levels) <= 1:
        return np.empty((values.size, 0), dtype=float)
    return np.column_stack(
        [(values == level).astype(float) for level in levels[1:]]
    )


def _designs(block: np.ndarray, history: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    intercept = np.ones((block.size, 1), dtype=float)
    b = _dummy(block)
    h = _dummy(history)
    reduced = np.column_stack([intercept, b])
    full = np.column_stack([intercept, b, h])
    return reduced, full


def _residual_ss_scalar(values: np.ndarray, design: np.ndarray) -> float:
    beta = np.linalg.lstsq(design, values, rcond=None)[0]
    residual = values - design @ beta
    return float(np.sum(residual * residual))


def _projection(design: np.ndarray) -> np.ndarray:
    return design @ np.linalg.pinv(design)


def _residual_ss_distance(distance: np.ndarray, design: np.ndarray) -> float:
    n = distance.shape[0]
    centering = np.eye(n) - np.ones((n, n), dtype=float) / n
    gower = -0.5 * centering @ (distance ** 2) @ centering
    projection = _projection(design)
    return float(np.trace((np.eye(n) - projection) @ gower))


def _partial_scalar(values: np.ndarray, reduced: np.ndarray, full: np.ndarray) -> float:
    r = _residual_ss_scalar(values, reduced)
    f = _residual_ss_scalar(values, full)
    return 0.0 if r <= 0 else float(np.clip((r - f) / r, 0, 1))


def _partial_distance(distance: np.ndarray, reduced: np.ndarray, full: np.ndarray) -> float:
    r = _residual_ss_distance(distance, reduced)
    f = _residual_ss_distance(distance, full)
    return 0.0 if r <= 0 else float(np.clip((r - f) / r, 0, 1))


def _permute_within_block(
    history: np.ndarray,
    block: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    output = history.copy()
    for level in _levels(block):
        idx = np.flatnonzero(block == level)
        output[idx] = rng.permutation(history[idx])
    return output


def _summary(observed: float, null: np.ndarray) -> dict[str, float]:
    return {
        "partial_r2": float(observed),
        "null_mean": float(np.mean(null)),
        "null_median": float(np.median(null)),
        "null_sd": float(np.std(null, ddof=1)),
        "null_q025": float(np.quantile(null, 0.025)),
        "null_q975": float(np.quantile(null, 0.975)),
        "excess_over_null_median": float(observed - np.median(null)),
        "permutation_p": float((np.sum(null >= observed - 1e-12) + 1) / (len(null) + 1)),
    }


def _build_panel(shoot_rows: list[dict[str, str]], root_rows: list[dict[str, str]], protocol: dict) -> dict:
    histories = set(protocol["primary_history"]["levels"])
    layer_order = protocol["targets"]["root_vertical_distribution"]["layer_order"]

    shoot = {}
    for row in shoot_rows:
        rz = row["Rz"]
        if rz in shoot:
            raise RuntimeError(f"duplicate shoot Rz {rz}")
        shoot[rz] = row

    root = {}
    for row in root_rows:
        root.setdefault(row["Rz"], []).append(row)

    rows = []
    for rz, srow in shoot.items():
        if srow["Treatment"] not in histories:
            continue
        if rz not in root:
            continue
        rrows = root[rz]
        treatments = {row["Treatment"] for row in rrows}
        reps = {row["Replicate"] for row in rrows}
        if treatments != {srow["Treatment"]} or reps != {srow["Replicate"]}:
            raise RuntimeError(f"joined metadata disagreement for Rz {rz}")
        if len(rrows) != 6 or {row["Layer"] for row in rrows} != set(layer_order):
            raise RuntimeError(f"Rz {rz} does not have exactly the frozen six root layers")
        by_layer = {row["Layer"]: row for row in rrows}

        shoot_vector = np.asarray(
            [_float(srow[column], f"Rz {rz} {column}") for column in protocol["targets"]["shoot_composition"]["columns"]],
            dtype=float,
        )
        root_vector = np.asarray(
            [_float(by_layer[layer]["RDW"], f"Rz {rz} {layer} RDW") for layer in layer_order],
            dtype=float,
        )
        if np.any(shoot_vector < 0) or np.any(root_vector < 0):
            raise RuntimeError(f"negative biomass in Rz {rz}")
        total_shoot = _float(srow["Total"], f"Rz {rz} Total")
        root_total = float(root_vector.sum())
        if root_total <= 0:
            raise RuntimeError(f"zero total root biomass in Rz {rz}")
        midpoints = np.asarray(
            protocol["scalar_sensitivities"]["root_mean_depth"]["midpoints_cm"],
            dtype=float,
        )
        root_mean_depth = float(np.sum(root_vector * midpoints) / root_total)
        rows.append(
            {
                "Rz": int(rz),
                "history": srow["Treatment"],
                "replicate": srow["Replicate"],
                "shoot": shoot_vector,
                "root": root_vector,
                "total_shoot": total_shoot,
                "root_mean_depth": root_mean_depth,
            }
        )

    rows.sort(key=lambda row: row["Rz"])
    return {"rows": rows}


def _validate_primary(panel: dict, protocol: dict) -> None:
    rows = panel["rows"]
    expected = protocol["primary_common_panel"]
    if len(rows) != expected["n"]:
        raise RuntimeError(f"expected {expected['n']} primary rhizoboxes, got {len(rows)}")

    counts = {}
    block_histories = {}
    for row in rows:
        counts[row["history"]] = counts.get(row["history"], 0) + 1
        block_histories.setdefault(row["replicate"], set()).add(row["history"])
    if counts != expected["counts_by_history"]:
        raise RuntimeError(f"history counts changed: {counts}")
    if any(len(values) < 2 for values in block_histories.values()):
        raise RuntimeError("a retained replicate has fewer than two history labels")


def _score(rows: list[dict], protocol: dict) -> dict:
    shoot = np.vstack([row["shoot"] for row in rows])
    root = np.vstack([row["root"] for row in rows])
    history = np.asarray([row["history"] for row in rows], dtype=object)
    block = np.asarray([row["replicate"] for row in rows], dtype=object)
    total_shoot = np.asarray([row["total_shoot"] for row in rows], dtype=float)
    root_mean_depth = np.asarray([row["root_mean_depth"] for row in rows], dtype=float)

    shoot_distance = _bray_curtis(shoot)
    root_distance = _bray_curtis(root)
    reduced, full = _designs(block, history)

    observed_shoot = partial_r2_nested_distance(
        shoot_distance, reduced, full, history_levels=len(_levels(history))
    ).partial_r2
    observed_root = partial_r2_nested_distance(
        root_distance, reduced, full, history_levels=len(_levels(history))
    ).partial_r2
    observed_total_shoot = partial_r2_nested_scalar(
        total_shoot, reduced, full, history_levels=len(_levels(history))
    ).partial_r2
    observed_root_depth = partial_r2_nested_scalar(
        root_mean_depth, reduced, full, history_levels=len(_levels(history))
    ).partial_r2

    if not np.isclose(observed_shoot, _partial_distance(shoot_distance, reduced, full), atol=1e-9):
        raise RuntimeError("generic/fast shoot statistic mismatch")
    if not np.isclose(observed_root, _partial_distance(root_distance, reduced, full), atol=1e-9):
        raise RuntimeError("generic/fast root statistic mismatch")

    nperm = int(protocol["randomization"]["permutations"])
    rng = np.random.default_rng(int(protocol["randomization"]["seed"]))
    null_shoot = np.empty(nperm)
    null_root = np.empty(nperm)
    null_total_shoot = np.empty(nperm)
    null_root_depth = np.empty(nperm)

    for i in range(nperm):
        permuted = _permute_within_block(history, block, rng)
        reduced_p, full_p = _designs(block, permuted)
        null_shoot[i] = _partial_distance(shoot_distance, reduced_p, full_p)
        null_root[i] = _partial_distance(root_distance, reduced_p, full_p)
        null_total_shoot[i] = _partial_scalar(total_shoot, reduced_p, full_p)
        null_root_depth[i] = _partial_scalar(root_mean_depth, reduced_p, full_p)

    shoot_summary = _summary(observed_shoot, null_shoot)
    root_summary = _summary(observed_root, null_root)

    return {
        "n": len(rows),
        "primary": {
            "shoot_functional_group_composition": shoot_summary,
            "root_vertical_distribution": root_summary,
            "delta_E_shoot_minus_root": float(
                shoot_summary["excess_over_null_median"]
                - root_summary["excess_over_null_median"]
            ),
        },
        "scalar_sensitivities": {
            "total_shoot_biomass": _summary(observed_total_shoot, null_total_shoot),
            "root_mean_depth": _summary(observed_root_depth, null_root_depth),
        },
        "gates": {
            "generic_fast_shoot_match": True,
            "generic_fast_root_match": True,
        },
    }


def run() -> dict:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_eog_v30_scoring":
        raise RuntimeError("v30 protocol is not frozen")

    source = protocol["source"]
    payloads = {}
    for key in ("shoot", "root", "dictionary"):
        spec = source["files"][key]
        payloads[key] = _download(
            source["repository"],
            source["pinned_commit"],
            spec["path"],
            spec["blob_sha"],
        )

    panel = _build_panel(
        _read_tsv(payloads["shoot"]),
        _read_tsv(payloads["root"]),
        protocol,
    )
    _validate_primary(panel, protocol)
    primary = _score(panel["rows"], protocol)

    without_137 = [row for row in panel["rows"] if row["Rz"] != 137]
    outlier_sensitivity = _score(without_137, protocol)

    result = {
        "schema": "eog.grassland_above_below_history_retention.result.v30",
        "status": "completed_frozen_external_benchmark",
        "source_commit": source["pinned_commit"],
        "source_blobs_verified": True,
        "primary_panel": {
            "n": len(panel["rows"]),
            "Rz": [row["Rz"] for row in panel["rows"]],
            "history_counts": {
                level: sum(row["history"] == level for row in panel["rows"])
                for level in protocol["primary_history"]["levels"]
            },
        },
        "score": primary,
        "source_outlier_sensitivity_without_Rz137": outlier_sensitivity,
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    result["fingerprint"] = hashlib.sha256(payload).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
