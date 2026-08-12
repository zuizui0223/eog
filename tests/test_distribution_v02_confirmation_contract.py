from pathlib import Path

import pytest

from benchmarks.run_distribution_v02_confirmation import (
    DEFAULT_AUTHORIZATION,
    DEFAULT_CONTRACT,
    load_authorization,
    load_contract,
    run_confirmation,
    validate_authorization,
    validate_contract,
)


def test_v02_confirmation_contract_is_frozen_and_inert_before_authorization():
    contract = load_contract(DEFAULT_CONTRACT)
    authorization = load_authorization(DEFAULT_AUTHORIZATION)
    validation = validate_contract(contract)
    authorization_validation = validate_authorization(DEFAULT_CONTRACT, authorization)

    assert validation["valid"] is True
    assert validation["development_confirmation_seed_overlap"] == 0
    assert validation["n_confirmation_seeds"] == 12
    assert validation["n_regimes"] == 6
    assert validation["n_modules_per_seed"] == 24
    assert validation["stack_weight"] == 0.125
    assert all(item["matches"] for item in validation["blob_checks"].values())

    assert authorization_validation["valid"] is True
    assert authorization_validation["contract_matches"] is True
    assert authorization_validation["execution_authorized"] is False

    with pytest.raises(RuntimeError, match="not authorized"):
        run_confirmation(
            contract,
            authorization,
            contract_path=DEFAULT_CONTRACT,
        )


def test_v02_confirmation_contract_contains_strong_comparator_gates():
    contract = load_contract(DEFAULT_CONTRACT)
    gates = contract["promotion_gates"]
    assert gates == {
        "null_regime_maximum_mean_log_loss_harm_vs_environmental": 0.01,
        "maximum_single_seed_log_loss_harm_vs_environmental": 0.05,
        "each_structural_regime_requires_positive_mean_log_loss_gain_vs_environmental": True,
        "each_structural_regime_requires_positive_mean_log_loss_gain_vs_single_path": True,
    }
    assert contract["null_regimes"] == ["habitat_only", "long_jump"]
    assert contract["structural_regimes"] == [
        "dispersal_limited",
        "graded_barrier",
        "stepping_stone",
        "mixed",
    ]
    assert contract["candidate_model"]["formula"] == (
        "D = 0.875 * D_probability_gate + 0.125 * D_cross_fitted_stack"
    )
