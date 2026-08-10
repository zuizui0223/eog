# Tanzania benchmark: held-out scoring contract

This document freezes the predictive scoring hierarchy before any species-level EOG outcome is inspected.

The published dataset contains only 14 forest fragments. That sample size makes thresholded classification summaries and per-species AUC unstable as primary evidence, especially for species near the minimum class-support boundary. The primary evaluation therefore uses continuous held-out probabilistic scores.

## Primary score

For every executable species x held-out site prediction, record Bernoulli log loss (equivalently held-out binomial deviance up to a constant factor):

`- [ y * log(p) + (1-y) * log(1-p) ]`

Probabilities must be clipped only by one globally frozen numerical epsilon used for all methods; epsilon is a numerical-stability setting, not a tunable threshold.

Primary method comparison is the paired difference in held-out log loss on the exact same executable species/site predictions. Differences are always `candidate - reference`, so negative values favor the candidate.

## Secondary scores

Report, where estimable:

- Brier score, paired on the same held-out predictions;
- held-out deviance explained relative to the local patch baseline;
- AUC only as a secondary discrimination summary for species with both held-out classes represented;
- calibration slope/intercept only when the number and spread of held-out predictions are sufficient, otherwise mark non-estimable.

No classification threshold, sensitivity/specificity cutoff, or Youden-style optimization is primary.

## Applicability accounting

Every comparison must report:

- total 89 source species;
- source-eligible species under the frozen class-support rule;
- species/folds executable for every tier being paired;
- failures by reason (single-class training fold, source-formula failure, circuit fit failure, EOG graph/support failure, numerical failure, or missing verified alignment);
- the exact paired denominator used for each method contrast.

A method may not improve its apparent score by silently dropping difficult species/folds. Pairwise contrasts use the intersection of predictions that are valid for both methods, while method-specific applicability is reported separately. Nonfinite placeholder probabilities are permitted only where that method's explicit validity mask is false; every probability marked valid must be finite and lie in `[0, 1]`.

## Frozen replication unit and uncertainty

Species, not individual held-out sites, are the biological replication unit for inference.

For each comparison:

1. Compute candidate-minus-reference log-loss differences on the exact matched valid species-site predictions.
2. Average those differences within each species.
3. Use the equal-weight mean of the per-species means as the primary inferential point estimate (`macro_mean_species_difference`).
4. Also report the observation-weighted mean across all matched predictions (`micro_mean_difference`) as a descriptive diagnostic, not as the clustered inferential estimand.

This prevents species with more executable held-out folds from receiving greater inferential weight merely because they contributed more predictions.

The interval is frozen as a species-cluster percentile bootstrap:

- resampling unit: species;
- bootstrap replicates: **10,000**;
- seed: **20260810**;
- interval: **95% percentile interval** using the 0.025 and 0.975 quantiles;
- each selected species contributes its already-computed mean difference once per bootstrap draw;
- sites are not independently resampled and no nested site bootstrap is used.

A two-sided Monte Carlo sign-flip test of the equal-weight species mean is retained as a secondary null diagnostic:

- sign-flip replicates: **100,000**;
- seed: **20260810**;
- statistic: absolute equal-weight mean of per-species differences;
- p-value correction: `(extreme + 1) / (replicates + 1)`.

The sign-flip test assumes symmetry of species-level effects and therefore does not replace the effect size and bootstrap interval. No resampling count, seed, weighting rule, interval type, or test direction may be changed after inspecting Tanzania outcomes.

## Model-role symmetry

- Local and simple-isolation regression coefficients are fit on training data only.
- Fold-safe current-flow resistance selection and regression use training data only.
- EOG anchors/local support use training data only.
- Held-out labels are used only once: to score the frozen prediction.

## Paper reproduction remains separate

The published full-data AIC/pseudo-R2 reproduction is an implementation sanity check. It must never be mixed with the held-out predictive score table.

## Decision interpretation

The strict incremental contrast is:

`local + fold-safe current flow + EOG` minus `local + fold-safe current flow`.

A negative species-macro log-loss difference favors EOG. The effect estimate, 95% species-cluster bootstrap interval, exact paired denominator, applicability profile, and secondary sign-flip p-value must all be reported. A null or adverse difference is a valid boundary result.

No held-out Tanzania outcome is computed in this contract.
