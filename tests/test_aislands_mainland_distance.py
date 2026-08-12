import numpy as np
import pytest

from benchmarks.build_aislands_mainland_distance import (
    minimum_spherical_polyline_distance_km,
)


def _square_ring():
    return np.asarray(
        [
            [0.0, 0.0],
            [10.0, 0.0],
            [10.0, -10.0],
            [0.0, -10.0],
            [0.0, 0.0],
        ],
        dtype=float,
    )


def test_point_to_great_circle_segment_uses_segment_interior() -> None:
    distance = minimum_spherical_polyline_distance_km(5.0, 1.0, _square_ring())
    assert distance == pytest.approx(111.195, rel=0.003)


def test_point_outside_segment_falls_back_to_endpoint() -> None:
    distance = minimum_spherical_polyline_distance_km(20.0, 0.0, _square_ring())
    assert distance == pytest.approx(1111.95, rel=0.005)


def test_point_on_mainland_ring_has_zero_distance() -> None:
    distance = minimum_spherical_polyline_distance_km(5.0, 0.0, _square_ring())
    assert distance == pytest.approx(0.0, abs=1e-8)


def test_invalid_query_coordinate_is_rejected() -> None:
    with pytest.raises(ValueError, match="outside lon/lat bounds"):
        minimum_spherical_polyline_distance_km(200.0, 0.0, _square_ring())
