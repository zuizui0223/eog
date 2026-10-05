#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.history_retention import (
    partial_r2_factorial_distance,
    partial_r2_factorial_scalar,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_wood_decomposer_history_retention_v29/protocol_v29.json"

FILES = {
    "sample_data": "sample.data.csv",
    "species_prevalence": "species.prevalence.csv",
    "collembola": "collembola.csv",
}


def _md5(payload: bytes) -> str:
    return hashlib.md5(payload).hexdigest()


def _read_csv(path: Path) -> tuple[bytes, list[dict[str, str]]]:
    payload = path.read_bytes()
    text = payload.decode("utf-8-sig")
    return payload, list(csv.DictReader(text.splitlines()))


def _require_float(value: str, *, label: str) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError) as error:
        raise RuntimeError(f"non-numeric {label}: {value!r}") from error
    if not np.isfinite(output):
        raise RuntimeError(f"non-finite {label}: {value!r}")
    return output


def _context(nitrogen: str, fungivores: str) -> str:
    n = nitrogen.strip().upper()
    f = fungivores.strip().upper()
    if n not in {"TRUE", "FALSE"} or f not in {"TRUE", "FALSE"}:
        raise RuntimeError(
            f"invalid Boolean context nitrogen={nitrogen!r}, fungivores={fungivores!r}"
        )
    return f"N={n}|F={f}"


def _index_unique(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value:
            raise RuntimeError(f"missing {key}")
        if value in output:
            raise RuntimeError(f"duplicate {key}: {value}")
        output[value] = row
    return output


def _bray_curtis(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    distance = np.zeros((n, n), dtype=float)
    for i in range(n):
        numerator = np.abs(matrix[i + 1 :] - matrix[i]).sum(axis=1)
        denominator = (matrix[i + 1 :] + matrix[i]).sum(axis=1)
        if np.any(denominator <= 0):
            raise RuntimeError("zero Bray-Curtis denominator")
        values = numerator / denominator
        distance[i, i + 1 :] = values
        distance[i + 1 :, i] = values
    return distance


def _jaccard(matrix: np.ndarray) -> np.ndarray:
    binary = matrix > 0
    n = binary.shape[0]
    distance = np.zeros((n, n), dtype=float)
    for i in range(n):
        left = binary[i]
        for j in range(i + 1, n):
            union = np.logical_or(left, binary[j]).sum()
            intersection = np.logical_and(left, binary[j]).sum()
            value = 0.0 if union == 0 else 1.0 - intersection / union
            distance[i, j] = value
            distance[j, i] = value
    return distance


def _group_labels(a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    if b is None:
        return np.asarray([str(value) for value in a], dtype=object)
    return np.asarray(
        [f"{x}\x1f{y}" for x, y in zip(a, b, strict=True)],
        dtype=object,
    )


def _scalar_residual_ss(values: np.ndarray, labels: np.ndarray) -> float:
    total = 0.0
    for label in np.unique(labels):
        group = values[labels == label]
        total += float(np.sum((group - np.mean(group)) ** 2))
    return total


def _distance_residual_ss(distance: np.ndarray, labels: np.ndarray) -> float:
    total = 0.0
    for label in np.unique(labels):
        index = np.flatnonzero(labels == label)
        if index.size <= 1:
            continue
        sub = distance[np.ix_(index, index)]
        total += float(np.sum(np.triu(sub * sub, 1)) / index.size)
    return total


def _fast_partial_scalar(
    values: np.ndarray,
    context: np.ndarray,
    history: np.ndarray,
) -> float:
    reduced = _scalar_residual_ss(values, _group_labels(context))
    full = _scalar_residual_ss(values, _group_labels(context, history))
    return 0.0 if reduced <= 0 else float(np.clip((reduced - full) / reduced, 0, 1))


def _fast_partial_distance(
    distance: np.ndarray,
    context: np.ndarray,
    history: np.ndarray,
) -> float:
    reduced = _distance_residual_ss(distance, _group_labels(context))
    full = _distance_residual_ss(distance, _group_labels(context, history))
    return 0.0 if reduced <= 0 else float(np.clip((reduced - full) / reduced, 0, 1))


def _permute_within_context(
    history: np.ndarray,
    context: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    output = history.copy()
    for level in np.unique(context):
        index = np.flatnonzero(context == level)
        output[index] = rng.permutation(history[index])
    return output


def _null_summary(observed: float, values: np.ndarray) -> dict[str, float]:
    return {
        "partial_r2": float(observed),
        "null_mean": float(np.mean(values)),
        "null_median": float(np.median(values)),
        "null_sd": float(np.std(values, ddof=1)),
        "null_q025": float(np.quantile(values, 0.025)),
        "null_q975": float(np.quantile(values, 0.975)),
        "excess_over_null_median": float(observed - np.median(values)),
        "permutation_p": float((np.sum(values >= observed - 1e-12) + 1) / (len(values) + 1)),
    }


def _build_panel(
    sample_rows: list[dict[str, str]],
    prevalence_rows: list[dict[str, str]],
    protocol: dict,
    *,
    harvest: str,
) -> dict[str, object]:
    primary = protocol["primary"]
    targets = protocol["targets"]
    history_levels = set(primary["history_levels"])
    community_columns = targets["community"]["columns"]

    prevalence = _index_unique(prevalence_rows, "Sample_ID")
    selected = []
    excluded_initial_labels: dict[str, int] = {}

    for row in sample_rows:
        if row.get("Experiment") != primary["experiment"]:
            continue
        if row.get("Harvest") != harvest:
            continue
        history = row.get(primary["history_variable"], "")
        if history not in history_levels:
            excluded_initial_labels[history] = excluded_initial_labels.get(history, 0) + 1
            continue

        sample_id = row.get("Sample_ID", "")
        if sample_id not in prevalence:
            raise RuntimeError(f"missing prevalence row for {sample_id}")
        community_row = prevalence[sample_id]

        initial_mass = _require_float(
            row.get("Disc_dry_mass_g_initial", ""),
            label=f"{sample_id} initial mass",
        )
        final_mass = _require_float(
            row.get("Disc_dry_mass_g_final", ""),
            label=f"{sample_id} final mass",
        )
        if initial_mass <= 0:
            raise RuntimeError(f"nonpositive initial mass for {sample_id}")

        vector = []
        for column in community_columns:
            value = _require_float(
                community_row.get(column, ""),
                label=f"{sample_id} {column}",
            )
            if value < 0 or value > 9:
                raise RuntimeError(
                    f"community prevalence outside [0,9] for {sample_id} {column}: {value}"
                )
            vector.append(value)

        selected.append(
            {
                "sample_id": sample_id,
                "history": history,
                "context": _context(
                    row.get("Nitrogen_added", ""),
                    row.get("Fungivores", ""),
                ),
                "community": vector,
                "mass_loss_fraction": (initial_mass - final_mass) / initial_mass,
                "mass_loss_absolute": initial_mass - final_mass,
            }
        )

    if len({row["sample_id"] for row in selected}) != len(selected):
        raise RuntimeError("duplicate Sample_ID in selected panel")

    context_history_counts: dict[str, int] = {}
    for row in selected:
        key = f"{row['context']}|H={row['history']}"
        context_history_counts[key] = context_history_counts.get(key, 0) + 1

    return {
        "rows": selected,
        "excluded_initial_labels": excluded_initial_labels,
        "context_history_counts": context_history_counts,
    }


def _score_panel(
    panel: dict[str, object],
    protocol: dict,
    *,
    enforce_primary_balance: bool,
) -> dict[str, object]:
    rows = panel["rows"]
    if enforce_primary_balance:
        expected_n = int(protocol["primary"]["expected_primary_n"])
        expected_rep = int(protocol["primary"]["expected_replicates_per_context_history_cell"])
        if len(rows) != expected_n:
            raise RuntimeError(f"primary common panel expected {expected_n}, got {len(rows)}")
        counts = panel["context_history_counts"]
        if len(counts) != 16 or any(value != expected_rep for value in counts.values()):
            raise RuntimeError(
                "primary context-history cells are not exactly 16 cells x 5 replicates"
            )

    community = np.asarray([row["community"] for row in rows], dtype=float)
    decomposition = np.asarray([row["mass_loss_fraction"] for row in rows], dtype=float)
    absolute_loss = np.asarray([row["mass_loss_absolute"] for row in rows], dtype=float)
    history = np.asarray([row["history"] for row in rows], dtype=object)
    context = np.asarray([row["context"] for row in rows], dtype=object)

    bray = _bray_curtis(community)
    jaccard = _jaccard(community)

    observed_community = partial_r2_factorial_distance(bray, history, context).partial_r2
    observed_decomposition = partial_r2_factorial_scalar(
        decomposition, history, context
    ).partial_r2

    fast_community = _fast_partial_distance(bray, context, history)
    fast_decomposition = _fast_partial_scalar(decomposition, context, history)
    if not np.isclose(observed_community, fast_community, atol=1e-9, rtol=0):
        raise RuntimeError("fast/generic community statistic mismatch")
    if not np.isclose(observed_decomposition, fast_decomposition, atol=1e-9, rtol=0):
        raise RuntimeError("fast/generic decomposition statistic mismatch")

    nperm = int(protocol["randomization"]["permutations"])
    rng = np.random.default_rng(int(protocol["randomization"]["seed"]))
    null_community = np.empty(nperm, dtype=float)
    null_decomposition = np.empty(nperm, dtype=float)
    for i in range(nperm):
        permuted = _permute_within_context(history, context, rng)
        null_community[i] = _fast_partial_distance(bray, context, permuted)
        null_decomposition[i] = _fast_partial_scalar(decomposition, context, permuted)

    primary_community = _null_summary(observed_community, null_community)
    primary_decomposition = _null_summary(
        observed_decomposition, null_decomposition
    )

    jaccard_observed = _fast_partial_distance(jaccard, context, history)
    absolute_observed = _fast_partial_scalar(absolute_loss, context, history)

    return {
        "n": len(rows),
        "context_levels": sorted(set(context.tolist())),
        "history_levels": sorted(set(history.tolist())),
        "context_history_counts": panel["context_history_counts"],
        "primary": {
            "community_bray_curtis": primary_community,
            "decomposition_fractional_mass_loss": primary_decomposition,
            "delta_E_community_minus_decomposition": (
                primary_community["excess_over_null_median"]
                - primary_decomposition["excess_over_null_median"]
            ),
        },
        "sensitivities": {
            "community_binary_jaccard_observed_partial_r2": float(jaccard_observed),
            "decomposition_absolute_mass_loss_observed_partial_r2": float(absolute_observed),
        },
        "gates": {
            "generic_fast_community_match": True,
            "generic_fast_decomposition_match": True,
        },
    }


def run(source_dir: Path) -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_target_scoring_raw_transport_pending":
        raise RuntimeError("v29 protocol is not in the frozen pre-score state")

    payloads: dict[str, bytes] = {}
    rows: dict[str, list[dict[str, str]]] = {}
    verification = {}
    for key, filename in FILES.items():
        path = source_dir / filename
        payload, parsed = _read_csv(path)
        expected = protocol["source"]["files"][key]
        actual_md5 = _md5(payload)
        if actual_md5 != expected["md5"]:
            raise RuntimeError(
                f"MD5 mismatch for {filename}: expected {expected['md5']}, got {actual_md5}"
            )
        if len(payload) != int(expected["size_bytes"]):
            raise RuntimeError(
                f"size mismatch for {filename}: expected {expected['size_bytes']}, got {len(payload)}"
            )
        payloads[key] = payload
        rows[key] = parsed
        verification[key] = {
            "path": filename,
            "bytes": len(payload),
            "md5": actual_md5,
        }

    primary_panel = _build_panel(
        rows["sample_data"],
        rows["species_prevalence"],
        protocol,
        harvest=protocol["primary"]["harvest"],
    )
    primary_score = _score_panel(
        primary_panel,
        protocol,
        enforce_primary_balance=True,
    )

    six_month_panel = _build_panel(
        rows["sample_data"],
        rows["species_prevalence"],
        protocol,
        harvest="6 month",
    )
    six_month_score = _score_panel(
        six_month_panel,
        protocol,
        enforce_primary_balance=False,
    )

    result: dict[str, object] = {
        "schema": "eog.wood_decomposer_history_retention.result.v29",
        "status": "completed_frozen_external_benchmark",
        "source_verification": verification,
        "primary_harvest": protocol["primary"]["harvest"],
        "primary_panel": {
            "excluded_initial_labels": primary_panel["excluded_initial_labels"],
            "score": primary_score,
        },
        "temporal_sensitivity_6_month": {
            "excluded_initial_labels": six_month_panel["excluded_initial_labels"],
            "score": six_month_score,
        },
        "claim_boundary": protocol["claim_boundary"],
    }
    fingerprint_payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = hashlib.sha256(fingerprint_payload).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
