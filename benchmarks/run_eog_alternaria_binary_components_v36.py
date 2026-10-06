#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.history_retention import (
    partial_r2_factorial_distance,
    partial_r2_factorial_scalar,
)

try:
    from benchmarks import run_eog_original_idea_leopold_history_retention_v28 as v28
    from benchmarks import run_eog_dominance_tail_history_storage_v35 as v35
except ModuleNotFoundError:
    import run_eog_original_idea_leopold_history_retention_v28 as v28
    import run_eog_dominance_tail_history_storage_v35 as v35

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_alternaria_binary_components_v36/protocol_v36.json"
V34 = ROOT / "validation/eog_history_level_leverage_v34/result_summary_v34.json"


def _summary(observed: float, null: np.ndarray) -> dict[str, float]:
    median = float(np.median(null))
    return {
        "partial_r2": float(observed),
        "null_mean": float(np.mean(null)),
        "null_median": median,
        "null_sd": float(np.std(null, ddof=1)),
        "null_q025": float(np.quantile(null, 0.025)),
        "null_q975": float(np.quantile(null, 0.975)),
        "excess_over_null_median": float(observed - median),
        "permutation_p": float(
            (np.sum(null >= observed - 1e-12) + 1) / (len(null) + 1)
        ),
    }


def _binary_history(history: np.ndarray) -> np.ndarray:
    return np.asarray(
        ["Alternaria" if value == "Alternaria" else "Other" for value in history],
        dtype=object,
    )


def _score(
    matrix: np.ndarray,
    original_history: np.ndarray,
    genotype: np.ndarray,
    *,
    permutations: int,
    seed: int,
) -> dict[str, object]:
    ranked, dominance, tail = v35._rank_decompose(matrix)
    binary = _binary_history(original_history)

    counts = {
        level: int(np.sum(binary == level))
        for level in sorted(set(binary.tolist()), key=str)
    }

    rank_distance = v28.bray_curtis(ranked)
    tail_distance = v28.bray_curtis(tail)

    observed_rank = v28.partial_distance_fast(rank_distance, genotype, binary)
    generic_rank = partial_r2_factorial_distance(
        rank_distance, binary, genotype
    ).partial_r2
    if not np.isclose(observed_rank, generic_rank, atol=1e-9, rtol=0):
        raise RuntimeError("full-rank generic/fast mismatch")

    observed_dominance = v28.partial_scalar_fast(dominance, genotype, binary)
    generic_dominance = partial_r2_factorial_scalar(
        dominance, binary, genotype
    ).partial_r2
    if not np.isclose(
        observed_dominance,
        generic_dominance,
        atol=1e-9,
        rtol=0,
    ):
        raise RuntimeError("dominance generic/fast mismatch")

    observed_tail = v28.partial_distance_fast(tail_distance, genotype, binary)
    generic_tail = partial_r2_factorial_distance(
        tail_distance, binary, genotype
    ).partial_r2
    if not np.isclose(observed_tail, generic_tail, atol=1e-9, rtol=0):
        raise RuntimeError("tail generic/fast mismatch")

    null_rank = np.empty(permutations, dtype=float)
    null_dominance = np.empty(permutations, dtype=float)
    null_tail = np.empty(permutations, dtype=float)

    rng = np.random.default_rng(seed)
    for i in range(permutations):
        permuted = v28.permute_within_genotype(binary, genotype, rng)
        null_rank[i] = v28.partial_distance_fast(
            rank_distance, genotype, permuted
        )
        null_dominance[i] = v28.partial_scalar_fast(
            dominance, genotype, permuted
        )
        null_tail[i] = v28.partial_distance_fast(
            tail_distance, genotype, permuted
        )

    descriptive = {}
    for level in ("Alternaria", "Other"):
        values = dominance[binary == level]
        descriptive[level] = {
            "n": int(values.size),
            "mean_rank1_share": float(np.mean(values)),
            "median_rank1_share": float(np.median(values)),
            "sd_rank1_share": float(np.std(values, ddof=1)),
        }

    return {
        "n": int(binary.size),
        "binary_counts": counts,
        "full_rank_gate": _summary(observed_rank, null_rank),
        "dominance_rank1": _summary(observed_dominance, null_dominance),
        "lower_rank_tail": _summary(observed_tail, null_tail),
        "descriptive_rank1_by_binary_history": descriptive,
        "gates": {
            "full_rank_generic_fast_match": True,
            "dominance_generic_fast_match": True,
            "tail_generic_fast_match": True,
            "tail_sum_positive_all_rows": True,
            "rank_multiset_preserved_all_rows": True,
        },
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v36_scoring":
        raise RuntimeError("v36 protocol is not frozen")

    authoritative34 = json.loads(V34.read_text(encoding="utf-8"))
    inputs = v35._load_inputs()

    score = _score(
        inputs["matrix"],
        inputs["history"],
        inputs["genotype"],
        permutations=int(protocol["model"]["permutations"]),
        seed=int(protocol["model"]["seed"]),
    )

    expected_counts = {
        "Alternaria": int(protocol["panel"]["alternaria_n"]),
        "Other": int(protocol["panel"]["other_n"]),
    }
    if score["binary_counts"] != expected_counts:
        raise RuntimeError(
            f"binary count gate failed: {score['binary_counts']} vs {expected_counts}"
        )

    expected_rank_E = float(
        authoritative34["secondary_Alternaria_vs_rest"][
            "excess_over_null_median"
        ]
    )
    actual_rank_E = float(
        score["full_rank_gate"]["excess_over_null_median"]
    )
    if not np.isclose(actual_rank_E, expected_rank_E, atol=1e-12, rtol=0):
        raise RuntimeError(
            f"v34 binary rank-E gate failed: {actual_rank_E} vs {expected_rank_E}"
        )

    E_dom = float(
        score["dominance_rank1"]["excess_over_null_median"]
    )
    E_tail = float(
        score["lower_rank_tail"]["excess_over_null_median"]
    )
    delta = E_dom - E_tail

    supported = E_dom > 0 and delta > 0

    result = {
        "schema": "eog.alternaria_binary_components.result.v36",
        "status": "completed_frozen_binary_component_test",
        "score": score,
        "primary_contrast": {
            "E_dominance": E_dom,
            "E_tail": E_tail,
            "DeltaE_dominance_minus_tail": float(delta),
        },
        "prospective_prediction": {
            "statement": "Alternaria_vs_rest_is_dominance_centered",
            "criteria": {
                "E_dominance_positive": bool(E_dom > 0),
                "DeltaE_dominance_minus_tail_positive": bool(delta > 0),
            },
            "supported": bool(supported),
        },
        "gates": {
            "v34_binary_full_rank_E_reproduced": True,
            "binary_counts_48_and_185": True,
            "generic_fast_observed_statistics_match": True,
            "tail_sums_positive": True,
            "rank_multisets_preserved": True,
        },
        "claim_boundary": protocol["claim_boundary"],
    }

    payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = hashlib.sha256(payload).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
