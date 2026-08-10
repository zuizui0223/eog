# Tanzania training-only current-flow selection contract

## Purpose

The Tanzania external benchmark compares EOG against a strong, species-adaptive
matrix-aware current-flow competitor. The original study selected one of 512
resistance combinations using species occurrence data. Reusing a combination
selected on all 14 fragments would leak held-out labels into the benchmark.

This contract makes the adaptation symmetric and leakage-safe: current flow may
adapt its resistance values to outer-training occurrences only, while EOG may
use outer-training occurrences only as anchors. Neither method may inspect the
held-out label before prediction.

## Training-only candidate selection

For each species and outer fold:

1. take the 512 precomputed current-flow isolation vectors;
2. restrict patch area, isolation and occurrence to outer-training fragments;
3. fit the released source model separately for every candidate:

   `occur ~ log10(area_ha) * log10(current_flow_isolation)`;

4. retain only candidates whose unpenalized binomial fit converges and has a
   finite pseudo-R2 in `[0, 1)` plus finite AIC;
5. select the minimum training AIC;
6. group AIC ties at ten decimal places and choose the lowest frozen candidate
   index.

The selection API does not accept a held-out response. If every candidate is
invalid, the species-fold is explicitly non-estimable. It may not borrow the
full-data optimum or another fold's choice.

## Held-out probability tiers

The selected current-flow vector is then reused unchanged in both probability
models.

Reference predictors:

- `log10(area_ha)`;
- `log10(selected current-flow isolation)`;
- their interaction;
- `log10(1 + nearest outer-training occurrence distance in km)`.

Candidate predictors add only:

- EOG `connected_frequency`.

Both tiers use the same deterministic L2 logistic engine, lambda 1, an
unpenalized intercept and standardization estimated from outer-training rows
only. One observation of each class is the minimum executable training set.
Training-constant predictor columns are removed and recorded. Thus a constant
EOG feature yields the same model as the reference rather than a selective
failure.

## Separation of roles

The unpenalized source GLM is used only to choose a current-flow resistance
combination within training data. The final held-out probabilities are always
refitted with the common L2 engine. The EOG candidate cannot trigger a second
current-flow selection.

## Current boundary

This stage implements and tests the selector and paired probability tiers only.
It does not execute the 60 official species, generate held-out predictions,
calculate log loss or inspect whether EOG improves performance. Those outcomes
remain sealed until this contract is merged.
