# EOG v2 frozen dynamic-occupancy confirmation result

## Outcome

**PASS — correctly specified repeated-incidence process reference retains primacy.**

One-time workflow run: `31602971494`.

Frozen source head: `7bfa0369efddb948400fb7f3f6d9845ef400fc3f`.

Contract fingerprint:

`ee967ddb36e670eb8946cce9e1c96ac51cd78b392a393cc6036958a010b31848`

Artifact ID: `9144227274`.

Artifact digest:

`sha256:14e9c415ca1c5e03b09ac3a3dbb2ce181310dbcb735ca26ef3441c32131749e1`

## Frozen confirmation design

Unused confirmation seeds:

`3301, 3407, 3511, 3607, 3701, 3803, 3907, 4001`.

The truth is a first-order repeated-incidence colonisation/persistence process. Validation holds out complete island motifs rather than individual time rows. This prevents temporal records from the same motif from appearing in both training and test sets.

Compared models:

- state + local environment;
- state + local environment + static fixed-source EOG-R;
- correctly specified dynamic occupancy/process reference using current neighbour pressure;
- dynamic process reference + static fixed-source EOG-R.

The purpose is a negative-control boundary: EOG-R must not be promoted when a repeated-incidence process model already represents the generating mechanism.

## Mean held-out performance

Mean log loss:

- state + environment: `0.5920506111`;
- state + environment + EOG-R: `0.5728218563`;
- dynamic process: `0.5402643957`;
- dynamic process + EOG-R: `0.5403882236`.

Mean Brier score:

- state + environment: `0.2017709176`;
- state + environment + EOG-R: `0.1911287464`;
- dynamic process: `0.1775955185`;
- dynamic process + EOG-R: `0.1776064631`.

## Frozen decision gates

All gates passed:

- process gain over state + environment: `0.0517862154` log loss, threshold `>= 0.03`;
- process gain over static EOG-R reference: `0.0325574606`, threshold `>= 0.02`;
- process favourable seed count: `8/8`, threshold `>= 6/8`;
- EOG increment over the correctly specified process model: `+0.0001238279`, threshold `>= -0.005`.

The last quantity is candidate-minus-reference log loss, so the small positive value is slightly adverse to adding EOG-R and is fully consistent with the no-added-information boundary.

## Interpretation

When repeated surveyed incidence exists and a correctly specified colonisation/persistence process can be estimated, that process model is the appropriate reference. EOG-R is not promoted as a replacement for dynamic occupancy or mechanistic spread modelling.

This does not invalidate EOG-R for the separate setting it was designed to address: sparse or historical island occurrence data where the estimand is frozen-source reachability, intermediate bottlenecks, route structure, survey prioritisation, or long-term connectivity support rather than one-step transition probability.

The result therefore narrows the method claim:

> EOG v2 is a graph-native source-conditioned reachability framework for structural information that is absent from local-support and simpler connectivity references; it must retreat when an appropriate repeated-incidence process model already contains the relevant dynamics.

No seed, gate, process truth, fold or EOG construction is changed after this confirmation.
