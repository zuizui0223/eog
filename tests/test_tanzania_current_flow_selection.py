from __future__ import annotations

import inspect

import numpy as np
import pytest

from eog.tanzania_current_flow_selection import (
    CurrentFlowSelectionError,
    SOURCE_GLM_AIC_TIE_DECIMALS,
    current_flow_eog_candidate_predictors,
    current_flow_reference_predictors,
    fit_shared_current_flow_reference_and_eog_tiers,
    fit_source_candidate_glm,
    select_training_current_flow_candidate,
)


def _training_fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = 24
    area = np.linspace(-1.1, 1.2, n)
    signal = np.sin(np.linspace(0.0, 3.4 * np.pi, n)) + 0.35 * area
    response = (signal > 0.0).astype(float)
    response[[3, 14, 20]] = 1.0 - response[[3, 14, 20]]
    isolation = 10.0 ** (1.2 + 0.18 * signal)
    return area, response, isolation


def test_selection_signature_cannot_accept_heldout_labels() -> None:
    parameters = inspect.signature(select_training_current_flow_candidate).parameters
    assert "response_train" in parameters
    assert all("heldout" not in name and "target" not in name for name in parameters)


def test_identical_aic_candidates_use_lower_frozen_index() -> None:
    area, response, isolation = _training_fixture()
    candidates = np.repeat(isolation[None, :], 512, axis=0)
    indices = np.arange(512, dtype=np.int64)[::-1]

    selection, fits = select_training_current_flow_candidate(
        log_area_train=area,
        candidate_isolation_train=candidates,
        response_train=response,
        candidate_indices=indices,
    )

    assert selection.selected_candidate_index == 0
    assert selection.n_valid_candidates == 512
    assert selection.aic_tie_decimals == SOURCE_GLM_AIC_TIE_DECIMALS
    assert selection.heldout_labels_used is False
    assert all(fit.valid for fit in fits)


def test_invalid_candidate_is_explicit_and_cannot_win() -> None:
    area, response, isolation = _training_fixture()
    candidates = np.repeat(isolation[None, :], 512, axis=0)
    candidates[0, 0] = 0.0

    selection, fits = select_training_current_flow_candidate(
        log_area_train=area,
        candidate_isolation_train=candidates,
        response_train=response,
    )

    assert fits[0].valid is False
    assert fits[0].failure_reason == "candidate isolation must be positive"
    assert selection.selected_candidate_index == 1
    assert selection.n_valid_candidates == 511


def test_source_fit_rejects_single_class_training_response() -> None:
    area = np.linspace(-1.0, 1.0, 10)
    isolation = np.linspace(2.0, 5.0, 10)
    fit = fit_source_candidate_glm(
        candidate_index=4,
        log_area=area,
        isolation=isolation,
        response=np.ones(10),
    )
    assert fit.valid is False
    assert fit.failure_reason == "training response must contain both classes"


def test_candidate_grid_must_contain_exactly_512_rows() -> None:
    area, response, isolation = _training_fixture()
    with pytest.raises(CurrentFlowSelectionError, match="expected 512 candidates"):
        select_training_current_flow_candidate(
            log_area_train=area,
            candidate_isolation_train=np.repeat(isolation[None, :], 511, axis=0),
            response_train=response,
        )


def test_reference_and_candidate_share_selected_current_flow_and_drop_constant_eog() -> None:
    n = 14
    area = np.linspace(-1.0, 1.0, n)
    isolation = np.linspace(4.0, 16.0, n)
    distance = np.linspace(0.1, 1.2, n)
    response = np.asarray([0, 1] * 7, dtype=float)
    eog = np.full(n, 0.5)

    reference, reference_names = current_flow_reference_predictors(
        log_area=area,
        selected_isolation=isolation,
        log10_1p_anchor_distance_km=distance,
    )
    candidate, candidate_names = current_flow_eog_candidate_predictors(
        log_area=area,
        selected_isolation=isolation,
        log10_1p_anchor_distance_km=distance,
        eog_connected_frequency=eog,
    )
    prediction = fit_shared_current_flow_reference_and_eog_tiers(
        selected_candidate_index=37,
        response_train=response[:12],
        reference_predictors_train=reference[:12],
        candidate_predictors_train=candidate[:12],
        reference_predictors_target=reference[12:],
        candidate_predictors_target=candidate[12:],
        reference_predictor_names=reference_names,
        candidate_predictor_names=candidate_names,
    )

    assert prediction.shared_selected_candidate_index == 37
    assert prediction.candidate_dropped_constant_predictors == (
        "eog_connected_frequency",
    )
    assert np.allclose(
        prediction.reference_probability,
        prediction.candidate_probability,
        atol=1e-12,
        rtol=0.0,
    )


def test_eog_connected_frequency_must_be_bounded() -> None:
    with pytest.raises(CurrentFlowSelectionError, match="must lie in"):
        current_flow_eog_candidate_predictors(
            log_area=[0.0, 1.0],
            selected_isolation=[2.0, 3.0],
            log10_1p_anchor_distance_km=[0.1, 0.2],
            eog_connected_frequency=[0.0, 1.1],
        )
