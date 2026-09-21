import pytest

from eog.v2.coordinate_registry import (
    CoordinateObservation,
    CoordinateRegistryPolicy,
    audit_coordinate_registry,
)


def test_exact_repeated_coordinates_form_exact_registry():
    result = audit_coordinate_registry(
        (
            CoordinateObservation("A", 140.0, 38.0),
            CoordinateObservation("A", 140.0, 38.0),
            CoordinateObservation("B", 141.0, 39.0),
        ),
        CoordinateRegistryPolicy(
            tolerance=0.0,
            units="degrees",
            representative_policy="median",
        ),
    )
    assert result.status == "exact_registry"
    assert result.exact_node_count == 2
    assert result.tolerance_used_node_count == 0
    assert result.coordinates["A"] == pytest.approx((140.0, 38.0))


def test_declared_tolerance_accepts_bounded_drift_and_reports_it():
    result = audit_coordinate_registry(
        (
            CoordinateObservation("A", 140.0000, 38.0000),
            CoordinateObservation("A", 140.0004, 38.0002),
            CoordinateObservation("A", 140.0002, 38.0001),
            CoordinateObservation("B", 141.0, 39.0),
        ),
        CoordinateRegistryPolicy(
            tolerance=0.0005,
            units="degrees",
            representative_policy="median",
        ),
    )
    assert result.status == "within_frozen_tolerance"
    assert result.tolerance_used_node_count == 1
    assert result.maximum_x_span == pytest.approx(0.0004)
    assert result.maximum_y_span == pytest.approx(0.0002)
    assert result.coordinates["A"] == pytest.approx((140.0002, 38.0001))


def test_full_span_not_pairwise_step_controls_drift():
    with pytest.raises(ValueError, match="exceeds frozen tolerance"):
        audit_coordinate_registry(
            (
                CoordinateObservation("A", 0.0, 0.0),
                CoordinateObservation("A", 0.4, 0.0),
                CoordinateObservation("A", 0.8, 0.0),
            ),
            CoordinateRegistryPolicy(
                tolerance=0.5,
                units="native",
                representative_policy="mean",
            ),
        )


def test_representative_policy_is_explicit():
    observations = (
        CoordinateObservation("A", 0.0, 0.0),
        CoordinateObservation("A", 0.2, 0.4),
        CoordinateObservation("A", 1.0, 1.0),
    )
    policy_mean = CoordinateRegistryPolicy(
        tolerance=1.0,
        units="native",
        representative_policy="mean",
    )
    policy_median = CoordinateRegistryPolicy(
        tolerance=1.0,
        units="native",
        representative_policy="median",
    )
    mean = audit_coordinate_registry(observations, policy_mean)
    median = audit_coordinate_registry(observations, policy_median)
    assert mean.coordinates["A"] == pytest.approx((0.4, 1.4 / 3))
    assert median.coordinates["A"] == pytest.approx((0.2, 0.4))
    assert mean.policy_fingerprint != median.policy_fingerprint


def test_first_policy_preserves_frozen_source_order():
    observations = (
        CoordinateObservation("A", 0.2, 0.3),
        CoordinateObservation("A", 0.1, 0.2),
    )
    result = audit_coordinate_registry(
        observations,
        CoordinateRegistryPolicy(
            tolerance=1.0,
            units="native",
            representative_policy="first",
        ),
    )
    assert result.coordinates["A"] == pytest.approx((0.2, 0.3))


def test_nonfinite_coordinates_are_rejected():
    with pytest.raises(ValueError, match="must be finite"):
        CoordinateObservation("A", float("nan"), 0.0)


def test_negative_tolerance_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        CoordinateRegistryPolicy(
            tolerance=-1.0,
            units="degrees",
            representative_policy="median",
        )


def test_invalid_representative_policy_is_rejected():
    with pytest.raises(ValueError, match="representative_policy"):
        CoordinateRegistryPolicy(
            tolerance=0.0,
            units="degrees",
            representative_policy="snap",
        )


def test_audit_is_deterministic_for_same_frozen_input():
    observations = (
        CoordinateObservation("B", 1.0, 1.0),
        CoordinateObservation("A", 0.0, 0.0),
        CoordinateObservation("A", 0.1, 0.1),
    )
    policy = CoordinateRegistryPolicy(
        tolerance=0.2,
        units="native",
        representative_policy="median",
    )
    left = audit_coordinate_registry(observations, policy)
    right = audit_coordinate_registry(observations, policy)
    assert left.fingerprint == right.fingerprint
    assert tuple(node.node_id for node in left.nodes) == ("A", "B")
