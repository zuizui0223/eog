# Layer-B v2 mechanism factorial — frozen result

This note supersedes the **mechanism ranking** section of `layer_b_mechanism_upgrade_v2.md`; it does not replace the Tampa posthoc audit, the v2 safety gate, or the closed EOG-WF manuscript boundary.

## Result

The predeclared response-free 2^3 known-truth factorial used 64 paired replicates. Within each replicate, the synthetic outcome realization, baseline features, heldout split, learner family and RF hyperparameters were identical across all eight factor cells. Only the three declared representation interventions changed.

| Intervention | Mean log-loss penalty | Median penalty | Positive replicates | Frozen verdict |
|---|---:|---:|---:|---|
| train/serve generator shift | -0.005323 | -0.005154 | 35.94% | **predeclared positive-median hypothesis refuted** |
| static repeated state under dynamic truth | +0.050953 | +0.048107 | 92.19% | supported |
| arbitrary label-dependent single source | +0.060244 | +0.053661 | 95.31% | supported |
| all three defects, 111 minus 000 | +0.137977 | +0.131643 | 100% | supported |

The clean augmented representation beat the baseline in all 64 replicates; median augmented-minus-baseline log loss was `-0.130004`.

Canonical machine-readable result: `../validation/layer_b_mechanism_v2/causal_factorial_result_v1.json`.

## What changed scientifically

The earlier posthoc ranking treated Tampa's train/serve generator mismatch as a leading mechanism candidate because it is a direct contract asymmetry. The factorial result narrows that interpretation. Under the exact frozen generator-shift intervention tested here, generator mismatch **did not independently increase median heldout log loss**. It remains a legitimate product-interface hazard and therefore stays in the v2 eligibility gate, but it is no longer independently supported as a leading causal explanation of degradation.

By contrast, two representation failures survived direct one-factor intervention tests:

1. **Static repeated state under dynamic truth.** Removing context refresh while the relevant latent state changes through context produced positive median degradation and harmed 92.19% of replicates.
2. **Arbitrary label-dependent source encoding.** Letting the prediction-facing representation change because of arbitrary node labels produced positive median degradation and harmed 95.31% of replicates.

The combined defect condition was harmful in every replicate. Therefore interaction among defects remains plausible, even though the generator-shift main effect was not supported on its own.

## Updated mechanism priority

For future response-blind empirical discrimination, including Issue #401 if its transport gate ever passes:

1. **static node-reused state vs sequential/context-refreshed state**;
2. **arbitrary sole-source vs source-symmetric prediction-facing projection**;
3. **world-set saturation vs genuine evidence-driven contraction**, because a saturated set can leave only a static spatial signature;
4. **train/serve generator parity**, retained as a conservative safety contract but not promoted as an independently demonstrated cause;
5. learner-specific calibration/interaction effects, only after the representation contrasts above.

## Boundary

This known-truth experiment does not estimate how much of Tampa's observed `+0.1010287` log-loss difference came from any mechanism. Its effect sizes are benchmark-specific. It uses no biological response, does not authorize a Tampa rerun, does not authorize a fourth fresh EOG-WF endpoint, does not change Layer A, and does not alter the frozen favorable/favorable/adverse synthesis.
