#!/usr/bin/env python3
"""Known-truth comparison of ensemble consensus and universal finite-world certificates.

Consensus frequency and EOG robustness are deliberately different estimands. A state
supported by 99 of 100 admissible worlds has very high ensemble agreement, but it is
not invariant across the declared universe. Conversely, a state unreachable in every
world supports both a zero consensus frequency and a finite-universe exclusion
certificate.

This benchmark treats neither summary as wrong. It verifies that EOG does not silently
turn majority/consensus agreement into a universal robustness claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    build_world_flow_set,
    reconstruct_compatible_worlds,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    declared = [
        DynamicReachabilityEdge(
            source=index[source],
            target=index[target],
            geographic_support=float(support),
        )
        for source, target, support in edges
    ]
    return build_dynamic_transition_operator(node_ids, declared, loss_support=1.0)


def _world(world_id, *, target_reachable):
    # A and S are fixed observed sources in every world.  The second source is not a
    # rescue device: it satisfies the already-frozen FiniteWorld reconstruction contract
    # that occurrence configurations contain at least two unique observed nodes.
    nodes = ("A", "S", "T", "E")
    edges = (("A", "T", 1.0),) if target_reachable else ()
    return FiniteWorld(world_id, _operator(nodes, edges), ("A", "S"))


def _flow_set(worlds):
    reconstruction = reconstruct_compatible_worlds(worlds, ("A", "S"), max_steps=1)
    return reconstruction, build_world_flow_set(reconstruction, worlds)


def _reachability_frequency(flow_set, node_id):
    envelope = next(row for row in flow_set.node_envelopes if row.node_id == node_id)
    positive = sum(1 for _world_id, support in envelope.support_by_world if support > 0.0)
    return positive / len(envelope.support_by_world)


def run_consensus_certificate_comparator():
    supporting = tuple(_world(f"support_{index:02d}", target_reachable=True) for index in range(99))
    excluding = _world("exclude_target", target_reachable=False)

    base_reconstruction, base_flow = _flow_set(supporting)
    expanded_worlds = supporting + (excluding,)
    expanded_reconstruction, expanded_flow = _flow_set(expanded_worlds)

    target_frequency = _reachability_frequency(expanded_flow, "T")
    excluded_frequency = _reachability_frequency(expanded_flow, "E")
    target_base_robust = "T" in base_flow.reachable_in_all_ids
    target_expanded_robust = "T" in expanded_flow.reachable_in_all_ids
    target_expanded_contingent = "T" in expanded_flow.contingent_ids
    excluded_robust = "E" in expanded_flow.robustly_unreachable_ids

    consensus_threshold = 0.95
    consensus_supported = target_frequency >= consensus_threshold

    return {
        "schema_version": 1,
        "claim_boundary": (
            "known-truth consensus-frequency vs universal finite-world certificate comparison; "
            "neither estimand is treated as incorrect"
        ),
        "universe": {
            "base_world_count": len(supporting),
            "expanded_world_count": len(expanded_worlds),
            "added_world_id": excluding.world_id,
            "fixed_observed_sources": ["A", "S"],
            "all_worlds_compatible_with_source_observations": (
                len(expanded_reconstruction.compatible_world_ids) == len(expanded_worlds)
            ),
        },
        "target_T": {
            "reachability_frequency": target_frequency,
            "consensus_threshold": consensus_threshold,
            "consensus_supported": consensus_supported,
            "robust_in_99_supporting_worlds": target_base_robust,
            "robust_after_adding_one_excluding_world": target_expanded_robust,
            "contingent_after_expansion": target_expanded_contingent,
        },
        "always_excluded_E": {
            "reachability_frequency": excluded_frequency,
            "robustly_unreachable": excluded_robust,
        },
        "monotonicity": {
            "base_reachable_in_all_ids": list(base_flow.reachable_in_all_ids),
            "expanded_reachable_in_all_ids": list(expanded_flow.reachable_in_all_ids),
            "base_contingent_ids": list(base_flow.contingent_ids),
            "expanded_contingent_ids": list(expanded_flow.contingent_ids),
            "base_robustly_unreachable_ids": list(base_flow.robustly_unreachable_ids),
            "expanded_robustly_unreachable_ids": list(expanded_flow.robustly_unreachable_ids),
            "adding_world_does_not_create_new_robust_target_claim": (
                target_base_robust and not target_expanded_robust
            ),
            "possible_target_is_not_relabelled_impossible": (
                "T" not in expanded_flow.robustly_unreachable_ids
            ),
        },
        "separation_checks": {
            "high_consensus_is_not_universal_robustness": (
                consensus_supported
                and target_frequency == 0.99
                and target_expanded_contingent
                and not target_expanded_robust
            ),
            "unanimous_exclusion_supports_finite_certificate": (
                excluded_frequency == 0.0 and excluded_robust
            ),
            "consensus_and_certificate_answer_different_questions": (
                consensus_supported and target_expanded_contingent
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_consensus_certificate_comparator()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
