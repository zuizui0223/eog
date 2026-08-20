# EOG method-validation protocol

## Status

This document defines the active prospective validation protocol after four empirical
lessons:

1. STOC showed that a frozen world universe can fail before prediction;
2. Glanville showed that exact world IDs can remain scientifically useful while harming direct supervised prediction;
3. Tvärminne Daphnia showed that label-invariant Layer B carries small non-redundant information but can remain worse than a strong RF;
4. Chicago coyote showed that even a fully frozen scientific/model contract can still fail before scoring if categorical response-token parsing was not prospectively specified.

Current verdict:

> **Layer A is the auditable exact update/falsification state. Layer B is a candidate complementary representation. Any predictive claim must use a prospectively paired strong-learner comparison, and all response semantics—including deterministic categorical token normalization—must be frozen before row-level outcome access.**

Frozen empirical attempts are never repaired and rerun as independent confirmation.

## 1. Scientific objects

EOG keeps distinct:

1. local possibility;
2. reachability from declared current sources;
3. distributional realizability under declared worlds;
4. historical truth.

For finite world universe `W` and evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

Observed states constrain the compatible set; they do not identify one true route or
history.

## 2. Two-layer architecture

### Layer A — exact latent/update state

Retain exact:

- world/rule IDs and fingerprints;
- current source state;
- per-world support;
- compatible/surviving set;
- possible / robust / unresolved / finite-world-excluded structure;
- monotone sequential contraction;
- finite-universe falsification.

Exact identities are required to say which rule was eliminated. They are not default
supervised prediction columns and are not historical truth.

### Layer B — label-invariant representation

Production implementation:

`src/eog/v2/world_predictive_summary.py`

Current v1 features:

- surviving-world fraction;
- support mean / SD / min / max;
- q25 / q50 / q75;
- positive-support fraction;
- support range.

The representation must be invariant to arbitrary world names and member order.

## 3. Validation estimands are separate

### A. Algorithmic correctness

Do exact reconstruction, propagation and contraction obey declared invariants?

### B. World-universe adequacy

Can the prospectively declared world set represent the intended structural/process scale
before response access?

### C. Layer-A scientific value

Does exact identity support meaningful compatibility, elimination or finite-universe
falsification?

### D. Layer-B information value

Does the symmetric representation contain heldout information beyond a simpler EOG
projection?

### E. Standalone predictive value

Does an EOG prediction head outperform strong external prediction?

Current independent Daphnia evidence says no.

### F. Complementary predictive added value — active prediction estimand

Does adding unchanged Layer-B features improve an already frozen strong learner compared
with the **same learner** using the same conventional features without EOG?

Executable evaluator:

`src/eog/v2/predictive_complementarity.py`

### G. Historical identification

Actual route, ancestry and colonization sequence require stronger evidence and are not
implied by A–F.

## 4. Response semantics and token schema

Define the observed target before row-level outcome access.

For survey transitions, a zero may be a recorded negative target only under the frozen
observation interpretation. It is not automatically latent biological absence.

For every categorical response field used by the runner, also freeze any deterministic
text normalization needed to recognize categories.

Implementation:

`src/eog/v2/response_schema.py`

A `CategoricalTokenRule` may declare only:

- complete canonical categories;
- outer-whitespace stripping;
- Unicode casefolding;
- optional internal ASCII-whitespace removal.

No fuzzy matching, punctuation repair or post-open aliasing is allowed. Canonical
categories that collide after normalization are invalid. Unknown values fail closed.

The `ResponseTokenSchemaDeclaration.fingerprint` is incorporated into the candidate's
existing `response_semantics` fingerprint. The generic outcome-access contract remains a
sixteen-key surface; no historical ledger rewrite is required.

If an undeclared token is first encountered after response opening, stop the attempt
before count/model/scoring as applicable. Parser repair may inform a future fresh attempt,
but the opened endpoint is not rerun and called independent.

Canonical documentation:

`docs/response_token_schema_contract.md`

## 5. World-scale construction and adequacy

Before response access, use defensible external process scales and/or a prospectively
declared response-blind structural scale ladder.

Structural worlds must be audited for the quantities relevant to the claim, such as:

- component count;
- largest-component fraction;
- isolated-node fraction;
- degree;
- directed horizon reach.

Structural thresholds are analyst-choice regimes unless separately calibrated as
biological movement/dispersal scales.

## 6. Process/source closure

Before response access establish at least one:

1. the node universe approximately closes the relevant transition process;
2. external source states are explicitly represented;
3. the claim is explicitly conditional on internal realized sources.

Observed sources are conditioning states, not inferred ancestors.

## 7. Paired complementarity contract

Freeze one strong baseline learner before response access:

- model family;
- preprocessing;
- hyperparameters / fit policy;
- conventional feature set;
- calibration procedure.

Then freeze one augmented model using:

- the **same learner and fit policy**;
- the same conventional features;
- the same response endpoint and split;
- plus the unchanged Layer-B feature block.

For each frozen heldout outer unit `u` record paired scores:

```text
S_base(u) = strong learner
S_aug(u)  = same strong learner + Layer B
```

Use `PredictiveComplementarityDeclaration` to freeze:

- primary metric;
- score direction;
- expected heldout outer-unit count;
- favourable minimum augmented wins;
- adverse minimum baseline wins;
- tie tolerance.

For lower-is-better metrics, favourable requires both lower augmented macro score and the
prospectively declared number of augmented outer-unit wins. Adverse is symmetric.
Conflicting evidence remains `no_confirmed_complementary_added_value`.

Rows within a year/site network do not substitute for independent heldout outer units.

## 8. Required fresh independent sequence

### Gate 0 — immutable source and response identity

Freeze exact source versions, response identity and non-response inputs.

### Gate 1 — node universe / response-free geometry

Freeze the complete analysis registry and geometry without response conditioning.

### Gate 2 — response semantics and token schema

Freeze target meaning, missingness/effort semantics, canonical categorical values and any
allowed deterministic token normalization.

### Gate 3 — process/source closure

Freeze why current-source propagation is scientifically admissible.

### Gate 4 — world scale and structural adequacy

Construct worlds without response tuning and stop if the prospective adequacy gate fails.

### Gate 5 — Layer A

Freeze world IDs, source update policy, support/falsification rules and monotonic
contraction.

### Gate 6 — Layer B

Freeze the unchanged label-invariant representation.

### Gate 7 — strong learner and paired augmentation

Freeze identical learner/preprocessing/conventional features, differing only by the Layer-B
augmentation.

### Gate 8 — split, estimability and decision rules

Freeze calibration/heldout outer units, exact count minima, metric and favourable/adverse
rules.

### Gate 9 — response-free full smoke

Run the exact scientific/model path with synthetic outcome only. Freeze runner/runtime and
smoke fingerprints.

### Gate 10 — outcome-access authorization

Use the existing 16-key `FrozenOutcomeAccessContract`. The `response_semantics` entry must
bind the token-schema fingerprint when categorical fields are used.

### Gate 11 — open response once

After authorization:

1. verify frozen response/runtime/runner identity;
2. open row-level response once;
3. parse only with the frozen token schema;
4. run the exact count gate before any model fit;
5. if count gate fails, stop with zero fits/scores;
6. otherwise fit and score the already-frozen paired models once.

No post-open world, parser, split, model, feature, metric or threshold redesign is
permitted.

## 9. Empirical boundary

### Glanville

Completed independent heldout forecast. Exact world identity was adverse as a direct
supervised encoding while retaining Layer-A contraction value.

### Daphnia

Completed fresh independent heldout forecast.

- Layer B vs mean-only: `0.285714` vs `0.287275`, 8/11 wins;
- Layer B vs strong RF: `0.285714` vs `0.204084`, 0/11 wins.

This established the paired complementarity question as the next valid predictive
estimand.

### Snapshot Serengeti

Stopped before response because its regular camera grid collapsed all prospective LCC
levels to one structural threshold.

### Chicago striped skunk

Stopped before response because the response-free external coordinate registry matched
only 100/106 frozen analysis sites. No alias repair was allowed.

### Chicago coyote

Passed 113/113 response-free registry join, four structural scales, paired design, full
synthetic smoke and 16-key authorization. On its sole response opening, the frozen parser
encountered `Week="week1"` while it had declared `week 1` etc.

Status: `pre_model_response_schema_mismatch`.

- exact count gate executed: false;
- models fit: 0;
- heldout scores: 0;
- complementarity: not evaluated.

The endpoint is not rerun after parser repair. This failure motivates the generic token
schema contract; it provides no favourable/adverse EOG evidence.

## 10. Novelty boundary

Do not claim generic novelty for:

- threshold filtration, percolation or MST machinery;
- dynamic reachability;
- stepping stones, least-cost or circuit methods;
- dynamic/mechanistic SDMs;
- ensembles/model averaging;
- permutation-invariant summaries;
- generic feature augmentation/stacking;
- credal/imprecise prediction;
- history matching/NROY;
- Pareto/minimum-relaxation frontiers;
- generic schema normalization;
- generic adaptive survey design.

The candidate EOG contribution is the domain-specific composition:

> **a prospectively source- and scale-certified finite world universe is conditioned by distribution evidence; exact world identities remain auditable sequential update/falsification state; a label-invariant representation exposes surviving world-set structure; later evidence contracts or falsifies the same frozen universe; and predictive added value is tested as a paired augmentation of a strong unchanged predictor under once-only, schema-frozen outcome access.**

## 11. Stop rules

- Do not add ecological operators to rescue failed validation.
- Do not weaken the external learner after outcomes.
- Do not retune graph/world scale after response access.
- Do not repair a categorical parser after opening and rerun the same endpoint as independent.
- Do not expose arbitrary world IDs as default prediction features.
- Do not change learner family/hyperparameters/conventional features between paired models.
- Do not call structural thresholds biological movement limits without calibration.
- Do not call survey non-detection latent biological absence without observation justification.
- Do not identify a surviving world as historical truth.
- Do not claim robustness outside the declared finite-world certificate.
