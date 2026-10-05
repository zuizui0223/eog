# Original EOG history-observability experiment — v22

## Question

v21 fixes the final source set and graph while varying only source activation order.

The final equilibrium occupancy can therefore forget history even when the
earliest-source provenance map remembers it.

v22 asks:

> **How much post-activation temporal observation is needed to recover that hidden
> history?**

## Avoiding a trivial test

The three source activations occur at structural times 0, 2 and 4.

Snapshots begin only at t4, when all three source identities are already active.

Source nodes themselves are removed from the observed snapshot.

Thus the benchmark cannot identify history simply by seeing which source has not yet
activated.

## Frozen snapshot library

Complete non-source occupancy snapshots are available at:

- t4;
- t5;
- t6;
- t8.

For each row/design, exact subset search finds the smallest snapshot set sufficient for:

1. full activation-history identity;
2. the coarser equilibrium provenance class.

The equilibrium occupancy map is audited separately as a negative control and is
identical by construction.

## Why target specificity matters

If two activation histories induce the same equilibrium provenance map, distinguishing
them is unnecessary when provenance is the ecological target.

v22 therefore asks whether the target-sufficient history quotient needs fewer temporal
observations than full history identity.
