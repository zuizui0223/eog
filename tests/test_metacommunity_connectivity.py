import numpy as np
import pytest

from eog.v2.metacommunity_connectivity import (
    aggregate_emergence_test,
    assemblage_row_permutation_null,
    calculate_metacommunity_connectivity,
    deterministic_site_seed,
)


def _graph(n, edges):
    adjacency = np.zeros((n, n), dtype=bool)
    for left, right in edges:
        adjacency[left, right] = True
        adjacency[right, left] = True
    return adjacency


def test_species_turnover_can_create_strict_emergent_community_connectivity():
    # A occurs at 0 and 2; B occurs at 1 and 3. Neither species has adjacent
    # conspecific positives, but the pooled guild occupies a continuous chain.
    world = _graph(4, [(0, 1), (1, 2), (2, 3)])
    incidence = np.asarray(
        [
            [1, 0],
            [0, 1],
            [1, 0],
            [0, 1],
        ],
        dtype=bool,
    )

    result = calculate_metacommunity_connectivity(
        {"world": world},
        incidence,
        species_ids=("A", "B"),
    )

    assert result.community_survival_fraction == 1.0
    assert result.max_species_survival_fraction == 0.0
    assert result.emergent_connectivity_gain == 1.0
    assert result.strict_emergent_world_fraction == 1.0
    assert result.cross_species_rescue_fraction == 1.0
    assert result.dominance_coverage == 0.5


def test_single_dominant_species_explains_community_connectivity_without_emergence():
    world = _graph(4, [(0, 1), (1, 2), (2, 3)])
    incidence = np.asarray(
        [
            [1, 0],
            [1, 1],
            [1, 0],
            [1, 0],
        ],
        dtype=bool,
    )

    result = calculate_metacommunity_connectivity(
        {"world": world},
        incidence,
        species_ids=("dominant", "rare"),
    )

    assert result.community_survival_fraction == 1.0
    assert result.max_species_survival_fraction == 1.0
    assert result.emergent_connectivity_gain == 0.0
    assert result.cross_species_rescue_fraction == 0.0
    assert result.dominance_coverage == 1.0


def test_duplicate_worlds_must_be_removed_upstream_not_weighted_here():
    world = _graph(4, [(0, 1), (1, 2), (2, 3)])
    incidence = np.asarray([[1, 0], [0, 1], [1, 0], [0, 1]], dtype=bool)

    result = calculate_metacommunity_connectivity(
        {"canonical_a": world, "canonical_b": world.copy()},
        incidence,
        species_ids=("A", "B"),
    )
    # The metric does exactly what the caller declares: it does not silently
    # deduplicate. The prospective protocol requires deduplication upstream.
    assert result.world_ids == ("canonical_a", "canonical_b")


def test_assemblage_row_permutation_preserves_frozen_margins():
    worlds = {
        "chain": _graph(4, [(0, 1), (1, 2), (2, 3)]),
        "dense": _graph(4, [(0, 1), (1, 2), (2, 3), (0, 2), (1, 3)]),
    }
    incidence = np.asarray(
        [
            [1, 0, 0],
            [0, 1, 1],
            [1, 0, 1],
            [0, 1, 0],
        ],
        dtype=bool,
    )

    result = assemblage_row_permutation_null(
        worlds,
        incidence,
        species_ids=("A", "B", "C"),
        replicates=50,
        seed=123,
    )

    assert result.replicates == 50
    assert result.row_sum_preserved is True
    assert result.column_sum_preserved is True
    assert result.guild_positive_set_preserved is True
    assert len(result.null_gains) == 50
    assert 0.0 <= result.upper_tail_p <= 1.0


def test_deterministic_site_seed_is_stable_and_site_specific():
    a1 = deterministic_site_seed("programme", "SITE")
    a2 = deterministic_site_seed("programme", "SITE")
    b = deterministic_site_seed("programme", "OTHR")
    assert a1 == a2
    assert a1 != b


def test_aggregate_primary_requires_positive_observed_gain_and_sign_test_support():
    result = aggregate_emergence_test(
        observed_gains=[0.5] * 8,
        null_adjusted_gains=[0.2] * 8,
        minimum_sites=8,
        alpha=0.05,
    )
    assert result.confirmatory_estimable is True
    assert result.positive_null_adjusted_site_count == 8
    assert result.one_sided_sign_test_p == pytest.approx(1 / 256)
    assert result.primary_supported is True


def test_zero_null_adjusted_effect_counts_as_nonpositive():
    result = aggregate_emergence_test(
        observed_gains=[0.5] * 8,
        null_adjusted_gains=[0.1, 0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.0],
        minimum_sites=8,
        alpha=0.05,
    )
    assert result.positive_null_adjusted_site_count == 4
    assert result.primary_supported is False


def test_site_with_no_species_on_two_nodes_is_not_estimable():
    world = _graph(3, [(0, 1), (1, 2)])
    incidence = np.asarray(
        [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ],
        dtype=bool,
    )
    with pytest.raises(ValueError, match="at least one species must occupy at least two nodes"):
        calculate_metacommunity_connectivity(
            {"world": world},
            incidence,
            species_ids=("A", "B", "C"),
        )
