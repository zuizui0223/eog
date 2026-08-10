# Tanzania held-out current-flow versus EOG benchmark

## Verification status

The first complete execution succeeded under the previously merged source, geometry, current-flow selection, scoring, and species-cluster inference contracts. Its complete quantized result projection is now frozen in `benchmarks/tanzania_heldout_expected.json`.

The numerical direction below remains **provisional until an independent full rerun reproduces the frozen result fingerprint** `df4667532ea7c7e4cfe372488d6a6cf86186cdaf19b90b6638f8a17e82dc9621`.

The first independent confirmation attempt stopped before species scoring at the upstream current-flow fingerprint gate. Direct comparison with the first-run library showed only sparse-LU noise: the largest West pairwise difference was `3.430500328249764e-11`, the largest primary-isolation difference was `3.9540282159578055e-10`, and every physical invariant and all 512 candidate distinctions were preserved. A few values straddled a seven-decimal rounding boundary, so the diagnostic cross-run hash was corrected to six decimals without changing any raw float64 current-flow value, resistance selection rule, probability model, or biological result. The correction and its post-result timing are documented in `tanzania_current_flow_fingerprint_policy.md`; a fresh full confirmation run is required.

## Strict primary contrast

Reference:

`patch area + training-selected matrix-aware current flow + area × current flow + nearest training occurrence`

Candidate:

`reference + EOG connected frequency`

Differences are candidate minus reference; negative values favor EOG.

### First execution

For primary leave-one-fragment-out validation:

- matched held-out predictions: 826;
- species: 60;
- macro mean species log-loss difference: **+0.032113119**;
- species-bootstrap 95% interval: **+0.017458000 to +0.048675011**;
- species sign-flip diagnostic: **p = 0.000030**;
- macro mean species Brier difference: **+0.004799276**;
- Brier bootstrap 95% interval: **+0.002281285 to +0.007314864**.

Thus the first execution indicates that adding the present four-scenario EOG connected-frequency feature **worsened**, rather than improved, held-out prediction relative to the already strong current-flow-plus-distance reference.

The inverse-area source-weight sensitivity has the same direction:

- macro mean species log-loss difference: **+0.030629623**;
- 95% interval: **+0.016213807 to +0.046937476**.

The geometry-only spatial-block sensitivity is weaker and uncertain:

- primary source weighting: **+0.010953824**, 95% interval **−0.012171416 to +0.033431278**;
- inverse-area weighting: **+0.005701619**, 95% interval **−0.015532523 to +0.025823893**.

## Interpretation boundary

If independently reproduced, this result would not invalidate the A-Islands conditional-reachability finding. It would show a narrower boundary: in this 14-fragment bird dataset, a coarse occurrence-anchored geographic connected-frequency feature does not add predictive value after a species-adaptive matrix-aware current-flow quantity and nearest-known-occurrence distance are already included.

It would also not establish that EOG is generally harmful, that current flow universally dominates graph methods, or that the inferred graph represents realized dispersal routes. The benchmark is deliberately small, contains only 14 surveyed fragments, and tests one frozen geography-only EOG representation against a strong matrix-aware competitor.
