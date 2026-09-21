# EOG development mainline

## Status

This file is the **single source of truth for the current scientific and release mainline**.

The fresh paired-complementarity validation line is now **closed**.

Frozen empirical boundary:

- fresh scored endpoints: **3**;
- endpoint pattern: **favorable / favorable / adverse**;
- scientific/protocol STOPs: **31**;
- administrative exclusions: **3**;
- fourth fresh endpoint allowed: **false**;
- candidate hunting hard stop: **true**.

Frozen product boundary:

> **Layer A remains an auditable structural compatibility / contraction / falsification framework. Layer B is a world-label-invariant, context-dependent predictive complement whose added value is not uniformly beneficial.**

Frozen submission boundary:

- primary route: **Methods in Ecology and Evolution**;
- Nature Ecology & Evolution escalation trigger: **closed**;
- primary aggregation: **endpoint-wise; no row-level pooling or common-effect claim**.

Canonical closure assets:

- [`../manuscript/paper_ready/submission_boundary.json`](../manuscript/paper_ready/submission_boundary.json)
- [`../manuscript/paper_ready/methods_results_core.md`](../manuscript/paper_ready/methods_results_core.md)
- [`../manuscript/paper_ready/fresh_endpoint_results.csv`](../manuscript/paper_ready/fresh_endpoint_results.csv)
- [`../manuscript/paper_ready/candidate_flow_table.csv`](../manuscript/paper_ready/candidate_flow_table.csv)
- [`../manuscript/paper_ready/generation_manifest.json`](../manuscript/paper_ready/generation_manifest.json)

The previous state in which no fresh post-Daphnia paired endpoint had completed is historical and must not be used to reopen candidate search.

## Scientific center

EOG keeps four objects separate:

1. **local possibility**;
2. **reachability from declared current sources**;
3. **distributional realizability under declared worlds**;
4. **historical truth**.

For a finite declared universe `W` and evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

Observed positives constrain worlds but do not identify one true route or history.

For exact finite worlds, EOG exposes:

- `possible` — reachable in at least one declared world;
- `robust` — reachable in every declared world;
- `unresolved` — possible but not robust;
- `robustly_unreachable` — unreachable in every declared world.

These statements are conditional on the declared universe. Expanding the universe may enlarge `possible` and shrink robust exclusion; adding possibilities cannot justify a stronger impossibility claim.

## Final two-layer architecture

### Layer A — exact scientific state

Retain exact world/rule identity for:

- compatibility;
- per-world support;
- evidence-driven rule elimination;
- possible / robust / unresolved / excluded interpretation;
- sequential contraction;
- finite-universe falsification;
- deterministic provenance and fingerprints.

Exact identity is required to say which declared rule was eliminated. It is **not** historical truth and is **not** the default supervised prediction representation.

### Layer B — label-invariant predictive projection

Production interface:

`src/eog/v2/world_predictive_summary.py`

Frozen `symmetric_world_support_summary_v1` features per node/horizon:

- surviving-world fraction;
- support mean / SD / min / max;
- q25 / q50 / q75;
- positive-support fraction;
- support range.

World IDs remain in Layer A and are not exposed as default supervised columns.

### Predictive endpoint — paired complementarity

Production evaluator:

`src/eog/v2/predictive_complementarity.py`

For each frozen heldout outer unit compare:

```text
strong learner + frozen conventional features
```

with:

```text
same learner + same conventional features + frozen Layer B
```

Learner family, preprocessing, hyperparameters, external features, Layer B, response endpoint, split, metric and favorable/adverse rules are frozen before response access.

The product question is deliberately narrow:

> **Does the frozen Layer-B representation add heldout information beyond the unchanged strong conventional learner in this endpoint?**

It is not a claim that EOG universally improves prediction.

## Closed fresh endpoint evidence

### Azores yellow eel telemetry

- baseline macro log loss: `0.1422727`;
- augmented macro log loss: `0.1322871`;
- paired difference: `-0.0099856` (`-7.0%`);
- augmented wins: `5/5` heldout blocks;
- terminal class: **favorable**.

### Southwest Louisiana King Rail passive acoustics

- baseline macro log loss: `0.2463173`;
- augmented macro log loss: `0.2453455`;
- paired difference: `-0.0009718` (`-0.39%`);
- augmented wins: `7/8` heldout occasions;
- terminal class: **favorable**.

Independently, all six frozen local Layer-A worlds were eventually falsified and only `external_open` survived. This is the key decoupling example: a small predictive complement can coexist with strong structural falsification without identifying a local movement mechanism.

### Tampa Bay seagrass monitoring

- baseline macro log loss: `0.3377354`;
- augmented macro log loss: `0.4387640`;
- paired difference: `+0.1010287` (`+29.9%`);
- augmented wins: `1/5` folds;
- terminal class: **adverse**.

Secondary feature-count placebo:

- 20 replicates × 10 features;
- placebo median macro log loss: `0.3361758`;
- real Layer-B augmentation beat `0%` of placebo replicates.

The placebo does not rescue the adverse primary result.

## Final interpretation

The three fresh endpoints are heterogeneous rather than uniformly favorable.

Supported:

> **Layer A is an auditable structural compatibility / falsification state, and Layer B can contain non-redundant predictive information in some systems.**

Not supported:

- universal predictive superiority;
- a standalone Layer-B predictor;
- causal identification;
- recovery of a unique dispersal history;
- truth of an exact surviving Layer-A world;
- continued candidate hunting to improve the endpoint pattern.

The final product boundary is:

`structural_diagnostic_plus_context_dependent_predictive_complement`

## Validation integrity boundary

The final denominator is part of the method result:

- **3** scored fresh endpoints;
- **31** scientific/protocol STOPs;
- **3** administrative exclusions.

Pre-response and pre-model STOPs remain integrity evidence. They are not converted into favorable, null or adverse predictive results, and opened endpoints are not repaired and rerun as independent confirmation.

Physical response-header identity, categorical response-token semantics, registry identity, source/process closure, structural adequacy, exact runtime identity and the once-only outcome-access contract remain part of the reusable validation machinery.

## Post-closure Layer-B v2 real-translation programme

A separate post-closure experiment asked whether the synthetic known-truth support for calibration-only selective promotion could translate into a genuinely fresh real ecological system. This programme is **not part of the three-endpoint EOG-WF denominator**.

Frozen synthetic result:

- `selective_promotion_known_truth_result_v1.json`: **known-truth support for calibration-only selective promotion**;
- this remains synthetic mechanism evidence only, not real-system predictive evidence.

Fresh-real attempts under unchanged `qualification v2`:

- **India tiger** — terminal pre-response transport STOP; response unopened; no model fit or outer score;
- **Illinois coyote** — terminal pre-response transport STOP; response unopened; no model fit or outer score;
- **NCRN Red-bellied Woodpecker** — passed the complete response-blind qualification path and one-shot authorization, then terminated after the single response fetch because `PointCode="2550"` was absent from the frozen points registry.

NCRN response consumption was exactly one request / `91,825,004` bytes. Site-year response construction did not complete; model fits = `0`; inner-selection decisions = `0`; outer-scoring runs = `0`; `counts_as_predictive_evidence = false`.

Therefore the post-closure real-translation programme ends with:

- scored fresh-real predictive endpoints: **0**;
- Layer-B real selective-promotion benefit / protection / harm: **unanswered**;
- known-truth selector support: **unchanged**;
- closed EOG-WF synthesis: **unchanged**;
- registry repair, alias discovery, rerun and replacement-candidate rescue: **forbidden**.

Canonical closure assets:

- [`../validation/layer_b_mechanism_v2/ncrn_final_terminal_result_v1.json`](../validation/layer_b_mechanism_v2/ncrn_final_terminal_result_v1.json)
- [`../validation/layer_b_mechanism_v2/real_translation_programme_closure_v1.json`](../validation/layer_b_mechanism_v2/real_translation_programme_closure_v1.json)

Any future real-system Layer-B translation test must be a **new separately preregistered protocol/version**. It cannot be represented as rescue or continuation of this closed programme.

## EOG-WF submission lane — frozen science, parallel administration only

The EOG-WF scientific manuscript is closed and the deterministic submission-package builder is on `main`. Remaining EOG-WF work is limited to author/admin/release completion:

1. final title page / author metadata;
2. review-ready archive or DOI/private-review link;
3. author-approved AI/LLM disclosure.

These items may proceed in parallel, but **they do not reopen scientific development, endpoint search, model fitting or claim expansion**.

## Structural paper moved to standalone repository

The Structural/reference-adequacy paper now has a separate canonical repository:

- `https://github.com/zuizui0223/Structural`

Its A-Islands and Tanzania empirical denominator, manuscript, figures, submission assets, release administration and Structural↔EGWE methodological framing are maintained there.

The Structural files retained in this EOG repository are **historical migration provenance only**, pinned by the standalone migration record to EOG commit `d7d18be0d34ba28065a947df59338e4d660a4b4c`. Do not continue Structural analysis, figure development, release preparation, author administration or journal submission from this repository.

The scientific separation remains strict:

- EOG-WF uses its frozen three-endpoint denominator: Azores / Louisiana / Tampa;
- Structural uses A-Islands original + A-Islands strong-reference + Tanzania;
- neither programme supplies extra replications for the other.

## Hard stop rules

1. **Do not select a fourth EOG-WF fresh endpoint.**
2. Do not rerun opened/stopped EOG-WF systems and relabel them independent confirmation.
3. Do not add a favorable case to change the EOG-WF `favorable / favorable / adverse` pattern.
4. Do not expose arbitrary exact world labels as default supervised EOG-WF features.
5. Do not change learner family, hyperparameters or conventional features between paired EOG-WF fits.
6. Do not identify a surviving world as historical truth.
7. Do not claim universal robustness outside the declared finite-world certificate.
8. Do not pool EOG-WF endpoint rows to manufacture a common-effect predictive claim.
9. New response-independent synthetic exposition may clarify an already-frozen method property but cannot reopen or alter an empirical endpoint decision.
10. Do not repair or rerun the consumed NCRN attempt; any future Layer-B real translation requires a new protocol version.

The current EOG mainline is therefore:

> **keep EOG-WF scientifically frozen, complete only its author/admin/release gates, and submit it to Methods in Ecology and Evolution without reopening endpoint search or method expansion. Structural work belongs exclusively in the standalone Structural repository.**
