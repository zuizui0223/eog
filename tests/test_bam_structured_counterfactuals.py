from eog.v2.bam_ecological_expansion_margin import (
    build_expanded_ecological_lattice,
    declared_world_is_embedded_exactly,
)
from eog.v2.bam_structured_counterfactuals import (
    declared_world_counterfactual,
    expanded_variant_bam_state_key,
    expanded_variant_counterfactual,
)
from eog.v2.known_truth_bam_direct_evidence import bam_state_key
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    build_generality_system,
)


def test_declared_worlds_embed_and_reconstruct_current_bam_state():
    system = build_generality_system(SYSTEM_SPECS[0])
    lattice = build_expanded_ecological_lattice(system)
    by_coords = {row.coordinates: row for row in lattice}
    from eog.v2.bam_ecological_expansion_margin import declared_world_coordinates

    for world in system.worlds:
        assert declared_world_is_embedded_exactly(system, world, lattice)
        variant = by_coords[declared_world_coordinates(system, world)]
        assert expanded_variant_bam_state_key(system, variant) == bam_state_key(world)


def test_biotic_stress_never_adds_current_occupied_nodes():
    system = build_generality_system(SYSTEM_SPECS[0])
    lattice = build_expanded_ecological_lattice(system)
    for variant in lattice:
        out = expanded_variant_counterfactual(system, variant, "biotic_stress")
        assert out.counterfactual_G & ~out.current_G == 0
        assert out.binary_decision == (out.counterfactual_G != out.current_G)


def test_barrier_restoration_never_removes_current_occupied_nodes():
    system = build_generality_system(SYSTEM_SPECS[0])
    lattice = build_expanded_ecological_lattice(system)
    for variant in lattice:
        out = expanded_variant_counterfactual(system, variant, "barrier_restoration")
        assert out.current_G & ~out.counterfactual_G == 0
        assert out.binary_decision == bool(out.counterfactual_G & ~out.current_G)


def test_climate_shift_binary_target_matches_net_range_loss():
    system = build_generality_system(SYSTEM_SPECS[0])
    for world in system.worlds:
        out = declared_world_counterfactual(system, world, "climate_shift")
        assert out.binary_decision == (
            out.counterfactual_G.bit_count() < out.current_G.bit_count()
        )
