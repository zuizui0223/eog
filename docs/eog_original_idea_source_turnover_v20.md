# Original EOG source-turnover experiment — v20

## Question

v18 showed that source count and source placement are different ecological variables.

v20 asks the temporal version:

> **If a three-source network loses one source and then gains one replacement, does
> restoring the source count restore the original distributional function?**

The graph itself is unchanged. Only source identity changes.

## Frozen loss event

Starting from the v18 clustered and dispersed three-source networks, v20 removes the
source whose loss causes the largest reduction in union reachable coverage.

The lost source cannot simply be reintroduced.

## Frozen replacement rules

One new source is chosen by each of three geometry-only rules:

- local-near-lost;
- clustered-near-survivors;
- dispersed-far-from-survivors.

All return the network to exactly three sources.

## Outputs

The replacement networks are compared for:

- union reachable coverage;
- multi-source overlap;
- worst-source-loss insurance;
- exclusive source territory;
- fraction of lost coverage recovered;
- whether replacement exceeds the original pre-loss coverage.

The design directly tests whether **source number recovery is equivalent to
distributional-function recovery**.

If the three replacement rules produce different outcomes, source turnover leaves a
spatial legacy even after the source count is restored.
