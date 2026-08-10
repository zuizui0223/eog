# Tanzania held-out current-flow versus EOG benchmark

## Verification status

The complete benchmark was independently regenerated from the official Dryad
version bytes through all 1,024 regional current-flow candidates, 60-species
training-only resistance selection, held-out prediction, scoring, and
species-cluster inference. The independent execution preserved every prediction,
group, species, contrast, selected-candidate count, confidence interval, and
p-value from the first run.

The verified result fingerprint is:

`6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`

The independent artifact-confirmation workflow completed successfully in GitHub
Actions run `31432034117`. The verified six-decimal candidate-library identity is
`3cabff50f138f7ccfe77cdbe87aefe14d5ec4dd40db15f16fb7b072cd3d01026`.

A separate audit found harmless sparse-LU differences below `3.96e-10` in the
upstream West current-flow library. Because a few values straddled a seven-decimal
rounding boundary, cross-run diagnostic hashes were corrected to six decimals;
raw float64 model inputs were never rounded or altered. The correction, its
post-result timing, and its inability to affect the biological contrast are
recorded in `tanzania_current_flow_fingerprint_policy.md`.

## Strict primary contrast

Reference:

`patch area + training-selected matrix-aware current flow + area × current flow + nearest training occurrence`

Candidate:

`reference + EOG connected frequency`

Differences are candidate minus reference; negative values favor EOG.

### Independently reproduced result

For primary leave-one-fragment-out validation:

- matched held-out predictions: 826;
- species: 60;
- macro mean species log-loss difference: **+0.032113119**;
- species-bootstrap 95% interval: **+0.017458000 to +0.048675011**;
- species sign-flip diagnostic: **p = 0.000030**;
- macro mean species Brier difference: **+0.004799276**;
- Brier bootstrap 95% interval: **+0.002281285 to +0.007314864**.

The independently reproduced result shows that adding the present four-scenario EOG connected-frequency feature **worsened**, rather than improved, held-out prediction relative to the already strong current-flow-plus-distance reference.

The inverse-area source-weight sensitivity has the same direction:

- macro mean species log-loss difference: **+0.030629623**;
- 95% interval: **+0.016213807 to +0.046937476**.

The geometry-only spatial-block sensitivity is weaker and uncertain:

- primary source weighting: **+0.010953824**, 95% interval **−0.012171416 to +0.033431278**;
- inverse-area weighting: **+0.005701619**, 95% interval **−0.015532523 to +0.025823893**.

## Interpretation boundary

This independently reproduced result does not invalidate the A-Islands conditional-reachability finding. It establishes a narrower boundary: in this 14-fragment bird dataset, a coarse occurrence-anchored geographic connected-frequency feature does not add predictive value after a species-adaptive matrix-aware current-flow quantity and nearest-known-occurrence distance are already included.

The benchmark therefore separates two claims that should not be collapsed:

1. graph configuration can carry information missing from pointwise environmental support and nearest-source distance, as in A-Islands;
2. the same generic graph feature need not improve prediction after a strong, landscape-specific connectivity model has already absorbed matrix structure, as in Tanzania.

It does not establish that EOG is generally harmful, that current flow universally dominates graph methods, or that the inferred graph represents realized dispersal routes. The benchmark is deliberately small, contains only 14 surveyed fragments, and tests one frozen geography-only EOG representation against a strong matrix-aware competitor. Any trait-informed, directed, shrinkage-based, or differently scaled extension must be treated as a new preregistered analysis rather than a rescue of this result.
