# Experimental EOG distribution-model core (v0.1)

## Status

This is a **prospective development line** created after the frozen A-Islands and Tanzania structural results. It does not modify, reinterpret, rerun, or rescue those outcomes, and it is not part of the frozen structural manuscript unless independently validated later.

The purpose is to develop EOG into a distribution-modelling framework that can occupy the same workflow position as an SDM rather than remain only a post-hoc structural diagnostic.

## Target estimand

For a declared landscape node universe, EOG separates three location-indexed objects:

1. **environmental support** `H(x)` — pointwise support from environmental predictors;
2. **structural accessibility** `M_EOG(x | A_train)` — continuous accessibility from positive training sources through the declared landscape graph;
3. **distribution support** `D_EOG(x)` — environmental support after a training-estimated structural accessibility gate.

The present implementation is intentionally lower-assumption than a dynamic occupancy, mechanistic spread, or integrated movement model: it does not estimate colonisation, extinction, detection, demographic flow, or realised movement.

## Why this is not `connected_frequency + SDM`

The frozen empirical benchmarks showed that a single generic connected-frequency predictor is not a universally beneficial add-on to strong reference models. The new development therefore does **not** make connected frequency the central predictor and does not retune the frozen feature.

Instead, each node receives a continuous source-conditioned field based on graph transitions:

- minimum cumulative transition cost from any positive training source;
- minimum bottleneck cost from any positive training source;
- secondary-source cost and a source-redundancy diagnostic.

For graph edge `e`, total transition cost remains explicitly decomposable through the existing EOG bridge contract:

`w_geo * geographic_cost + w_env * environmental_cost + w_barrier * barrier_cost`.

The graph is built over the complete, declared landscape node universe. Unlabelled nodes can therefore act as neutral intermediate states, but only positive training observations are anchors/sources. During held-out validation, the held-out response must not be supplied to the fit call.

## Structural accessibility v0.1

Let `C(x)` be the minimum cumulative path cost and `B(x)` the minimum minimax bottleneck cost from any source. Their scales are learned from finite positive costs on the declared landscape. The v0.1 accessibility field is

`M_EOG(x) = exp(- mean_w[C(x)/scale_C, B(x)/scale_B])`.

Disconnected nodes receive zero accessibility. Source nodes have zero source-to-self transition cost and therefore accessibility one in the final fitted landscape map.

`secondary_source_cost` is also retained. `source_redundancy` summarizes how close the second-best source cost is to the best source cost. It is **not** route redundancy, current flow, or evidence of realised multiple dispersal routes and is not yet used in the accessibility score.

## Shrinkable structural gate

EOG must not force a structural penalty onto species whose distributions are already explained by local environment. The distribution layer therefore estimates a scalar structural gate `lambda` in `[0, 1]`:

`D_EOG(x) = H(x) * ((1 - lambda) + lambda * M_EOG(x))`.

This gives two exact boundaries:

- `lambda = 0`: `D_EOG(x) = H(x)` and the model reduces exactly to the pointwise environmental SDM;
- `lambda = 1`: `D_EOG(x) = H(x) * M_EOG(x)` and full structural accessibility is required.

When `structural_gate_weight` is not supplied explicitly, `lambda` is estimated on training observations only by a deterministic grid search minimizing binary log loss plus an optional shrinkage penalty. Ties retain the smaller `lambda`, so unsupported structural complexity collapses toward the environmental model.

Positive training rows are themselves source anchors. Allowing a source to use its zero-cost self path while learning `lambda` would leak its own response into the structural gate. EOG therefore uses the **second-best distinct source path** for positive training rows during gate fitting. The final landscape prediction still uses the ordinary best-source field.

This training-only gate is an initial development implementation. A stronger version should inner-cross-fit both `H(x)` and the gate inside each outer training fold before empirical confirmation.

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
print(model.structural_gate_weight)
```

The prediction object reports, per node:

- `environmental_support`;
- `structural_accessibility`;
- `minimum_cumulative_cost`;
- `minimum_bottleneck_cost`;
- `secondary_source_cost`;
- `source_redundancy`;
- `distribution_support`.

The fitted model additionally records whether the structural gate was estimated or fixed, the fitted gate weight, training gate loss, full graph fingerprint, source IDs, and environmental reference.

## Current synthetic validation contracts

### Structural estimand discrimination

The low-level contract fixes `lambda=1` and constructs targets with identical pointwise environmental support and identical direct source distance but different intermediate landscape structure. The required ordering is:

`open bridge > high-cost barrier bridge > disconnected target`.

### Training-fitted structural activation

A replicated held-out benchmark supplies training examples in which high environmental support alone cannot distinguish occurrence from structural non-occurrence. Target labels are withheld. The current frozen synthetic design requires:

- environmental-only held-out AUC = 0.5;
- environmental + nearest-source held-out AUC = 0.5;
- EOG structural accessibility AUC = 1.0;
- EOG distribution-support AUC = 1.0;
- a nontrivial training-fitted structural gate.

The first training-fitted implementation selected `lambda = 1.0` under this deliberately structure-dependent generator.

### Environmental fallback

A complementary generator makes structural accessibility identically one and makes occurrence depend only on the environmental predictor. The required behavior is:

- training-fitted `lambda = 0`;
- `D_EOG` equals `H` exactly;
- environmental predictive ordering is retained.

Together, the two gate contracts test the intended model class rather than a one-way advantage: EOG can activate structural constraints when the training process requires them and collapse exactly to an environmental SDM when they carry no information.

## Validation boundary

These synthetic contracts establish estimand implementation, leakage guards, deterministic behavior, structural activation, and environmental fallback. They do **not** establish empirical superiority over SDM, current flow, dynamic occupancy, habitat-network models, or mechanistic dispersal models.

The existing A-Islands and Tanzania outcomes cannot be used to select future v0.1 accessibility or calibration variants. Any empirical test of this new distribution-model line requires a new pre-outcome contract.

## Next gates

1. Add nested synthetic generators for habitat-only, dispersal-limited, graded-barrier, stepping-stone, long-jump, and mixed processes with noise rather than perfect separation.
2. Add **inner cross-fitting** for structural-gate estimation so both environmental support and gate tuning are out-of-fold within each outer training set.
3. Compare environmental-only SDM, nearest-source SDM, patch/network or current-flow baselines, and EOG under identical outer spatial folds.
4. Test sensitivity to graph scale, environmental-edge scale, barrier misspecification, prevalence, sparse sources, and unlabelled-node density.
5. Add a scalable raster/patch adapter so the declared node universe is not hand-assembled.
6. Only after the synthetic benchmark family and comparator hierarchy are frozen, preregister a new empirical benchmark independent of the existing frozen outcomes.
