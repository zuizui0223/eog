import math

import pytest
import shapefile

from benchmarks.audit_aislands_polygon_area import spherical_polygon_area_km2


def _polygon(parts):
    shape = shapefile.Shape(shapeType=shapefile.POLYGON)
    shape.points = []
    shape.parts = []
    for ring in parts:
        shape.parts.append(len(shape.points))
        shape.points.extend(ring)
    return shape


def test_one_degree_equatorial_polygon_has_expected_area() -> None:
    # Clockwise exterior ring. A one-degree square at the equator is about
    # 12.36 thousand km2 on a sphere with R=6371 km.
    shape = _polygon([
        [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
    ])
    area, signed = spherical_polygon_area_km2(
        shape,
        center_longitude_deg=0.5,
        center_latitude_deg=0.5,
    )
    assert len(signed) == 1
    assert area == pytest.approx(12364.0, rel=0.02)


def test_counteroriented_hole_subtracts_from_exterior() -> None:
    exterior = [
        (-1.0, -1.0), (-1.0, 1.0), (1.0, 1.0), (1.0, -1.0), (-1.0, -1.0)
    ]
    hole = [
        (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5), (-0.5, -0.5)
    ]
    outer_shape = _polygon([exterior])
    holed_shape = _polygon([exterior, hole])
    outer_area, _ = spherical_polygon_area_km2(
        outer_shape, center_longitude_deg=0.0, center_latitude_deg=0.0
    )
    holed_area, signed = spherical_polygon_area_km2(
        holed_shape, center_longitude_deg=0.0, center_latitude_deg=0.0
    )
    assert len(signed) == 2
    assert signed[0] * signed[1] < 0
    assert 0.0 < holed_area < outer_area


def test_multipart_exteriors_add_when_oriented_consistently() -> None:
    west = [
        (-2.0, -0.5), (-2.0, 0.5), (-1.0, 0.5), (-1.0, -0.5), (-2.0, -0.5)
    ]
    east = [
        (1.0, -0.5), (1.0, 0.5), (2.0, 0.5), (2.0, -0.5), (1.0, -0.5)
    ]
    multi = _polygon([west, east])
    west_only = _polygon([west])
    east_only = _polygon([east])
    total, signed = spherical_polygon_area_km2(
        multi, center_longitude_deg=0.0, center_latitude_deg=0.0
    )
    west_area, _ = spherical_polygon_area_km2(
        west_only, center_longitude_deg=-1.5, center_latitude_deg=0.0
    )
    east_area, _ = spherical_polygon_area_km2(
        east_only, center_longitude_deg=1.5, center_latitude_deg=0.0
    )
    assert len(signed) == 2
    assert math.copysign(1.0, signed[0]) == math.copysign(1.0, signed[1])
    assert total == pytest.approx(west_area + east_area, rel=0.002)


def test_nonpolygon_shape_is_rejected() -> None:
    shape = shapefile.Shape(shapeType=shapefile.POINT)
    shape.points = [(0.0, 0.0)]
    with pytest.raises(ValueError, match="not one of"):
        spherical_polygon_area_km2(
            shape, center_longitude_deg=0.0, center_latitude_deg=0.0
        )
