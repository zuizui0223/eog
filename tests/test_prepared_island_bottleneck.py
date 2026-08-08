import numpy as np

from eog.island_reachability import evaluate_island_reachability
from eog.prepared_island_bottleneck import prepare_island_bottleneck, evaluate_prepared_bottleneck


def test_prepared_bottleneck_matches_full_evaluator():
    node_ids = tuple(str(i) for i in range(8))
    lat = np.array([-35.0, -35.0, -35.0, -35.0, -34.8, -34.8, -34.8, -34.8])
    lon = np.array([150.0, 150.2, 150.4, 150.6, 150.0, 150.2, 150.4, 150.6])
    env = np.column_stack([lat, lon, lat * lon, lat ** 2, lon ** 2])
    training = np.array([1, 1, 1, 1, 1, 1, 0, 0], dtype=bool)
    anchors = np.array([1, 0, 0, 1, 0, 0, 0, 0], dtype=bool)
    full = evaluate_island_reachability(node_ids, lat, lon, env, training, anchors)
    prepared = prepare_island_bottleneck(node_ids, lat, lon, env, training)
    nearest, median = evaluate_prepared_bottleneck(prepared, anchors)
    np.testing.assert_allclose(nearest, full.nearest_anchor_distance_km)
    np.testing.assert_allclose(median, full.median_normalized_geographic_bottleneck, equal_nan=True)
