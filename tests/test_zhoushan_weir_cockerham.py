from __future__ import annotations

import math

import pytest

from benchmarks.zhoushan_weir_cockerham import (
    all_pairwise_theta,
    pairwise_weir_cockerham_theta,
)


def _loci(genotypes):
    return {"L1": genotypes}


def test_complete_fixed_difference_is_one():
    left = _loci([("A", "A")] * 10)
    right = _loci([("B", "B")] * 10)
    result = pairwise_weir_cockerham_theta("A", "B", left, right, locus_order=("L1",))
    assert result.theta == pytest.approx(1.0, abs=1e-12)
    assert result.n_usable_loci == 1


def test_allele_relabeling_does_not_change_theta():
    left = _loci([("A", "A"), ("A", "B"), ("A", "B"), ("B", "B")] * 4)
    right = _loci([("A", "A"), ("A", "A"), ("A", "B"), ("A", "B")] * 4)
    original = pairwise_weir_cockerham_theta("P1", "P2", left, right, locus_order=("L1",))
    recoded_left = _loci([(1 if a == "A" else 9, 1 if b == "A" else 9) for a, b in left["L1"]])
    recoded_right = _loci([(1 if a == "A" else 9, 1 if b == "A" else 9) for a, b in right["L1"]])
    recoded = pairwise_weir_cockerham_theta("P1", "P2", recoded_left, recoded_right, locus_order=("L1",))
    assert recoded.theta == pytest.approx(original.theta, abs=1e-12)


def test_missing_genotypes_are_excluded_locuswise_not_imputed():
    left = {
        "L1": [("A", "A"), None, ("A", "B"), ("B", "B")],
        "L2": [None, None, None, None],
    }
    right = {
        "L1": [("A", "A"), ("A", "A"), None, ("A", "B")],
        "L2": [("C", "C")] * 4,
    }
    result = pairwise_weir_cockerham_theta("P1", "P2", left, right, locus_order=("L1", "L2"))
    reference = pairwise_weir_cockerham_theta(
        "P1",
        "P2",
        {"L1": left["L1"]},
        {"L1": right["L1"]},
        locus_order=("L1",),
    )
    assert result.n_usable_loci == 1
    assert result.theta == pytest.approx(reference.theta, abs=1e-12)


def test_theta_is_not_clipped_when_sampling_variance_makes_it_negative():
    # Identical balanced populations can yield a small negative unbiased estimate.
    population = _loci([("A", "A"), ("A", "B"), ("A", "B"), ("B", "B")] * 5)
    result = pairwise_weir_cockerham_theta("P1", "P2", population, population, locus_order=("L1",))
    assert math.isfinite(result.theta)
    assert result.theta <= 0.0


def test_all_pairwise_requires_frozen_population_order():
    populations = {
        "P1": _loci([("A", "A")] * 4),
        "P2": _loci([("A", "B")] * 4),
        "P3": _loci([("B", "B")] * 4),
    }
    results = all_pairwise_theta(populations, population_order=("P1", "P2", "P3"), locus_order=("L1",))
    assert [(r.population_a, r.population_b) for r in results] == [
        ("P1", "P2"),
        ("P1", "P3"),
        ("P2", "P3"),
    ]
    with pytest.raises(ValueError):
        all_pairwise_theta(populations, population_order=("P2", "P1", "P3"), locus_order=("L1",))
