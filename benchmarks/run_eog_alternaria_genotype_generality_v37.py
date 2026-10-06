#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

try:
    from benchmarks import run_eog_original_idea_leopold_history_retention_v28 as v28
    from benchmarks import run_eog_dominance_tail_history_storage_v35 as v35
except ModuleNotFoundError:
    import run_eog_original_idea_leopold_history_retention_v28 as v28
    import run_eog_dominance_tail_history_storage_v35 as v35

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_alternaria_genotype_generality_v37/protocol_v37.json"


def _levels(values: np.ndarray) -> list[object]:
    return sorted(set(values.tolist()), key=str)


def _dummy(values: np.ndarray) -> np.ndarray:
    levels = _levels(values)
    if len(levels) <= 1:
        return np.empty((values.size, 0), dtype=float)
    return np.column_stack(
        [(values == level).astype(float) for level in levels[1:]]
    )


def _designs(
    genotype: np.ndarray,
    binary: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    intercept = np.ones((genotype.size, 1), dtype=float)
    g = _dummy(genotype)
    b = _dummy(binary)

    m0 = np.column_stack([intercept, g])
    m1 = np.column_stack([intercept, g, b])

    interaction = []
    for gi in range(g.shape[1]):
        for bi in range(b.shape[1]):
            interaction.append(g[:, gi] * b[:, bi])
    m2 = (
        np.column_stack([intercept, g, b, *interaction])
        if interaction
        else m1.copy()
    )
    return m0, m1, m2


def _sse(y: np.ndarray, design: np.ndarray) -> float:
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ beta
    return float(np.sum(residual * residual))


def _binary_history(history: np.ndarray) -> np.ndarray:
    return np.asarray(
        ["Alternaria" if value == "Alternaria" else "Other" for value in history],
        dtype=object,
    )


def _genotype_deltas(
    dominance: np.ndarray,
    binary: np.ndarray,
    genotype: np.ndarray,
) -> dict[str, float]:
    result = {}
    for level in _levels(genotype):
        mask = genotype == level
        a = dominance[mask & (binary == "Alternaria")]
        o = dominance[mask & (binary == "Other")]
        if a.size == 0 or o.size == 0:
            raise RuntimeError(f"genotype {level} lacks one binary history level")
        result[str(level)] = float(np.mean(a) - np.mean(o))
    return result


def _model_stats(
    dominance: np.ndarray,
    binary: np.ndarray,
    genotype: np.ndarray,
) -> dict[str, float]:
    m0, m1, m2 = _designs(genotype, binary)
    r0 = int(np.linalg.matrix_rank(m0))
    r1 = int(np.linalg.matrix_rank(m1))
    r2 = int(np.linalg.matrix_rank(m2))
    if not (r0 < r1 < r2):
        raise RuntimeError(
            f"nested model rank gate failed: {r0}, {r1}, {r2}"
        )

    sse0 = _sse(dominance, m0)
    sse1 = _sse(dominance, m1)
    sse2 = _sse(dominance, m2)

    ss_common = sse0 - sse1
    ss_context = sse1 - sse2
    ss_total = sse0 - sse2

    if ss_common < -1e-10 or ss_context < -1e-10 or ss_total < -1e-10:
        raise RuntimeError("negative nested incremental SS")
    if not np.isclose(
        ss_common + ss_context,
        ss_total,
        atol=1e-10,
        rtol=0,
    ):
        raise RuntimeError("history SS decomposition does not add")

    common_fraction = (
        float(ss_common / ss_total)
        if ss_total > 1e-15
        else 0.0
    )

    return {
        "SSE_M0": float(sse0),
        "SSE_M1": float(sse1),
        "SSE_M2": float(sse2),
        "SS_common": float(ss_common),
        "SS_context": float(ss_context),
        "SS_total": float(ss_total),
        "R2_common": float(ss_common / sse0),
        "R2_context": float(ss_context / sse0),
        "R2_total": float(ss_total / sse0),
        "common_fraction": common_fraction,
        "rank_M0": r0,
        "rank_M1": r1,
        "rank_M2": r2,
    }


def _summary(observed: float, null: np.ndarray) -> dict[str, float]:
    median = float(np.median(null))
    return {
        "observed": float(observed),
        "null_mean": float(np.mean(null)),
        "null_median": median,
        "null_q025": float(np.quantile(null, 0.025)),
        "null_q975": float(np.quantile(null, 0.975)),
        "permutation_p_upper": float(
            (np.sum(null >= observed - 1e-12) + 1)
            / (len(null) + 1)
        ),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v37_genotype_response_inspection":
        raise RuntimeError("v37 protocol is not frozen")

    inputs = v35._load_inputs()
    matrix = inputs["matrix"]
    history = inputs["history"]
    genotype = inputs["genotype"]

    _, dominance, _ = v35._rank_decompose(matrix)
    binary = _binary_history(history)

    counts = {
        str(g): {
            "Alternaria": int(np.sum((genotype == g) & (binary == "Alternaria"))),
            "Other": int(np.sum((genotype == g) & (binary == "Other"))),
        }
        for g in _levels(genotype)
    }
    expected_counts = protocol["panel"]["binary_counts_by_genotype"]
    if counts != expected_counts:
        raise RuntimeError(
            f"genotype allocation changed: {counts} vs {expected_counts}"
        )

    deltas = _genotype_deltas(dominance, binary, genotype)
    observed_model = _model_stats(dominance, binary, genotype)

    delta_values = np.asarray(list(deltas.values()), dtype=float)
    positive_count = int(np.sum(delta_values > 0))
    equal_weight_mean_delta = float(np.mean(delta_values))

    nperm = int(protocol["randomization"]["permutations"])
    seed = int(protocol["randomization"]["seed"])
    rng = np.random.default_rng(seed)

    null_common = np.empty(nperm, dtype=float)
    null_total = np.empty(nperm, dtype=float)
    null_context = np.empty(nperm, dtype=float)
    null_mean_delta = np.empty(nperm, dtype=float)

    for i in range(nperm):
        permuted = v28.permute_within_genotype(binary, genotype, rng)
        stats = _model_stats(dominance, permuted, genotype)
        null_common[i] = stats["R2_common"]
        null_total[i] = stats["R2_total"]
        null_context[i] = stats["R2_context"]
        p_deltas = _genotype_deltas(dominance, permuted, genotype)
        null_mean_delta[i] = float(np.mean(list(p_deltas.values())))

    region_by_genotype = {
        item["genotype"]: item["region"]
        for item in json.loads(v28.MANIFEST.read_text(encoding="utf-8"))["plants"]
    }
    region_summary = {}
    for region in ("East", "West"):
        vals = [
            value
            for g, value in deltas.items()
            if region_by_genotype[g] == region
        ]
        region_summary[region] = {
            "genotype_count": len(vals),
            "mean_delta": float(np.mean(vals)),
            "median_delta": float(np.median(vals)),
            "positive_count": int(np.sum(np.asarray(vals) > 0)),
        }

    criteria = {
        "common_fraction_greater_than_0_5": bool(
            observed_model["common_fraction"] > 0.5
        ),
        "at_least_7_of_12_positive": bool(positive_count >= 7),
        "equal_weight_mean_delta_positive": bool(
            equal_weight_mean_delta > 0
        ),
    }

    result = {
        "schema": "eog.alternaria_genotype_generality.result.v37",
        "status": "completed_frozen_genotype_generality_test",
        "n": int(binary.size),
        "binary_counts_by_genotype": counts,
        "model_decomposition": observed_model,
        "genotype_deltas": deltas,
        "genotype_delta_summary": {
            "positive_count": positive_count,
            "negative_or_zero_count": int(len(deltas) - positive_count),
            "equal_weight_mean_delta": equal_weight_mean_delta,
            "median_delta": float(np.median(delta_values)),
            "min_delta": float(np.min(delta_values)),
            "max_delta": float(np.max(delta_values)),
        },
        "randomization": {
            "common_R2": _summary(
                observed_model["R2_common"], null_common
            ),
            "total_R2": _summary(
                observed_model["R2_total"], null_total
            ),
            "context_R2": _summary(
                observed_model["R2_context"], null_context
            ),
            "equal_weight_mean_delta": _summary(
                equal_weight_mean_delta, null_mean_delta
            ),
            "permutations": nperm,
            "seed": seed,
        },
        "region_descriptive": region_summary,
        "prospective_prediction": {
            "statement": protocol["prospective_prediction"]["statement"],
            "criteria": criteria,
            "supported": bool(all(criteria.values())),
        },
        "gates": {
            "v28_common_panel_reproduced": True,
            "binary_counts_match_frozen_allocation": True,
            "all_genotypes_have_both_levels": True,
            "rank1_response_constructed_from_v35_rule": True,
            "nested_model_ranks_valid": True,
            "history_ss_decomposition_adds": True,
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
