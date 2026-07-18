#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

REQUIRED_PATCH = {
    "patch_id",
    "priority_score",
    "nearest_occurrence_distance",
    "environmental_similarity",
    "travel_cost",
    "accessible",
}
REQUIRED_OUTCOME = {"patch_id", "surveyed", "detected", "effort"}
LEAKAGE_NAMES = {"detected", "detection", "surveyed", "outcome", "presence", "absence"}


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate(patches: list[dict[str, str]], outcomes: list[dict[str, str]]) -> None:
    if not patches or not outcomes:
        raise ValueError("both input tables must contain rows")
    patch_cols = set(patches[0])
    outcome_cols = set(outcomes[0])
    missing_patch = REQUIRED_PATCH - patch_cols
    missing_outcome = REQUIRED_OUTCOME - outcome_cols
    if missing_patch:
        raise ValueError(f"candidate table missing columns: {sorted(missing_patch)}")
    if missing_outcome:
        raise ValueError(f"outcome table missing columns: {sorted(missing_outcome)}")
    leaked = {c for c in patch_cols if c.lower() in LEAKAGE_NAMES}
    if leaked:
        raise ValueError(f"candidate table contains outcome-like columns: {sorted(leaked)}")
    patch_ids = [r["patch_id"] for r in patches]
    outcome_ids = [r["patch_id"] for r in outcomes]
    if len(set(patch_ids)) != len(patch_ids):
        raise ValueError("duplicate patch_id in candidate table")
    if len(set(outcome_ids)) != len(outcome_ids):
        raise ValueError("duplicate patch_id in outcome table")
    unknown = sorted(set(outcome_ids) - set(patch_ids))
    if unknown:
        raise ValueError(f"outcomes reference unknown patch IDs: {unknown[:5]}")


def prepare(patches: list[dict[str, str]], outcomes: list[dict[str, str]]) -> list[dict[str, object]]:
    outcome_by_id = {r["patch_id"]: r for r in outcomes}
    rows: list[dict[str, object]] = []
    for patch in patches:
        outcome = outcome_by_id.get(patch["patch_id"])
        if not truth(patch["accessible"]) or outcome is None or not truth(outcome["surveyed"]):
            continue
        rows.append(
            {
                "patch_id": patch["patch_id"],
                "priority_score": float(patch["priority_score"]),
                "nearest_occurrence_distance": float(patch["nearest_occurrence_distance"]),
                "environmental_similarity": float(patch["environmental_similarity"]),
                "travel_cost": max(float(patch["travel_cost"]), 1e-12),
                "detected": int(truth(outcome["detected"])),
                "effort": max(float(outcome["effort"]), 0.0),
            }
        )
    if len(rows) < 4:
        raise ValueError("at least four accessible surveyed patches are required")
    return rows


def ordered(rows: list[dict[str, object]], rule: str) -> list[dict[str, object]]:
    if rule == "priority":
        return sorted(rows, key=lambda r: (-float(r["priority_score"]), str(r["patch_id"])))
    if rule == "nearest":
        return sorted(rows, key=lambda r: (float(r["nearest_occurrence_distance"]), str(r["patch_id"])))
    if rule == "environment":
        return sorted(rows, key=lambda r: (-float(r["environmental_similarity"]), str(r["patch_id"])))
    raise ValueError(rule)


def summarize_order(rows: list[dict[str, object]], rule: str, primary_k: int) -> dict[str, object]:
    ranked = ordered(rows, rule)
    detections = np.asarray([float(r["detected"]) for r in ranked])
    costs = np.asarray([float(r["travel_cost"]) for r in ranked])
    k = min(primary_k, len(ranked))
    total_detected = max(float(detections.sum()), 1.0)
    cumulative_cost = np.cumsum(costs)
    cumulative_detection = np.cumsum(detections)
    half_budget = 0.5 * float(costs.sum())
    at_half = int(np.searchsorted(cumulative_cost, half_budget, side="right"))
    at_half = min(max(at_half, 1), len(ranked))
    return {
        "rule": rule,
        "n_eligible": len(ranked),
        "primary_k": k,
        "detections_top_k": int(detections[:k].sum()),
        "yield_top_k": float(detections[:k].mean()),
        "recall_top_k": float(detections[:k].sum() / total_detected),
        "detections_at_half_cost": int(detections[:at_half].sum()),
        "recall_at_half_cost": float(detections[:at_half].sum() / total_detected),
        "cost_top_k": float(costs[:k].sum()),
    }


def random_reference(
    rows: list[dict[str, object]], primary_k: int, draws: int, seed: int
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    detections = np.asarray([float(r["detected"]) for r in rows])
    costs = np.asarray([float(r["travel_cost"]) for r in rows])
    k = min(primary_k, len(rows))
    yields, recalls = [], []
    total = max(float(detections.sum()), 1.0)
    for _ in range(draws):
        idx = rng.permutation(len(rows))
        yields.append(float(detections[idx[:k]].mean()))
        cumulative_cost = np.cumsum(costs[idx])
        half = 0.5 * float(costs.sum())
        n_half = min(max(int(np.searchsorted(cumulative_cost, half, side="right")), 1), len(rows))
        recalls.append(float(detections[idx[:n_half]].sum() / total))
    return {
        "random_yield_top_k_median": float(np.median(yields)),
        "random_yield_top_k_p90": float(np.quantile(yields, 0.9)),
        "random_recall_half_cost_median": float(np.median(recalls)),
        "random_recall_half_cost_p90": float(np.quantile(recalls, 0.9)),
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    patches = read_rows(args.candidates)
    outcomes = read_rows(args.outcomes)
    validate(patches, outcomes)
    eligible = prepare(patches, outcomes)
    summaries = [summarize_order(eligible, r, args.primary_k) for r in ("priority", "nearest", "environment")]
    by_rule = {str(r["rule"]): r for r in summaries}
    random = random_reference(eligible, args.primary_k, args.random_draws, args.seed)
    priority = by_rule["priority"]
    nearest = by_rule["nearest"]
    decision = {
        "eligible_surveyed_patches": len(eligible),
        "observed_detections": int(sum(int(r["detected"]) for r in eligible)),
        "primary_k": int(priority["primary_k"]),
        "priority_yield_top_k": float(priority["yield_top_k"]),
        "nearest_yield_top_k": float(nearest["yield_top_k"]),
        **random,
    }
    decision["beats_random_median"] = bool(
        decision["priority_yield_top_k"] > decision["random_yield_top_k_median"]
    )
    decision["beats_nearest"] = bool(
        decision["priority_yield_top_k"] > decision["nearest_yield_top_k"]
    )
    decision["passes_outcome_gate"] = bool(
        decision["beats_random_median"] and decision["beats_nearest"]
    )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "survey_patch_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    with (args.output / "survey_patch_eligible.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(eligible[0]))
        writer.writeheader(); writer.writerows(eligible)
    (args.output / "survey_patch_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/survey_patch_validation"))
    parser.add_argument("--primary-k", type=int, default=10)
    parser.add_argument("--random-draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261015)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2))


if __name__ == "__main__":
    main()
