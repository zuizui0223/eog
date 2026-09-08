"""Parallel execution wrapper for the frozen Layer-B v2 causal factorial.

Scientific semantics are defined by causal_factorial_contract_v1.json and the canonical
cell generator in layer_b_v2_causal_factorial.py.  This wrapper only distributes
independent replicate seeds across processes; it does not alter learner settings,
random seeds, cells, outcomes, splits or estimands.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import json
import os
from pathlib import Path

import numpy as np

from benchmarks.layer_b_v2_causal_factorial import (
    CONTRACT,
    DEFAULT_OUTPUT,
    _build_replication,
    _main_effect,
)


def _one(args: tuple[int, dict[str, object]]) -> dict[str, object]:
    seed, contract = args
    return _build_replication(seed, contract)


def run_benchmark() -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    seeds = [int(seed) for seed in contract["design"]["replicate_seeds"]]
    max_workers = max(1, min(4, os.cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        reps = list(pool.map(_one, [(seed, contract) for seed in seeds]))

    generator = np.asarray([_main_effect(r, 0, "log_loss") for r in reps])
    static = np.asarray([_main_effect(r, 1, "log_loss") for r in reps])
    source = np.asarray([_main_effect(r, 2, "log_loss") for r in reps])
    full = np.asarray(
        [
            float(r["cells"]["111"]["log_loss"])
            - float(r["cells"]["000"]["log_loss"])
            for r in reps
        ]
    )
    clean_minus_baseline = np.asarray(
        [
            float(r["cells"]["000"]["log_loss"])
            - float(r["baseline_log_loss"])
            for r in reps
        ]
    )
    effects = {
        "generator_shift": generator,
        "static_reuse": static,
        "label_dependent_single_source": source,
        "full_defect": full,
    }
    summaries = {
        name: {
            "mean_log_loss_penalty": float(np.mean(values)),
            "median_log_loss_penalty": float(np.median(values)),
            "q025": float(np.quantile(values, 0.025)),
            "q975": float(np.quantile(values, 0.975)),
            "positive_replicate_fraction": float(np.mean(values > 0.0)),
        }
        for name, values in effects.items()
    }
    checks = {
        "generator_shift_median_positive": bool(np.median(generator) > 0.0),
        "static_reuse_median_positive": bool(np.median(static) > 0.0),
        "single_source_median_positive": bool(np.median(source) > 0.0),
        "full_defect_median_positive": bool(np.median(full) > 0.0),
        "clean_augmented_median_better_than_baseline": bool(
            np.median(clean_minus_baseline) < 0.0
        ),
    }
    if not all(checks.values()):
        raise AssertionError(f"predeclared causal-factorial check failed: {checks}")

    return {
        "schema": "eog.layer_b_mechanism_v2.causal_factorial_result.v1",
        "execution": {
            "replicate_parallelism_only": True,
            "max_workers": max_workers,
            "canonical_cell_generator": "benchmarks.layer_b_v2_causal_factorial._build_replication",
        },
        "counts_as_fresh_predictive_endpoint": False,
        "uses_biological_response": False,
        "changes_closed_eog_wf_synthesis": False,
        "replicate_count": len(reps),
        "primary_estimand": "paired within-replicate log-loss penalty under one-factor interventions",
        "effect_summaries": summaries,
        "clean_augmented_minus_baseline": {
            "mean": float(np.mean(clean_minus_baseline)),
            "median": float(np.median(clean_minus_baseline)),
            "favorable_fraction": float(np.mean(clean_minus_baseline < 0.0)),
        },
        "checks": checks,
        "cell_macro_log_loss": {
            key: float(
                np.mean([float(r["cells"][key]["log_loss"]) for r in reps])
            )
            for key in sorted(reps[0]["cells"])
        },
        "interpretation": "In this frozen synthetic known-truth system, each representation defect has a causal intervention effect on heldout transfer because all other data, outcomes, learner, baseline and split are paired and fixed. Effect magnitudes are benchmark-specific and cannot be assigned to Tampa.",
        "forbidden_interpretations": contract["forbidden_interpretations"],
    }


def main(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    result = run_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
