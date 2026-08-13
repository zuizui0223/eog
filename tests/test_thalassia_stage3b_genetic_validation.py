from __future__ import annotations

import numpy as np
import pytest

from benchmarks.thalassia_stage3b_genetic_validation import (
    NonEstimable,
    SampleGenotype,
    clone_correct,
    population_bootstrap_interval,
    validate_primary_theta,
)


def _sample(row, sample_id, population_id, *genotypes):
    return SampleGenotype(row, sample_id, population_id, tuple(genotypes))


def test_clone_correction_is_exact_within_population_and_deterministic():
    samples = (
        _sample(4, "P1-02", "P1", (100, 100), (200, 202)),
        _sample(5, "P1-01", "P1", (100, 100), (202, 200)),
        _sample(6, "P1-03", "P1", (102, 102), (202, 202)),
        _sample(7, "P2-01", "P2", (100, 100), (200, 202)),
        _sample(8, "P2-02", "P2", (102, 102), (202, 202)),
    )
    retained, qc = clone_correct(samples, population_order=("P1", "P2"))
    assert [sample.sample_id for sample in retained["P1"]] == ["P1-01", "P1-03"]
    # The same MLG in another population is not collapsed across populations.
    assert [sample.sample_id for sample in retained["P2"]] == ["P2-01", "P2-02"]
    assert qc["clone_duplicates_removed_by_population"] == {"P1": 1, "P2": 0}


def test_incomplete_samples_are_removed_before_clone_correction():
    samples = (
        _sample(4, "P1-a", "P1", (100, 100), None),
        _sample(5, "P1-b", "P1", (100, 102), (200, 202)),
        _sample(6, "P1-c", "P1", (102, 102), (202, 202)),
        _sample(7, "P2-a", "P2", (100, 100), (200, 202)),
        _sample(8, "P2-b", "P2", (102, 102), (202, 202)),
    )
    retained, qc = clone_correct(samples, population_order=("P1", "P2"))
    assert [sample.sample_id for sample in retained["P1"]] == ["P1-b", "P1-c"]
    assert qc["n_incomplete_samples"] == 1


def test_fewer_than_two_complete_unique_mlgs_is_non_estimable():
    samples = (
        _sample(4, "P1-a", "P1", (100, 100)),
        _sample(5, "P1-b", "P1", (100, 100)),
        _sample(6, "P2-a", "P2", (100, 100)),
        _sample(7, "P2-b", "P2", (102, 102)),
    )
    with pytest.raises(NonEstimable) as error:
        clone_correct(samples, population_order=("P1", "P2"))
    assert error.value.status == "non_estimable_insufficient_clone_corrected_genets"


def test_primary_linearized_fst_domain_is_frozen_without_clipping():
    assert validate_primary_theta(0.2, "A-B") == pytest.approx(0.2)
    for value in (-0.01, 1.0, float("nan")):
        with pytest.raises(NonEstimable) as error:
            validate_primary_theta(value, "A-B")
        assert error.value.status == "non_estimable_linearized_fst_domain"


def test_population_bootstrap_is_deterministic_and_equal_weight():
    values = [-0.4, -0.2, -0.1, 0.05]
    first = population_bootstrap_interval(values, seed=123, resamples=2000)
    second = population_bootstrap_interval(values, seed=123, resamples=2000)
    assert first == second
    assert np.isfinite(first).all()
    assert first[0] <= np.mean(values) <= first[1]
