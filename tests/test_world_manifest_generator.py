import numpy as np
import pytest

from eog.v2.world_manifest_generator import (
    coordinate_distance_matrix,
    generate_coordinate_world_family,
)


def test_haversine_distance_matrix_uses_declared_node_order():
    node_ids = ("A", "B")
    coordinates = {"A": (0.0, 0.0), "B": (1.0, 0.0)}
    matrix = coordinate_distance_matrix(
        node_ids,
        coordinates,
        metric="haversine_km",
    )
    assert matrix.shape == (2, 2)
    assert matrix[0, 0] == 0.0
    assert matrix[1, 1] == 0.0
    assert matrix[0, 1] == pytest.approx(111.1950802, rel=1e-6)
    assert matrix[0, 1] == pytest.approx(matrix[1, 0])


def test_declared_thresholds_generate_exact_local_and_external_worlds():
    node_ids = ("A", "B", "C")
    coordinates = {
        "A": (0.0, 0.0),
        "B": (1.0, 0.0),
        "C": (3.0, 0.0),
    }
    result = generate_coordinate_world_family(
        node_ids,
        coordinates,
        metric="euclidean",
        construction_mode="declared_thresholds",
        threshold_specs=(
            {"world_id": "near", "threshold": 1.1},
            {"world_id": "far", "threshold": 3.1},
        ),
        threshold_semantics_key="distance_threshold",
        local_semantics={"operator": "symmetric_unit_support"},
        include_external_open=True,
        external_open_semantics={"supports_every_node": True},
    )

    assert set(result.worlds) == {"near", "far", "external_open"}
    assert result.structural_world_ids == ("near", "far")
    assert np.array_equal(
        result.worlds["near"],
        np.asarray(
            [
                [False, True, False],
                [True, False, False],
                [False, False, False],
            ]
        ),
    )
    assert np.all(result.worlds["external_open"][~np.eye(3, dtype=bool)])
    assert result.world_semantics["near"] == {
        "kind": "local",
        "distance_threshold": 1.1,
        "operator": "symmetric_unit_support",
    }
    assert result.world_semantics["external_open"] == {
        "kind": "external_open",
        "supports_every_node": True,
    }


def test_structural_lcc_ladder_deduplicates_identical_thresholds():
    node_ids = ("A", "B", "C", "D")
    coordinates = {
        "A": (0.0, 0.0),
        "B": (1.0, 0.0),
        "C": (2.0, 0.0),
        "D": (5.0, 0.0),
    }
    result = generate_coordinate_world_family(
        node_ids,
        coordinates,
        metric="euclidean",
        construction_mode="structural_lcc_ladder",
        axis_id="synthetic_distance",
        target_lcc_fractions=(0.25, 0.50, 0.75, 1.0),
        world_id_prefix="geo",
        deduplicate_identical_thresholds=True,
    )

    assert result.geometry_thresholds == pytest.approx((0.0, 1.0, 3.0))
    assert tuple(result.worlds) == ("geo1", "geo2", "geo3")
    assert result.structural_world_ids == ("geo1", "geo2", "geo3")


def test_geometry_can_be_replicated_across_rule_variants_without_structural_duplication():
    result = generate_coordinate_world_family(
        ("A", "B", "C"),
        {"A": (0.0, 0.0), "B": (1.0, 0.0), "C": (2.0, 0.0)},
        metric="euclidean",
        construction_mode="declared_thresholds",
        threshold_specs=(
            {"world_id": "geo1", "threshold": 1.1},
            {"world_id": "geo2", "threshold": 2.1},
        ),
        threshold_semantics_key="threshold",
        variants=(
            {
                "variant_id": "immediate",
                "semantics": {"source_mode": "immediate_previous_observed"},
            },
            {
                "variant_id": "cumulative",
                "semantics": {"source_mode": "cumulative_observed_history"},
            },
        ),
        structural_variant_id="immediate",
    )

    assert set(result.worlds) == {
        "geo1::immediate",
        "geo1::cumulative",
        "geo2::immediate",
        "geo2::cumulative",
    }
    assert result.structural_world_ids == (
        "geo1::immediate",
        "geo2::immediate",
    )
    assert np.array_equal(
        result.worlds["geo1::immediate"],
        result.worlds["geo1::cumulative"],
    )
    assert (
        result.world_semantics["geo2::cumulative"]["source_mode"]
        == "cumulative_observed_history"
    )


def test_generator_is_deterministic_for_same_declaration():
    kwargs = dict(
        metric="euclidean",
        construction_mode="declared_thresholds",
        threshold_specs=({"world_id": "w", "threshold": 2.0},),
        local_semantics={"rule": "fixed"},
    )
    coordinates = {"A": (0.0, 0.0), "B": (1.0, 0.0)}
    left = generate_coordinate_world_family(("A", "B"), coordinates, **kwargs)
    right = generate_coordinate_world_family(("A", "B"), coordinates, **kwargs)
    assert left.generator_fingerprint == right.generator_fingerprint
    assert left.fingerprint == right.fingerprint
    assert left.distance_matrix_fingerprint == right.distance_matrix_fingerprint


def test_haversine_rejects_non_wgs84_coordinates():
    with pytest.raises(ValueError, match="longitude"):
        coordinate_distance_matrix(
            ("A",),
            {"A": (181.0, 0.0)},
            metric="haversine_km",
        )


def test_variants_require_explicit_structural_representative():
    with pytest.raises(ValueError, match="structural_variant_id is required"):
        generate_coordinate_world_family(
            ("A", "B"),
            {"A": (0.0, 0.0), "B": (1.0, 0.0)},
            metric="euclidean",
            construction_mode="declared_thresholds",
            threshold_specs=({"world_id": "w", "threshold": 1.0},),
            variants=(
                {"variant_id": "a", "semantics": {}},
                {"variant_id": "b", "semantics": {}},
            ),
        )


def test_semantic_key_conflicts_fail_closed():
    with pytest.raises(ValueError, match="conflicting values"):
        generate_coordinate_world_family(
            ("A", "B"),
            {"A": (0.0, 0.0), "B": (1.0, 0.0)},
            metric="euclidean",
            construction_mode="declared_thresholds",
            threshold_specs=({"world_id": "w", "threshold": 1.0},),
            threshold_semantics_key="threshold",
            local_semantics={"threshold": 999.0},
        )
