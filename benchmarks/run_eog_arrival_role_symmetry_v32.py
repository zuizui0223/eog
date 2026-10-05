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
PROTOCOL = ROOT / "validation/eog_arrival_role_symmetry_v32/protocol_v32.json"
V28 = ROOT / "validation/eog_original_idea_leopold_history_retention_v28/result_summary_v28.json"
V30 = ROOT / "validation/eog_grassland_above_below_history_retention_v30/result_summary_v30.json"
V31 = ROOT / "validation/eog_identity_storage_rank_abundance_v31/result_summary_v31.json"


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


def _rank(matrix: np.ndarray) -> np.ndarray:
    return np.sort(matrix, axis=1)[:, ::-1]


def _role_align(
    matrix: np.ndarray,
    history: np.ndarray,
    identity_names: list[str],
    history_to_identity: dict[str, str] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    index = {name: i for i, name in enumerate(identity_names)}
    output = np.empty_like(matrix, dtype=float)
    first_share = np.empty(matrix.shape[0], dtype=float)
    for i, (row, hist) in enumerate(zip(matrix, history, strict=True)):
        identity = hist if history_to_identity is None else history_to_identity[str(hist)]
        if identity not in index:
            raise RuntimeError(f"history identity {identity!r} is absent from target columns")
        first_index = index[identity]
        first = float(row[first_index])
        remaining = np.delete(row, first_index)
        remaining = np.sort(remaining)[::-1]
        output[i] = np.concatenate([[first], remaining])
        total = float(np.sum(row))
        if total <= 0:
            raise RuntimeError("nonpositive abundance total")
        first_share[i] = first / total
        if not np.allclose(np.sort(output[i]), np.sort(row), atol=0, rtol=0):
            raise RuntimeError("role alignment changed raw abundance multiset")
    return output, first_share


def _history_share_summary(history: np.ndarray, share: np.ndarray) -> dict[str, dict[str, float]]:
    result = {}
    for level in sorted(set(history.tolist()), key=str):
        values = share[history == level]
        result[str(level)] = {
            "n": int(values.size),
            "mean": float(np.mean(values)),
            "sd": float(np.std(values, ddof=1)) if values.size > 1 else 0.0,
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }
    return result


def _score_v28(protocol: dict, authoritative31: dict) -> dict:
    manifest = json.loads(v28.MANIFEST.read_text(encoding="utf-8"))
    source = {key: v28.download_source(path, blob) for key, (path, blob) in v28.SOURCE.items()}
    inputs = v28.build_inputs(source, manifest)

    matrix = np.asarray(inputs["corrected"], dtype=float)
    history = np.asarray(inputs["treatment"], dtype=object)
    context = np.asarray(inputs["genotype"], dtype=object)
    identities = list(v28.FOCAL_TAXA)

    labeled = v28.bray_curtis(matrix)
    rank = v28.bray_curtis(_rank(matrix))
    role_matrix, first_share = _role_align(matrix, history, identities)
    role = v28.bray_curtis(role_matrix)

    observed = {
        "labeled": v28.partial_distance_fast(labeled, context, history),
        "rank": v28.partial_distance_fast(rank, context, history),
        "role": v28.partial_distance_fast(role, context, history),
    }

    nperm = int(protocol["systems"]["v28_microbiome"]["permutations"])
    seed = int(protocol["systems"]["v28_microbiome"]["seed"])
    null = {key: np.empty(nperm, dtype=float) for key in observed}
    rng = np.random.default_rng(seed)
    for i in range(nperm):
        permuted = v28.permute_within_genotype(history, context, rng)
        null["labeled"][i] = v28.partial_distance_fast(labeled, context, permuted)
        null["rank"][i] = v28.partial_distance_fast(rank, context, permuted)
        # role response is fixed from the actual randomized history assignment
        null["role"][i] = v28.partial_distance_fast(role, context, permuted)

    s = {key: _summary(observed[key], null[key]) for key in observed}
    expected_labeled = authoritative31["systems"]["v28_microbiome"]["labeled_E"]
    expected_rank = authoritative31["systems"]["v28_microbiome"]["rank_abundance_E"]
    if not np.isclose(s["labeled"]["excess_over_null_median"], expected_labeled, atol=1e-12, rtol=0):
        raise RuntimeError("v28 labeled gate failed")
    if not np.isclose(s["rank"]["excess_over_null_median"], expected_rank, atol=1e-12, rtol=0):
        raise RuntimeError("v28 rank gate failed")

    labeled_E = s["labeled"]["excess_over_null_median"]
    rank_E = s["rank"]["excess_over_null_median"]
    role_E = s["role"]["excess_over_null_median"]
    return {
        "n": int(matrix.shape[0]),
        "labeled": s["labeled"],
        "rank": s["rank"],
        "role_aligned": s["role"],
        "role_gain_over_rank": float(role_E - rank_E),
        "role_fraction_of_labeled": float(role_E / labeled_E),
        "first_arriver_share_by_history": _history_share_summary(history, first_share),
        "gates": {"labeled_reproduced": True, "rank_reproduced": True, "raw_multiset_preserved": True},
    }


def _score_v30(protocol: dict, authoritative31: dict) -> dict:
    source_protocol = json.loads(v30.PROTOCOL.read_text(encoding="utf-8"))
    source = source_protocol["source"]
    payloads = {}
    for key in ("shoot", "root", "dictionary"):
        spec = source["files"][key]
        payloads[key] = v30._download(source["repository"], source["pinned_commit"], spec["path"], spec["blob_sha"])
    panel = v30._build_panel(v30._read_tsv(payloads["shoot"]), v30._read_tsv(payloads["root"]), source_protocol)
    v30._validate_primary(panel, source_protocol)
    rows = panel["rows"]

    matrix = np.vstack([row["shoot"] for row in rows]).astype(float)
    history = np.asarray([row["history"] for row in rows], dtype=object)
    block = np.asarray([row["replicate"] for row in rows], dtype=object)
    identities = list(source_protocol["targets"]["shoot_composition"]["columns"])
    mapping = protocol["systems"]["v30_grassland"]["mapping"]

    labeled = v30._bray_curtis(matrix)
    rank = v30._bray_curtis(_rank(matrix))
    role_matrix, first_share = _role_align(matrix, history, identities, mapping)
    role = v30._bray_curtis(role_matrix)

    reduced, full = v30._designs(block, history)
    observed = {
        "labeled": v30._partial_distance(labeled, reduced, full),
        "rank": v30._partial_distance(rank, reduced, full),
        "role": v30._partial_distance(role, reduced, full),
    }

    nperm = int(protocol["systems"]["v30_grassland"]["permutations"])
    seed = int(protocol["systems"]["v30_grassland"]["seed"])
    null = {key: np.empty(nperm, dtype=float) for key in observed}
    rng = np.random.default_rng(seed)
    for i in range(nperm):
        permuted = v30._permute_within_block(history, block, rng)
        reduced_p, full_p = v30._designs(block, permuted)
        null["labeled"][i] = v30._partial_distance(labeled, reduced_p, full_p)
        null["rank"][i] = v30._partial_distance(rank, reduced_p, full_p)
        # role response is fixed from actual treatment-specific assembly roles
        null["role"][i] = v30._partial_distance(role, reduced_p, full_p)

    s = {key: _summary(observed[key], null[key]) for key in observed}
    expected_labeled = authoritative31["systems"]["v30_grassland"]["labeled_E"]
    expected_rank = authoritative31["systems"]["v30_grassland"]["rank_abundance_E"]
    if not np.isclose(s["labeled"]["excess_over_null_median"], expected_labeled, atol=1e-12, rtol=0):
        raise RuntimeError("v30 labeled gate failed")
    if not np.isclose(s["rank"]["excess_over_null_median"], expected_rank, atol=1e-12, rtol=0):
        raise RuntimeError("v30 rank gate failed")

    labeled_E = s["labeled"]["excess_over_null_median"]
    rank_E = s["rank"]["excess_over_null_median"]
    role_E = s["role"]["excess_over_null_median"]
    return {
        "n": int(matrix.shape[0]),
        "labeled": s["labeled"],
        "rank": s["rank"],
        "role_aligned": s["role"],
        "role_gain_over_rank": float(role_E - rank_E),
        "role_fraction_of_labeled": float(role_E / labeled_E),
        "first_arriver_share_by_history": _history_share_summary(history, first_share),
        "gates": {"labeled_reproduced": True, "rank_reproduced": True, "raw_multiset_preserved": True},
    }


def run() -> dict:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_v32_scoring":
        raise RuntimeError("v32 protocol is not frozen")
    authoritative31 = json.loads(V31.read_text(encoding="utf-8"))

    microbiome = _score_v28(protocol, authoritative31)
    grassland = _score_v30(protocol, authoritative31)
    prediction = microbiome["role_fraction_of_labeled"] > grassland["role_fraction_of_labeled"]

    result = {
        "schema": "eog.arrival_role_symmetry.result.v32",
        "status": "completed_frozen_role_alignment_test",
        "systems": {"v28_microbiome": microbiome, "v30_grassland": grassland},
        "prospective_prediction": {
            "statement": protocol["prospective_prediction"],
            "supported": bool(prediction),
            "difference_in_role_fraction_v28_minus_v30": float(
                microbiome["role_fraction_of_labeled"] - grassland["role_fraction_of_labeled"]
            ),
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
