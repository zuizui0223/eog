# Experimental EOG distribution-model core (v0)

## Status

This is a **prospective development line** created after the frozen A-Islands and Tanzania structural results. It does not modify, reinterpret, rerun, or rescue those outcomes, and it is not part of the frozen structural manuscript unless independently validated later.

The purpose is to develop EOG into a distribution-modelling framework that can occupy the same workflow position as an SDM rather than remain only a post-hoc structural diagnostic.

## Target estimand

For a declared landscape node universe, EOG now separates three location-indexed objects:

1. **environmental support** `H(x)` — pointwise support from environmental predictors;
2. **structural accessibility** `M_EOG(x | A_train)` — continuous accessibility from positive training sources through the declared landscape graph;
3. **distribution support** `D_EOG(x)` — an explicit fusion of `H(x)` and `M_EOG(x | A_train)`.

This is motivated by the long-standing distinction between environmental suitability and accessibility in species-distribution theory. The present implementation is intentionally lower-assumption than a dynamic occupancy, mechanistic spread, or integrated movement model: it does not estimate colonisation, extinction, detection, demographic flow, or realised movement.

## Why this is not `connected_frequency + SDM`

The frozen empirical benchmarks showed that a single generic connected-frequency predictor is not a universally beneficial add-on to strong reference models. The new development therefore does **not** make connected frequency the central predictor.

Instead, each node receives a continuous source-conditioned field based on graph transitions:

- minimum cumulative transition cost from any positive training source;
- minimum bottleneck cost from any positive training source;
- secondary-source cost and a source-redundancy diagnostic.

For graph edge `e`, total transition cost remains explicitly decomposable through the existing EOG bridge contract:

`w_geo * geographic_cost + w_env * environmental_cost + w_barrier * barrier_cost`.

The graph is built over the complete, declared landscape node universe. Unlabelled nodes can therefore act as neutral intermediate states, but only positive training observations are anchors/sources. During held-out validation, the held-out response must not be supplied to the fit call.

## Structural accessibility v0

Let `C(x)` be the minimum cumulative path cost and `B(x)` the minimum minimax bottleneck cost from any source. Their scales are learned from finite positive costs on the declared training landscape. The v0 accessibility field is

`M_EOG(x) = exp(- mean_w[C(x)/scale_C, B(x)/scale_B])`.

Disconnected nodes receive zero accessibility. Source nodes have zero source-to-self transition cost and therefore accessibility one in the fitted full-landscape map.

`source_redundancy` is currently a separate diagnostic based on how close the second-best source cost is to the best source cost. It is **not** route redundancy or current flow and is not yet used in the v0 accessibility score.

## Distribution support v0

The pointwise environmental learner is the repository's deterministic L2 logistic support model, fitted only on labelled training nodes. Environmental support is predicted across the declared landscape.

The current distribution fusion is deliberately simple and auditable:

`D_EOG(x) = weighted_geometric_mean(H(x), M_EOG(x))`.

This keeps the method falsifiable and avoids tuning a new response calibration after seeing the frozen empirical outcomes. `D_EOG` is a unit-interval **support index**, not yet a calibrated probability.

The next development gate is to compare prospectively frozen alternatives for calibration and accessibility construction under nested spatial holdout. No alternative may be selected using the already-frozen A-Islands or Tanzania outcomes.

## Public API

```python
from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    EOGDistributionConfig,
    fit_eog_distribution,
)

model = fit_eog_distribution(
    landscape_nodes,
    observed_node_ids,
    observed_response,
    EOGDistributionConfig(
        graph_declaration=BridgeGraphDeclaration(max_geographic_km=50.0),
    ),
)

prediction = model.predict()
```

The prediction object reports, per node:

- `environmental_support`;
- `structural_accessibility`;
- `minimum_cumulative_cost`;
- `minimum_bottleneck_cost`;
- `secondary_source_cost`;
- `source_redundancy`;
- `distribution_support`.

## Validation boundary

The first synthetic contract requires two locations with the **same pointwise environmental support** to receive different distribution support when one is structurally reachable from training sources and the other lies in a disconnected component. The implementation must also be deterministic under landscape-input reordering.

Passing this contract establishes only that the new estimand is implemented correctly. It does not establish empirical superiority over SDM, current flow, dynamic occupancy, or habitat-network models.

## Next gates

1. Add spatially nested synthetic benchmarks for habitat-only, dispersal-limited, barrier, stepping-stone and long-jump generators.
2. Compare environmental-only SDM, nearest-source SDM, habitat-network/current-flow baselines, and EOG under identical outer folds.
3. Develop calibration only inside training folds; keep graph construction and source anchors leakage-safe.
4. Add a scalable raster/patch adapter so the declared node universe is not hand-assembled.
5. Only after the synthetic gate is frozen and passed, preregister a new empirical benchmark independent of the existing frozen outcomes.
