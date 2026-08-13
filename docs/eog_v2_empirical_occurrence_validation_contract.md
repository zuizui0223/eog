# EOG v2 prospective empirical occurrence-validation contract

## Purpose

This contract defines how a new, independent empirical occurrence dataset may be used to test the **confirmed fixed-source EOG-R method**. It does not authorize reuse of the failed source-expansion claim.

The software runner is deliberately split into two stages:

1. a **response-free feature builder** that freezes source-conditioned EOG-R and conventional reference predictors;
2. a held-out evaluator that attaches surveyed incidence outcomes only after the feature bundle is fingerprinted.

## Dataset independence

A confirmatory dataset must not have been used to design EOG v2, choose its dynamic estimator, tune graph rules, choose source policy, choose propagation depth, or set benchmark gates.

A-Islands and Tanzania are not independent v2 confirmation datasets because their results and structure informed earlier EOG development.

## Required response data

Primary occurrence validation requires surveyed incidence or another defensible binary outcome.

- Unsurveyed nodes are `NaN` / missing, not zeros.
- Presence-only background points are not biological absences.
- If detection probability is material, repeated-detection data require an appropriate occupancy/detection model rather than this binary incidence evaluator.

Frozen historical/source nodes are excluded from held-out target scoring.

## Response-free feature construction

Before the empirical response vector is attached, freeze:

- node IDs and order;
- local viability/environmental support;
- fixed source mask;
- dynamic transition operator and fingerprint;
- finite propagation depth for the occurrence estimand;
- all conventional reference predictors;
- predeclared fold IDs or the deterministic rule that produces them.

`build_fixed_source_occurrence_features` accepts none of the target response labels.

The feature fingerprint must be archived before the outcome is scored.

## Comparator ladder

The runner reports:

- viability alone;
- viability + fixed-source EOG-R;
- viability + each declared conventional reference;
- viability + each declared reference + fixed-source EOG-R.

Appropriate references may include nearest-source distance, incidence/source pressure, resistance/current-flow, or static topology, but only if they can be constructed without held-out response leakage.

## Held-out validation

Use spatially meaningful, predeclared folds. The full fold unit is held out.

The primary effect of adding EOG beyond a declared reference is:

`held-out log loss(reference + EOG) - held-out log loss(reference)`.

Negative values favour EOG.

Brier score is secondary.

## Promotion rule

The dataset-specific GO/NO-GO threshold must be frozen **after the dataset and reference set are identified but before target outcomes are inspected through this runner**.

A single positive empirical dataset is not sufficient for a universal superiority claim. Adverse or null increments must remain visible.

## Fixed source policy

The source policy for this empirical confirmation is the already confirmed **fixed-source** EOG-R estimand.

The separately tested expanded-source policy failed its one-time frozen promotion gate and may not be substituted after observing empirical outcomes.
