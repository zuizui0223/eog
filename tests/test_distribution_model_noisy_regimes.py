from benchmarks.distribution_model_noisy_regimes import (
    DEVELOPMENT_SEEDS,
    REGIMES,
    build_noisy_landscape,
)


def test_noisy_regime_development_contract_is_prospective_and_leakage_safe():
    assert DEVELOPMENT_SEEDS == (101, 211, 307, 401, 503, 601, 701, 809)
    assert REGIMES == (
        "habitat_only",
        "dispersal_limited",
        "graded_barrier",
        "stepping_stone",
        "long_jump",
        "mixed",
    )

    for regime in REGIMES:
        bundle = build_noisy_landscape(regime, DEVELOPMENT_SEEDS[0], n_modules=8)
        assert set(bundle.target_ids).isdisjoint(bundle.observed_ids)
        assert set(bundle.gate_folds) == {"inner_a", "inner_b"}
        assert bundle.config.structural_gate_weight is None
        assert bundle.config.gate_grid_size == 201
        assert len(bundle.target_ids) == 16
        assert len(bundle.observed_ids) == 32
