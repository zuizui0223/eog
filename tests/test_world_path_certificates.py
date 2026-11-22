"""Tests of exact finite-world reachability/path quantifier separation."""
from __future__ import annotations

import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    audit_world_path_quantifiers,
    build_dynamic_transition_operator,
    reconstruct_compatible_worlds,
    summarize_occurrence_relations,
)

NODES = ("A", "B", "C", "D", "X")
INDEX = {name: i for i, name in enumerate(NODES)}


def _world(name, edges, *, sources=("A",), weights=None):
    operator = build_dynamic_transition_operator(
        NODES,
        [
            DynamicReachabilityEdge(
                source=INDEX[left],
                target=INDEX[right],
                geographic_support=float(support),
            )
            for left, right, support in edges
        ],
        loss_support=1.0,
    )
    return FiniteWorld(name, operator, sources, source_weights=weights)


def _edges(*pairs, support=1.0):
    return tuple((a, b, support) for a, b in pairs)


def _audit(worlds, *, observations=("A", "C"), steps=3, floor=0.0, target="C"):
    frozen = reconstruct_compatible_worlds(
        worlds, observations, max_steps=steps
    )
    return frozen, audit_world_path_quantifiers(
        frozen, worlds, source_id="A", target_id=target,
        edge_support_floor=floor,
    )


def test_universally_reachable_target_may_have_no_common_corridor():
    via_b = _world("via_b", _edges(("A", "B"), ("B", "C")))
    via_d = _world("via_d", _edges(("A", "D"), ("D", "C")))
    frozen, audit = _audit((via_b, via_d))
    relations = summarize_occurrence_relations(frozen, (via_b, via_d))
    assert relations.relation("A", "C").reachability_status == "reachable_in_all"
    assert audit.every_world_reachable
    assert audit.common_path is None
    assert not audit.common_path_exists
    assert dict(audit.shortest_path_by_world) == {
        "via_b": ("A", "B", "C"),
        "via_d": ("A", "D", "C"),
    }
    assert audit.necessary_in_every_world == ()
    assert audit.necessary_in_some_reachable_worlds == ("B", "D")


def test_shared_corridor_does_not_prove_globally_unavoidable_stepping_stone():
    narrow = _world("narrow", _edges(("A", "B"), ("B", "C")))
    wide = _world(
        "wide", _edges(("A", "B"), ("B", "C"), ("A", "D"), ("D", "C"))
    )
    _, audit = _audit((narrow, wide))
    assert audit.every_world_reachable
    assert audit.common_path_exists
    assert audit.common_path == ("A", "B", "C")
    assert dict(audit.mandatory_intermediates_by_world) == {
        "narrow": ("B",), "wide": ()
    }
    assert audit.necessary_in_every_world == ()


def test_common_mandatory_node_can_exist_without_a_shared_entire_route():
    via_b = _world(
        "via_b", _edges(("A", "B"), ("B", "X"), ("X", "C"))
    )
    via_d = _world(
        "via_d", _edges(("A", "D"), ("D", "X"), ("X", "C"))
    )
    _, audit = _audit((via_b, via_d))
    assert audit.every_world_reachable
    assert not audit.common_path_exists
    assert audit.necessary_in_every_world == ("X",)
    assert audit.necessary_in_some_reachable_worlds == ("B", "D", "X")
    assert audit.shared_active_edges == (("X", "C"),)


def test_same_route_across_all_worlds_can_have_truly_necessary_middle():
    a = _world("a", _edges(("A", "B"), ("B", "C")))
    b = _world("b", _edges(("A", "B"), ("B", "C")))
    _, audit = _audit((a, b))
    assert audit.every_world_reachable
    assert audit.common_path == ("A", "B", "C")
    assert audit.necessary_in_every_world == ("B",)
    assert audit.coverage_certificate == (
        "exhaustive_declared_compatible_world_structural_paths"
    )


def test_world_growth_can_erase_a_common_route_while_preserving_all_world_reachability():
    b = _world("b", _edges(("A", "B"), ("B", "C")))
    d = _world("d", _edges(("A", "D"), ("D", "C")))
    _, before = _audit((b,))
    _, after = _audit((b, d))
    assert before.every_world_reachable and after.every_world_reachable
    assert before.common_path_exists and not after.common_path_exists
    assert before.necessary_in_every_world == ("B",)
    assert after.necessary_in_every_world == ()


def test_a_world_without_target_access_withholds_universal_and_necessity_claims():
    b = _world("b", _edges(("A", "D"), ("A", "B"), ("B", "C")))
    absent = _world("absent", _edges(("A", "D")))
    _, audit = _audit((b, absent), observations=("A", "D"))
    assert audit.any_world_reachable
    assert not audit.every_world_reachable
    assert not audit.common_path_exists
    assert audit.necessary_in_every_world == ()
    assert dict(audit.shortest_path_by_world)["absent"] is None
    assert audit.necessary_in_some_reachable_worlds == ("B",)


def test_raw_edge_floor_is_separate_from_first_passage_mass_threshold():
    low = _world("low", _edges(("A", "B"), ("B", "C"), support=0.05))
    frozen, permissive = _audit((low,), floor=0.0)
    strict = audit_world_path_quantifiers(
        frozen, (low,), source_id="A", target_id="C",
        edge_support_floor=0.1,
    )
    assert permissive.every_world_reachable
    assert not strict.any_world_reachable
    assert permissive.fingerprint != strict.fingerprint


def test_world_input_order_is_fingerprint_invariant():
    b = _world("b", _edges(("A", "B"), ("B", "C")))
    d = _world("d", _edges(("A", "D"), ("D", "C")))
    frozen, expected = _audit((b, d))
    reverse = audit_world_path_quantifiers(
        frozen, (d, b), source_id="A", target_id="C"
    )
    assert expected == reverse


def test_world_definition_changes_fail_closed():
    b = _world("b", _edges(("A", "B"), ("B", "C")))
    d = _world("d", _edges(("A", "D"), ("D", "C")))
    frozen, _ = _audit((b, d))
    replaced = _world("b", _edges(("A", "C")))
    with pytest.raises(ValueError, match="fingerprints"):
        audit_world_path_quantifiers(
            frozen, (replaced, d), source_id="A", target_id="C"
        )


def test_missing_source_or_nondeclared_target_or_bad_floor_is_rejected():
    b = _world("b", _edges(("A", "B"), ("B", "C")))
    frozen, _ = _audit((b,))
    with pytest.raises(ValueError, match="selected source"):
        audit_world_path_quantifiers(
            frozen, (b,), source_id="D", target_id="C"
        )
    with pytest.raises(ValueError, match="distinct declared"):
        audit_world_path_quantifiers(
            frozen, (b,), source_id="A", target_id="missing"
        )
    for invalid_floor in (-0.1, 1.0, float("nan")):
        with pytest.raises(ValueError, match="edge_support_floor"):
            audit_world_path_quantifiers(
                frozen, (b,), source_id="A", target_id="C",
                edge_support_floor=invalid_floor,
            )


def test_zero_weight_selected_source_cannot_certify_a_path():
    w = _world(
        "w", _edges(("A", "D"), ("D", "C")),
        sources=("A", "D"), weights=(0.0, 1.0),
    )
    # Fixed-source reconstruction requires a separate non-source positive.
    # C can be reached from D, while selected source A has zero mass.
    frozen = reconstruct_compatible_worlds((w,), ("A", "C", "D"), max_steps=2)
    with pytest.raises(ValueError, match="positive weight"):
        audit_world_path_quantifiers(
            frozen, (w,), source_id="A", target_id="C"
        )


def test_world_with_no_surviving_compatible_models_has_no_path_certificate():
    w = _world("w", _edges(("A", "D")))
    frozen = reconstruct_compatible_worlds((w,), ("A", "C"), max_steps=2)
    assert frozen.compatible_world_ids == ()
    with pytest.raises(ValueError, match="no compatible world"):
        audit_world_path_quantifiers(
            frozen, (w,), source_id="A", target_id="C"
        )
