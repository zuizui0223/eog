# EOG v2.1 nested conventional genetic-reference contract

## Status

**Prospective development for future independent datasets only.**

This contract was created after the frozen Zhoushan exact-genetic validation result. It is not a re-analysis plan for Zhoushan and may not be used to replace, weaken or reinterpret that result.

Frozen Zhoushan result:

- status: `indeterminate_strong_reference_failure`;
- promotion: `false`;
- result fingerprint: `585b4b6c3a616d353e3abcfd95b5c341cb4e022da012a8d72ad310ddb9ae48cd`;
- result document: `docs/eog_v2_zhoushan_frog_independent_genetic_result.md`.

The motivation is methodological: a conventional graph reference can be biologically reasonable yet transfer poorly to a new island system. Future validation therefore selects among a **predeclared conventional reference family inside the training data**, rather than choosing a reference after inspecting outer-test performance.

## Estimand

For a future independent genetic dataset, estimate whether frozen EOG genetic predictors add held-out population-level information beyond the conventional reference that would have been selected without access to that population's genetic response.

The selector does not estimate migration direction. Symmetric FST or other symmetric genetic distances remain symmetric validation endpoints.

## Outer validation

The outer unit is a population.

For outer population `h`:

- every genetic pair involving `h` is an untouched outer-test pair;
- every pair involving `h` is excluded from conventional-reference selection;
- every pair involving `h` is excluded from fitting both the selected baseline and the baseline+EOG model.

No transformation, graph construction, distance matrix or candidate reference may use the outer-test genetic response.

## Inner conventional-reference selection

Within the outer-training populations, evaluate every predeclared conventional reference using inner leave-one-population-out validation.

For inner population `k != h`:

- inner-test pairs involve `k` but not `h`;
- inner-training pairs involve neither `h` nor `k`.

Each conventional reference is fitted alone using the common ridge regression contract. The selection loss is the **equal-weight mean inner-population MSE**, not pooled pair MSE. The reference with the smallest value is selected.

Tie rule: exact numerical ties are resolved lexicographically by the frozen candidate ID.

Candidate input order has no meaning and cannot affect the result.

## EOG firewall

EOG predictors are prohibited from conventional-reference selection.

Only after the reference has been selected inside the outer-training data are two outer models fitted:

1. selected conventional reference;
2. the same selected reference + frozen EOG continuous distance + frozen EOG disconnection indicator.

The candidate reference is identical between those two models.

## Primary contrast

For each outer population:

`delta_MSE = MSE(selected reference + EOG) - MSE(selected reference)`.

Negative values favour added EOG information.

The primary aggregate for a future empirical promotion gate is the **equal-weight mean outer-population delta MSE**. Pooled pair MSE and MAE are descriptive secondary summaries.

Any empirical confidence interval/bootstrap rule must be frozen for that dataset before its genetic response is opened.

## Conventional candidate family

The generic implementation accepts externally supplied symmetric distance matrices. It does not hard-code a candidate family because construction and admissibility are dataset-specific.

Before a future empirical response is accessed, its dataset contract must freeze the complete candidate family. Candidate classes may include, where biologically defensible and computable without genetic outcomes:

- straight-line geographic/IBD distance;
- a predeclared graph shortest-path distance;
- a predeclared effective-resistance/current-flow distance;
- a predeclared dimensionless transformation of a conventional connectivity distance.

A candidate cannot be removed because it performs poorly after genetic response access. Conversely, no new candidate can be added after response access.

## Development boundaries

The implementation must pass at least:

1. geographic known-truth: geographic reference selected;
2. conventional resistance known-truth: resistance reference selected;
3. omitted dynamic structure: EOG can improve the selected conventional baseline when EOG uniquely contains the missing structure;
4. outer-test response perturbation: changing only one outer population's genetic response does not change the reference selected for that same outer fold;
5. candidate-order invariance;
6. lexicographic exact-tie behaviour;
7. deterministic fingerprint;
8. invalid/misaligned distance rejection.

These are method-development tests, not empirical confirmation.

## Zhoushan hard boundary

The nested selector **must not be run on the frozen Zhoushan response as a replacement confirmation**. In particular it may not be used to select IBD over the failed Gabriel current-flow reference and then relabel the already-observed small IBD+EOG improvement as a successful prospective result.

Zhoushan remains exactly:

`indeterminate_strong_reference_failure`, `promotion_go = false`.

## Future promotion boundary

Nested reference selection becomes empirically relevant only after:

1. a new independent dataset is identified;
2. nodes and response-free geography/environment are frozen;
3. EOG predictors are frozen;
4. the entire conventional candidate family is frozen;
5. outer/inner folds, response transform, ridge penalty and any bootstrap rule are frozen;
6. only then is the genetic response accessed and scored once.

A null, adverse or indeterminate result remains visible and cannot trigger candidate/reference redesign on the same dataset.
