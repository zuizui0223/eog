"""Exploratory BAM-to-EOG geometry bridge with a frozen shared reference.

This module profiles *known* A/B/M masks and their intersections. It neither
recovers A/B/M from occurrence geometry nor estimates latent suitability,
movement, historical routes, or causal contributions of constraint axes.

The root EOG v0.1 API and all frozen manuscript endpoints are untouched.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Sequence

import numpy as np

from .comparative import RobustReference, infer_comparative_geometry
from .reference_policy import ReferenceDeclaration, validate_reference_declaration


SUBSETS = ("U", "A", "B", "M", "AB", "AM", "BM", "ABM")
METRICS = ("span", "mst_compactness", "gap_strength", "mst_cut_components")


def _sha256_json(data: Any) -> str:
    payload = json.dumps(
        data, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mask(mask: np.ndarray, n: int, name: str) -> np.ndarray:
    values = np.asarray(mask)
    if values.shape != (n,) or values.dtype.kind != "b":
        raise ValueError(f"{name} must be a one-dimensional boolean mask of length {n}")
    return values.copy()


def _geometry(values: np.ndarray, reference: RobustReference) -> dict[str, float | int]:
    result = infer_comparative_geometry(values, reference)
    return {
        "span": float(result.span),
        "mst_compactness": float(result.continuity),
        "gap_strength": float(result.gap_strength),
        "mst_cut_components": int(result.component_count),
    }


def _seed_for_mask(seed: int, mask: np.ndarray) -> int:
    # The ABM/G draw must be identical for distinct BAM worlds with the same G.
    payload = str(seed).encode("ascii") + b"|" + mask.tobytes()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _profile_group(
    values: np.ndarray,
    mask: np.ndarray,
    reference: RobustReference,
    *,
    matched_size: int | None,
    n_draws: int,
    seed: int,
) -> dict[str, Any]:
    indices = np.flatnonzero(mask)
    n = int(indices.size)
    row: dict[str, Any] = {
        "n_nodes": n,
        "full_status": "estimable" if n >= 2 else "not_estimable_lt2",
        "full": _geometry(values[indices], reference) if n >= 2 else None,
        "matched_status": "not_estimable",
        "matched": None,
    }
    if matched_size is None:
        row["matched_status"] = "not_estimable_g_lt2"
    elif n < matched_size:
        row["matched_status"] = "insufficient_nodes"
    else:
        rng = np.random.default_rng(_seed_for_mask(seed, mask))
        sampled: dict[str, list[float]] = {name: [] for name in METRICS}
        for _ in range(n_draws):
            chosen = np.sort(rng.choice(indices, size=matched_size, replace=False))
            metrics = _geometry(values[chosen], reference)
            for name in METRICS:
                sampled[name].append(float(metrics[name]))
        row["matched_status"] = "estimable"
        row["matched"] = {
            "sample_size": matched_size,
            "n_draws": n_draws,
            "median": {name: float(np.median(v)) for name, v in sampled.items()},
            "q05": {name: float(np.quantile(v, 0.05)) for name, v in sampled.items()},
            "q95": {name: float(np.quantile(v, 0.95)) for name, v in sampled.items()},
        }
    return row


def profile_bam_geometry(
    node_features: np.ndarray,
    *,
    A: np.ndarray,
    B: np.ndarray,
    M: np.ndarray,
    reference: RobustReference,
    declaration: ReferenceDeclaration,
    matched_size: int | None = None,
    n_draws: int = 64,
    seed: int = 20261029,
) -> dict[str, Any]:
    """Profile U/A/B/M/AB/AM/BM/ABM in the same frozen feature coordinates.

    The masks are known generative states, never inferred from an observed G.
    If no matched_size is specified, every subset is matched to the size of
    G=A&B&M. With fewer than two G nodes, no cross-group matched comparison
    is reported. q05/q95 are *sampling-sensitivity quantiles*, not CIs.
    """
    values = np.asarray(node_features, dtype=float)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 1:
        raise ValueError("node_features must have >=2 nodes and >=1 feature")
    if not np.isfinite(values).all():
        raise ValueError("node_features must be finite")
    if values.shape[1] != reference.median.size:
        raise ValueError("node_features dimension differs from reference")
    validate_reference_declaration(declaration)
    if not isinstance(n_draws, int) or isinstance(n_draws, bool) or n_draws < 1:
        raise ValueError("n_draws must be a positive integer")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if matched_size is not None and (
        not isinstance(matched_size, int)
        or isinstance(matched_size, bool)
        or matched_size < 2
    ):
        raise ValueError("matched_size must be at least two")

    a = _mask(A, len(values), "A")
    b = _mask(B, len(values), "B")
    m = _mask(M, len(values), "M")
    masks = {
        "U": np.ones(len(values), dtype=bool),
        "A": a,
        "B": b,
        "M": m,
        "AB": a & b,
        "AM": a & m,
        "BM": b & m,
        "ABM": a & b & m,
    }
    g_size = int(masks["ABM"].sum())
    size = matched_size if matched_size is not None else (
        g_size if g_size >= 2 else None
    )

    rows = {
        name: _profile_group(
            values, masks[name], reference,
            matched_size=size, n_draws=n_draws, seed=seed,
        )
        for name in SUBSETS
    }

    def log_span_ratio(numerator: str, denominator: str) -> float | None:
        num = rows[numerator]["matched"]
        den = rows[denominator]["matched"]
        if num is None or den is None:
            return None
        x = num["median"]["span"]
        y = den["median"]["span"]
        return float(np.log(x / y)) if x > 0 and y > 0 else None

    data: dict[str, Any] = {
        "schema": "eog.bam_shared_reference_geometry.v0",
        "scope": "known-masks retrospective diagnostic; no causal attribution",
        "reference": reference.to_dict(),
        "reference_declaration": declaration.to_dict(),
        "n_nodes": int(len(values)),
        "n_features": int(values.shape[1]),
        "parameters": {
            "matched_size": size,
            "n_draws": n_draws,
            "seed": seed,
        },
        "feature_sha256": hashlib.sha256(
            np.ascontiguousarray(values, dtype="<f8").tobytes()
        ).hexdigest(),
        "mask_sha256": {
            name: hashlib.sha256(mask.tobytes()).hexdigest()
            for name, mask in masks.items()
        },
        "groups": rows,
        "contrasts": {
            f"ABM_vs_{baseline}_matched_log_span_ratio":
                log_span_ratio("ABM", baseline)
            for baseline in ("U", "A", "B", "M", "AB", "AM", "BM")
        },
        "limits": [
            "MST cut components are environmental-point-cloud diagnostics, "
            "not geographic support topology or actual populations.",
            "No observed G geometry can identify a unique BAM decomposition.",
            "Subsampling quantiles are not confidence or posterior intervals.",
            "Full group metrics use different n; only matched spans are "
            "intended for descriptive cross-group contrasts.",
            "This known-mask analysis cannot infer movement or causal effects.",
        ],
    }
    data["fingerprint"] = _sha256_json(data)
    return data


def profile_known_truth_bam_world(
    world: Any,
    node_features: np.ndarray,
    *,
    feature_node_ids: Sequence[str],
    reference: RobustReference,
    declaration: ReferenceDeclaration,
    matched_size: int | None = None,
    n_draws: int = 64,
    seed: int = 20261029,
) -> dict[str, Any]:
    """Adapt existing `eog.v2.known_truth_bam.BAMWorld` integer bit masks."""
    n = len(world.node_ids)
    if tuple(feature_node_ids) != tuple(world.node_ids):
        raise ValueError("feature node ID order does not match BAMWorld")
    if np.asarray(node_features).shape[0] != n:
        raise ValueError("node feature rows must match BAMWorld node IDs")
    integer_masks = (world.abiotic_mask, world.biotic_mask, world.movement_mask)
    if any(
        not isinstance(bits, (int, np.integer))
        or bits < 0 or bits >> n
        for bits in integer_masks + (world.occupied_mask,)
    ):
        raise ValueError("BAMWorld masks must be nonnegative within node universe")
    if world.occupied_mask != (
        world.abiotic_mask & world.biotic_mask & world.movement_mask
    ):
        raise ValueError("BAMWorld occupied_mask is not A & B & M")

    def decode(bits: int) -> np.ndarray:
        return np.asarray([(int(bits) >> i) & 1 for i in range(n)], dtype=bool)

    result = profile_bam_geometry(
        node_features,
        A=decode(world.abiotic_mask),
        B=decode(world.biotic_mask),
        M=decode(world.movement_mask),
        reference=reference,
        declaration=declaration,
        matched_size=matched_size,
        n_draws=n_draws,
        seed=seed,
    )
    result["world_id"] = str(world.world_id)
    result["node_order_sha256"] = _sha256_json(tuple(feature_node_ids))
    result["source_world_fingerprint"] = str(world.fingerprint)
    result["fingerprint"] = _sha256_json(
        {k: v for k, v in result.items() if k != "fingerprint"}
    )
    return result
