# SW Finland colonization inference freeze

This file is a prospective extension of `docs/eog_v2_finland_colonization_preoutcome_contract.md` and is frozen **before EOG v2 reads the released `outcome` values**.

It closes the remaining numerical details needed by `benchmarks/finland_colonization_prepare.py` and the one-time scorer.

## Response-free species eligibility

A sourceful species enters the primary analysis only when the frozen response-free predictor mask contains:

- at least `5` complete potential-colonization rows; and
- rows spanning at least `2` of the frozen five island spatial folds.

This eligibility rule is evaluated before `outcome` is read. It may not be tightened or relaxed using observed success/failure counts.

The dataset-level GO rule still requires at least `100` response-free eligible species.

## Model fitting

The primary models are exactly:

- `R0` — local island predictors;
- `R1` — R0 + released historical nearest-distance and historical-range summaries;
- `R2` — R1 + reconstructed source pressure + minimum effective resistance to a historical source;
- `C` — R2 + primary fixed-source finite-depth EOG-R;
- `C_geo` — R2 + geography-only EOG-R, **sensitivity only**.

All use the same deterministic L2 logistic fit with penalty `1.0`, unpenalized intercept and training-fold-only predictor standardization. Complete island folds are held out. No model-specific feature selection is allowed.

If an outer training fold lacks both outcome classes, the frozen analysis is non-estimable for this dataset; folds are not redrawn.

## Primary inference

For every response-free eligible species, calculate its held-out mean rowwise log-loss difference:

`delta_s = loss_C,s - loss_R2,s`.

Negative values favour EOG.

Report:

- equal-weight mean `delta_s`;
- median `delta_s`;
- fraction with `delta_s < 0`;
- 95% percentile bootstrap interval of the equal-weight mean using exactly `10,000` species resamples with NumPy RNG seed `20260812`;
- pooled R0/R1/R2/C log loss and Brier scores;
- pooled C-R2 and C_geo-R2 differences as descriptive sensitivities.

The bootstrap resamples species, not rows.

## Frozen GO/NO-GO

`empirical_added_information_go` requires all of:

1. at least `100` response-free eligible species;
2. pooled held-out R2 log loss `<=` pooled held-out R0 log loss;
3. mean species `C - R2 < 0`;
4. upper 95% species-bootstrap bound `< 0`.

If condition 2 fails, status is `indeterminate_strong_reference_failure` regardless of C. R2 may not be dropped after the outcome is known.

Otherwise failure of condition 3 or 4 is `no_empirical_added_information`. The result remains frozen and visible.

`C_geo` never substitutes for C in the primary decision.

## Artifact firewall

Before outcome scoring, the response-free prepare stage must archive:

- raw CSV SHA-256;
- response-free admission fingerprint;
- source-set fingerprint;
- island-fold fingerprint;
- primary and geography-only operator fingerprints;
- exact row-key fingerprint;
- every predictor-array SHA-256;
- this file and the parent pre-outcome contract SHA-256 values;
- one feature-bundle fingerprint covering the above.

The scorer must reject any mismatch before fitting a model.
