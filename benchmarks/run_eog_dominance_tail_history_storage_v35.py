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
except ModuleNotFoundError:
    import run_eog_original_idea_leopold_history_retention_v28 as v28

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_dominance_tail_history_storage_v35/protocol_v35.json"
V31 = ROOT / "validation/eog_identity_storage_rank_abundance_v31/result_summary_v31.json"
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


def _rank_decompose(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if matrix.ndim != 2 or matrix.shape[1] != 5:
        raise ValueError("expected a five-column abundance matrix")
    ranked = np.sort(matrix, axis=1)[:, ::-1]
    dominance = ranked[:, 0].copy()
    tail = ranked[:, 1:].copy()
    tail_sum = tail.sum(axis=1)
    if np.any(tail_sum <= 0):
        raise RuntimeError("lower-rank tail sum is nonpositive")
    tail_normalized = tail / tail_sum[:, None]
    for original, transformed in zip(matrix, ranked, strict=True):
        if not np.array_equal(np.sort(original), np.sort(transformed)):
            raise RuntimeError("rank transform changed abundance multiset")
    return ranked, dominance, tail_normalized


def _score_components(
    matrix: np.ndarray,
    history: np.ndarray,
    genotype: np.ndarray,
    *,
    permutations: int,
    seed: int,
) -> dict[str, object]:
    ranked, dominance, tail = _rank_decompose(matrix)
    rank_distance = v28.bray_curtis(ranked)
    tail_distance = v28.bray_curtis(tail)

    # Reproduce the complete rank-abundance score on this panel.
    rank_fast = v28.partial_distance_fast(rank_distance, genotype, history)
    rank_generic = partial_r2_factorial_distance(
        rank_distance, history, genotype
    ).partial_r2
    if not np.isclose(rank_fast, rank_generic, atol=1e-9, rtol=0):
        raise RuntimeError("rank generic/fast mismatch")

    dominance_fast = v28.partial_scalar_fast(dominance, genotype, history)
    dominance_generic = partial_r2_factorial_scalar(
        dominance, history, genotype
    ).partial_r2
    if not np.isclose(dominance_fast, dominance_generic, atol=1e-9, rtol=0):
        raise RuntimeError("dominance generic/fast mismatch")

    tail_fast = v28.partial_distance_fast(tail_distance, genotype, history)
    tail_generic = partial_r2_factorial_distance(
        tail_distance, history, genotype
    ).partial_r2
    if not np.isclose(tail_fast, tail_generic, atol=1e-9, rtol=0):
        raise RuntimeError("tail generic/fast mismatch")

    null_rank = np.empty(permutations, dtype=float)
    null_dominance = np.empty(permutations, dtype=float)
    null_tail = np.empty(permutations, dtype=float)
    rng = np.random.default_rng(seed)
    for i in range(permutations):
        permuted = v28.permute_within_genotype(history, genotype, rng)
        null_rank[i] = v28.partial_distance_fast(
            rank_distance, genotype, permuted
        )
        null_dominance[i] = v28.partial_scalar_fast(
            dominance, genotype, permuted
        )
        null_tail[i] = v28.partial_distance_fast(
            tail_distance, genotype, permuted
        )

    medians_by_history = {}
    for level in sorted(set(history.tolist()), key=str):
        values = dominance[history == level]
        medians_by_history[str(level)] = {
            "n": int(values.size),
            "median_rank1_share": float(np.median(values)),
            "mean_rank1_share": float(np.mean(values)),
        }

    return {
        "n": int(history.size),
        "history_levels": sorted(set(history.tolist()), key=str),
        "rank_abundance": _summary(rank_fast, null_rank),
        "dominance_rank1": _summary(dominance_fast, null_dominance),
        "lower_rank_tail": _summary(tail_fast, null_tail),
        "descriptive_rank1_by_history": medians_by_history,
        "gates": {
            "rank_generic_fast_match": True,
            "dominance_generic_fast_match": True,
            "tail_generic_fast_match": True,
            "tail_sum_positive_all_rows": True,
            "rank_multiset_preserved_all_rows": True,
        },
    }


def _load_inputs() -> dict[str, np.ndarray]:
    manifest = json.loads(v28.MANIFEST.read_text(encoding="utf-8"))
    source = {
        key: v28.download_source(path, blob)
        for key, (path, blob) in v28.SOURCE.items()
    }
    inputs = v28.build_inputs(source, manifest)
    if int(inputs["sample_id"].size) != int(manifest["counts"]["common_panel"]):
        raise RuntimeError("v28 common panel changed")
    return {
        "matrix": np.asarray(inputs["corrected"], dtype=float),
        "history": np.asarray(inputs["treatment"], dtype=object),
        "genotype": np.asarray(inputs["genotype"], dtype=object),
        "sample_id": np.asarray(inputs["sample_id"], dtype=object),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v35_scoring":
        raise RuntimeError("v35 protocol is not frozen")

    authoritative31 = json.loads(V31.read_text(encoding="utf-8"))
    authoritative34 = json.loads(V34.read_text(encoding="utf-8"))
    inputs = _load_inputs()

    matrix = inputs["matrix"]
    history = inputs["history"]
    genotype = inputs["genotype"]

    permutations = int(protocol["history_model"]["permutations"])
    seed = int(protocol["history_model"]["seed"])

    full = _score_components(
        matrix,
        history,
        genotype,
        permutations=permutations,
        seed=seed,
    )

    expected_rank_E = float(
        authoritative31["systems"]["v28_microbiome"]["rank_abundance_E"]
    )
    actual_rank_E = float(
        full["rank_abundance"]["excess_over_null_median"]
    )
    if not np.isclose(actual_rank_E, expected_rank_E, atol=1e-12, rtol=0):
        raise RuntimeError(
            f"v31 full rank E gate failed: {actual_rank_E} vs {expected_rank_E}"
        )

    mask = history != "Alternaria"
    if int(mask.sum()) != int(
        authoritative34["leave_one_history_out"]["Alternaria"]["n"]
    ):
        raise RuntimeError("v34 Alternaria deletion membership count changed")
    if int((~mask).sum()) != int(
        authoritative34["leave_one_history_out"]["Alternaria"]["removed_n"]
    ):
        raise RuntimeError("v34 Alternaria removed count changed")
    if "Alternaria" in set(history[mask].tolist()):
        raise RuntimeError("Alternaria remained after deletion")

    without_alternaria = _score_components(
        matrix[mask],
        history[mask],
        genotype[mask],
        permutations=permutations,
        seed=seed,
    )

    expected_minus_A_rank_E = float(
        authoritative34["leave_one_history_out"]["Alternaria"]["E_without"]
    )
    actual_minus_A_rank_E = float(
        without_alternaria["rank_abundance"]["excess_over_null_median"]
    )
    if not np.isclose(
        actual_minus_A_rank_E,
        expected_minus_A_rank_E,
        atol=1e-12,
        rtol=0,
    ):
        raise RuntimeError(
            "v34 Alternaria-deletion rank-E gate failed: "
            f"{actual_minus_A_rank_E} vs {expected_minus_A_rank_E}"
        )

    E_dom_full = float(full["dominance_rank1"]["excess_over_null_median"])
    E_dom_minus = float(
        without_alternaria["dominance_rank1"]["excess_over_null_median"]
    )
    E_tail_full = float(full["lower_rank_tail"]["excess_over_null_median"])
    E_tail_minus = float(
        without_alternaria["lower_rank_tail"]["excess_over_null_median"]
    )

    L_dom = E_dom_full - E_dom_minus
    L_tail = E_tail_full - E_tail_minus
    supported = L_dom > 0 and L_dom > L_tail

    result = {
        "schema": "eog.dominance_tail_history_storage.result.v35",
        "status": "completed_frozen_dominance_tail_test",
        "full_panel": full,
        "without_Alternaria": without_alternaria,
        "leverage": {
            "L_dominance": float(L_dom),
            "L_tail": float(L_tail),
            "dominance_minus_tail_leverage": float(L_dom - L_tail),
        },
        "prospective_prediction": {
            "statement": "Alternaria_leverage_is_dominance_centered",
            "criteria": {
                "L_dominance_positive": bool(L_dom > 0),
                "L_dominance_greater_than_L_tail": bool(L_dom > L_tail),
            },
            "supported": bool(supported),
        },
        "gates": {
            "v31_full_rank_E_reproduced": True,
            "v34_Alternaria_deletion_panel_reproduced": True,
            "v34_Alternaria_deletion_rank_E_reproduced": True,
            "generic_fast_matches_all_components": True,
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
