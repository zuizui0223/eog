import numpy as np
import pytest

from eog.genetic_validation import GeneticValidationConfig, evaluate_genetic_validation_ladder


def pairwise(values):
    values = np.asarray(values, dtype=float)
    return np.abs(values[:, None] - values[None, :])


def base_inputs():
    ids = tuple(f"p{i}" for i in range(6))
    d_geo = pairwise([0, 1, 2, 3, 4, 5])
    d_env = pairwise([0.0, 0.2, 0.1, 1.0, 1.2, 1.1])
    d_eog = pairwise([0.0, 0.1, 0.3, 1.8, 2.0, 2.2])
    disconnected = np.zeros((6, 6), dtype=bool)
    response = 0.03 * d_geo + 0.12 * d_eog
    np.fill_diagonal(response, 0.0)
    return ids, response, d_geo, d_env, d_eog, disconnected


def model_map(result):
    return {model.model_id: model for model in result.models}


def contrast_map(result):
    return {contrast.contrast_id: contrast for contrast in result.contrasts}


def test_lopo_holds_out_whole_population_and_eog_recovers_added_structure():
    ids, response, d_geo, d_env, d_eog, disconnected = base_inputs()
    result = evaluate_genetic_validation_ladder(ids, response, d_geo, d_env, d_eog, disconnected)
    models = model_map(result)
    assert models["ibd"].n_estimable_folds == 6
    assert models["ibd"].n_predictions == 30
    assert all(fold.n_test_pairs == 5 for fold in models["ibd"].folds)
    assert all(fold.n_train_pairs == 10 for fold in models["ibd"].folds)
    assert contrast_map(result)["ibd_ibe_eog_minus_ibd_ibe"].delta_mse < 0.0
    assert len(result.fingerprint) == 64


def test_strong_reference_is_evaluated_on_identical_population_holdouts():
    ids, response, d_geo, d_env, d_eog, disconnected = base_inputs()
    result = evaluate_genetic_validation_ladder(
        ids,
        response,
        d_geo,
        d_env,
        d_eog,
        disconnected,
        strong_reference_distance=response,
    )
    models = model_map(result)
    assert "strong_reference" in models
    assert "strong_reference_eog" in models
    assert models["strong_reference"].n_predictions == models["strong_reference_eog"].n_predictions
    assert "strong_reference_eog_minus_strong_reference" in contrast_map(result)


def test_symmetric_missing_pair_is_retained_as_missing_not_imputed():
    ids, response, d_geo, d_env, d_eog, disconnected = base_inputs()
    response = response.copy()
    response[0, 1] = np.nan
    response[1, 0] = np.nan
    result = evaluate_genetic_validation_ladder(ids, response, d_geo, d_env, d_eog, disconnected)
    assert result.n_observed_pairs == 14
    assert all(model.n_predictions > 0 for model in result.models)


def test_linearized_fst_transform_is_explicit_and_validated():
    ids, response, d_geo, d_env, d_eog, disconnected = base_inputs()
    response = np.clip(response, 0.0, 0.8)
    result = evaluate_genetic_validation_ladder(
        ids,
        response,
        d_geo,
        d_env,
        d_eog,
        disconnected,
        config=GeneticValidationConfig(response_transform="linearized_fst", ridge_penalty=1.0),
    )
    assert result.config.response_transform == "linearized_fst"
    invalid = response.copy()
    invalid[0, 1] = invalid[1, 0] = 1.0
    with pytest.raises(ValueError, match="linearized_fst"):
        evaluate_genetic_validation_ladder(
            ids,
            invalid,
            d_geo,
            d_env,
            d_eog,
            disconnected,
            config=GeneticValidationConfig(response_transform="linearized_fst"),
        )


def test_zero_ridge_penalty_uses_stable_least_squares_path():
    ids, response, d_geo, d_env, d_eog, disconnected = base_inputs()
    result = evaluate_genetic_validation_ladder(
        ids,
        response,
        d_geo,
        d_env,
        d_eog,
        disconnected,
        config=GeneticValidationConfig(ridge_penalty=0.0),
    )
    assert all(np.isfinite(model.mse) for model in result.models)


def test_asymmetric_inputs_and_invalid_disconnection_are_rejected():
    ids, response, d_geo, d_env, d_eog, disconnected = base_inputs()
    bad_geo = d_geo.copy()
    bad_geo[0, 1] += 0.5
    with pytest.raises(ValueError, match="symmetric"):
        evaluate_genetic_validation_ladder(ids, response, bad_geo, d_env, d_eog, disconnected)
    bad_disconnect = disconnected.copy()
    bad_disconnect[0, 1] = True
    with pytest.raises(ValueError, match="symmetric"):
        evaluate_genetic_validation_ladder(ids, response, d_geo, d_env, d_eog, bad_disconnect)


def test_too_few_populations_are_rejected():
    with pytest.raises(ValueError, match="at least five"):
        evaluate_genetic_validation_ladder(
            ("a", "b", "c", "d"),
            np.zeros((4, 4)),
            np.zeros((4, 4)),
            np.zeros((4, 4)),
            np.zeros((4, 4)),
            np.zeros((4, 4), dtype=bool),
        )
