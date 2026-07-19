import numpy as np
import pytest

from eog import compare_geometry, fit_robust_reference, reference_fingerprint


def test_span_contrast_recovers_dilation():
    rng = np.random.default_rng(4)
    a = rng.normal(size=(120, 2))
    b = 2.0 * rng.normal(size=(120, 2))
    reference = fit_robust_reference(a, provenance="training-only baseline")
    result = compare_geometry(a, b, reference, n_resamples=80, random_state=2)
    assert result.estimate > 0.45
    assert result.direction_stability > 0.95
    assert result.reference_fingerprint == reference_fingerprint(reference)


def test_tree_metric_requires_support_class():
    rng = np.random.default_rng(1)
    a = rng.normal(size=(50, 2))
    b = rng.normal(size=(50, 2))
    reference = fit_robust_reference(a, provenance="external")
    with pytest.raises(ValueError, match="support_class"):
        compare_geometry(a, b, reference, metric="continuity", n_resamples=30)


def test_null_comparison_is_not_forced_directional():
    rng = np.random.default_rng(8)
    a = rng.normal(size=(100, 2))
    b = rng.normal(size=(100, 2))
    reference = fit_robust_reference(np.vstack([a, b]), provenance="pooled descriptive")
    result = compare_geometry(a, b, reference, n_resamples=100, random_state=9)
    assert result.ambiguous
