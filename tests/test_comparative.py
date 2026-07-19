import numpy as np
import pytest

from eog import (
    RobustReference,
    fit_robust_reference,
    infer_comparative_geometry,
    infer_occupancy_geometry,
    transform_with_reference,
)


def test_reference_round_trip_and_constant_feature() -> None:
    values = np.array([[1.0, 5.0], [2.0, 5.0], [3.0, 5.0]])
    reference = fit_robust_reference(values, provenance="external training set")
    restored = RobustReference.from_dict(reference.to_dict())
    transformed = transform_with_reference(values, restored)
    assert np.allclose(transformed[:, 1], 0.0)
    assert restored.provenance == "external training set"


def test_same_reference_preserves_relative_dilation() -> None:
    rng = np.random.default_rng(42)
    compact = rng.normal(size=(120, 2))
    broad = compact * 2.5
    pooled = np.vstack([compact, broad])
    reference = fit_robust_reference(pooled, provenance="predeclared pooled reference")
    compact_geometry = infer_comparative_geometry(compact, reference)
    broad_geometry = infer_comparative_geometry(broad, reference)
    assert broad_geometry.span > 2.0 * compact_geometry.span


def test_independent_scaling_removes_global_dilation() -> None:
    rng = np.random.default_rng(7)
    compact = rng.normal(size=(120, 2))
    broad = compact * 3.0
    compact_geometry = infer_occupancy_geometry(compact)
    broad_geometry = infer_occupancy_geometry(broad)
    assert broad_geometry.span == pytest.approx(compact_geometry.span)


def test_reference_feature_dimension_is_enforced() -> None:
    reference = fit_robust_reference(np.ones((3, 2)), provenance="test")
    with pytest.raises(ValueError, match="feature dimension"):
        transform_with_reference(np.ones((3, 3)), reference)


def test_empty_provenance_is_rejected() -> None:
    with pytest.raises(ValueError, match="provenance"):
        fit_robust_reference(np.ones((3, 2)), provenance="")
