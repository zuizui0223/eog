"""Matched-information developmental comparison; no biological outcomes."""

from __future__ import annotations

import hashlib
import json
import platform

import numpy as np
import sklearn

from benchmarks.geometry_offset_comparison import NAMES
from benchmarks.innovation_offset_comparison import (
    _loss,
    _probability,
    _rf,
    choose_on_calibration,
)
from eog.v2.contextual_innovation_summary import summarize_contextual_innovation
from eog.v2.innovation_offset import fit_innovation_offset
from eog.v2.reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    summarize_first_passage,
)
from eog.v2.source_symmetric_predictive_summary import (
    summarize_source_symmetric_support,
)

SEEDS = (901, 907, 911, 919, 929, 937, 941, 947)
REGIMES = ("diffusion", "best_path", "environment_only", "unseen_diffusion_reversal")


def best_path_support(transition, source, target, steps=4):
    """Maximum single first-arrival path weight, not the sum over paths."""
    if source == target:
        return 1.0
    mass = np.zeros(len(transition))
    mass[source] = 1.0
    best = 0.0
    for _ in range(steps):
        mass = np.max(mass[:, None] * transition, axis=0)
        best = max(best, float(mass[target]))
        mass[target] = 0
    return best


def simulate_hits(transition, rng, trajectories=512, steps=4):
    """Independent killed-walk simulation; no EOG first-passage call."""
    n = len(transition)
    # Missing row mass enters an absorbing cemetery state.
    cdf = np.cumsum(transition, axis=1)
    fractions = []
    for source in (0, 1):
        state = np.full(trajectories, source)
        hits = np.zeros((trajectories, n), dtype=bool)
        hits[:, source] = True
        for _ in range(steps):
            alive = np.flatnonzero(state < n)
            if not alive.size:
                break
            draw = rng.uniform(size=len(alive))
            state[alive] = np.sum(draw[:, None] >= cdf[state[alive]], axis=1)
            arrived = np.flatnonzero(state < n)
            hits[arrived, state[arrived]] = True
        fractions.append(hits.mean(axis=0))
    return np.mean(fractions, axis=0)


def matched_state(xy):
    distance = np.linalg.norm(xy[:, None] - xy[None, :], axis=2)
    total, best = np.zeros((2, 2, 8)), np.zeros((2, 2, 8))
    operators = []
    for world, radius in enumerate((0.45, 0.65)):
        edges = [
            DynamicReachabilityEdge(
                i, j, geographic_support=float(np.exp(-distance[i, j] / 0.4))
            )
            for i in range(8)
            for j in range(8)
            if i != j and distance[i, j] <= radius
        ]
        operator = build_dynamic_transition_operator(NAMES, edges, loss_support=0.3)
        operators.append(operator)
        for source in range(2):
            for target in range(8):
                total[source, world, target] = summarize_first_passage(
                    operator, (NAMES[source],), NAMES[target], max_steps=4
                ).horizon_support
                best[source, world, target] = best_path_support(
                    operator.transition, source, target
                )
    if np.any(best > total + 1e-12):
        raise AssertionError("single path exceeds all first-arrival paths")
    summaries = [
        summarize_source_symmetric_support(
            tensor,
            source_ids=NAMES[:2],
            world_ids=("r045", "r065"),
            node_ids=NAMES,
            declared_world_count=2,
        )
        for tensor in (total, best)
    ]
    return summaries, operators, best, np.min(distance[:2], axis=0)


def build_design(seed, graph_count=120):
    rng = np.random.default_rng(seed)
    rows = {
        k: [] for k in ("x", "eog", "path", "diffusion_change", "path_change", "groups")
    }
    fingerprints = []
    for graph in range(graph_count):
        reference = rng.uniform(size=(8, 2))
        current = reference + rng.normal(0, 0.12, size=(8, 2))
        ref, ref_ops, ref_best, ref_direct = matched_state(reference)
        cur, cur_ops, cur_best, cur_direct = matched_state(current)
        world = int(rng.integers(2))  # Never returned as a predictor.
        diffusion_change = simulate_hits(
            cur_ops[world].transition, rng
        ) - simulate_hits(ref_ops[world].transition, rng)
        path_change = cur_best[:, world].mean(axis=0) - ref_best[:, world].mean(axis=0)
        eog = summarize_contextual_innovation(ref[0], cur[0])
        path = summarize_contextual_innovation(ref[1], cur[1])
        rows["x"].extend(
            np.c_[current[2:], reference[2:], cur_direct[2:], ref_direct[2:]]
        )
        rows["eog"].extend(eog.feature_matrix[2:])
        rows["path"].extend(path.feature_matrix[2:, 1:3])
        rows["diffusion_change"].extend(diffusion_change[2:])
        rows["path_change"].extend(path_change[2:])
        rows["groups"].extend([graph] * 6)
        fingerprints.append(
            [
                *[op.fingerprint for op in ref_ops + cur_ops],
                eog.fingerprint,
                path.fingerprint,
            ]
        )
    return {
        **{k: np.asarray(v) for k, v in rows.items()},
        "uniforms": rng.uniform(size=graph_count * 6),
        "provenance": hashlib.sha256(json.dumps(fingerprints).encode()).hexdigest(),
    }


def run_comparison():
    rows, provenance = [], {}
    for seed in SEEDS:
        d = build_design(seed)
        x, groups = d["x"], d["groups"]
        fit, cal, outer = groups < 60, (groups >= 60) & (groups < 90), groups >= 90
        provenance[str(seed)] = d["provenance"]
        shuffled = d["eog"][:, 1:3].copy()
        rng = np.random.default_rng(seed + 10000)
        for mask in (fit, cal, outer):
            shuffled[mask] = shuffled[mask][rng.permutation(mask.sum())]
        for regime in REGIMES:
            effect = (
                8
                * d[
                    "path_change" if regime == "best_path" else "diffusion_change"
                ].copy()
            )
            if regime == "environment_only":
                effect[:] = 0
            if regime == "unseen_diffusion_reversal":
                effect[outer] *= -1
            p = 1 / (
                1 + np.exp(-(0.8 * (x[:, 0] - 0.5) - 0.4 * (x[:, 1] - 0.5) + effect))
            )
            y = (d["uniforms"] < p).astype(int)
            base = _probability(_rf().fit(x[fit], y[fit]), x)
            oof = np.full(len(x), np.nan)
            for fold in range(3):
                train, valid = fit & (groups % 3 != fold), fit & (groups % 3 == fold)
                if set(groups[train]) & set(groups[valid]):
                    raise AssertionError("OOF graph leakage")
                oof[valid] = _probability(_rf().fit(x[train], y[train]), x[valid])
            candidates = {}
            for name, features in (
                ("eog_two", d["eog"][:, 1:3]),
                ("path_two", d["path"]),
                ("eog_ten", d["eog"]),
                ("permuted_two", shuffled),
            ):
                names = tuple(f"{name}_{i}" for i in range(features.shape[1]))
                model = fit_innovation_offset(
                    oof[fit], features[fit], y[fit], feature_names=names, ridge=0.1
                )
                candidates[name] = model.predict(base, features, feature_names=names)
            full = np.c_[x, d["eog"][:, 1:3]]
            candidates["concat_eog_two"] = _probability(
                _rf().fit(full[fit], y[fit]), full
            )
            decisions = {
                name: choose_on_calibration(y[cal], base[cal], value[cal])
                for name, value in candidates.items()
            }
            baseline_loss = _loss(y[outer], base[outer])
            losses = {
                name: _loss(y[outer], value[outer])
                for name, value in candidates.items()
            }
            rows.append(
                {
                    "seed": seed,
                    "regime": regime,
                    "baseline_loss": baseline_loss,
                    "always_on_loss": losses,
                    "promoted": decisions,
                    "selected_loss": {
                        name: loss if decisions[name] else baseline_loss
                        for name, loss in losses.items()
                    },
                }
            )
    summaries = {}
    for regime in REGIMES:
        subset = [r for r in rows if r["regime"] == regime]
        differences = [
            r["selected_loss"]["eog_two"] - r["selected_loss"]["path_two"]
            for r in subset
        ]
        summaries[regime] = {
            "methods": {
                name: {
                    "selected_delta": float(
                        np.mean(
                            [
                                r["selected_loss"][name] - r["baseline_loss"]
                                for r in subset
                            ]
                        )
                    ),
                    "always_on_delta": float(
                        np.mean(
                            [
                                r["always_on_loss"][name] - r["baseline_loss"]
                                for r in subset
                            ]
                        )
                    ),
                    "promotions": sum(r["promoted"][name] for r in subset),
                }
                for name in subset[0]["always_on_loss"]
            },
            "eog_minus_path_selected": {
                "mean": float(np.mean(differences)),
                "minimum": min(differences),
                "maximum": max(differences),
                "eog_wins": sum(v < 0 for v in differences),
                "ties": sum(v == 0 for v in differences),
            },
        }
    return {
        "schema": "eog.matched_information_offset.v1",
        "rows": rows,
        "summaries": summaries,
        "provenance": provenance,
        "uses_biological_response": False,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_comparison(), sort_keys=True, indent=2, allow_nan=False))
