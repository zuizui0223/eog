# EOG v0.2: source-conditioned distribution model

## Status

This is a prospective development track. It does **not** alter, rerun, reinterpret, or rescue the frozen v0.1 A-Islands or Tanzania structural results. Those results remain evidence about the earlier connected-frequency feature and its declared references.

## Goal

EOG v0.2 is intended to become a distribution-modelling method that can be fitted and mapped in the same operational sense as an SDM while retaining a distinct estimand.

A conventional pointwise environmental model maps local predictors to support:

\[
x \mapsto H(x).
\]

EOG v0.2 additionally conditions every candidate node on observed training sources and the intermediate landscape graph:

\[
(x, A_{train}, G) \mapsto R(x \mid A_{train}, G),
\]

and learns a final location-indexed distribution support

\[
D_{EOG}(x) = f\{H(x), R(x), H(x)R(x)\}.
\]

`D_EOG` is a fitted distribution-support prediction. `R(x)` remains a structural accessibility index, not a realised movement, colonisation, occupancy, or dispersal probability.

## Structural accessibility field

For graph specification \(G\), EOG computes from all outer-training occurrence sources:

- minimum cumulative path cost \(C(x)\);
- minimum bottleneck path cost \(B(x)\).

The first implementation defines

\[
R(x)=\exp\left[-w_C C(x)/s_C - w_B B(x)/s_B\right],
\]

where the cost weights and scales are explicit configuration values. Disconnected nodes receive zero accessibility.

Geographic, environmental, and barrier edge costs remain separate in `BridgeEdge`; their combination is controlled by explicit `BridgeWeights`.

## Leakage boundary

Training occurrences are both response observations and structural sources, so naïve in-sample accessibility would leak the response by assigning each positive row a zero-cost path to itself.

The v0.2 fit contract therefore requires **self-source exclusion**:

- for a positive training node, its structural feature is recomputed using all other positive training nodes as sources;
- for a negative training node, all positive training nodes are sources;
- for prediction nodes, all fitted positive training nodes are sources.

At least two positive source nodes are required by this first implementation.

## Current API

```python
from eog import AccessibilityConfig, fit_eog_distribution

model = fit_eog_distribution(
    predictors,
    response,
    n_nodes=n_nodes,
    edges=edges,
    training_node_indices=training_nodes,
    accessibility_config=AccessibilityConfig(...),
)

prediction = model.predict(
    candidate_predictors,
    node_indices=candidate_nodes,
)
```

The prediction keeps the decomposition visible:

- `environmental_support`;
- `structural_accessibility`;
- `cumulative_cost`;
- `bottleneck_cost`;
- `distribution_support`.

## What this first implementation is not

It is not yet:

- a time-dynamic colonisation model;
- a latent occupancy model with detection probability;
- a point-process presence-only likelihood;
- a Bayesian posterior over graph specifications;
- a learned dispersal kernel;
- a current-flow replacement;
- a claim that path costs are realised routes.

These are possible comparators or later extensions, not properties to imply from the static v0.2 model.

## Required development sequence before public-method promotion

### Gate 1 — synthetic identifiability

Freeze generators in which local environment is deliberately non-identifying and test whether EOG separates:

1. same environment, source-connected versus disconnected target;
2. same endpoint distance, continuous versus single severe bottleneck;
3. same nearest-source distance, one versus multiple alternative routes;
4. hard barrier versus long but barrier-free route;
5. irrelevant graph complexity;
6. source sparsity and source-location perturbation.

Primary comparators:

- environmental-only logistic SDM;
- environmental + nearest-source distance;
- environmental + generic graph distance;
- EOG cumulative-only;
- EOG bottleneck-only;
- full EOG accessibility.

Do not promote one fixed accessibility formula from a development generator alone.

### Gate 2 — spatial held-out prediction

Add an outer-fold runner in which all response-derived sources and graph adaptations are rebuilt from outer-training data only. Compare matched held-out log loss and Brier score. No post-outcome graph-scale or feature rescue is allowed.

### Gate 3 — strong ecological comparators

Where data permit, compare against:

- landscape resistance / least-cost distance;
- circuit/current-flow connectivity;
- habitat-network predictors;
- spatial random-field reference;
- dynamic occupancy or mechanistic spread models when repeated temporal data support those estimands.

EOG need not dominate process-rich methods. The target niche is a source-conditioned distribution model requiring less process data than dynamic/mechanistic models while representing more intermediate landscape structure than a local environmental SDM.

### Gate 4 — independent real-data validation

Use at least one new dataset whose outcome was not involved in v0.2 development. Preserve the frozen v0.1 negative results alongside any later positive result.

## Immediate next implementation

1. add a scenario-ensemble accessibility field rather than a single graph;
2. add optional path redundancy without collapsing it into connectivity probability;
3. build the frozen synthetic comparator benchmark;
4. add outer-fold fitting/prediction that reconstructs source-conditioned features inside each fold;
5. only then evaluate a new ecological dataset.
