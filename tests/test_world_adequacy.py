from __future__ import annotations

import inspect

import numpy as np
import pytest

from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)


def _symmetric(n: int, edges: list[tuple[int, int]]) -> np.ndarray:
    adjacency = np.zeros((n, n), dtype=bool)
    for i, j in edges:
        adjacency[i, j] = True
        adjacency[j, i] = True
    return adjacency


def test_response_blind_audit_reports_fragmentation_and_horizon_coverage():
    nodes = ("a", "b", "c", "d")
    fragmented = _symmetric(4, [(0, 1)])
    spanning = _symmetric(4, [(0, 1), (1, 2), (2, 3)])

    audit = audit_world_universe_structure(
        nodes,
        {"fragmented": fragmented, "spanning": spanning},
        horizon=1,
    )
    by_id = {row.world_id: row for row in audit.world_audits}

    frag = by_id["fragmented"]
    assert frag.weak_component_count == 3
    assert frag.largest_weak_component_size == 2
    assert frag.largest_weak_component_fraction == pytest.approx(0.5)
    assert frag.isolated_node_count == 2
    assert frag.isolated_node_fraction == pytest.approx(0.5)
    assert frag.median_horizon_reachable_fraction == pytest.approx(0.375)

    span = by_id["spanning"]
    assert span.weak_component_count == 1
    assert span.largest_weak_component_fraction == pytest.approx(1.0)
    assert span.isolated_node_count == 0
    assert span.median_horizon_reachable_fraction == pytest.approx(0.625)
    assert audit.most_spanning_world_id == "spanning"


def test_prospective_declaration_can_stop_universe_without_species_responses():
    nodes = ("a", "b", "c", "d")
    fragmented = _symmetric(4, [(0, 1)])
    spanning = _symmetric(4, [(0, 1), (1, 2), (2, 3)])
    audit = audit_world_universe_structure(
        nodes,
        {"fragmented": fragmented, "spanning": spanning},
        horizon=1,
    )
    declaration = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.75,
        max_isolated_node_fraction=0.25,
        min_median_horizon_reachable_fraction=0.5,
        require_at_least_one_world_pass=True,
    )
    gate = apply_structural_adequacy_gate(audit, declaration)

    assert gate.passed is True
    assert gate.passing_world_ids == ("spanning",)
    by_id = {row.world_id: row for row in gate.world_results}
    assert set(by_id["fragmented"].failed_criteria) == {
        "min_largest_weak_component_fraction",
        "max_isolated_node_fraction",
        "min_median_horizon_reachable_fraction",
    }
    assert by_id["spanning"].passed is True


def test_no_universal_threshold_is_hidden_in_the_api():
    with pytest.raises(ValueError, match="at least one structural adequacy criterion"):
        StructuralAdequacyDeclaration()


def test_structural_audit_api_cannot_accept_response_vectors():
    signature = inspect.signature(audit_world_universe_structure)
    assert "response" not in signature.parameters
    assert "occurrence" not in signature.parameters
    assert "species" not in signature.parameters

    with pytest.raises(TypeError):
        audit_world_universe_structure(
            ("a", "b"),
            {"w": _symmetric(2, [(0, 1)])},
            horizon=1,
            response=np.array([1, 0]),  # type: ignore[call-arg]
        )


def test_directed_horizon_reachability_respects_edge_direction():
    adjacency = np.zeros((3, 3), dtype=bool)
    adjacency[0, 1] = True
    adjacency[1, 2] = True
    audit = audit_world_universe_structure(("a", "b", "c"), {"w": adjacency}, horizon=1)
    row = audit.world_audits[0]

    assert row.weak_component_count == 1
    assert row.largest_weak_component_fraction == pytest.approx(1.0)
    # one-step directed reachable fractions are 2/3, 2/3, 1/3
    assert row.median_horizon_reachable_fraction == pytest.approx(2 / 3)
