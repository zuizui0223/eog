"""Frozen structural confirmation for occurrence-conditioned transition-rule constraints."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.v2 import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    compare_occurrence_transition_rules,
    evaluate_occurrence_rule_compatibility,
)


CONFIRMATION_SEEDS = (3109, 3203, 3301, 3407, 3511, 3607, 3701, 3803)
NODE_IDS = ("A", "B", "C", "D")
OCCURRENCE_IDS = NODE_IDS
FIXED_SOURCE_IDS = ("A",)
MAX_STEPS = 3
LOSS_SUPPORT = 0.5
CONTRACT_VERSION = "eog_v2_occurrence_rule_compatibility_confirmation_v1"


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
    chain_support = rng.uniform(0.35, 0.90, 3)
    chain_edges = [
        DynamicReachabilityEdge(index, index + 1, geographic_support=float(chain_support[index]))
        for index in range(3)
    ]
    broken_edges = chain_edges[:2]
    permissive_support = float(rng.uniform(0.70, 0.95))
    permissive_edges = [
        DynamicReachabilityEdge(i, j, geographic_support=permissive_support)
        for i in range(4)
        for j in range(4)
        if i != j
    ]
    return {
        "true_chain": build_dynamic_transition_operator(
            NODE_IDS, chain_edges, loss_support=LOSS_SUPPORT
        ),
        "broken_chain": build_dynamic_transition_operator(
            NODE_IDS, broken_edges, loss_support=LOSS_SUPPORT
        ),
        "permissive": build_dynamic_transition_operator(
            NODE_IDS, permissive_edges, loss_support=LOSS_SUPPORT
        ),
    }


def _evaluate() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for seed in CONFIRMATION_SEEDS:
        operators = _operators(seed)
        fixed = compare_occurrence_transition_rules(
            operators,
            OCCURRENCE_IDS,
            fixed_source_ids=FIXED_SOURCE_IDS,
            max_steps=MAX_STEPS,
        )
        fixed_by_rule = {result.rule_id: result for result in fixed.rule_results}
        peer = evaluate_occurrence_rule_compatibility(
            operators["true_chain"],
            OCCURRENCE_IDS,
            rule_id="true_chain_peer",
            max_steps=MAX_STEPS,
        )
        rows.append(
            {
                "seed": seed,
                "true_fixed_coverage": fixed_by_rule["true_chain"].coverage_fraction,
                "broken_fixed_coverage": fixed_by_rule["broken_chain"].coverage_fraction,
                "permissive_fixed_coverage": fixed_by_rule["permissive"].coverage_fraction,
                "true_active_edge_fraction": fixed_by_rule["true_chain"].operator_active_edge_fraction,
                "permissive_active_edge_fraction": fixed_by_rule["permissive"].operator_active_edge_fraction,
                "true_mean_outgoing_mass": fixed_by_rule["true_chain"].operator_mean_outgoing_mass,
                "permissive_mean_outgoing_mass": fixed_by_rule["permissive"].operator_mean_outgoing_mass,
                "peer_true_coverage": peer.coverage_fraction,
                "peer_unsupported": list(peer.unsupported_occurrence_ids),
                "comparison_fingerprint": fixed.fingerprint,
            }
        )

    gates = {
        "true_fixed_supported": {
            "passed": all(row["true_fixed_coverage"] == 1.0 for row in rows),
            "minimum_coverage": min(row["true_fixed_coverage"] for row in rows),
        },
        "broken_rule_constrained": {
            "passed": all(row["broken_fixed_coverage"] < 1.0 for row in rows),
            "maximum_coverage": max(row["broken_fixed_coverage"] for row in rows),
        },
        "permissive_rule_not_uniquely_identified": {
            "passed": all(
                row["permissive_fixed_coverage"] == 1.0
                and row["permissive_active_edge_fraction"] > row["true_active_edge_fraction"]
                and row["permissive_mean_outgoing_mass"] > row["true_mean_outgoing_mass"]
                for row in rows
            ),
            "minimum_permissive_coverage": min(row["permissive_fixed_coverage"] for row in rows),
            "minimum_edge_fraction_advantage": min(
                row["permissive_active_edge_fraction"] - row["true_active_edge_fraction"]
                for row in rows
            ),
        },
        "peer_source_not_directional_history": {
            "passed": all(
                row["peer_true_coverage"] < 1.0 and row["peer_unsupported"] == ["A"]
                for row in rows
            ),
            "maximum_peer_coverage": max(row["peer_true_coverage"] for row in rows),
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
    print(json.dumps({"decision": result["decision"], "gates": result["gates"], "fingerprint": result["fingerprint"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
