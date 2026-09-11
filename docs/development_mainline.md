# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

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

## Active scientific milestone — structural/island second paper

The active scientific-development line is now the separate structural/island manuscript governed by:

- [`../manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json`](../manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json)
- [`../manuscript/structural_reachability_manuscript.md`](../manuscript/structural_reachability_manuscript.md)
- [`../manuscript/structural_submission_checklist.md`](../manuscript/structural_submission_checklist.md)
- [`../manuscript/submission/submission_manifest.json`](../manuscript/submission/submission_manifest.json)

Its scientific content is closed. The central claim is:

> **Occurrence-conditioned landscape structure can retain held-out information under a restricted declared reference yet fail to add predictive value beyond a richer reference; structural adequacy must therefore be earned relative to the reference and endpoint being tested.**

The empirical basis is separate from EOG-WF:

- original A-Islands conditional ordering: positive under climatic support + nearest-source conditioning;
- prospectively frozen A-Islands `C − R3`: adverse predictive increment;
- Tanzania strong-reference test: adverse primary LOSO increment, spatial-block sensitivity uncertain.

The active sequence is presentation/release only:

1. revise Figure 1 around `declared reference -> held-out structural probe -> earned / adverse-or-redundant / indeterminate`;
2. revise the A-Islands figure so the original conditional-concordance result and strong-reference `C − R3` result remain on distinct axes and cannot be read as one effect size;
3. add the R0/R1/R2/R3/C explanatory tier panel, with `C − R3` marked as the only primary extension contrast;
4. rebuild and fingerprint the final figure set and run display-size visual QA;
5. freeze the structural-paper release/archive only after those presentation assets are final;
6. complete author metadata, AI disclosure and submission-day Ecological Informatics policy verification.

No new biological endpoint is needed or allowed to rescue the observed pattern.

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
11. **Do not rerun the authoritative A-Islands strong-reference outcome.**
12. Do not weaken R3, retune graph radii or change taxa after the A-Islands outcome.
13. Do not add a favorable structural/island dataset to rescue the adverse strong-reference results.
14. Do not pool the original A-Islands conditional-concordance estimand with the strong-reference log-loss increment as a common effect size.
15. Do not reinterpret Tanzania spatial-block uncertainty as a resolved effect.
16. Do not merge the structural/island empirical denominator into EOG-WF, or use EOG-WF endpoints as extra replications of the structural paper.

The active scientific mainline is therefore:

> **finish and submit the structural/island second paper as a reference-conditioned structural-adequacy result, while keeping the EOG-WF paper scientifically frozen and limited to its existing author/admin/release lane.**
