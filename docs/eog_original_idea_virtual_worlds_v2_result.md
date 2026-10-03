# Original EOG randomized virtual worlds — v2 result

## Result

Seven of eight preregistered hypotheses were supported.

The important result is the one that failed: **G2 was refuted in the opposite
direction**.

## Strong generalities in the frozen generator

### Suitable does not mean reachable

Increasing barrier density from 0.05 to 0.35 increased mean locally-permissive but
unreachable nodes from **0.258 to 0.583**.

The increase was nondecreasing in all four autocorrelation × neighbourhood strata.

### Sparse landscapes create stepping-stone dependence

Critical stepping-node fraction:

- rook: **0.359**;
- queen: **0.229**.

### Wider neighbourhoods create route redundancy

Single-node-robust reachable-target fraction:

- rook: **0.487**;
- queen: **0.536**.

Thus stepping stones and route redundancy are two sides of the same landscape
connectivity problem.

### Static occurrence history is highly non-identifying

Median static source-history alias count: **21**.

So even in the randomized panel, a final reachable component usually admitted many
possible source histories.

### Time carries substantial additional information

Among 355 eligible rows, the median contraction of source-history aliases after the
frozen early-positive temporal constraints was **0.815**.

This supports the original idea that a distribution is more informative when treated as
a realised transition history rather than an unordered occurrence cloud.

### Impossibility has multiple causes

Among currently unreachable locally permissive targets:

- barrier-only rescue: **1,687**;
- environment-only rescue: **805**;
- either single axis sufficient: **825**;
- both barrier and environment required: **623**;
- not rescued by either edge relaxation: **897**.

So “unreachable” is not one state.  Reverse diagnosis can distinguish different missing
conditions even before one mechanism is declared true.

## The G2 refutation

Predeclared G2 expected low environmental autocorrelation to create more endpoint-similar
but pathwise-blocked pairs.

Observed means were:

- low autocorrelation: **0.052**;
- high autocorrelation: **0.232**.

The direction reversed in all six neighbourhood × barrier strata.

G2 remains **REFUTED**.

## Why the reversal matters

A secondary generator-only diagnostic shows that the frozen environmental transition
rule was relative: each landscape used the 70th percentile of its own edge differences.

Mean absolute q70 tolerance:

| field | rook | queen |
|---|---:|---:|
| low autocorrelation | 1.521 | 1.531 |
| high autocorrelation | 0.124 | 0.142 |

Smoothing made neighbouring environments more similar, but because the analysis
renormalized the threshold inside each landscape it also made the allowed absolute
transition difference roughly an order of magnitude tighter.

This is not a rescue of G2. It reveals a deeper original-EOG issue:

> **A conclusion about environmental continuity can change because the analyst's rule
> for turning environmental differences into traversability changes with the
> landscape.**

That is exactly the analyst-world problem that motivated set-valued EOG inference.

## Next question

The next phase should hold the latent landscapes fixed and vary the **analytical
translation from environment to traversability**.

The target is no longer “which autocorrelation is worse?” It is:

> Which occurrence-relation / impossibility conclusions survive disagreement among
> reasonable response-independent environmental transition rules?

That is a direct virtual-world test of robustness to analyst choices.
