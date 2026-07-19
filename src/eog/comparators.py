"""Established point-cloud comparators used in EOG validation."""
from __future__ import annotations

import numpy as np


def _matrix(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or len(matrix) < 2:
        raise ValueError("values must be a two-dimensional matrix with at least two rows")
    if not np.isfinite(matrix).all():
        raise ValueError("values contain non-finite entries")
    return matrix


def pairwise_euclidean(x: np.ndarray, y: np.ndarray | None = None) -> np.ndarray:
    a = _matrix(x)
    b = a if y is None else _matrix(y)
    if a.shape[1] != b.shape[1]:
        raise ValueError("matrices must have matching feature dimensions")
    aa = np.sum(a * a, axis=1)[:, None]
    bb = np.sum(b * b, axis=1)[None, :]
    return np.sqrt(np.maximum(aa + bb - 2.0 * a @ b.T, 0.0))


def mean_centroid_distance(values: np.ndarray) -> float:
    matrix = _matrix(values)
    return float(np.mean(np.linalg.norm(matrix - matrix.mean(axis=0), axis=1)))


def median_centroid_distance(values: np.ndarray) -> float:
    matrix = _matrix(values)
    return float(np.median(np.linalg.norm(matrix - matrix.mean(axis=0), axis=1)))


def gaussian_linear_extent(values: np.ndarray, *, tolerance: float = 1e-12) -> float:
    matrix = _matrix(values)
    covariance = np.atleast_2d(np.cov(matrix, rowvar=False))
    eigenvalues = np.linalg.eigvalsh(covariance)
    positive = eigenvalues[eigenvalues > tolerance]
    if not positive.size:
        return 0.0
    return float(np.exp(0.5 * np.mean(np.log(positive))))


def convex_hull_area_2d(values: np.ndarray) -> float:
    matrix = _matrix(values)
    if matrix.shape[1] != 2:
        raise ValueError("convex-hull area is defined here only for two features")
    points = sorted(set(map(tuple, matrix.tolist())))
    if len(points) < 3:
        return 0.0

    def cross(origin, a, b):
        return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

    lower = []
    for point in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return 0.0
    twice_area = sum(
        hull[i][0] * hull[(i + 1) % len(hull)][1]
        - hull[(i + 1) % len(hull)][0] * hull[i][1]
        for i in range(len(hull))
    )
    return float(abs(twice_area) / 2.0)


def energy_distance(x: np.ndarray, y: np.ndarray) -> float:
    a = _matrix(x)
    b = _matrix(y)
    if a.shape[1] != b.shape[1]:
        raise ValueError("matrices must have matching feature dimensions")
    return float(
        2.0 * pairwise_euclidean(a, b).mean()
        - pairwise_euclidean(a).mean()
        - pairwise_euclidean(b).mean()
    )
