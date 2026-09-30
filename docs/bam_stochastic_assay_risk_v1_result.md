# BAM stochastic assay-risk v1 — frozen result

## Result

The preregistered Phase-VIII audit completed successfully.

- protocol commit: `a61740c21ce2ec4f92ed858a3106ca0c42e65db5`;
- workflow run: `36721046768`;
- job: `109905960456`;
- artifact: `11099281233`;
- artifact digest:
  `sha256:5522f4d860255b4b232d2d170b04ebe47a4740c93d5a6378598923abe2baa480`;
- result fingerprint:
  `545fad056cdfe3f93eca3e1a973560aeb67c605cb0ae8508ff6fc75c01b09121`.

Predeclared verdicts:

- H1 exact robustness remains impossible at finite repeat depth: **SUPPORTED**;
- H2 repetition reduces pairwise risk across the frozen 5% bound: **SUPPORTED**;
- H3 calibrated designs reach the bound for all fibers by 30 repeats: **SUPPORTED**;
- H4 quality calibration saves total synthetic action cost somewhere: **REFUTED**.

No stochastic result was used to change the Phase-VII field sets.

## Exact robustness did not return

The assay kernels have full categorical support.

Therefore, for any same-quality target-discordant ecological pair, every finite assay
sequence retains positive probability under both hypotheses.

Across all **67** frozen target-unresolved fibers:

> finite-repeat support-disjoint exact target separation = **0/67**.

This is not a failure of the repeat design.  It is the expected consequence of the
declared stochastic observation contract.

The relevant stochastic claim is instead risk-bounded distinguishability.

## Repetition crossed the pairwise 5% bound in every fiber

The frozen score is the worst target-discordant pair Bhattacharyya upper bound

[
P_e^*\le \frac{BC}{2}.
]

All fibers were above 0.05 at one reading and crossed the threshold after iid
repetition.

| target | unresolved fibers | minimum repeat depth |
|---|---:|---|
| climate shift | 18 | **8 in all 18** |
| biotic stress | 43 | **27 in all 43** |
| barrier restoration | 6 | **11 in 1; 27 in 5** |

Thus independent repetition is informative under random error even though repetition
under the fixed systematic-bias world of Phase VII was exactly redundant.

These are different observation-process statements, not contradictory results.

## Quality calibration did not reduce the repeat burden

The preregistered H4 expected at least one strict synthetic action-cost saving after
perfectly identifying whether assay accuracy was 0.7 or 0.9.

That hypothesis was false.

For every scored fiber:

- minimum repeat depth with quality calibration = minimum depth without calibration;
- strict calibration action-cost savings = **0/67**.

At the stopping depth, the worst pair was **same-quality** in every fiber.

Hence removing cross-quality ambiguity could not improve the worst-pair bound.

The bottleneck was ecological target disagreement observed under the same lower-quality
assay world.

This gives an exact decision rule for this finite setup:

> **calibration helps the worst-case pairwise criterion only if the limiting ambiguity
> crosses observation-quality worlds; it cannot improve a bottleneck that already
> exists within one quality world.**

## S11 climate example

The frozen Phase-VII fields were:

- `A_level`;
- `antagonist_excluded`.

At one reading:

- worst (BC=0.72915);
- worst (BC/2=0.36458);
- bottleneck = same `moderate_accuracy` world.

At eight iid repeats per field:

- worst (BC=0.07990);
- worst (BC/2=0.03995).

Therefore the 5% pairwise sufficient bound is crossed at **8 repeats**.

Synthetic action count:

- no quality calibration: (8\times2=16);
- with calibration: (8\times2+1=17).

Quality calibration is therefore strictly more expensive under this frozen criterion.

Exact robust separation nevertheless remains impossible at eight repeats—or at any
finite depth—because the full-support kernels still overlap.

## Phase VII versus Phase VIII

The two observation-process experiments now give a useful contrast.

### Fixed systematic miscoding

- same-assay repetition adds no new partition;
- some fibers require explicit process calibration;
- multiple assay channels can sometimes target-self-calibrate.

### iid full-support random error

- repetition reduces distributional overlap exponentially;
- exact support separation remains impossible at every finite depth;
- the frozen 5% pairwise bound is reached by repetition in all 67 fibers;
- quality calibration does not help when the worst pair lies within one quality world.

So “repeat or calibrate?” is not a generic choice.  It depends on **which observation
process creates the ambiguity** and **which inferential guarantee is being requested**.

## Boundary

The stochastic kernels are synthetic.

The 5% threshold is preregistered but not a universal ecological decision threshold.

The Bhattacharyya result is a pairwise sufficient error bound, not a global classifier
guarantee.

Do not rewrite “risk bound below 5%” as “95% certain.”
