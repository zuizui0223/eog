import numpy as np
import pytest

from eog.comparators import (
    convex_hull_area_2d,
    energy_distance,
    gaussian_linear_extent,
    mean_centroid_distance,
    median_centroid_distance,
    pairwise_euclidean,
)


def test_pairwise_euclidean_matches_known_triangle():
    values = np.array([[0.0, 0.0], [3.0, 4.0]])
    distances = pairwise_euclidean(values)
    assert distances[0, 1] == pytest.approx(5.0)
    assert distances[1, 0] == pytest.approx(5.0)


def test_centroid_summaries_scale_linearly():
    values = np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
    assert mean_centroid_distance(2.0 * values) == pytest.approx(2.0 * mean_centroid_distance(values))
    assert median_centroid_distance(2.0 * values) == pytest.approx(2.0 * median_centroid_distance(values))


def test_gaussian_linear_extent_scales_linearly():
    rng = np.random.default_rng(3)
    values = rng.normal(size=(50, 3))
    assert gaussian_linear_extent(2.0 * values) == pytest.approx(2.0 * gaussian_linear_extent(values))


def test_convex_hull_area_square_and_dimension_rejection():
    square = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    assert convex_hull_area_2d(square) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="only for two features"):
        convex_hull_area_2d(np.c_[square, np.ones(4)])


def test_energy_distance_is_zero_for_identical_samples_and_symmetric():
    values = np.array([[0.0], [1.0], [2.0], [3.0]])
    shifted = values + 1.0
    assert energy_distance(values, values) == pytest.approx(0.0)
    assert energy_distance(values, shifted) == pytest.approx(energy_distance(shifted, values))
    assert energy_distance(values, shifted) > 0.0


def test_nonfinite_values_are_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        mean_centroid_distance(np.array([[0.0], [np.nan]]))
