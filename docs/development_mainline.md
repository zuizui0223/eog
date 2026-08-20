# EOG development mainline

## Status

This file is the **single source of truth for active scientific development**.

Current empirical state:

> **Two fully prospective independent heldout results now define the product boundary. Glanville rejected exact world IDs as direct supervised features. Tvärminne Daphnia then showed that the label-invariant Layer-B world-set summary carries small non-redundant information beyond mean support, but is substantially worse than a strong frozen external random forest.**

Current method/product state:

> **Layer A remains the exact sequential update/falsification state. Layer B remains a world-label-invariant summary of that state, but it is no longer treated as a candidate standalone replacement for a strong predictor. The active prediction question is complementary added value: does unchanged Layer B improve the same prospectively frozen strong learner when added to it?**

Generic connectivity/operator growth remains stopped.

Canonical documents:

- [`worldset_forecast_algorithm.md`](worldset_forecast_algorithm.md)
- [`method_validation_protocol.md`](method_validation_protocol.md)
- [`world_universe_scale_design.md`](world_universe_scale_design.md)
- [`two_layer_forecast_architecture.md`](two_layer_forecast_architecture.md)
- [`predictive_complementarity_contract.md`](predictive_complementarity_contract.md)

## Scientific center

EOG keeps four objects separate:

1. **local possibility**;
2. **reachability from declared current sources**;
3. **distributional realizability under declared worlds**;
4. **historical truth**.

Observed positive states constrain worlds but do not identify one true route/history.

For finite universe `W` and evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

The exact identity of surviving worlds remains auditable and is required for evidence-driven contraction/falsification.

## Active two-layer architecture

### Layer A — exact latent/update state

Retain:

- exact world/rule IDs and fingerprints;
- current source state;
- per-world support;
- compatible/surviving rule set;
- possible/robust/unresolved and finite-world-excluded structure;
- sequential contraction and finite-universe falsification.

Core implementations include:

- `src/eog/v2/world_reconstruction.py`;
- `src/eog/v2/world_forecast.py`;
- `src/eog/v2/sequential_world_forecast.py`.

The finite-world exact reachability interface additionally exposes exact `possible`, `robust`, `unresolved` and `robustly_unreachable` projections for a declared exhaustively enumerated world set. Expanding that declared universe may enlarge possible support and may shrink robust/excluded claims; it cannot justify stronger exclusion merely by adding worlds.

### Layer B — world-label-invariant representation

Default features remain:

`src/eog/v2/world_predictive_summary.py`

The v1 projection uses ten symmetric quantities per node/horizon:

- surviving-world fraction;
- support mean/std/min/max;
- q25/q50/q75;
- positive-support fraction;
- support range.

World IDs remain in Layer A and are **not** supervised predictive columns by default.

The feature representation must be invariant to world renaming and member order. The exact upstream latent fingerprint remains separate for scientific provenance.

## Independent evidence that fixed the architecture

### Åland Glanville fritillary — exact identity prediction adverse

Glanville was the first independent EOG-WF system to pass the prospective structural gates and complete heldout prediction.

Authoritative result fingerprint:

`628511ac3f42fe108d334a6458428bbf56f3c3fea1e753b2bee8d980b3d84c33`

Primary macro-year log loss:

| representation/model | log loss |
|---|---:|
| same-world symmetric compression | **0.187983** |
| random forest | 0.191725 |
| IFM logistic | 0.200242 |
| exact world identity | **0.230197** |

Exact identity lost to compression in **6/6** heldout transitions.

Frozen statuses:

- `adverse_identity_predictive_value`;
- `adverse_external_predictive_added_value`.

This rejected exact arbitrary world labels as the default supervised prediction surface. It did **not** invalidate exact identity as update state: four truncated structural worlds were eliminated during calibration while the full process world survived.

Canonical evidence: [`../validation/glanville_eogwf/README.md`](../validation/glanville_eogwf/README.md).

### Tvärminne Daphnia — Layer B non-redundant but externally adverse

PR #217 executed a genuinely fresh prospectively frozen validation on 546 rock pools with annual released *D. magna* occupancy from 1982–2017.

Before response access it froze:

- response-independent patch size and 546×546 distance;
- four distinct structural LCC scales;
- 24 calibration and 11 heldout annual transitions;
- five Layer-A worlds;
- unchanged `symmetric_world_support_summary_v1`;
- strong geometry/process logistic and RF comparators;
- count/metric/decision rules;
- exact runtime and once-only response runner.

The generic 16-key outcome-access gate authorized a single exact-count-first run. The sole response-capable execution was workflow run `32368225530`, `run_number=1`, `run_attempt=1`.

Authoritative result fingerprint:

`8fcf0e74452e29e14fd63efa51184bfbb00b7fb075ad485616798d8fd3a5a4ae`

Exact count gate passed with 730/10,102 calibration events/non-events and 258/4,502 heldout events/non-events across 11 heldout years.

#### Layer A result

At the first calibration transition (`1982→1983`), all four finite hard-threshold worlds were eliminated. Only `geo_exponential_full` survived thereafter.

This independently supports exact world identity as an auditable compatibility/contraction state. It does not identify the survivor as true dispersal history.

#### Layer B internal predictive information

Layer B was estimable beyond mean-only (`max residual SD = 0.453242`).

Macro heldout-transition log loss:

- Layer B: `0.285714`;
- mean-only: `0.287275`;
- delta Layer B − mean-only: `-0.001561`;
- Layer B won `8/11` heldout transitions.

Frozen status:

`favorable_layer_b_predictive_value`

Thus symmetric world-set shape/dispersion carries small independently validated information beyond surviving fraction + mean support.

#### External predictive added value

The prospectively frozen strong RF was clearly better:

- geometry/process RF: **`0.204084`**;
- geometry/process logistic: `0.258052`;
- Layer B: `0.285714`.

Layer B beat RF in `0/11` heldout transitions.

Frozen status:

`adverse_external_predictive_added_value`

Therefore EOG Layer B is **not supported as a superior standalone general prediction product**.

Candidate-specific evidence remains on the closed-unmerged PR #217 branch; production `main` should not absorb its system-specific workflows/runners.

## Product boundary after Daphnia

The evidence supports three separate roles:

1. **Layer A — scientific state**  
   Exact worlds are retained for compatibility, contraction, falsification, provenance and finite-world impossibility certificates.

2. **Layer B — diagnostic/complementary representation**  
   Symmetric summaries can retain non-redundant information from the world set, but current evidence does not support using them to replace a strong predictor.

3. **Strong external learner — prediction engine when accuracy is the objective**  
   EOG should earn predictive product value by adding information to that strong learner, not by requiring the strong learner to be discarded.

This is a narrower and stronger claim than “EOG predicts better than SDM/ML”.

## Active prediction estimand: complementary added value

Generic executable contract:

`src/eog/v2/predictive_complementarity.py`

For each prospectively fixed heldout outer unit, compare:

```text
strong learner + frozen conventional features
```

against:

```text
same strong learner + same conventional features + unchanged EOG Layer B
```

The learner family, preprocessing, hyperparameters, response endpoint, split, conventional features, Layer-B representation, metric and decision thresholds must all be frozen before response access.

A favourable result requires both better macro heldout score and the prospectively declared minimum number of paired outer-unit wins. Adverse is the symmetric reverse condition. Ambiguous results remain no-confirmed.

Daphnia cannot independently confirm this new estimand because `strong learner + EOG` was not its prospectively declared endpoint. It may be used only for engineering/smoke. A claim requires a genuinely fresh system selected after the complementarity contract is frozen.

## Prospective gates remain mandatory

Any future independent predictive test must freeze before response access:

1. immutable source/schema and response semantics;
2. process/source closure;
3. process-calibrated and/or response-blind world-scale construction;
4. response-blind structural adequacy;
5. current-source/sequential Layer-A update policy;
6. Layer-B representation;
7. strong learner + conventional feature contract;
8. paired strong-learner-with-EOG augmentation contract;
9. holdout outer units, metrics and favourable/adverse/no-confirmed rules;
10. exact-count-first outcome access and no-retuning rule.

Then execute once.

## Earlier validation ledger

### A-Islands

Exploratory evidence showed scalar frequency can erase exact world identity. Not independent confirmation. Earlier strong-reference predictive extension adverse.

### SIVFLORA

Independent attempt stopped pre-outcome on frozen climate coverage. Not rescued.

### Azores

Independent attempt stopped pre-model on frozen taxonomic scope. Not rescued.

### STOC

Independent attempt stopped because the frozen world universe was structurally inadequate before heldout prediction. This motivated response-blind world-scale construction and adequacy gates. STOC remains frozen and is not reused.

### Glanville

Completed independent heldout forecast; exact world identity adverse as direct predictive encoding. Established the two-layer architecture.

### Daphnia

Completed independent heldout forecast; symmetric Layer B favourable relative to mean-only but adverse relative to strong RF. Established the complementarity product boundary.

## Fixed novelty boundary

Do not claim novelty for:

- graph threshold/percolation/MST machinery;
- dynamic reachability;
- least-cost/stepping-stone/circuit methods;
- functional habitat / suitability+accessibility;
- dynamic/mechanistic SDMs;
- model averaging/ensembles;
- permutation-invariant set functions or distributional summaries;
- generic feature augmentation or stacking;
- credal/imprecise prediction;
- history matching/NROY;
- Pareto/minimum-relaxation frontiers;
- generic adaptive survey design.

The candidate EOG contribution remains the domain-specific composition:

> **a prospectively source- and scale-certified finite world universe is conditioned by positive distribution evidence; exact world identities remain auditable sequential update/falsification state; a label-invariant projection can expose the surviving world-set structure; later evidence contracts or falsifies the same frozen rule universe, and any predictive added-value claim is tested as a prospectively paired augmentation of a strong unchanged predictor.**

## Next scientific milestone

Do **not** add another graph/connectivity operator, do **not** rerun Daphnia to validate the new complementarity endpoint, and do **not** sequentially shop datasets until standalone EOG beats RF.

The next valid milestone is:

> **freeze a strong-learner + EOG complementarity endpoint, then validate it once on a genuinely fresh independent system.**

If EOG augmentation is null/adverse, preserve that result and narrow the prediction-product claim further. Layer A scientific update/falsification value remains a separate estimand.

## Stop rules

1. Preserve favourable, adverse, blocked, null/no-confirmed and non-estimable evidence.
2. Do not rescue Glanville, Daphnia or earlier stopped systems by redesign and relabel the rerun independent.
3. Do not expose arbitrary exact world labels to the default predictive head.
4. Do not change the strong learner or conventional features between baseline and EOG-augmented fits.
5. Do not tune the Layer-B representation on Daphnia heldout outcomes and call it prospective.
6. Do not promote raw EOG support to colonisation/occupancy probability without calibration.
7. Do not identify a surviving world as historical truth.
8. Do not claim universal robustness outside the declared finite-world certificate.

The active mainline is now **prospective validation of EOG as complementary information to a strong frozen predictor, while retaining exact Layer A as the scientific update/falsification core**.
