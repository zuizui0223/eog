# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

Current empirical boundary:

> **Glanville rejected exact world IDs as direct supervised features. Tvärminne Daphnia showed that label-invariant Layer B contains small non-redundant information beyond mean support but is substantially worse than a strong frozen RF. Southern California giant kelp became the first post-#218 candidate to reach once-only outcome access, but it stopped before the exact count gate because the published metadata column schema disagreed with the physical CSV header. No fresh post-Daphnia system has yet completed the paired `strong learner` versus `same learner + Layer B` endpoint.**

Current method/product boundary:

> **Layer A is the exact sequential compatibility/contraction/falsification state. Layer B is a world-label-invariant diagnostic/complementary representation. Predictive value must now be earned as prospectively paired added value on top of an unchanged strong learner, not by replacing or weakening that learner.**

Current validation-interface boundary:

> **Physical response-header identity and categorical response-token handling are part of response semantics. A bounded first-record header must be checked against the frozen physical-column contract before row-level outcome access when source metadata can drift from the file; categorical normalization must likewise be declared and fingerprinted. Any unexpected post-open column or token stops the attempt and does not authorize parser repair and rerun.**

Generic connectivity/operator growth remains stopped.

Canonical documents:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`two_layer_forecast_architecture.md`](two_layer_forecast_architecture.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)
- [`predictive_complementarity_contract.md`](predictive_complementarity_contract.md)
- [`outcome_access_gate.md`](outcome_access_gate.md)
- [`response_header_schema_gate.md`](response_header_schema_gate.md)
- [`response_token_schema_contract.md`](response_token_schema_contract.md)

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

Observed positives constrain worlds but do not identify one true route/history.

For exact finite worlds, EOG exposes:

- `possible` — reachable in at least one declared world;
- `robust` — reachable in every declared world;
- `unresolved` — possible but not robust;
- `robustly_unreachable` — unreachable in every declared world.

These are conditional on the declared universe. Expanding that universe may enlarge
`possible` and shrink robust exclusion; adding possibilities cannot justify a stronger
impossibility claim.

## Active two-layer architecture

### Layer A — exact scientific state

Retain:

- exact world/rule IDs and fingerprints;
- current source state;
- per-world support;
- surviving compatible rule set;
- possible/robust/unresolved/excluded projections;
- monotone sequential contraction;
- finite-universe falsification.

Exact identity is required to say which rule was eliminated. It is not historical truth.

### Layer B — label-invariant representation

Production interface:

`src/eog/v2/world_predictive_summary.py`

Current v1 features per node/horizon:

- surviving-world fraction;
- support mean / SD / min / max;
- q25 / q50 / q75;
- positive-support fraction;
- support range.

World IDs remain in Layer A and are not default supervised columns.

### Prediction endpoint — paired complementarity

Production evaluator:

`src/eog/v2/predictive_complementarity.py`

For each frozen heldout outer unit compare:

```text
strong learner + frozen conventional features
```

with:

```text
same learner + same features + frozen Layer B
```

Learner family, preprocessing, hyperparameters, external features, Layer B, response
endpoint, split, metric and favourable/adverse thresholds must all be frozen before
response access.

## Independent evidence fixing the architecture

### Glanville

Completed prospectively gated heldout forecast.

Macro log loss:

- same-world symmetric compression `0.187983`;
- RF `0.191725`;
- IFM logistic `0.200242`;
- exact world identity `0.230197`.

Exact identity lost to compression in 6/6 heldout transitions. Frozen status:
`adverse_identity_predictive_value`.

Exact worlds still contracted during calibration, preserving their Layer-A scientific
role.

### Tvärminne Daphnia

Completed fresh prospectively frozen heldout forecast.

- exact count gate: calibration `730 / 10,102`, heldout `258 / 4,502`;
- four finite threshold worlds were eliminated at the first calibration update;
- only `geo_exponential_full` survived.

Layer B versus mean-only:

- `0.285714` vs `0.287275` macro log loss;
- delta `-0.001561`;
- Layer B won 8/11 heldout years;
- status `favorable_layer_b_predictive_value`.

Layer B versus strong RF:

- RF `0.204084`;
- Layer B `0.285714`;
- Layer B won 0/11;
- status `adverse_external_predictive_added_value`.

Therefore Layer B is supported as non-redundant information, not as a superior standalone
prediction product.

## Post-#218 fresh complementarity ledger

The paired complementarity contract was merged in PR #218. Systems selected afterward
have been screened without weakening that contract.

### Snapshot Serengeti — STOP before response

- 225 response-independent camera sites;
- response remained unopened;
- LCC 25/50/75/90% all collapsed at the same nearest-neighbour grid threshold;
- distinct positive structural scales `1 < 3`.

Status: `gate0_stop_structural_scale_collapse`. PR #223 closed unmerged.

### Chicago striped skunk — STOP before response

Scientifically attractive because the published model explicitly separates local and
long-distance colonization, but the complete skunk coordinate registry was not physically
separate from response rows.

An earlier response-free Chicago coordinate registry matched only 100/106 analysis sites.
Six exact IDs were missing. No fuzzy alias repair was allowed.

Status: `gate0_stop_external_registry_incomplete`. PR #225 closed unmerged.

### Chicago coyote — pre-model STOP after sole response opening

This candidate passed the strongest pre-response sequence so far:

- same immutable release separated site covariates, UTM coordinates and response;
- 113/113 response-free exact registry match;
- four distinct nested structural thresholds: approximately 3.078, 3.619, 4.792 and 5.230 km;
- frozen 10 calibration + 5 heldout transitions;
- same-RF paired complementarity design;
- response-free smoke completed 2 fits and 10 synthetic heldout scores;
- all 16 outcome-access freeze keys were present;
- generic outcome-access gate authorized the once-only exact-count-first run.

The sole response-capable run opened the frozen response and immediately encountered:

```text
Week = "week1"
```

while the frozen parser had declared `week 1` through `week 4`.

Execution stopped **before the exact count gate**:

- exact count gate executed: false;
- models fit: 0;
- heldout scores: 0;
- complementarity: not evaluated;
- post-response redesign: none.

Status: `pre_model_response_schema_mismatch`. PR #227 closed unmerged.

This is neither favourable nor adverse EOG evidence. The coyote endpoint is not rerun
with a repaired parser and called independent.

### Southern California giant kelp — pre-model STOP after sole response opening

This candidate became the first post-#218 system to pass the full response-blind sequence
through once-only outcome authorization:

- 469 fixed patches over 22 semi-annual periods;
- response-independent geometry and response were physically separated;
- structural gate, process/source mapping, prospective estimability, paired smoke and
  16-key freeze ledger completed;
- once-only run identity was fixed to run #1 / attempt #1.

The metadata-derived response contract required:

```text
pixel_latitude, pixel_longitude
```

but the physical CSV header contained:

```text
patch_latitude, patch_longitude
```

The sole response-capable run therefore stopped during header comparison **before the
exact count gate**:

- exact count gate executed: false;
- models fit: 0;
- heldout scores: 0;
- complementarity: not evaluated;
- rerun performed: false;
- post-response redesign: none.

Status: `pre_model_physical_header_schema_mismatch`. PR #238 closed unmerged.

This is neither favourable nor adverse EOG evidence. It demonstrates that published
metadata identity is not sufficient to guarantee physical response-file schema identity.
The giant-kelp endpoint is not repaired and rerun as independent evidence.

## Response schema is now prospectively two-stage

### Physical header gate

Generic implementation:

`src/eog/v2/response_header_schema.py`

The existing bounded first-record firewall in `src/eog/v2/response_firewall.py` is used
to verify physical column names before row-level outcome access. Missing/unexpected
columns, duplicate/empty names or a frozen order mismatch fail closed.

The physical header fingerprint is incorporated into the existing `response_semantics`
freeze; the 16-key `FrozenOutcomeAccessContract` surface is not expanded.

### Categorical token gate

Generic implementation:

`src/eog/v2/response_schema.py`

For each categorical response field, a future attempt must freeze:

- complete canonical values;
- outer-whitespace stripping;
- casefolding;
- optional internal ASCII-whitespace removal.

Canonical values that collide after normalization are invalid. Unknown values fail
closed. No fuzzy matching or post-open aliases are allowed.

The token schema fingerprint is also incorporated into the existing `response_semantics`
freeze.

## Required fresh validation sequence

Before row-level response access:

1. freeze immutable source and response identity;
2. freeze full response-independent node registry / geometry;
3. acquire only the bounded physical response header under the response firewall;
4. verify/freeze physical response-column schema;
5. freeze remaining response semantics including categorical token schema;
6. establish process/source closure;
7. pass response-blind structural-scale/adequacy gates;
8. freeze Layer-A worlds and update policy;
9. freeze unchanged Layer B;
10. freeze strong learner, preprocessing and conventional features;
11. freeze same-learner + Layer-B augmentation;
12. freeze heldout outer units, count minima, metric and paired decision rule;
13. run response-free synthetic smoke and freeze exact runtime/runner identity;
14. pass the 16-key outcome-access authorization;
15. open response once;
16. revalidate the already-frozen physical header and apply the already-frozen token schema;
17. run exact count gate before any fit;
18. only if count gate passes, fit and score once.

Any undeclared physical column or categorical token after step 15 stops the attempt before
scientific scoring.

## Fixed novelty boundary

Do not claim generic novelty for:

- threshold/percolation/MST machinery;
- dynamic reachability;
- least-cost, stepping-stone or circuit methods;
- suitability + accessibility;
- dynamic/mechanistic SDMs;
- ensembles/model averaging;
- permutation-invariant set summaries;
- generic feature augmentation or stacking;
- credal/imprecise prediction;
- history matching/NROY;
- Pareto/minimum-relaxation frontiers;
- generic adaptive survey design;
- generic schema normalization or header validation.

The candidate EOG contribution remains the domain-specific composition:

> **a prospectively source- and scale-certified finite world universe is conditioned by distribution evidence; exact world identities remain auditable sequential update/falsification state; a label-invariant projection exposes surviving world-set structure; later evidence contracts or falsifies the same frozen rule universe; and predictive added value is tested as a paired augmentation of a strong unchanged predictor under once-only, schema-frozen outcome access.**

## Next scientific milestone

Do not rerun coyote, giant kelp, Daphnia or earlier stopped systems as independent
confirmation.

After the generic bounded physical-header schema gate is merged, the next milestone is:

> **select a genuinely fresh system, freeze physical response-column identity and categorical response-token semantics before row-level access, and complete the paired strong-learner complementarity endpoint once without redesign.**

## Stop rules

1. Preserve favourable, adverse, blocked, null/no-confirmed and non-estimable evidence.
2. Do not rescue opened endpoints by header, parser, registry, scale or model redesign and relabel the rerun independent.
3. Do not expose arbitrary exact world labels as default supervised features.
4. Do not change learner family, hyperparameters or conventional features between paired fits.
5. Do not tune Layer B on Daphnia outcomes and call it prospective.
6. Do not call structural thresholds biological movement limits without calibration.
7. Do not call survey non-detection latent biological absence without observation justification.
8. Do not identify a surviving world as historical truth.
9. Do not claim universal robustness outside the declared finite-world certificate.

The active mainline is **schema-frozen prospective validation of EOG Layer B as
complementary information to a strong predictor, while exact Layer A remains the
scientific update/falsification core**.
