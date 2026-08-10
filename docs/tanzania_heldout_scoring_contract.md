# Tanzania benchmark: held-out scoring contract

This document freezes the predictive scoring hierarchy before any species-level EOG outcome is inspected.

The published dataset contains only 14 forest fragments. That sample size makes thresholded classification summaries and per-species AUC unstable as primary evidence, especially for species near the minimum class-support boundary. The primary evaluation therefore uses continuous held-out probabilistic scores.

## Primary score

For every executable species x held-out site prediction, record Bernoulli log loss (equivalently held-out binomial deviance up to a constant factor):

`- [ y * log(p) + (1-y) * log(1-p) ]`

Probabilities must be clipped only by one globally frozen numerical epsilon used for all methods; epsilon is a numerical-stability setting, not a tunable threshold.

Primary method comparison is the paired difference in held-out log loss on the exact same executable species/site predictions. Lower is better.

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

A method may not improve its apparent score by silently dropping difficult species/folds. Pairwise contrasts use the intersection of predictions that are valid for both methods, while method-specific applicability is reported separately.

## Aggregation

Because predictions are clustered within species, the primary summary is not a naive site-level standard error. Report:

1. mean paired held-out log-loss difference across all matched predictions;
2. species-level mean difference distribution;
3. a species-cluster bootstrap or equivalent species-level resampling interval, with the resampling rule frozen before outcomes;
4. East/West study-region summaries as diagnostics after verified region mapping, not as separately tuned analyses.

## Model-role symmetry

- Local and simple-isolation regression coefficients are fit on training data only.
- Fold-safe current-flow resistance selection and regression use training data only.
- EOG anchors/local support use training data only.
- Held-out labels are used only once: to score the frozen prediction.

## Paper reproduction remains separate

The published full-data AIC/pseudo-R2 reproduction is an implementation sanity check. It must never be mixed with the held-out predictive score table.

## Decision interpretation

Evidence for incremental EOG value requires lower held-out log loss for `local + fold-safe current flow + EOG` than for `local + fold-safe current flow` on matched predictions, with uncertainty reported across species. A null or adverse difference is a valid boundary result.

No held-out Tanzania outcome is computed in this contract.
