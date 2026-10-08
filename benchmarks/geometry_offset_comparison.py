"""Independent geometry-derived development check; frozen design in docs."""

from __future__ import annotations

import hashlib
import json
import platform

import numpy as np
import scipy
import sklearn
from scipy.sparse.csgraph import shortest_path

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

SEEDS = (801, 809, 811, 821)
REGIMES = ("route_signal", "environment_only", "unseen_route_reversal")
NAMES = tuple(f"n{i}" for i in range(8))


def geometry_state(coordinates):
    coordinates = np.asarray(coordinates, dtype=float)
    if coordinates.shape != (8, 2) or not np.isfinite(coordinates).all():
        raise ValueError("geometry must be eight finite 2-D coordinates")
    distances = np.linalg.norm(coordinates[:, None] - coordinates[None, :], axis=2)
    support = np.zeros((2, 2, 8))
    fingerprints = []
    for world, radius in enumerate((0.45, 0.65)):
        edges = [
            DynamicReachabilityEdge(
                i, j, geographic_support=float(np.exp(-distances[i, j] / 0.4))
            )
            for i in range(8)
            for j in range(8)
            if i != j and distances[i, j] <= radius
        ]
        operator = build_dynamic_transition_operator(NAMES, edges, loss_support=0.3)
        fingerprints.append(operator.fingerprint)
        for source in range(2):
            for target in range(8):
                support[source, world, target] = summarize_first_passage(
                    operator,
                    (NAMES[source],),
                    NAMES[target],
                    max_steps=4,
                ).horizon_support
    summary = summarize_source_symmetric_support(
        support,
        source_ids=NAMES[:2],
        world_ids=("radius_045", "radius_065"),
        node_ids=NAMES,
        declared_world_count=2,
    )
    # Different graph and algorithm from EOG propagation; no response is involved.
    adjacency = np.where((distances <= 0.55) & (distances > 0), distances, np.inf)
    np.fill_diagonal(adjacency, 0)
    routes = np.minimum(
        np.min(shortest_path(adjacency, directed=False, indices=[0, 1]), axis=0), 4
    )
    return summary, routes, np.min(distances[:2], axis=0), fingerprints


def build_design(seed, graph_count=120):
    rng = np.random.default_rng(seed)
    conventional, innovations, absolute, route_change, groups, provenance = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for graph in range(graph_count):
        reference = rng.uniform(size=(8, 2))
        current = reference + rng.normal(0, 0.12, size=(8, 2))
        ref, ref_route, ref_direct, ref_fp = geometry_state(reference)
        cur, cur_route, cur_direct, cur_fp = geometry_state(current)
        innovation = summarize_contextual_innovation(ref, cur)
        conventional.extend(
            np.c_[current[2:], reference[2:], cur_direct[2:], ref_direct[2:]]
        )
        innovations.extend(innovation.feature_matrix[2:])
        absolute.extend(cur.feature_matrix[2:])
        route_change.extend((ref_route - cur_route)[2:])
        groups.extend([graph] * 6)
        provenance.append(
            {
                "graph": graph,
                "reference_operators": ref_fp,
                "current_operators": cur_fp,
                "innovation": innovation.fingerprint,
            }
        )
    return {
        "x": np.asarray(conventional),
        "z": np.asarray(innovations),
        "absolute": np.asarray(absolute),
        "route_change": np.asarray(route_change),
        "groups": np.asarray(groups),
        "uniforms": rng.uniform(size=len(groups)),
        "feature_names": innovation.feature_names,
        "provenance": provenance,
    }


def run_comparison():
    rows, provenance = [], {}
    for seed in SEEDS:
        design = build_design(seed)
        x, z, groups = design["x"], design["z"], design["groups"]
        fit, calibration, outer = (
            groups < 60,
            (groups >= 60) & (groups < 90),
            groups >= 90,
        )
        masks = (fit, calibration, outer)
        if any(
            set(groups[a]) & set(groups[b])
            for i, a in enumerate(masks)
            for b in masks[i + 1 :]
        ):
            raise AssertionError("graph leakage between partitions")
        provenance[str(seed)] = design["provenance"]
        shuffled = z.copy()
        rng = np.random.default_rng(seed + 10000)
        for mask in masks:
            shuffled[mask] = z[mask][rng.permutation(mask.sum())]
        for regime in REGIMES:
            effect = 2 * np.tanh(2 * design["route_change"])
            if regime == "environment_only":
                effect[:] = 0
            elif regime == "unseen_route_reversal":
                effect[outer] *= -1
            probability = 1 / (
                1 + np.exp(-(0.8 * (x[:, 0] - 0.5) - 0.4 * (x[:, 1] - 0.5) + effect))
            )
            y = (design["uniforms"] < probability).astype(int)
            baseline_model = _rf().fit(x[fit], y[fit])
            base = _probability(baseline_model, x)
            oof = np.full(len(x), np.nan)
            for fold in range(3):
                training = fit & (groups % 3 != fold)
                validation = fit & (groups % 3 == fold)
                if set(groups[training]) & set(groups[validation]):
                    raise AssertionError("OOF graph leakage")
                oof[validation] = _probability(
                    _rf().fit(x[training], y[training]), x[validation]
                )
            candidates = {}
            for name, features in (
                ("concat_absolute", design["absolute"]),
                ("concat_innovation", z),
            ):
                full = np.c_[x, features]
                candidates[name] = _probability(_rf().fit(full[fit], y[fit]), full)
            for name, features, names in (
                ("offset_all", z, design["feature_names"]),
                ("offset_mean_std", z[:, 1:3], design["feature_names"][1:3]),
                (
                    "offset_distance",
                    design["route_change"][:, None],
                    ("shortest_distance_change",),
                ),
                ("offset_permuted", shuffled, design["feature_names"]),
            ):
                model = fit_innovation_offset(
                    oof[fit], features[fit], y[fit], feature_names=names, ridge=0.1
                )
                candidates[name] = model.predict(base, features, feature_names=names)
            decisions = {
                name: choose_on_calibration(
                    y[calibration], base[calibration], p[calibration]
                )
                for name, p in candidates.items()
            }
            baseline_loss = _loss(y[outer], base[outer])
            scores = {name: _loss(y[outer], p[outer]) for name, p in candidates.items()}
            rows.append(
                {
                    "seed": seed,
                    "regime": regime,
                    "baseline_loss": baseline_loss,
                    "always_on_loss": scores,
                    "promoted": decisions,
                    "selected_loss": {
                        name: value if decisions[name] else baseline_loss
                        for name, value in scores.items()
                    },
                }
            )
    summaries = {
        regime: {
            name: {
                "selected_delta": float(
                    np.mean(
                        [
                            r["selected_loss"][name] - r["baseline_loss"]
                            for r in rows
                            if r["regime"] == regime
                        ]
                    )
                ),
                "always_on_delta": float(
                    np.mean(
                        [
                            r["always_on_loss"][name] - r["baseline_loss"]
                            for r in rows
                            if r["regime"] == regime
                        ]
                    )
                ),
                "promotions": sum(
                    r["promoted"][name] for r in rows if r["regime"] == regime
                ),
            }
            for name in rows[0]["always_on_loss"]
        }
        for regime in REGIMES
    }
    return {
        "schema": "eog.geometry_offset_development.v1",
        "rows": rows,
        "summaries": summaries,
        "geometry_provenance_sha256": {
            seed: hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
            for seed, items in provenance.items()
        },
        "graphs_per_seed": 120,
        "uses_biological_response": False,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
            "scipy": scipy.__version__,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_comparison(), sort_keys=True, indent=2, allow_nan=False))
