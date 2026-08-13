import numpy as np
import pytest

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
)
from eog.reachability_visualization import build_dynamic_reachability_visualization_payload


def test_graph_native_payload_preserves_mass_flux_and_static_layers():
    operator = build_dynamic_transition_operator(
        ("source", "bridge", "target"),
        [
            DynamicReachabilityEdge(0, 1, geographic_support=0.8),
            DynamicReachabilityEdge(1, 2, geographic_support=0.6),
        ],
        loss_support=0.5,
    )
    result = propagate_dynamic_reachability(operator, ["source"], max_steps=3)
    payload = build_dynamic_reachability_visualization_payload(
        operator,
        result,
        positions={"source": (0, 0), "bridge": (1, 0), "target": (2, 0)},
        viability={"source": 0.7, "bridge": 0.8, "target": 0.9},
        persistence={"target": 0.6},
    )
    assert payload["schema"] == "eog_dynamic_reachability_graph_v1"
    assert len(payload["frames"]) == 4
    assert payload["frames"][0]["total_mass"] == pytest.approx(1.0)
    assert payload["frames"][0]["nodes"][0]["reachability_mass"] == pytest.approx(1.0)
    first_flux = sum(edge["flux"] for edge in payload["frames"][0]["edges"])
    assert first_flux == pytest.approx(np.sum(operator.transition[0]))
    target = next(node for node in payload["nodes"] if node["id"] == "target")
    assert target["viability"] == pytest.approx(0.9)
    assert target["persistence"] == pytest.approx(0.6)
    assert target["first_arrival_step"] == 2
    assert len(payload["fingerprint"]) == 64


def test_payload_is_deterministic_and_does_not_require_positions():
    operator = build_dynamic_transition_operator(
        ("a", "b"),
        [DynamicReachabilityEdge(0, 1, geographic_support=0.8)],
        loss_support=0.5,
    )
    result = propagate_dynamic_reachability(operator, ["a"], max_steps=2)
    first = build_dynamic_reachability_visualization_payload(operator, result)
    second = build_dynamic_reachability_visualization_payload(operator, result)
    assert first == second
    assert all(node["position"] is None for node in first["nodes"])


def test_payload_rejects_mismatched_operator():
    operator = build_dynamic_transition_operator(
        ("a", "b"),
        [DynamicReachabilityEdge(0, 1, geographic_support=0.8)],
        loss_support=0.5,
    )
    other = build_dynamic_transition_operator(
        ("a", "b"),
        [DynamicReachabilityEdge(0, 1, geographic_support=0.4)],
        loss_support=0.5,
    )
    result = propagate_dynamic_reachability(operator, ["a"], max_steps=2)
    with pytest.raises(ValueError, match="fingerprints"):
        build_dynamic_reachability_visualization_payload(other, result)
