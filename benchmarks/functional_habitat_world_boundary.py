#!/usr/bin/env python3
"""Functional-habitat prior-art boundary and analytical-world uncertainty test.

Van Moorter et al. (2023) formalized functional habitat by combining habitat quality in
environmental space with geographic/topological connectivity. Their landscape matrix
has elements m_st = q_s * q_t * k_st, where q is habitat quality and k is pairwise
connectivity/proximity. EOG therefore must not claim novelty merely for combining
suitability with accessibility or for down-ranking isolated but locally suitable
habitat.

This benchmark constructs two equally admissible analytical representations with the
same local habitat qualities and the same observed A->R relation:

- connected_representation also connects source A to candidate C;
- isolated_representation leaves C locally suitable but inaccessible from A.

Functional habitat is computed correctly in each representation. EOG's additional
question is not how to compute functional habitat in one chosen landscape, but whether
alternative analytical landscapes should be averaged/collapsed before inference. The
finite-world layer retains C as contingent across the two declared worlds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    build_world_flow_set,
    reconstruct_compatible_worlds,
)


NODE_IDS = ("A", "R", "C")
INDEX = {node_id: i for i, node_id in enumerate(NODE_IDS)}
QUALITY = {node_id: 1.0 for node_id in NODE_IDS}


def _proximity(*, c_connected: bool) -> np.ndarray:
    matrix = np.eye(len(NODE_IDS), dtype=float)
    # A-R is common to both analytical representations and supports the frozen
    # occurrence configuration A,R.
    matrix[INDEX["A"], INDEX["R"]] = 1.0
    matrix[INDEX["R"], INDEX["A"]] = 1.0
    if c_connected:
        matrix[INDEX["A"], INDEX["C"]] = 1.0
        matrix[INDEX["C"], INDEX["A"]] = 1.0
    return matrix


def _functional_habitat(proximity: np.ndarray):
    q = np.asarray([QUALITY[node_id] for node_id in NODE_IDS], dtype=float)
    landscape_matrix = q[:, None] * q[None, :] * proximity
    node_scores = np.sum(landscape_matrix, axis=0)
    return landscape_matrix, node_scores


def _operator(*, c_connected: bool):
    declared = [
        DynamicReachabilityEdge(
            source=INDEX["A"],
            target=INDEX["R"],
            geographic_support=1.0,
        )
    ]
    if c_connected:
        declared.append(
            DynamicReachabilityEdge(
                source=INDEX["A"],
                target=INDEX["C"],
                geographic_support=1.0,
            )
        )
    return build_dynamic_transition_operator(NODE_IDS, declared, loss_support=1.0)


def _world(world_id: str, *, c_connected: bool):
    return FiniteWorld(
        world_id,
        _operator(c_connected=c_connected),
        ("A",),
        analytical_variant=world_id,
    )


def run_functional_habitat_world_boundary():
    connected_k = _proximity(c_connected=True)
    isolated_k = _proximity(c_connected=False)
    connected_m, connected_scores = _functional_habitat(connected_k)
    isolated_m, isolated_scores = _functional_habitat(isolated_k)
    mean_scores = 0.5 * (connected_scores + isolated_scores)

    connected_world = _world("connected_representation", c_connected=True)
    isolated_world = _world("isolated_representation", c_connected=False)
    worlds = (connected_world, isolated_world)
    reconstruction = reconstruct_compatible_worlds(
        worlds,
        ("A", "R"),
        max_steps=1,
    )
    flow_set = build_world_flow_set(reconstruction, worlds)

    score_by_world = {
        "connected_representation": {
            node_id: float(connected_scores[INDEX[node_id]]) for node_id in NODE_IDS
        },
        "isolated_representation": {
            node_id: float(isolated_scores[INDEX[node_id]]) for node_id in NODE_IDS
        },
    }
    c_world_scores = {
        score_by_world[world_id]["C"] for world_id in score_by_world
    }
    mean_c = float(mean_scores[INDEX["C"]])

    return {
        "schema_version": 1,
        "literature_boundary": {
            "method": "functional habitat: suitability in E-space plus accessibility in G/T-space",
            "reference": "Van Moorter et al. 2023, Ecology 104:e4105",
            "doi": "10.1002/ecy.4105",
            "landscape_matrix_definition": "m_st = q_s * q_t * k_st",
        },
        "local_quality": QUALITY,
        "functional_habitat": {
            "connected_proximity": connected_k.tolist(),
            "isolated_proximity": isolated_k.tolist(),
            "connected_landscape_matrix": connected_m.tolist(),
            "isolated_landscape_matrix": isolated_m.tolist(),
            "scores_by_world": score_by_world,
            "mean_scores_if_world_identity_is_collapsed": {
                node_id: float(mean_scores[INDEX[node_id]]) for node_id in NODE_IDS
            },
            "C_same_local_quality_but_different_functionality": bool(
                QUALITY["C"] == 1.0
                and connected_scores[INDEX["C"]] > isolated_scores[INDEX["C"]]
            ),
        },
        "eog_world_set": {
            "compatible_world_ids": list(reconstruction.compatible_world_ids),
            "identifiable": reconstruction.identifiable,
            "reachable_in_all_ids": list(flow_set.reachable_in_all_ids),
            "contingent_ids": list(flow_set.contingent_ids),
            "robustly_unreachable_ids": list(flow_set.robustly_unreachable_ids),
            "C_is_contingent": "C" in flow_set.contingent_ids,
        },
        "world_aggregation": {
            "C_functional_scores_in_declared_worlds": sorted(c_world_scores),
            "C_mean_score_after_collapse": mean_c,
            "mean_score_occurs_in_no_declared_world": mean_c not in c_world_scores,
        },
        "negative_boundary": {
            "suitable_plus_accessible_is_prior_art": True,
            "E_G_T_space_integration_is_not_unique_to_eog": True,
            "isolated_suitable_habitat_downranking_is_not_unique_to_eog": True,
            "remaining_eog_question": (
                "how to retain mutually alternative ecological/analytical connectivity worlds, "
                "their underidentification, inverse occurrence constraints, Pareto rescues, and "
                "finite-universe certificates without collapsing them into one chosen or averaged landscape"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_functional_habitat_world_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
