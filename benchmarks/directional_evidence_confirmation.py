"""Frozen synthetic confirmation for independent directional evidence discrimination."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.v2 import (
    DirectionalOrderConstraint,
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    combine_occurrence_and_directional_evidence,
    compare_occurrence_transition_rules,
    evaluate_directional_order_evidence,
)


CONFIRMATION_SEEDS = (4103, 4201, 4303, 4409, 4513, 4603, 4703, 4801)
NODE_IDS = ("A", "B", "C", "D")
OCCURRENCE_IDS = NODE_IDS
FIXED_SOURCE_IDS = ("A",)
MAX_STEPS = 3
LOSS_SUPPORT = 0.5
MINIMUM_SUPPORT_RATIO = 2.0
CONSTRAINTS = (
    DirectionalOrderConstraint("A", "B", "order_ab"),
    DirectionalOrderConstraint("B", "C", "order_bc"),
    DirectionalOrderConstraint("C", "D", "order_cd"),
)
CONTRACT_VERSION = "eog_v2_directional_evidence_confirmation_v1"


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _operators(seed: int):
    rng = np.random.default_rng(seed)

    forward = rng.uniform(0.40, 0.90, 3)
    true_edges = [
        DynamicReachabilityEdge(i, i + 1, geographic_support=float(forward[i]))
        for i in range(3)
    ]

    symmetric_support = float(rng.uniform(0.55, 0.90))
    permissive_edges = [
        DynamicReachabilityEdge(i, j, geographic_support=symmetric_support)
        for i in range(4)
        for j in range(4)
        if i != j
    ]

    reverse_edges = []
    for i in range(3):
        forward_support = float(rng.uniform(0.03, 0.08))
        reverse_support = float(rng.uniform(0.75, 0.95))
        reverse_edges.append(
            DynamicReachabilityEdge(i, i + 1, geographic_support=forward_support)
        )
        reverse_edges.append(
            DynamicReachabilityEdge(i + 1, i, geographic_support=reverse_support)
        )

    return {
        "true_chain": build_dynamic_transition_operator(
            NODE_IDS, true_edges, loss_support=LOSS_SUPPORT
        ),
        "permissive": build_dynamic_transition_operator(
            NODE_IDS, permissive_edges, loss_support=LOSS_SUPPORT
        ),
        "reverse_dominant": build_dynamic_transition_operator(
            NODE_IDS, reverse_edges, loss_support=LOSS_SUPPORT
        ),
    }


def _evaluate() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for seed in CONFIRMATION_SEEDS:
        operators = _operators(seed)
        occurrence = compare_occurrence_transition_rules(
            operators,
            OCCURRENCE_IDS,
            fixed_source_ids=FIXED_SOURCE_IDS,
            max_steps=MAX_STEPS,
        )
        occurrence_by_rule = {result.rule_id: result for result in occurrence.rule_results}
        directional = {
            rule_id: evaluate_directional_order_evidence(
                operator,
                CONSTRAINTS,
                rule_id=rule_id,
                max_steps=MAX_STEPS,
                minimum_support_ratio=MINIMUM_SUPPORT_RATIO,
            )
            for rule_id, operator in operators.items()
        }
        combined = combine_occurrence_and_directional_evidence(occurrence, directional)
        combined_by_rule = {row.rule_id: row.status for row in combined.rule_statuses}

        rows.append(
            {
                "seed": seed,
                "occurrence_coverage": {
                    rule_id: occurrence_by_rule[rule_id].coverage_fraction
                    for rule_id in sorted(occurrence_by_rule)
                },
                "true_supports_count": directional["true_chain"].supports_count,
                "permissive_ambiguous_count": directional["permissive"].ambiguous_count,
                "reverse_contradicts_count": directional["reverse_dominant"].contradicts_count,
                "combined_status": combined_by_rule,
                "combined_fingerprint": combined.fingerprint,
            }
        )

    gates = {
        "all_rules_occurrence_compatible": {
            "passed": all(
                all(value == 1.0 for value in row["occurrence_coverage"].values())
                for row in rows
            )
        },
        "true_direction_supported": {
            "passed": all(row["true_supports_count"] == len(CONSTRAINTS) for row in rows)
        },
        "permissive_direction_ambiguous": {
            "passed": all(row["permissive_ambiguous_count"] == len(CONSTRAINTS) for row in rows)
        },
        "reverse_direction_contradicted": {
            "passed": all(row["reverse_contradicts_count"] == len(CONSTRAINTS) for row in rows)
        },
        "combined_statuses_separate_rules": {
            "passed": all(
                row["combined_status"]
                == {
                    "permissive": "indistinguishable_directional_evidence",
                    "reverse_dominant": "contradicted_by_directional_evidence",
                    "true_chain": "compatible_with_occurrence_and_direction",
                }
                for row in rows
            )
        },
    }
    decision = "pass" if all(gate["passed"] for gate in gates.values()) else "fail"
    result = {
        "schema": CONTRACT_VERSION,
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "node_ids": list(NODE_IDS),
        "occurrence_ids": list(OCCURRENCE_IDS),
        "fixed_source_ids": list(FIXED_SOURCE_IDS),
        "max_steps": MAX_STEPS,
        "loss_support": LOSS_SUPPORT,
        "minimum_support_ratio": MINIMUM_SUPPORT_RATIO,
        "constraints": [
            {
                "evidence_id": item.evidence_id,
                "earlier_id": item.earlier_id,
                "later_id": item.later_id,
            }
            for item in CONSTRAINTS
        ],
        "gates": gates,
        "decision": decision,
        "rows": rows,
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = _evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "gates": result["gates"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
