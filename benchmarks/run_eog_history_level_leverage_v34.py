#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.history_retention import partial_r2_factorial_distance

try:
    from benchmarks import run_eog_original_idea_leopold_history_retention_v28 as v28
except ModuleNotFoundError:
    import run_eog_original_idea_leopold_history_retention_v28 as v28


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_history_level_leverage_v34/protocol_v34.json"
V31 = ROOT / "validation/eog_identity_storage_rank_abundance_v31/result_summary_v31.json"


def _rank(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    return np.sort(matrix, axis=1)[:, ::-1]


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


def _score(
    matrix: np.ndarray,
    history: np.ndarray,
    genotype: np.ndarray,
    *,
    permutations: int,
    seed: int,
) -> dict[str, object]:
    if matrix.shape[0] != history.size or history.size != genotype.size:
        raise ValueError("matrix, history and genotype row counts must match")
    if len(set(history.tolist())) < 2:
        raise RuntimeError("history must retain at least two levels")

    distance = v28.bray_curtis(_rank(matrix))
    fast = v28.partial_distance_fast(distance, genotype, history)
    generic = partial_r2_factorial_distance(
        distance,
        history,
        genotype,
    ).partial_r2
    if not np.isclose(fast, generic, atol=1e-9, rtol=0):
        raise RuntimeError(
            f"generic/fast rank statistic mismatch: {generic} vs {fast}"
        )

    null = np.empty(permutations, dtype=float)
    rng = np.random.default_rng(seed)
    for i in range(permutations):
        permuted = v28.permute_within_genotype(history, genotype, rng)
        null[i] = v28.partial_distance_fast(distance, genotype, permuted)

    result = _summary(fast, null)
    result["n"] = int(history.size)
    result["history_levels"] = sorted(set(history.tolist()), key=str)
    result["generic_fast_match"] = True
    return result


def _load_inputs() -> dict[str, np.ndarray]:
    manifest = json.loads(v28.MANIFEST.read_text(encoding="utf-8"))
    source = {
        key: v28.download_source(path, blob)
        for key, (path, blob) in v28.SOURCE.items()
    }
    inputs = v28.build_inputs(source, manifest)
    if int(inputs["sample_id"].size) != int(manifest["counts"]["common_panel"]):
        raise RuntimeError("v28 common panel count changed")
    return {
        "matrix": np.asarray(inputs["corrected"], dtype=float),
        "history": np.asarray(inputs["treatment"], dtype=object),
        "genotype": np.asarray(inputs["genotype"], dtype=object),
        "sample_id": np.asarray(inputs["sample_id"], dtype=object),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v34_scoring":
        raise RuntimeError("v34 protocol is not frozen")

    authoritative31 = json.loads(V31.read_text(encoding="utf-8"))
    inputs = _load_inputs()
    matrix = inputs["matrix"]
    history = inputs["history"]
    genotype = inputs["genotype"]

    histories = list(protocol["histories"])
    if set(history.tolist()) != set(histories):
        raise RuntimeError(
            f"history levels changed: {sorted(set(history.tolist()))}"
        )

    permutations = int(protocol["leave_one_history_out"]["permutations"])
    seed = int(protocol["leave_one_history_out"]["seed"])

    full = _score(
        matrix,
        history,
        genotype,
        permutations=permutations,
        seed=seed,
    )
    expected_E = float(
        authoritative31["systems"]["v28_microbiome"]["rank_abundance_E"]
    )
    if not np.isclose(
        full["excess_over_null_median"],
        expected_E,
        atol=1e-12,
        rtol=0,
    ):
        raise RuntimeError(
            f"v31 rank-E gate failed: {full['excess_over_null_median']} vs {expected_E}"
        )

    leave_one_out = {}
    for excluded in histories:
        mask = history != excluded
        remaining = history[mask]
        expected_remaining = set(histories) - {excluded}
        if set(remaining.tolist()) != expected_remaining:
            raise RuntimeError(
                f"excluding {excluded} did not leave exactly the four declared histories"
            )
        scored = _score(
            matrix[mask],
            remaining,
            genotype[mask],
            permutations=permutations,
            seed=seed,
        )
        scored["excluded_history"] = excluded
        scored["removed_n"] = int(np.sum(~mask))
        scored["leverage_D"] = float(
            full["excess_over_null_median"]
            - scored["excess_over_null_median"]
        )
        leave_one_out[excluded] = scored

    leverage_order = sorted(
        histories,
        key=lambda h: (-float(leave_one_out[h]["leverage_D"]), h),
    )
    alternaria_D = float(leave_one_out["Alternaria"]["leverage_D"])
    max_D = max(float(leave_one_out[h]["leverage_D"]) for h in histories)
    prediction_supported = (
        alternaria_D > 0
        and np.isclose(alternaria_D, max_D, atol=1e-12, rtol=0)
        and leverage_order[0] == "Alternaria"
    )

    binary = np.asarray(
        ["Alternaria" if value == "Alternaria" else "Other" for value in history],
        dtype=object,
    )
    binary_score = _score(
        matrix,
        binary,
        genotype,
        permutations=int(protocol["secondary_binary"]["permutations"]),
        seed=int(protocol["secondary_binary"]["seed"]),
    )

    result = {
        "schema": "eog.history_level_leverage.result.v34",
        "status": "completed_frozen_history_leverage_test",
        "full_rank_abundance": full,
        "leave_one_history_out": leave_one_out,
        "leverage_order_descending": leverage_order,
        "primary_prediction": {
            "statement": protocol["prospective_prediction"]["statement"],
            "supported": bool(prediction_supported),
            "Alternaria_D": alternaria_D,
            "max_D": float(max_D),
        },
        "secondary_Alternaria_vs_rest": binary_score,
        "gates": {
            "v31_full_rank_E_reproduced": True,
            "v28_source_and_common_panel_reproduced": True,
            "each_deletion_left_exactly_four_histories": True,
            "generic_fast_match_all_panels": True,
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
