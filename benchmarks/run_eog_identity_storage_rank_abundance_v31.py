#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

try:
    from benchmarks import run_eog_original_idea_leopold_history_retention_v28 as v28
    from benchmarks import run_eog_grassland_above_below_history_retention_v30 as v30
except ModuleNotFoundError:
    import run_eog_original_idea_leopold_history_retention_v28 as v28
    import run_eog_grassland_above_below_history_retention_v30 as v30

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_identity_storage_rank_abundance_v31/protocol_v31.json"
V28_SUMMARY = ROOT / "validation/eog_original_idea_leopold_history_retention_v28/result_summary_v28.json"
V30_SUMMARY = ROOT / "validation/eog_grassland_above_below_history_retention_v30/result_summary_v30.json"


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
        "permutation_p": float((np.sum(null >= observed - 1e-12) + 1) / (len(null) + 1)),
    }


def _rank_matrix(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    return np.sort(matrix, axis=1)[:, ::-1]


def _shannon(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    totals = matrix.sum(axis=1)
    if np.any(totals <= 0):
        raise RuntimeError("nonpositive composition total")
    p = matrix / totals[:, None]
    terms = np.zeros_like(p, dtype=float)
    mask = p > 0
    terms[mask] = -p[mask] * np.log(p[mask])
    return terms.sum(axis=1)


def _score_v28(protocol: dict) -> dict:
    manifest = json.loads(v28.MANIFEST.read_text(encoding="utf-8"))
    source = {}
    for key, (path, blob) in v28.SOURCE.items():
        source[key] = v28.download_source(path, blob)
    inputs = v28.build_inputs(source, manifest)

    matrix = np.asarray(inputs["corrected"], dtype=float)
    rank = _rank_matrix(matrix)
    entropy = _shannon(matrix)
    genotype = np.asarray(inputs["genotype"], dtype=object)
    history = np.asarray(inputs["treatment"], dtype=object)

    labeled_distance = v28.bray_curtis(matrix)
    rank_distance = v28.bray_curtis(rank)

    observed = {
        "labeled": v28.partial_distance_fast(labeled_distance, genotype, history),
        "rank": v28.partial_distance_fast(rank_distance, genotype, history),
        "shannon": v28.partial_scalar_fast(entropy, genotype, history),
    }

    nperm = int(protocol["systems"]["v28_microbiome"]["permutations"])
    seed = int(protocol["systems"]["v28_microbiome"]["seed"])
    null = {key: np.empty(nperm, dtype=float) for key in observed}
    rng = np.random.default_rng(seed)
    for i in range(nperm):
        permuted = v28.permute_within_genotype(history, genotype, rng)
        null["labeled"][i] = v28.partial_distance_fast(labeled_distance, genotype, permuted)
        null["rank"][i] = v28.partial_distance_fast(rank_distance, genotype, permuted)
        null["shannon"][i] = v28.partial_scalar_fast(entropy, genotype, permuted)

    summaries = {key: _summary(observed[key], null[key]) for key in observed}
    gap = summaries["labeled"]["excess_over_null_median"] - summaries["rank"]["excess_over_null_median"]

    authoritative = json.loads(V28_SUMMARY.read_text(encoding="utf-8"))
    expected = authoritative["primary"]["fungal_community_composition"]["excess_over_null_median"]
    if not np.isclose(summaries["labeled"]["excess_over_null_median"], expected, atol=1e-12, rtol=0):
        raise RuntimeError("v28 labeled retained-history excess failed authoritative gate")

    return {
        "n": int(matrix.shape[0]),
        "dimensions": int(matrix.shape[1]),
        "labeled_composition": summaries["labeled"],
        "identity_stripped_rank_abundance": summaries["rank"],
        "shannon_entropy_sensitivity": summaries["shannon"],
        "identity_storage_gap": float(gap),
        "fraction_of_labeled_excess_remaining_after_identity_stripping": (
            None
            if summaries["labeled"]["excess_over_null_median"] <= 0
            else float(
                summaries["rank"]["excess_over_null_median"]
                / summaries["labeled"]["excess_over_null_median"]
            )
        ),
        "authoritative_labeled_gate": True,
    }


def _score_v30(protocol: dict) -> dict:
    source_protocol = json.loads(v30.PROTOCOL.read_text(encoding="utf-8"))
    source = source_protocol["source"]
    payloads = {}
    for key in ("shoot", "root", "dictionary"):
        spec = source["files"][key]
        payloads[key] = v30._download(
            source["repository"],
            source["pinned_commit"],
            spec["path"],
            spec["blob_sha"],
        )
    panel = v30._build_panel(
        v30._read_tsv(payloads["shoot"]),
        v30._read_tsv(payloads["root"]),
        source_protocol,
    )
    v30._validate_primary(panel, source_protocol)
    rows = panel["rows"]

    matrix = np.vstack([row["shoot"] for row in rows]).astype(float)
    rank = _rank_matrix(matrix)
    entropy = _shannon(matrix)
    history = np.asarray([row["history"] for row in rows], dtype=object)
    block = np.asarray([row["replicate"] for row in rows], dtype=object)

    labeled_distance = v30._bray_curtis(matrix)
    rank_distance = v30._bray_curtis(rank)
    reduced, full = v30._designs(block, history)

    observed = {
        "labeled": v30._partial_distance(labeled_distance, reduced, full),
        "rank": v30._partial_distance(rank_distance, reduced, full),
        "shannon": v30._partial_scalar(entropy, reduced, full),
    }

    nperm = int(protocol["systems"]["v30_grassland"]["permutations"])
    seed = int(protocol["systems"]["v30_grassland"]["seed"])
    null = {key: np.empty(nperm, dtype=float) for key in observed}
    rng = np.random.default_rng(seed)
    for i in range(nperm):
        permuted = v30._permute_within_block(history, block, rng)
        reduced_p, full_p = v30._designs(block, permuted)
        null["labeled"][i] = v30._partial_distance(labeled_distance, reduced_p, full_p)
        null["rank"][i] = v30._partial_distance(rank_distance, reduced_p, full_p)
        null["shannon"][i] = v30._partial_scalar(entropy, reduced_p, full_p)

    summaries = {key: _summary(observed[key], null[key]) for key in observed}
    gap = summaries["labeled"]["excess_over_null_median"] - summaries["rank"]["excess_over_null_median"]

    authoritative = json.loads(V30_SUMMARY.read_text(encoding="utf-8"))
    expected = authoritative["primary"]["shoot_functional_group_composition"]["excess_over_null_median"]
    if not np.isclose(summaries["labeled"]["excess_over_null_median"], expected, atol=1e-12, rtol=0):
        raise RuntimeError("v30 labeled retained-history excess failed authoritative gate")

    return {
        "n": int(matrix.shape[0]),
        "dimensions": int(matrix.shape[1]),
        "labeled_composition": summaries["labeled"],
        "identity_stripped_rank_abundance": summaries["rank"],
        "shannon_entropy_sensitivity": summaries["shannon"],
        "identity_storage_gap": float(gap),
        "fraction_of_labeled_excess_remaining_after_identity_stripping": (
            None
            if summaries["labeled"]["excess_over_null_median"] <= 0
            else float(
                summaries["rank"]["excess_over_null_median"]
                / summaries["labeled"]["excess_over_null_median"]
            )
        ),
        "authoritative_labeled_gate": True,
    }


def run() -> dict:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v31_scoring":
        raise RuntimeError("v31 protocol is not frozen")

    microbiome = _score_v28(protocol)
    grassland = _score_v30(protocol)
    both_positive = microbiome["identity_storage_gap"] > 0 and grassland["identity_storage_gap"] > 0

    result = {
        "schema": "eog.identity_storage_rank_abundance.result.v31",
        "status": "completed_frozen_derived_target_test",
        "systems": {
            "v28_microbiome": microbiome,
            "v30_grassland": grassland,
        },
        "primary_hypothesis": {
            "prediction": protocol["primary_estimand"]["directional_prediction"],
            "supported": bool(both_positive),
        },
        "gates": {
            "v28_labeled_result_reproduced": microbiome["authoritative_labeled_gate"],
            "v30_labeled_result_reproduced": grassland["authoritative_labeled_gate"],
            "same_dimensions_before_after_identity_stripping": True,
            "same_raw_values_before_after_identity_stripping": True,
        },
        "claim_boundary": protocol["claim_boundary"],
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
