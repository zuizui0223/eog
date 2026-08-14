import numpy as np
import pytest

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.v2.world_reconstruction import (
    FiniteWorld,
    build_world_flow_set,
    compare_reconstructions,
    forward_reachable_configuration,
    minimum_relaxation_frontier,
    rank_positive_occurrence_candidates,
    reconstruct_compatible_worlds,
)


NODE_IDS = ("A", "B", "C", "D", "E")


def _operator(edges):
    return build_dynamic_transition_operator(
        NODE_IDS,
        [DynamicReachabilityEdge(source=source, target=target, geographic_support=1.0) for source, target in edges],
        loss_support=1.0,
    )


def _worlds():
    # Both chain and direct worlds can realize the observed A/C configuration, but
    # they require genuinely different latent routes.  E remains unreachable in all
    # compatible worlds and is therefore an exact finite-universe negative control.
    return (
        FiniteWorld(
            "chain",
            _operator(((0, 1), (1, 2))),
            ("A",),
            geographic_relaxation=0.1,
            environmental_relaxation=0.6,
        ),
        FiniteWorld(
            "direct",
            _operator(((0, 3), (3, 2))),
            ("A",),
            geographic_relaxation=0.6,
            environmental_relaxation=0.1,
        ),
        FiniteWorld(
            "broken",
            _operator(((0, 1),)),
            ("A",),
            geographic_relaxation=0.05,
            environmental_relaxation=0.05,
        ),
    )


def test_forward_envelopes_preserve_different_routes_without_calling_them_history():
    chain, direct, _ = _worlds()
    chain_forward = forward_reachable_configuration(chain, max_steps=3)
    direct_forward = forward_reachable_configuration(direct, max_steps=3)

    assert chain_forward.reachable_ids == ("A", "B", "C")
    assert direct_forward.reachable_ids == ("A", "C", "D")
    assert {"A", "C"}.issubset(chain_forward.reachable_ids)
    assert {"A", "C"}.issubset(direct_forward.reachable_ids)
    assert chain_forward.fingerprint != direct_forward.fingerprint


def test_inverse_reconstruction_keeps_multiple_compatible_worlds_explicit():
    reconstruction = reconstruct_compatible_worlds(_worlds(), ("A", "C"), max_steps=3)

    assert reconstruction.compatible_world_ids == ("chain", "direct")
    assert reconstruction.incompatible_world_ids == ("broken",)
    assert reconstruction.compatible_fraction == pytest.approx(2 / 3)
    assert reconstruction.identifiable is False
    assert reconstruction.coverage_certificate == "exhaustive_finite_world_enumeration"
    assert all(result.occurrence_result.coverage_fraction == 1.0 for result in reconstruction.world_results[:2])
    assert reconstruction.world_results[2].occurrence_result.coverage_fraction == 0.0


def test_world_flow_set_retains_world_identity_and_certifies_only_finite_universe_exclusion():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(worlds, ("A", "C"), max_steps=3)
    flow_set = build_world_flow_set(reconstruction, worlds)

    assert tuple(member.world_id for member in flow_set.members) == ("chain", "direct")
    assert flow_set.robustly_unreachable_ids == ("E",)
    assert flow_set.contingent_ids == ("B", "D")
    assert flow_set.reachable_in_all_ids == ("A", "C")
    assert flow_set.coverage_certificate == "exhaustive_finite_compatible_world_set"
    assert flow_set.mass_lower_envelope.shape == (4, len(NODE_IDS))
    assert flow_set.mass_upper_envelope.shape == (4, len(NODE_IDS))
    assert np.all(flow_set.mass_lower_envelope <= flow_set.mass_upper_envelope)


def test_relaxation_frontier_keeps_geographic_and_environmental_axes_separate():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(worlds, ("A", "C"), max_steps=3)
    frontier = minimum_relaxation_frontier(reconstruction, worlds)

    assert tuple(point.world_id for point in frontier.points) == ("chain", "direct")
    assert frontier.points[0].geographic_relaxation == pytest.approx(0.1)
    assert frontier.points[0].environmental_relaxation == pytest.approx(0.6)
    assert frontier.points[1].geographic_relaxation == pytest.approx(0.6)
    assert frontier.points[1].environmental_relaxation == pytest.approx(0.1)


def test_new_positive_occurrence_contracts_world_set_and_can_make_it_identifiable():
    worlds = _worlds()
    before = reconstruct_compatible_worlds(worlds, ("A", "C"), max_steps=3)
    after = reconstruct_compatible_worlds(worlds, ("A", "B", "C"), max_steps=3)
    update = compare_reconstructions(before, after)

    assert after.compatible_world_ids == ("chain",)
    assert after.identifiable is True
    assert update.retained_world_ids == ("chain",)
    assert update.eliminated_world_ids == ("direct",)
    assert update.contraction_fraction == pytest.approx(0.5)
    assert update.became_identifiable is True


def test_positive_occurrence_candidates_discriminate_worlds_without_treating_absence_as_evidence():
    worlds = _worlds()
    reconstruction = reconstruct_compatible_worlds(worlds, ("A", "C"), max_steps=3)
    ranking = rank_positive_occurrence_candidates(reconstruction, worlds, ("B", "D", "E"))

    by_id = {row.candidate_id: row for row in ranking.rows}
    assert by_id["B"].status == "discriminating"
    assert by_id["B"].reachable_world_ids == ("chain",)
    assert by_id["B"].unreachable_world_ids == ("direct",)
    assert by_id["B"].positive_elimination_fraction == pytest.approx(0.5)
    assert by_id["D"].status == "discriminating"
    assert by_id["D"].reachable_world_ids == ("direct",)
    assert by_id["E"].status == "unsupported_by_universe"
    assert by_id["E"].positive_elimination_fraction == pytest.approx(1.0)


def test_world_definitions_reject_unobserved_sources_in_first_reconstruction_core():
    world = FiniteWorld("source_b", _operator(((1, 2),)), ("B",))
    with pytest.raises(ValueError, match="observed fixed sources"):
        reconstruct_compatible_worlds((world,), ("A", "C"), max_steps=3)
