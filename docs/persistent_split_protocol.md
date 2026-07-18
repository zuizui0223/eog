# Persistent split validation protocol

This protocol addresses issue #9 after the fitted connected-null comparison failed.

## Candidate split

For an occurrence cloud, construct the EOG MST and remove its single longest edge. The two resulting components define the candidate fragmentation split.

## Quantities

- `edge_contrast`: longest MST edge divided by the second-longest edge.
- `split_balance`: smaller component size divided by total sample size.
- `split_persistence`: median label-invariant balanced agreement between the full candidate split and candidate splits recomputed on repeated 80% subsamples.
- `gap_stability`: exponential transform of the median absolute log ratio between subsample and full raw gap strength; one is perfectly stable.

The predeclared continuous score is

`log(edge_contrast) * (split_balance / 0.5) * max(0, 2 * split_persistence - 1) * gap_stability`.

This score is benchmark-level only. It is not added to the public API unless the frozen gate passes.

## Strong-evidence rule

A cloud has strong persistent-split evidence only when all conditions hold:

- edge contrast >= 1.5;
- split balance >= 0.10;
- split persistence >= 0.80;
- gap stability >= 0.75.

## Synthetic design

Connected generators:

- Gaussian;
- heavy-tailed t;
- skewed;
- curved banana.

Fragmented generators:

- two modes;
- missing bridge.

Sample sizes are 60, 120, and 240. The primary feature set has two predeclared signal dimensions.

## Comparisons

For each sample size and fragmented generator, calculate AUC against all connected generators at the same sample size for:

- raw gap strength;
- edge contrast;
- split persistence;
- persistent-split score.

Also report strong-evidence rates for every generator and sample size.

## Frozen gate

The persistent-split score passes only if:

1. minimum AUC is at least 0.80;
2. minimum AUC improves on raw gap strength by at least 0.05;
3. maximum connected strong-evidence rate is at most 0.15;
4. minimum fragmented strong-evidence rate is at least 0.50.

A failed gate is retained as a scientific result and does not change the EOG public API.