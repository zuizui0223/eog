from eog.v2.bam_ecological_expansion_margin import (
    BM_BITS,
    EcologicalCoordinates,
    build_expanded_ecological_lattice,
    changed_dimensions,
    declared_world_coordinates,
    declared_world_is_embedded_exactly,
    ecological_coordinate_distance,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    build_generality_system,
)


def test_expanded_lattice_size_and_declared_embedding():
    system = build_generality_system(SYSTEM_SPECS[0])
    lattice = build_expanded_ecological_lattice(system)
    assert len(lattice) == 4 * 2 * 2 * 3 * 3 * 3 * 2 * 3
    assert all(declared_world_is_embedded_exactly(system, world, lattice) for world in system.worlds)


def test_declared_world_coordinate_ranges_are_frozen_core():
    system = build_generality_system(SYSTEM_SPECS[0])
    coords = [declared_world_coordinates(system, world) for world in system.worlds]
    assert {row.A_level for row in coords} == {0, 1}
    assert {row.partner_range_level for row in coords} == {0}
    assert {row.antagonist_range_level for row in coords} == {0}
    assert {row.dispersal_radius_level for row in coords} == {0, 1}
    assert {row.horizon_level for row in coords} == {0, 1}
    assert {(row.partner_required, row.antagonist_excluded) for row in coords} == set(BM_BITS.values())


def test_coordinate_distance_is_exact_manhattan():
    left = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    right = EcologicalCoordinates(2, 1, 0, -1, 1, 2, 1, 1)
    assert ecological_coordinate_distance(left, right) == 2 + 1 + 1 + 1 + 2 + 1 + 1
    assert set(changed_dimensions(left, right)) == {
        "A_level",
        "partner_required",
        "partner_range_level",
        "antagonist_range_level",
        "dispersal_radius_level",
        "barrier_permeable",
        "horizon_level",
    }


def test_released_axis_only_cannot_change_release_target():
    system = build_generality_system(SYSTEM_SPECS[0])
    lattice = build_expanded_ecological_lattice(system)

    # If B and M masks are equal, release-A outcomes are equal regardless of A.
    grouped = {}
    for row in lattice:
        key = (row.biotic_mask, row.movement_mask, row.occupied_mask)
        grouped.setdefault(key, []).append(row)
    for rows in grouped.values():
        if len(rows) < 2:
            continue
        outcomes = {row.release_expands("A") for row in rows}
        assert len(outcomes) == 1

    # Symmetric logical checks for release B and M.
    grouped = {}
    for row in lattice:
        key = (row.abiotic_mask, row.movement_mask, row.occupied_mask)
        grouped.setdefault(key, []).append(row)
    for rows in grouped.values():
        if len(rows) >= 2:
            assert len({row.release_expands("B") for row in rows}) == 1

    grouped = {}
    for row in lattice:
        key = (row.abiotic_mask, row.biotic_mask, row.occupied_mask)
        grouped.setdefault(key, []).append(row)
    for rows in grouped.values():
        if len(rows) >= 2:
            assert len({row.release_expands("M") for row in rows}) == 1
