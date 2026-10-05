# Original EOG multi-source placement experiment — v18 result

## Result

All eight preregistered hypotheses were supported.

The result gives a more precise version of the source-population idea:

> **source number does not determine what a source network does. Placement controls a
> coverage–insurance tradeoff.**

Authoritative execution:

- run: `37251518108`;
- artifact: `11321111760`;
- artifact digest:
  `sha256:82fa7504b46b94369f787888be5d6c1a5e8d3caff622a8e686b23dc57007f9d2`;
- result fingerprint:
  `f039164f427f52f3d8b0ebd78705056c723689933a96cfd5740417f0f8f90089`.

## Same number, different landscape

With two sources, clustered versus dispersed placement changed reachable coverage in
**347/384** randomized directed landscapes.

Mean reachable fraction:

- clustered two-source: **0.404**;
- dispersed two-source: **0.445**.

So the same source count produced different realised accessibility.

## Coverage and insurance pointed in opposite directions

Dispersed placement increased coverage by **4.12 percentage points** on average.

But clustered placement produced far more overlap between source basins:

- clustered two-source overlap: **0.640**;
- dispersed: **0.078**.

And clustered placement was much more robust to losing the worst source:

- clustered worst-source-loss retention: **0.693**;
- dispersed: **0.264**.

The mean clustered-minus-dispersed insurance contrast was **+0.429**.

Thus the source geometry that maximized spatial coverage was not the geometry that
maximized source-loss insurance.

## Fewer sources can cover more

The strongest count-versus-placement comparison was also supported.

In **225/384** landscapes:

> **two dispersed sources reached more nodes than three clustered sources.**

Source count is therefore not even ordinal with reachable coverage once placement is
allowed to differ.

## The tradeoff was common

A row simultaneously counted as a coverage–insurance tradeoff when:

- dispersed two-source coverage > clustered two-source coverage; and
- clustered two-source worst-source-loss retention > dispersed.

This occurred in **280/384** landscapes.

The same qualitative direction appeared in every secondary stratum.

### Barrier density

Dispersed-minus-clustered coverage:

- 0.05: +0.054;
- 0.20: +0.043;
- 0.35: +0.026.

Clustered-minus-dispersed insurance:

- 0.05: +0.536;
- 0.20: +0.431;
- 0.35: +0.321.

### Environmental autocorrelation

Coverage advantage of dispersed sources remained positive under both low and high
autocorrelation.

Insurance advantage of clustered sources also remained positive under both.

### Rook and queen neighbourhoods

Both source-placement effects kept the same sign under both geographic graph rules.

These are secondary diagnostics, not new tests.

## More sources still helped monotonically

The exact nested-source checks had zero violations:

- adding a source never reduced union reachability;
- adding a source never reduced the absolute number of nodes reachable from at least
  two sources.

So the finding is not that source number is irrelevant.

It is that **source count and source geometry answer different ecological questions**.

## Source attribution

Clustered sources caused extensive basin overlap. Many downstream nodes could be
reached from multiple sources.

This improves structural insurance but makes source attribution more ambiguous.

Dispersed sources made more nodes reachable from exactly one source, increasing
coverage while preserving more source-specific territories.

## Corrected ecological statement

For a species surviving in only a few source populations, asking only how many sources
remain is incomplete.

At fixed count:

- dispersed sources can maximize reachable extent;
- clustered sources can maximize redundancy against source loss;
- the better arrangement depends on whether the target is expansion coverage or
  persistence insurance.

This is the multi-source distributional-watershed result the original EOG idea was
trying to capture.
