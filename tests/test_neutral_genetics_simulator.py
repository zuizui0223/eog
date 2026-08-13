import numpy as np
import pytest

from eog.neutral_genetics_simulator import (
    pairwise_heterozygosity_fst,
    simulate_neutral_drift_migration,
)


def test_pairwise_fst_is_symmetric_bounded_and_zero_on_diagonal():
    p = np.array([[0.1, 0.3, 0.8], [0.2, 0.4, 0.7], [0.9, 0.7, 0.2]])
    fst = pairwise_heterozygosity_fst(p)
    assert np.allclose(fst, fst.T)
    assert np.allclose(np.diag(fst), 0.0)
    assert np.all((fst >= 0.0) & (fst <= 1.0))


def test_migration_reduces_neutral_divergence_under_same_seed():
    no_migration = np.zeros((2, 2), dtype=float)
    connected = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=float)
    isolated = simulate_neutral_drift_migration(
        no_migration,
        migration_scale=0.0,
        effective_population_size=60,
        generations=60,
        n_loci=1024,
        seed=101,
    )
    linked = simulate_neutral_drift_migration(
        connected,
        migration_scale=0.08,
        effective_population_size=60,
        generations=60,
        n_loci=1024,
        seed=101,
    )
    assert linked.pairwise_fst[0, 1] < isolated.pairwise_fst[0, 1]


def test_simulator_is_deterministic_for_frozen_inputs():
    support = np.array([[0.0, 0.8], [0.4, 0.0]], dtype=float)
    a = simulate_neutral_drift_migration(
        support,
        migration_scale=0.05,
        effective_population_size=(50, 80),
        generations=10,
        n_loci=64,
        seed=211,
    )
    b = simulate_neutral_drift_migration(
        support,
        migration_scale=0.05,
        effective_population_size=(50, 80),
        generations=10,
        n_loci=64,
        seed=211,
    )
    assert np.array_equal(a.allele_frequencies, b.allele_frequencies)
    assert a.fingerprint == b.fingerprint


def test_rejects_excess_incoming_migration_fraction():
    support = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=float)
    with pytest.raises(ValueError, match="sum to < 1"):
        simulate_neutral_drift_migration(
            support,
            migration_scale=1.0,
            effective_population_size=50,
            generations=2,
            n_loci=8,
            seed=1,
        )
