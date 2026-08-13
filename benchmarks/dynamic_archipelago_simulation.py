"""Deterministic proof-of-estimand scenarios for EOG dynamic island reachability."""
from __future__ import annotations

import json

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    summarize_first_passage,
)


def edge(a: int, b: int, support: float) -> DynamicReachabilityEdge:
    return DynamicReachabilityEdge(a, b, geographic_support=support)


def evaluate() -> dict[str, object]:
    node_ids = ("source", "step1", "step2", "target")
    scenarios = {
        "open_chain": [edge(0, 1, 0.9), edge(1, 2, 0.9), edge(2, 3, 0.9)],
        "bottleneck": [edge(0, 1, 0.9), edge(1, 2, 0.05), edge(2, 3, 0.9)],
        "missing_intermediate": [edge(0, 1, 0.9), edge(2, 3, 0.9)],
    }
    rows = {}
    for name, edges in scenarios.items():
        operator = build_dynamic_transition_operator(node_ids, edges, loss_support=0.5)
        first_passage = summarize_first_passage(operator, ["source"], "target", max_steps=5)
        rows[name] = {
            "endpoint_environmental_support": 0.8,
            "endpoint_straight_line_distance_units": 3.0,
            "first_positive_step": first_passage.first_positive_step,
            "horizon_first_passage_support": first_passage.horizon_support,
            "operator_fingerprint": operator.fingerprint,
        }

    assert rows["open_chain"]["horizon_first_passage_support"] > rows["bottleneck"]["horizon_first_passage_support"] > 0.0
    assert rows["missing_intermediate"]["horizon_first_passage_support"] == 0.0
    assert rows["open_chain"]["first_positive_step"] == rows["bottleneck"]["first_positive_step"] == 3
    return {
        "claim": "matched endpoint viability/distance can hide different source-conditioned reachability",
        "scenarios": rows,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
