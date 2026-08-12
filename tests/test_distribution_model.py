import numpy as np
import pytest

from eog.bridge import BridgeEdge
from eog.distribution_model import (
    AccessibilityConfig,
    fit_eog_distribution,
    infer_structural_accessibility,
)


def _edge(a: int, b: int, cost: float = 1.0) -> BridgeEdge:
    return BridgeEdge(
        source=a,
        target=b,
        geographic_cost=cost,
        environmental_cost=0.0,
        barrier_cost=0.0,
    )


def test_structural_accessibility_is_source_conditioned_continuous_and_zero_when_disconnected():
    edges = (_edge(0, 1), _edge(1, 2), _edge(2, 3))
    result = infer_structural_accessibility(
        5,
        edges,
        (0,),
        AccessibilityConfig(cumulative_scale=2.0, bottleneck_scale=1.0),
    )

    assert result.accessibility[0] == pytest.approx(1.0)
    assert result.accessibility[1] > result.accessibility[2] > result.accessibility[3] > 0.0
    assert result.accessibility[4] == 0.0
    assert np.isinf(result.cumulative_cost[4])
    assert np.isinf(result.bottleneck_cost[4])


def test_accessibility_respects_declared_barrier_cost():
    low_barrier = (
        BridgeEdge(0, 1, geographic_cost=1.0, environmental_cost=0.0, barrier_cost=0.0),
    )
    high_barrier = (
        BridgeEdge(0, 1, geographic_cost=1.0, environmental_cost=0.0, barrier_cost=4.0),
    )
    low = infer_structural_accessibility(2, low_barrier, (0,)).accessibility[1]
    high = infer_structural_accessibility(2, high_barrier, (0,)).accessibility[1]
    assert low > high > 0.0


def test_fit_predict_returns_distribution_map_and_separates_same_environment_by_structure():
    # Three clustered presences, followed by three absences.  Node 6 is an
    # unsampled candidate attached next to a known source; node 7 is structurally
    # disconnected.  Both prediction nodes receive exactly the same environment.
    edges = (
        _edge(0, 1),
        _edge(1, 2),
        _edge(2, 3),
        _edge(3, 4),
        _edge(4, 5),
        _edge(1, 6),
    )
    predictors = np.array([[-1.0], [1.0], [-1.0], [1.0], [-1.0], [1.0]])
    response = np.array([1, 1, 1, 0, 0, 0], dtype=float)

    model = fit_eog_distribution(
        predictors,
        response,
        n_nodes=8,
        edges=edges,
        min_class_count=3,
    )
    prediction = model.predict(
        np.array([[0.0], [0.0]]),
        node_indices=(6, 7),
    )

    assert prediction.environmental_support[0] == pytest.approx(
        prediction.environmental_support[1]
    )
    assert prediction.structural_accessibility[0] > 0.0
    assert prediction.structural_accessibility[1] == 0.0
    assert prediction.distribution_support[0] > prediction.distribution_support[1]
    assert np.all((prediction.distribution_support > 0.0) & (prediction.distribution_support < 1.0))


def test_fit_requires_multiple_sources_for_self_exclusion():
    predictors = np.array([[-1.0], [0.0], [1.0], [2.0]])
    response = np.array([1, 0, 0, 0], dtype=float)
    edges = (_edge(0, 1), _edge(1, 2), _edge(2, 3))

    with pytest.raises(ValueError, match="at least two positive source nodes"):
        fit_eog_distribution(
            predictors,
            response,
            n_nodes=4,
            edges=edges,
            min_class_count=1,
        )
