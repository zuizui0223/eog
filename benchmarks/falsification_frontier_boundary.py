#!/usr/bin/env python3
"""Finite falsification-frontier negative boundary for EOG relaxation inference.

Masten & Poirier define a falsification frontier as the set of smallest relaxations of a
baseline model that are not falsified.  This benchmark asks whether EOG's finite
multi-axis minimum-relaxation frontier is, in a discrete deterministic special case,
exactly the componentwise Pareto-minimal set of nonfalsified relaxation vectors.

The baseline world cannot realize observed endpoint C.  Five relaxed worlds can.  Four
are mutually non-dominated and one relaxes every axis more than necessary.

Exact equality is the expected result.  Therefore EOG must not claim novelty for the
generic mathematics of minimum-assumption relaxation, Pareto-minimal rescue vectors, or
a falsification frontier itself.  The remaining EOG question is ecological: how
occurrence-conditioned biogeographic worlds and relaxation axes are declared, how
analyst-choice worlds are kept separate, and how structural claims are tied to explicit
coverage certificates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    minimum_relaxation_frontier,
    reconstruct_compatible_worlds,
)


NODE_IDS = ("A", "C")
INDEX = {node_id: i for i, node_id in enumerate(NODE_IDS)}

RELAXATION_SPECS = {
    "baseline_fail": (0.0, 0.0, 0.0, False),
    "geo_rescue": (1.0, 0.0, 0.0, True),
    "env_rescue": (0.0, 1.0, 0.0, True),
    "barrier_rescue": (0.0, 0.0, 1.0, True),
    "mixed_rescue": (0.5, 0.5, 0.0, True),
    "dominated_rescue": (1.0, 1.0, 1.0, True),
}


def _operator(*, reaches_c: bool):
    edges = []
    if reaches_c:
        edges.append(
            DynamicReachabilityEdge(
                source=INDEX["A"],
                target=INDEX["C"],
                geographic_support=1.0,
            )
        )
    return build_dynamic_transition_operator(NODE_IDS, edges, loss_support=1.0)


def _worlds():
    worlds = []
    for world_id in sorted(RELAXATION_SPECS):
        geographic, environmental, barrier, reaches_c = RELAXATION_SPECS[world_id]
        worlds.append(
            FiniteWorld(
                world_id,
                _operator(reaches_c=reaches_c),
                ("A",),
                geographic_relaxation=geographic,
                environmental_relaxation=environmental,
                barrier_relaxation=barrier,
                analytical_variant="reference",
            )
        )
    return tuple(worlds)


def _dominates(left, right):
    left_vector = left[:3]
    right_vector = right[:3]
    no_worse = all(l <= r for l, r in zip(left_vector, right_vector, strict=True))
    strictly_better = any(l < r for l, r in zip(left_vector, right_vector, strict=True))
    return no_worse and strictly_better


def _generic_falsification_frontier():
    nonfalsified = {
        world_id: spec
        for world_id, spec in RELAXATION_SPECS.items()
        if spec[3]
    }
    frontier = []
    for world_id, spec in nonfalsified.items():
        if any(
            other_id != world_id and _dominates(other_spec, spec)
            for other_id, other_spec in nonfalsified.items()
        ):
            continue
        frontier.append(
            {
                "world_id": world_id,
                "geographic_relaxation": spec[0],
                "environmental_relaxation": spec[1],
                "barrier_relaxation": spec[2],
            }
        )
    frontier.sort(
        key=lambda row: (
            row["geographic_relaxation"],
            row["environmental_relaxation"],
            row["barrier_relaxation"],
            row["world_id"],
        )
    )
    return frontier


def _eog_frontier_rows(frontier):
    return [
        {
            "world_id": point.world_id,
            "geographic_relaxation": point.geographic_relaxation,
            "environmental_relaxation": point.environmental_relaxation,
            "barrier_relaxation": point.barrier_relaxation,
        }
        for point in frontier.points
    ]


def run_falsification_frontier_boundary():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(
        worlds,
        ("A", "C"),
        max_steps=1,
    )
    eog_frontier = minimum_relaxation_frontier(reconstruction, worlds)
    generic_frontier = _generic_falsification_frontier()
    eog_rows = _eog_frontier_rows(eog_frontier)

    generic_ids = {row["world_id"] for row in generic_frontier}
    eog_ids = {row["world_id"] for row in eog_rows}
    expected_ids = {
        "geo_rescue",
        "env_rescue",
        "barrier_rescue",
        "mixed_rescue",
    }

    return {
        "schema_version": 1,
        "literature_boundary": {
            "method": "falsification frontier / falsification adaptive set",
            "reference": "Masten & Poirier 2021, Econometrica 89:1449-1469",
            "doi": "10.3982/ECTA17969",
            "prior_art_boundary": (
                "smallest relaxations of a falsified baseline model that are not falsified"
            ),
        },
        "finite_special_case_boundary": (
            "discrete deterministic relaxation vectors with componentwise Pareto ordering; "
            "not the linear-IV identified-set theory of the source paper"
        ),
        "baseline": {
            "world_id": "baseline_fail",
            "relaxation": [0.0, 0.0, 0.0],
            "compatible_with_A_C": "baseline_fail" in reconstruction.compatible_world_ids,
        },
        "generic_falsification_frontier": generic_frontier,
        "eog_minimum_relaxation_frontier": eog_rows,
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "negative_boundary": {
            "frontier_world_ids_match": generic_ids == eog_ids == expected_ids,
            "frontier_vectors_match": generic_frontier == eog_rows,
            "dominated_world_removed_by_both": (
                "dominated_rescue" not in generic_ids and "dominated_rescue" not in eog_ids
            ),
            "do_not_claim_minimum_relaxation_frontier_math_as_unique": True,
            "do_not_claim_pareto_rescue_set_as_unique": True,
            "remaining_eog_question": (
                "how ecological and analyst-choice biogeographic worlds and relaxation axes are "
                "constructed from occurrence/reachability constraints, and how the resulting "
                "world-indexed structural claims are certified and interpreted"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_falsification_frontier_boundary()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
