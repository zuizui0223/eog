# Prior known-truth evidence for the conditional structural-value paper

This file fixes the mechanism evidence that existed **before** the new reference-saturation × response-alignment 2×2 result is opened.

## Supported before the new 2×2

### Static repeated state under dynamic truth

The frozen Layer-B v2 causal factorial directly intervened on static reuse while holding outcome realization, baseline, learner and split fixed.

Result:
- mean log-loss penalty: +0.050953
- median penalty: +0.048107
- positive replicate fraction: 92.19%

Interpretation: when the relevant latent state changes across contexts, reusing a static node-level representation can causally degrade held-out transfer in the frozen known-truth generator.

### Arbitrary label-dependent single source

The same factorial found:
- mean log-loss penalty: +0.060244
- median penalty: +0.053661
- positive replicate fraction: 95.31%

This remains relevant to representation safety but is not one of the two focal moderators in the conditional structural-value paper.

## Not supported before the new 2×2

### Train/serve generator shift as an independent cause

The predeclared positive-median hypothesis was refuted:
- mean penalty: -0.005323
- median penalty: -0.005154
- positive replicate fraction: 35.94%

Generator parity remains a conservative engineering rule, but it is not promoted as a supported ecological mechanism moderator.

### Contraction conditioning

A separate 64-replicate known-truth test asked whether pruning incompatible worlds improved the same source-symmetric sequential representation relative to retaining all declared worlds.

Result:
- conditioned minus uncontracted mean log loss: +0.001892
- median: +0.002230
- conditioned win fraction: 0.375

Contraction occurred in all replicates and the true world survived in all replicates, yet contraction conditioning did not improve prediction.

Therefore the paper must **not** use "world-set contraction" as the general explanation for favorable structural added value.

## New unresolved mechanism before opening the 2×2

The remaining untested moderator is **reference saturation**:

> Does structural augmentation lose incremental value when the conventional reference already contains the same generating structural signal?

The frozen 2×2 benchmark tests this together with the already-supported response-alignment contrast.

No historical biological response is read by that benchmark.
