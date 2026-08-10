"""Training-only current-flow selection for the Tanzania benchmark.

The module implements the last pre-outcome gate before held-out scoring. It
selects one of the frozen 512 current-flow candidates from outer-training data
only, then fits the already-declared reference and EOG probability tiers with
one shared deterministic L2 logistic engine.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np

from .support_model import (
    PenalizedLogisticSupportModel,
    SupportModelError,
    fit_penalized_logistic_support,
)

EXPECTED_CANDIDATE_COUNT = 512
SOURCE_GLM_MAX_ITERATIONS = 100
SOURCE_GLM_TOLERANCE = 1e-8
SOURCE_GLM_AIC_TIE_DECIMALS = 10
SOURCE_GLM_STEP_FLOOR = 2.0 ** -20
HELDOUT_L2_PENALTY = 1.0
HELDOUT_MIN_CLASS_COUNT = 1
CONSTANT_PREDICTOR_TOLERANCE = 1e-12


class CurrentFlowSelectionError(ValueError):
    """Raised when a frozen Tanzania selection/model contract is violated."""


@dataclass(frozen=True)
class SourceCandidateFit:
    candidate_index: int
    valid: bool
    converged: bool
    aic: float | None
    log_likelihood: float | None
    pseudo_r2: float | None
    effective_parameter_count: int | None
    n_iterations: int
    failure_reason: str | None


@dataclass(frozen=True)
class CurrentFlowSelection:
    selected_candidate_index: int
    selected_aic: float
    selected_log_likelihood: float
    selected_pseudo_r2: float
    selected_effective_parameter_count: int
    n_candidates: int
    n_valid_candidates: int
    invalid_reason_counts: tuple[tuple[str, int], ...]
    aic_tie_decimals: int
    heldout_labels_used: bool = False


@dataclass(frozen=True)
class ReducedPenalizedLogisticModel:
    """A deterministic L2 logistic model with training-constant columns removed."""

    predictor_names: tuple[str, ...]
    active_indices: np.ndarray
    dropped_constant_predictors: tuple[str, ...]
    model: PenalizedLogisticSupportModel

    def predict_probability(self, predictors: np.ndarray) -> np.ndarray:
        x = _as_2d(predictors, "prediction predictors")
        if x.shape[1] != len(self.predictor_names):
            raise CurrentFlowSelectionError(
                "prediction predictor count does not match fitted tier"
            )
        return self.model.predict_support(x[:, self.active_indices])


@dataclass(frozen=True)
class PairedTierPrediction:
    reference_probability: np.ndarray
    candidate_probability: np.ndarray
    reference_active_predictors: tuple[str, ...]
    candidate_active_predictors: tuple[str, ...]
    reference_dropped_constant_predictors: tuple[str, ...]
    candidate_dropped_constant_predictors: tuple[str, ...]
    shared_selected_candidate_index: int


def _as_1d(values: Sequence[float] | np.ndarray, label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size < 1:
        raise CurrentFlowSelectionError(f"{label} must be a non-empty 1-D array")
    if not np.isfinite(array).all():
        raise CurrentFlowSelectionError(f"{label} contains non-finite values")
    return array


def _as_2d(values: np.ndarray, label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[0] < 1 or array.shape[1] < 1:
        raise CurrentFlowSelectionError(f"{label} must be a non-empty 2-D array")
    if not np.isfinite(array).all():
        raise CurrentFlowSelectionError(f"{label} contains non-finite values")
    return array


def _binary_response(values: Sequence[float] | np.ndarray) -> np.ndarray:
    response = _as_1d(values, "training response")
    if not np.all(np.isin(response, (0.0, 1.0))):
        raise CurrentFlowSelectionError("training response must contain only 0/1")
    if np.unique(response).size != 2:
        raise CurrentFlowSelectionError("training response must contain both classes")
    return response


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(values, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _log_likelihood(design: np.ndarray, response: np.ndarray, beta: np.ndarray) -> float:
    eta = design @ beta
    return float(np.sum(response * eta - np.logaddexp(0.0, eta)))


def _invalid_candidate(
    candidate_index: int,
    reason: str,
    *,
    iterations: int = 0,
    converged: bool = False,
) -> SourceCandidateFit:
    return SourceCandidateFit(
        candidate_index=int(candidate_index),
        valid=False,
        converged=bool(converged),
        aic=None,
        log_likelihood=None,
        pseudo_r2=None,
        effective_parameter_count=None,
        n_iterations=int(iterations),
        failure_reason=str(reason),
    )


def fit_source_candidate_glm(
    *,
    candidate_index: int,
    log_area: Sequence[float] | np.ndarray,
    isolation: Sequence[float] | np.ndarray,
    response: Sequence[float] | np.ndarray,
    max_iterations: int = SOURCE_GLM_MAX_ITERATIONS,
    tolerance: float = SOURCE_GLM_TOLERANCE,
) -> SourceCandidateFit:
    """Fit the source unpenalized area-by-isolation candidate on training rows.

    Candidate validity requires convergence and a finite pseudo-R2 in
    ``[0, 1)``. Separation-like fits that never stabilize remain explicit
    invalid candidates.
    """
    try:
        area = _as_1d(log_area, "log_area")
        iso = _as_1d(isolation, "candidate isolation")
        y = _binary_response(response)
    except CurrentFlowSelectionError as exc:
        return _invalid_candidate(candidate_index, str(exc))
    if not (area.shape == iso.shape == y.shape):
        return _invalid_candidate(candidate_index, "training arrays do not align")
    if np.any(iso <= 0.0):
        return _invalid_candidate(candidate_index, "candidate isolation must be positive")
    if max_iterations < 1 or tolerance <= 0.0 or not math.isfinite(tolerance):
        raise CurrentFlowSelectionError("invalid source-GLM numerical contract")

    log_iso = np.log10(iso)
    design = np.column_stack(
        [np.ones(y.size), area, log_iso, area * log_iso]
    )
    if not np.isfinite(design).all():
        return _invalid_candidate(candidate_index, "source design is non-finite")
    rank = int(np.linalg.matrix_rank(design, tol=1e-10))
    if rank < 2:
        return _invalid_candidate(candidate_index, "source design has insufficient rank")

    beta = np.zeros(design.shape[1], dtype=float)
    current = _log_likelihood(design, y, beta)
    converged = False
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        probability = _sigmoid(design @ beta)
        weights = probability * (1.0 - probability)
        gradient = design.T @ (y - probability)
        information = design.T @ (design * weights[:, None])
        try:
            step = np.linalg.lstsq(information, gradient, rcond=1e-12)[0]
        except np.linalg.LinAlgError:
            return _invalid_candidate(
                candidate_index,
                "source information matrix solve failed",
                iterations=iteration,
            )
        if not np.isfinite(step).all():
            return _invalid_candidate(
                candidate_index,
                "source Newton step is non-finite",
                iterations=iteration,
            )

        scale = 1.0
        accepted = False
        candidate_ll = current
        while scale >= SOURCE_GLM_STEP_FLOOR:
            candidate_beta = beta + scale * step
            candidate_ll = _log_likelihood(design, y, candidate_beta)
            if math.isfinite(candidate_ll) and candidate_ll >= current - 1e-12:
                beta = candidate_beta
                accepted = True
                break
            scale *= 0.5
        if not accepted:
            return _invalid_candidate(
                candidate_index,
                "source Newton line search failed",
                iterations=iteration,
            )
        improvement = candidate_ll - current
        current = candidate_ll
        if np.max(np.abs(scale * step)) <= tolerance or improvement <= tolerance:
            converged = True
            break
        if np.max(np.abs(beta)) > 1e6:
            return _invalid_candidate(
                candidate_index,
                "source coefficients diverged",
                iterations=iteration,
            )

    if not converged:
        return _invalid_candidate(
            candidate_index,
            "source GLM did not converge",
            iterations=iterations,
        )

    prevalence = float(np.mean(y))
    null_ll = float(
        np.sum(
            y * math.log(prevalence)
            + (1.0 - y) * math.log(1.0 - prevalence)
        )
    )
    deviance = -2.0 * current
    null_deviance = -2.0 * null_ll
    if not math.isfinite(null_deviance) or null_deviance <= 0.0:
        return _invalid_candidate(
            candidate_index,
            "source null deviance is invalid",
            iterations=iterations,
            converged=True,
        )
    pseudo_r2 = (null_deviance - deviance) / null_deviance
    if not math.isfinite(pseudo_r2) or not (0.0 <= pseudo_r2 < 1.0):
        return _invalid_candidate(
            candidate_index,
            "source pseudo-R2 outside [0,1)",
            iterations=iterations,
            converged=True,
        )
    aic = 2.0 * rank - 2.0 * current
    if not math.isfinite(aic):
        return _invalid_candidate(
            candidate_index,
            "source AIC is non-finite",
            iterations=iterations,
            converged=True,
        )
    return SourceCandidateFit(
        candidate_index=int(candidate_index),
        valid=True,
        converged=True,
        aic=float(aic),
        log_likelihood=float(current),
        pseudo_r2=float(pseudo_r2),
        effective_parameter_count=rank,
        n_iterations=iterations,
        failure_reason=None,
    )


def json_like_counts(values: dict[str, int]) -> str:
    return ", ".join(f"{key}={values[key]}" for key in sorted(values))


def select_training_current_flow_candidate(
    *,
    log_area_train: Sequence[float] | np.ndarray,
    candidate_isolation_train: np.ndarray,
    response_train: Sequence[float] | np.ndarray,
    candidate_indices: Sequence[int] | np.ndarray | None = None,
) -> tuple[CurrentFlowSelection, tuple[SourceCandidateFit, ...]]:
    """Select a resistance candidate using outer-training rows only.

    Held-out labels are absent from the signature by design. AIC values are
    rounded only for deterministic tie grouping; the lower frozen candidate
    index wins an exact or rounded tie.
    """
    area = _as_1d(log_area_train, "log_area_train")
    y = _binary_response(response_train)
    isolation = _as_2d(candidate_isolation_train, "candidate_isolation_train")
    if area.shape != y.shape or isolation.shape[1] != y.size:
        raise CurrentFlowSelectionError("candidate selection training arrays do not align")
    if isolation.shape[0] != EXPECTED_CANDIDATE_COUNT:
        raise CurrentFlowSelectionError(
            f"expected {EXPECTED_CANDIDATE_COUNT} candidates, got {isolation.shape[0]}"
        )
    if candidate_indices is None:
        indices = np.arange(isolation.shape[0], dtype=np.int64)
    else:
        raw = np.asarray(candidate_indices)
        if raw.ndim != 1 or raw.shape[0] != isolation.shape[0]:
            raise CurrentFlowSelectionError("candidate_indices must align with candidates")
        if raw.dtype.kind not in "iu":
            if not np.all(np.equal(raw, np.floor(raw))):
                raise CurrentFlowSelectionError("candidate_indices must be integers")
        indices = raw.astype(np.int64)
    if len(set(indices.tolist())) != isolation.shape[0]:
        raise CurrentFlowSelectionError("candidate_indices must be unique")

    fits = tuple(
        fit_source_candidate_glm(
            candidate_index=int(index),
            log_area=area,
            isolation=isolation[row],
            response=y,
        )
        for row, index in enumerate(indices)
    )
    valid = [fit for fit in fits if fit.valid]
    if not valid:
        reasons: dict[str, int] = {}
        for fit in fits:
            key = fit.failure_reason or "unknown"
            reasons[key] = reasons.get(key, 0) + 1
        raise CurrentFlowSelectionError(
            "no valid training-only current-flow candidate: "
            + json_like_counts(reasons)
        )
    selected = min(
        valid,
        key=lambda fit: (
            round(float(fit.aic), SOURCE_GLM_AIC_TIE_DECIMALS),
            fit.candidate_index,
        ),
    )
    reason_counts: dict[str, int] = {}
    for fit in fits:
        if fit.valid:
            continue
        key = fit.failure_reason or "unknown"
        reason_counts[key] = reason_counts.get(key, 0) + 1
    selection = CurrentFlowSelection(
        selected_candidate_index=selected.candidate_index,
        selected_aic=float(selected.aic),
        selected_log_likelihood=float(selected.log_likelihood),
        selected_pseudo_r2=float(selected.pseudo_r2),
        selected_effective_parameter_count=int(selected.effective_parameter_count),
        n_candidates=len(fits),
        n_valid_candidates=len(valid),
        invalid_reason_counts=tuple(sorted(reason_counts.items())),
        aic_tie_decimals=SOURCE_GLM_AIC_TIE_DECIMALS,
        heldout_labels_used=False,
    )
    return selection, fits


def current_flow_reference_predictors(
    *,
    log_area: Sequence[float] | np.ndarray,
    selected_isolation: Sequence[float] | np.ndarray,
    log10_1p_anchor_distance_km: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    area = _as_1d(log_area, "log_area")
    isolation = _as_1d(selected_isolation, "selected_isolation")
    distance = _as_1d(
        log10_1p_anchor_distance_km,
        "log10_1p_anchor_distance_km",
    )
    if not (area.shape == isolation.shape == distance.shape):
        raise CurrentFlowSelectionError("reference predictors do not align")
    if np.any(isolation <= 0.0):
        raise CurrentFlowSelectionError("selected current-flow isolation must be positive")
    log_iso = np.log10(isolation)
    return (
        np.column_stack([area, log_iso, area * log_iso, distance]),
        (
            "log10_area_ha",
            "log10_current_flow_isolation",
            "area_by_current_flow_isolation",
            "log10_1p_nearest_training_occurrence_km",
        ),
    )


def current_flow_eog_candidate_predictors(
    *,
    log_area: Sequence[float] | np.ndarray,
    selected_isolation: Sequence[float] | np.ndarray,
    log10_1p_anchor_distance_km: Sequence[float] | np.ndarray,
    eog_connected_frequency: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    reference, names = current_flow_reference_predictors(
        log_area=log_area,
        selected_isolation=selected_isolation,
        log10_1p_anchor_distance_km=log10_1p_anchor_distance_km,
    )
    eog = _as_1d(eog_connected_frequency, "eog_connected_frequency")
    if eog.shape[0] != reference.shape[0]:
        raise CurrentFlowSelectionError("EOG predictor does not align")
    if np.any((eog < 0.0) | (eog > 1.0)):
        raise CurrentFlowSelectionError("EOG connected frequency must lie in [0,1]")
    return np.column_stack([reference, eog]), names + ("eog_connected_frequency",)


def fit_reduced_penalized_logistic(
    predictors: np.ndarray,
    response: Sequence[float] | np.ndarray,
    predictor_names: Sequence[str],
    *,
    l2_penalty: float = HELDOUT_L2_PENALTY,
) -> ReducedPenalizedLogisticModel:
    x = _as_2d(predictors, "tier predictors")
    y = _binary_response(response)
    names = tuple(str(value).strip() for value in predictor_names)
    if x.shape[0] != y.size or x.shape[1] != len(names) or any(not name for name in names):
        raise CurrentFlowSelectionError("tier predictors, names, and response do not align")
    scale = np.std(x, axis=0, ddof=0)
    active = np.flatnonzero(scale > CONSTANT_PREDICTOR_TOLERANCE)
    if active.size == 0:
        raise CurrentFlowSelectionError("all probability-tier predictors are constant")
    dropped = tuple(
        names[index]
        for index in np.flatnonzero(scale <= CONSTANT_PREDICTOR_TOLERANCE)
    )
    try:
        model = fit_penalized_logistic_support(
            x[:, active],
            y,
            l2_penalty=l2_penalty,
            min_class_count=HELDOUT_MIN_CLASS_COUNT,
        )
    except SupportModelError as exc:
        raise CurrentFlowSelectionError(str(exc)) from exc
    return ReducedPenalizedLogisticModel(
        predictor_names=names,
        active_indices=active.astype(np.int64),
        dropped_constant_predictors=dropped,
        model=model,
    )


def fit_shared_current_flow_reference_and_eog_tiers(
    *,
    selected_candidate_index: int,
    response_train: Sequence[float] | np.ndarray,
    reference_predictors_train: np.ndarray,
    candidate_predictors_train: np.ndarray,
    reference_predictors_target: np.ndarray,
    candidate_predictors_target: np.ndarray,
    reference_predictor_names: Sequence[str],
    candidate_predictor_names: Sequence[str],
) -> PairedTierPrediction:
    """Fit reference/candidate tiers after one shared resistance selection."""
    reference = fit_reduced_penalized_logistic(
        reference_predictors_train,
        response_train,
        reference_predictor_names,
    )
    candidate = fit_reduced_penalized_logistic(
        candidate_predictors_train,
        response_train,
        candidate_predictor_names,
    )
    ref_probability = reference.predict_probability(reference_predictors_target)
    cand_probability = candidate.predict_probability(candidate_predictors_target)
    return PairedTierPrediction(
        reference_probability=ref_probability,
        candidate_probability=cand_probability,
        reference_active_predictors=tuple(
            reference.predictor_names[index] for index in reference.active_indices
        ),
        candidate_active_predictors=tuple(
            candidate.predictor_names[index] for index in candidate.active_indices
        ),
        reference_dropped_constant_predictors=reference.dropped_constant_predictors,
        candidate_dropped_constant_predictors=candidate.dropped_constant_predictors,
        shared_selected_candidate_index=int(selected_candidate_index),
    )
