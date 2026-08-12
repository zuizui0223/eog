"""Leakage-resistant pairwise genetic validation for prospective EOG v2.

This module evaluates frozen geographic, environmental, conventional-connectivity and
EOG-R predictors against an independent symmetric genetic-distance response. It does not
construct or tune the EOG network from genetic outcomes.

Pairwise observations are non-independent, so the primary validation holds out one whole
population at a time: all pairs involving the held-out population are test pairs and all
training pairs exclude that population. This is a predictive validation contract, not a
partial-Mantel significance test.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class GeneticValidationConfig:
    response_transform: str = "identity"
    ridge_penalty: float = 1.0

    def __post_init__(self) -> None:
        if self.response_transform not in {"identity", "linearized_fst"}:
            raise ValueError("response_transform must be 'identity' or 'linearized_fst'")
        if not np.isfinite(self.ridge_penalty) or self.ridge_penalty < 0.0:
            raise ValueError("ridge_penalty must be finite and non-negative")


@dataclass(frozen=True)
class GeneticValidationFoldResult:
    held_out_population: str
    n_train_pairs: int
    n_test_pairs: int
    mse: float
    mae: float


@dataclass(frozen=True)
class GeneticValidationModelResult:
    model_id: str
    predictor_names: tuple[str, ...]
    n_estimable_folds: int
    n_total_folds: int
    n_predictions: int
    mse: float
    mae: float
    folds: tuple[GeneticValidationFoldResult, ...]


@dataclass(frozen=True)
class GeneticValidationContrast:
    contrast_id: str
    reference_model: str
    augmented_model: str
    delta_mse: float
    delta_mae: float


@dataclass(frozen=True)
class GeneticValidationResult:
    node_ids: tuple[str, ...]
    config: GeneticValidationConfig
    n_observed_pairs: int
    models: tuple[GeneticValidationModelResult, ...]
    contrasts: tuple[GeneticValidationContrast, ...]
    fingerprint: str


def _sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_distance_matrix(values: np.ndarray, n: int, label: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.shape != (n, n) or not np.isfinite(matrix).all():
        raise ValueError(f"{label} must be a finite square matrix aligned to node_ids")
    if np.any(matrix < 0.0):
        raise ValueError(f"{label} must be non-negative")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise ValueError(f"{label} must be symmetric")
    if not np.allclose(np.diag(matrix), 0.0, rtol=0.0, atol=1e-12):
        raise ValueError(f"{label} diagonal must be zero")
    return matrix


def _validate_response_matrix(values: np.ndarray, n: int) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.shape != (n, n):
        raise ValueError("genetic_distance must be a square matrix aligned to node_ids")
    finite = np.isfinite(matrix)
    if not np.array_equal(finite, finite.T):
        raise ValueError("missing genetic-distance pairs must be symmetric")
    comparable = finite & finite.T
    if not np.allclose(
        np.where(comparable, matrix, 0.0),
        np.where(comparable, matrix.T, 0.0),
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError("genetic_distance must be symmetric")
    diagonal = np.diag(matrix)
    if not np.isfinite(diagonal).all() or not np.allclose(diagonal, 0.0, atol=1e-12):
        raise ValueError("genetic_distance diagonal must be finite zero")
    return matrix


def _validate_disconnected(values: np.ndarray, n: int) -> np.ndarray:
    matrix = np.asarray(values, dtype=bool)
    if matrix.shape != (n, n):
        raise ValueError("eog_disconnected must align to node_ids")
    if not np.array_equal(matrix, matrix.T):
        raise ValueError("eog_disconnected must be symmetric")
    if np.any(np.diag(matrix)):
        raise ValueError("eog_disconnected diagonal must be false")
    return matrix


def _transform_response(values: np.ndarray, transform: str) -> np.ndarray:
    y = np.asarray(values, dtype=float)
    if transform == "identity":
        return y
    if np.any((y < 0.0) | (y >= 1.0)):
        raise ValueError("linearized_fst requires observed genetic distances in [0, 1)")
    return y / (1.0 - y)


def _fit_ridge(
    predictors: np.ndarray,
    response: np.ndarray,
    penalty: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(predictors, dtype=float)
    y = np.asarray(response, dtype=float)
    mean = np.mean(x, axis=0)
    sd = np.std(x, axis=0)
    scale = np.where(sd > 1e-12, sd, 1.0)
    z = (x - mean) / scale
    design = np.column_stack([np.ones(len(z), dtype=float), z])
    if penalty == 0.0:
        beta = np.linalg.lstsq(design, y, rcond=None)[0]
    else:
        regularizer = np.diag([0.0, *([float(penalty)] * x.shape[1])])
        beta = np.linalg.solve(design.T @ design + regularizer, design.T @ y)
    return mean, scale, beta


def _predict_ridge(
    model: tuple[np.ndarray, np.ndarray, np.ndarray],
    predictors: np.ndarray,
) -> np.ndarray:
    mean, scale, beta = model
    z = (np.asarray(predictors, dtype=float) - mean) / scale
    design = np.column_stack([np.ones(len(z), dtype=float), z])
    return design @ beta


def evaluate_genetic_validation_ladder(
    node_ids: Sequence[str],
    genetic_distance: np.ndarray,
    geographic_distance: np.ndarray,
    environmental_distance: np.ndarray,
    eog_continuous_distance: np.ndarray,
    eog_disconnected: np.ndarray,
    *,
    strong_reference_distance: np.ndarray | None = None,
    config: GeneticValidationConfig = GeneticValidationConfig(),
) -> GeneticValidationResult:
    """Evaluate frozen isolation predictors with leave-one-population-out validation.

    The default ladder is ``ibd``, ``ibd_ibe`` and ``ibd_ibe_eog``. If a frozen
    ``strong_reference_distance`` is supplied, ``strong_reference`` and
    ``strong_reference_eog`` are added. Lower MSE/MAE is better; contrasts are always
    ``augmented - reference`` so negative values indicate improvement.
    """

    ids = tuple(str(value) for value in node_ids)
    if len(ids) < 5 or len(set(ids)) != len(ids) or any(not value.strip() for value in ids):
        raise ValueError("node_ids must contain at least five unique non-empty IDs")
    n = len(ids)
    response = _validate_response_matrix(genetic_distance, n)
    d_geo = _validate_distance_matrix(geographic_distance, n, "geographic_distance")
    d_env = _validate_distance_matrix(environmental_distance, n, "environmental_distance")
    d_eog = _validate_distance_matrix(eog_continuous_distance, n, "eog_continuous_distance")
    disconnected = _validate_disconnected(eog_disconnected, n).astype(float)
    strong = None
    if strong_reference_distance is not None:
        strong = _validate_distance_matrix(strong_reference_distance, n, "strong_reference_distance")

    upper = [(i, j) for i in range(n) for j in range(i + 1, n) if np.isfinite(response[i, j])]
    if len(upper) < n:
        raise ValueError("too few observed genetic-distance pairs for population-wise validation")

    pair_y = _transform_response(
        np.asarray([response[i, j] for i, j in upper], dtype=float),
        config.response_transform,
    )
    predictor_values: Mapping[str, np.ndarray] = {
        "geographic": np.asarray([d_geo[i, j] for i, j in upper], dtype=float),
        "environmental": np.asarray([d_env[i, j] for i, j in upper], dtype=float),
        "eog_continuous": np.asarray([d_eog[i, j] for i, j in upper], dtype=float),
        "eog_disconnected": np.asarray([disconnected[i, j] for i, j in upper], dtype=float),
    }
    if strong is not None:
        predictor_values = dict(predictor_values)
        predictor_values["strong_reference"] = np.asarray([strong[i, j] for i, j in upper], dtype=float)

    model_specs: list[tuple[str, tuple[str, ...]]] = [
        ("ibd", ("geographic",)),
        ("ibd_ibe", ("geographic", "environmental")),
        ("ibd_ibe_eog", ("geographic", "environmental", "eog_continuous", "eog_disconnected")),
    ]
    if strong is not None:
        model_specs.extend(
            [
                ("strong_reference", ("strong_reference",)),
                ("strong_reference_eog", ("strong_reference", "eog_continuous", "eog_disconnected")),
            ]
        )

    pair_array = np.asarray(upper, dtype=int)
    model_results: list[GeneticValidationModelResult] = []
    by_model: dict[str, GeneticValidationModelResult] = {}
    for model_id, predictor_names in model_specs:
        x_all = np.column_stack([predictor_values[name] for name in predictor_names])
        fold_results: list[GeneticValidationFoldResult] = []
        squared_errors: list[float] = []
        absolute_errors: list[float] = []
        for held_out in range(n):
            test_mask = (pair_array[:, 0] == held_out) | (pair_array[:, 1] == held_out)
            train_mask = ~test_mask
            n_train = int(np.sum(train_mask))
            n_test = int(np.sum(test_mask))
            if n_test == 0 or n_train <= len(predictor_names) + 1:
                continue
            model = _fit_ridge(x_all[train_mask], pair_y[train_mask], config.ridge_penalty)
            prediction = _predict_ridge(model, x_all[test_mask])
            error = pair_y[test_mask] - prediction
            squared = np.square(error)
            absolute = np.abs(error)
            squared_errors.extend(squared.tolist())
            absolute_errors.extend(absolute.tolist())
            fold_results.append(
                GeneticValidationFoldResult(
                    held_out_population=ids[held_out],
                    n_train_pairs=n_train,
                    n_test_pairs=n_test,
                    mse=float(np.mean(squared)),
                    mae=float(np.mean(absolute)),
                )
            )
        if not fold_results:
            raise ValueError(f"model {model_id} has no estimable leave-one-population-out folds")
        result = GeneticValidationModelResult(
            model_id=model_id,
            predictor_names=predictor_names,
            n_estimable_folds=len(fold_results),
            n_total_folds=n,
            n_predictions=len(squared_errors),
            mse=float(np.mean(squared_errors)),
            mae=float(np.mean(absolute_errors)),
            folds=tuple(fold_results),
        )
        model_results.append(result)
        by_model[model_id] = result

    contrast_specs = [("ibd_ibe", "ibd_ibe_eog")]
    if strong is not None:
        contrast_specs.append(("strong_reference", "strong_reference_eog"))
    contrasts = tuple(
        GeneticValidationContrast(
            contrast_id=f"{augmented}_minus_{reference}",
            reference_model=reference,
            augmented_model=augmented,
            delta_mse=float(by_model[augmented].mse - by_model[reference].mse),
            delta_mae=float(by_model[augmented].mae - by_model[reference].mae),
        )
        for reference, augmented in contrast_specs
    )

    payload = {
        "node_ids": list(ids),
        "config": {
            "response_transform": config.response_transform,
            "ridge_penalty": config.ridge_penalty,
        },
        "n_observed_pairs": len(upper),
        "genetic_distance": np.where(np.isfinite(response), response, None).tolist(),
        "geographic_distance": d_geo.tolist(),
        "environmental_distance": d_env.tolist(),
        "eog_continuous_distance": d_eog.tolist(),
        "eog_disconnected": disconnected.astype(int).tolist(),
        "strong_reference_distance": None if strong is None else strong.tolist(),
        "models": [
            {
                "model_id": result.model_id,
                "predictor_names": list(result.predictor_names),
                "n_estimable_folds": result.n_estimable_folds,
                "n_total_folds": result.n_total_folds,
                "n_predictions": result.n_predictions,
                "mse": result.mse,
                "mae": result.mae,
                "folds": [fold.__dict__ for fold in result.folds],
            }
            for result in model_results
        ],
        "contrasts": [contrast.__dict__ for contrast in contrasts],
    }
    return GeneticValidationResult(
        node_ids=ids,
        config=config,
        n_observed_pairs=len(upper),
        models=tuple(model_results),
        contrasts=contrasts,
        fingerprint=_sha256(payload),
    )
