"""Fixed synthetic boundary checks; qualitative discrimination is not inference."""

from __future__ import annotations

import json

from eog.v2 import (
    DirectionalOrderConstraint,
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    combine_occurrence_and_directional_evidence,
    compare_occurrence_transition_rules,
    evaluate_directional_order_evidence,
)


def run_benchmark():
    # A->B makes the occurrence evidence identical across candidates. C/X is an
    # independent declared order, not an order inferred from these occurrences.
    edge_sets = {
        "forward": ((2, 3, 1.0),),
        "forward_weak": ((2, 3, 0.25),),
        "reverse": ((3, 2, 1.0),),
        "symmetric": ((2, 3, 1.0), (3, 2, 1.0)),
        "no_direction": (),
    }
    operators = {
        name: build_dynamic_transition_operator(
            ("A", "B", "C", "X"),
            tuple(
                DynamicReachabilityEdge(i, j, geographic_support=weight)
                for i, j, weight in ((0, 1, 1.0),) + edges
            ),
            loss_support=1.0,
        )
        for name, edges in edge_sets.items()
    }
    universes = {
        "opposed": ("forward", "reverse"),
        "weight_twin": ("forward", "reverse", "forward_weak"),
        "ambiguous_extension": ("forward", "reverse", "symmetric"),
        "unresolved_extension": ("forward", "reverse", "no_direction"),
        "all": tuple(operators),
    }
    supported = "compatible_with_occurrence_and_direction"
    contradicted = "contradicted_by_directional_evidence"
    rows = []
    for orientation, endpoints in (("forward", ("C", "X")), ("reverse", ("X", "C"))):
        # One-step, one-way and equal-weight pairs have these analytic statuses.
        oracle = {
            "forward": supported if orientation == "forward" else contradicted,
            "forward_weak": supported if orientation == "forward" else contradicted,
            "reverse": supported if orientation == "reverse" else contradicted,
            "symmetric": "indistinguishable_directional_evidence",
            "no_direction": "unresolved",
        }
        baseline = None
        for case, names in universes.items():
            occurrence = compare_occurrence_transition_rules(
                {name: operators[name] for name in names},
                ("A", "B"),
                fixed_source_ids=("A",),
                max_steps=1,
            )
            if any(r.coverage_fraction != 1.0 for r in occurrence.rule_results):
                raise AssertionError("occurrence equivalence failed")
            directional = {
                name: evaluate_directional_order_evidence(
                    operators[name],
                    (DirectionalOrderConstraint(*endpoints, "independent_order"),),
                    rule_id=name,
                    max_steps=1,
                    minimum_support_ratio=2.0,
                )
                for name in names
            }
            combined = combine_occurrence_and_directional_evidence(
                occurrence, directional
            )
            statuses = {r.rule_id: r.status for r in combined.rule_statuses}
            if statuses != {name: oracle[name] for name in names}:
                raise AssertionError((case, orientation, statuses))
            # Ambiguous/unresolved are NOT contradictions. This is a reporting
            # boundary, not a new exact-world admissibility rule or winner API.
            not_contradicted = sorted(
                n for n, s in statuses.items() if s != contradicted
            )
            if baseline is None:
                baseline = set(not_contradicted)
            elif not baseline <= set(not_contradicted):
                raise AssertionError("universe expansion removed an existing candidate")
            rows.append(
                {
                    "case": case,
                    "declared_order": list(endpoints),
                    "statuses": statuses,
                    "not_contradicted": not_contradicted,
                    "supported": sorted(
                        n for n, s in statuses.items() if s == supported
                    ),
                    "comparison_fingerprint": combined.fingerprint,
                }
            )
    return {
        "schema": "eog.directional_identifiability_boundary.v1",
        "claim_ceiling": "synthetic qualitative status separation only; no truth identification",
        "max_steps": 1,
        "minimum_support_ratio": 2.0,
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), sort_keys=True, indent=2))
