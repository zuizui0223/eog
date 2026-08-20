# Predictive complementarity contract

## Status

This document defines the next generic prediction-validation estimand after the fresh independent Tvärminne Daphnia result.

Daphnia established two things simultaneously:

1. the label-invariant Layer-B world-set summary contained small heldout information beyond surviving-world fraction plus mean support;
2. the same Layer-B predictor was substantially worse than the prospectively frozen strong geometry/process random forest.

Therefore the active prediction question is no longer whether standalone EOG can be made to beat a strong learner by screening another dataset.

The next valid question is:

> **Does the unchanged EOG Layer-B representation improve a prospectively frozen strong learner when it is added to that same learner, with every other feature, fit rule, split and metric held fixed?**

This is a complementarity claim, not a replacement claim.

## Paired estimand

For each heldout outer unit `u`, define:

- `S_base(u)`: score from the frozen strong learner using the frozen conventional/external feature set;
- `S_aug(u)`: score from the **same learner and fit policy** using the same conventional/external features plus the frozen EOG Layer-B representation.

Only the EOG feature block may differ.

For a lower-is-better metric such as log loss:

```text
Delta = mean_u S_aug(u) - mean_u S_base(u)
```

A prospectively declared favourable result requires both:

1. `Delta < 0` beyond any frozen tie tolerance; and
2. the augmented model wins at least the prospectively declared minimum number of outer units.

Adverse is the symmetric reverse condition. Everything else remains `no_confirmed_complementary_added_value`.

The same machinery supports higher-is-better metrics by reversing score direction only.

## Frozen identity requirements

Before response access, freeze and fingerprint:

- response endpoint;
- outer validation split/units;
- strong learner family;
- preprocessing and fit/hyperparameter policy;
- conventional/external feature set;
- EOG Layer-B feature representation;
- primary metric and score direction;
- expected outer-unit count;
- favourable minimum augmented wins;
- adverse minimum baseline wins;
- tie tolerance, if nonzero.

Changing any of these after outcome access creates a different experiment.

## Executable API

`src/eog/v2/predictive_complementarity.py` provides:

- `PredictiveComplementarityDeclaration`;
- `PairedOuterUnitScore`;
- `PredictiveComplementarityResult`;
- `evaluate_predictive_complementarity()`.

The evaluator is deliberately model-agnostic. It does not fit a random forest, logistic regression or another learner. Candidate-specific frozen runners remain responsible for producing the paired heldout scores under the same learner specification.

The evaluator requires exactly the declared number of unique outer units and finite paired scores. It canonicalizes outer-unit order before fingerprinting so result identity is not affected by row ordering.

## Scientific boundary

A favourable complementarity result would support:

> **EOG contributes predictive information that a strong conventional predictor does not already capture, under the frozen learner/feature/split contract.**

It would not show that:

- EOG is a better standalone predictor;
- EOG's connectivity machinery is generally novel;
- the surviving world is the true ecological process;
- the current Layer-B summary is optimal;
- EOG should replace strong external predictors.

An adverse result is equally informative: it would narrow EOG toward scientific update/falsification and diagnostic interpretation rather than predictive augmentation.

## Daphnia boundary

The Daphnia outcome is frozen and cannot independently validate this new estimand because `strong learner + EOG` was not the prospectively declared endpoint there.

Daphnia may be used only for technical smoke/exploratory engineering of the paired interface. Independent evidence requires a genuinely fresh system selected after this contract is frozen.

## Stop rules

1. Do not change the strong learner after seeing whether EOG helps.
2. Do not change conventional features between baseline and augmented fits.
3. Do not expose exact arbitrary world labels as supervised columns.
4. Do not tune Layer-B on Daphnia heldout outcomes and call the result prospective.
5. Do not weaken the win-count or metric rule after outcome access.
6. Preserve favourable, adverse and no-confirmed outcomes without dataset shopping.
