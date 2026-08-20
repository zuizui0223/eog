# EOG method-validation protocol

## Status

This document defines the active EOG-WF validation protocol after:

1. the 2026-08 methodological audit;
2. STOC's independent world-universe failure before prediction;
3. the completed independent Glanville heldout forecast, in which exact world identity was adverse as a direct predictive representation; and
4. the completed fresh Tvärminne Daphnia heldout forecast, in which the label-invariant Layer-B summary was slightly favourable relative to mean-only EOG but clearly adverse relative to a strong frozen random forest.

Current verdict:

> **EOG-WF remains a coherent exact world-set reconstruction/update framework. Exact world identity is retained as latent sequential state. The world-label-invariant Layer-B representation has independently demonstrated non-redundant predictive information beyond mean support, but current evidence does not support it as a superior standalone predictor. New prediction claims must therefore be tested as paired complementary added value on top of a prospectively frozen strong learner.**

Frozen empirical results are never reopened or retuned to match later protocol improvements.

## 1. Scientific objects

EOG keeps distinct:

1. **local possibility**;
2. **reachability from declared current sources**;
3. **distributional realizability under declared worlds**;
4. **historical truth**.

For finite world universe `W` and positive evidence `O`:

```text
W(O) = {w in W : w is compatible with O}
```

This is an unranked compatible set unless ranking was prospectively justified.

Unobserved/zero records are not biological absences without an appropriate observation model.

## 2. Two-layer forecast object

### Layer A — exact latent/update state

The canonical scientific state retains:

- exact world/rule IDs and fingerprints;
- current realised source state;
- per-world support through horizon;
- surviving/compatible rule set;
- robust/contingent/excluded structure;
- sequential contraction and finite-universe falsification.

Exact identities remain necessary to say **which rule was eliminated**.

### Layer B — world-label-invariant representation

The default numerical projection must be invariant to arbitrary world labels and member order unless a future independent contract explicitly establishes otherwise.

Current v1 interface:

`src/eog/v2/world_predictive_summary.py`

It returns ten symmetric world-set quantities per node/horizon:

- surviving-world fraction;
- mean / SD / min / max support;
- q25 / q50 / q75;
- positive-support fraction;
- range.

This is not a novelty claim for generic set functions or statistical summaries.

Layer B is now treated as a diagnostic/complementary representation, not a presumed standalone prediction replacement.

## 3. Sequential updating

For repeated transitions with changing current sources, use frozen rule identity plus changing source state:

`src/eog/v2/sequential_world_forecast.py`

Evidence from transition `t→t+1` is evaluated only from the current sources at `t` to positive targets at `t+1`. Past positives are not re-tested from later source sets.

Surviving rules may only remain or contract:

```text
W_{t+1} ⊆ W_t
```

or the frozen universe is falsified.

## 4. Validation estimands remain separate

### A. Algorithmic correctness

Does exact reconstruction/propagation/update obey declared invariants?

Current state: supported by known-truth/package tests.

### B. World-universe adequacy

Can the prospectively declared world set represent the intended forecast scale before response access?

Current infrastructure:

- `src/eog/v2/world_scale_ladder.py`;
- `src/eog/v2/world_adequacy.py`.

### C. Latent identity/update value

Does retaining exact identity enable scientifically meaningful rule elimination, discrimination or finite-universe falsification?

Known-truth: supported.  
Independent Glanville: exact rule contraction observed.  
Independent Daphnia: all four finite hard-threshold worlds were eliminated at the first calibration update while the full-support world survived.

### D. Layer-B representation value

Does the frozen symmetric world-set representation retain heldout information beyond a prospectively declared simpler EOG projection such as surviving fraction + mean support?

Independent Daphnia: yes, slightly; Layer B beat mean-only in 8/11 heldout years with macro log-loss delta `-0.001561` and was estimable beyond mean-only.

### E. Standalone external predictive value

Does a Layer-B prediction head outperform strong external predictors?

Independent Daphnia: no. The frozen RF macro log loss was `0.204084` versus Layer B `0.285714`, and Layer B beat RF in 0/11 heldout years.

Standalone superiority is therefore not the active product claim.

### F. Complementary predictive added value — active new estimand

Does adding unchanged EOG Layer-B features improve an already frozen strong learner, compared with the **same learner** using the same conventional features without EOG?

Executable evaluator:

`src/eog/v2/predictive_complementarity.py`

This is the active prediction-validation endpoint for future fresh systems.

### G. Historical identification

Actual routes, ancestry or colonisation sequence require stronger evidence and are not implied by A–F.

## 5. Independent Glanville boundary

Glanville was the first independent EOG-WF system to reach the heldout predictive endpoint.

Authoritative result fingerprint:

`628511ac3f42fe108d334a6458428bbf56f3c3fea1e753b2bee8d980b3d84c33`

Primary macro-year log loss:

- symmetric same-world compression: `0.187983`;
- RF: `0.191725`;
- IFM logistic: `0.200242`;
- exact world identity: `0.230197`.

Identity minus compression = `+0.042214`; identity lost to compression in 6/6 heldout transitions.

Frozen statuses:

- `adverse_identity_predictive_value`;
- `adverse_external_predictive_added_value`.

Identity was estimable beyond the declared compression, so this cannot be dismissed as a redundant design matrix.

The exact world state still eliminated four truncated structural worlds during calibration and retained the full process world. Therefore the result narrowed the **prediction interface**, not the existence of an exact latent world state.

Do not rerun Glanville with later interfaces and call the rerun independent confirmation.

## 6. Independent Daphnia boundary

The Tvärminne Daphnia attempt was selected and frozen after the two-layer architecture was established.

Authoritative result fingerprint:

`8fcf0e74452e29e14fd63efa51184bfbb00b7fb075ad485616798d8fd3a5a4ae`

Exact count gate passed with:

- calibration events/non-events: `730 / 10,102`;
- heldout events/non-events: `258 / 4,502`;
- 11 heldout annual units with both classes.

At `1982→1983`, all four finite hard-threshold worlds were eliminated; only `geo_exponential_full` survived thereafter.

Layer-B vs mean-only macro log loss:

- Layer B `0.285714`;
- mean-only `0.287275`;
- delta `-0.001561`;
- Layer B won 8/11 years.

Frozen status:

`favorable_layer_b_predictive_value`

Strong external comparison:

- geometry/process RF `0.204084`;
- geometry/process logistic `0.258052`;
- Layer B `0.285714`;
- Layer B beat RF 0/11 years.

Frozen status:

`adverse_external_predictive_added_value`

This result is not rescued or reclassified. It establishes the current complementarity boundary.

Daphnia cannot independently validate a later `strong learner + EOG` endpoint because that paired augmentation was not prospectively declared there.

## 7. World-scale construction

Before response access, use one or both:

### 7.1 Externally calibrated process scale

Use defensible movement/dispersal/transport/barrier evidence, with provenance and uncertainty.

### 7.2 Response-blind structural scale ladder

When no sufficient biological scale exists, construct prospectively declared analyst-choice structural regimes.

For target largest-component fractions `c1 < ... < ck`, choose the minimum metric threshold reaching each target. These are not biological dispersal limits without external calibration.

Primary structural worlds should remain inspectable when secondary environment/barrier intersections are added.

## 8. Structural adequacy gate

Before response access, audit candidate worlds for:

- component structure;
- largest-component fraction;
- isolated-node fraction;
- degree;
- directed horizon reach.

Pass criteria must be frozen prospectively and tied to the intended forecast claim. EOG embeds no universal connectivity cutoff.

## 9. Process closure/source semantics

Before response access, justify why the declared source system is appropriate.

Eligible designs must prospectively establish at least one:

1. the node universe approximately closes the relevant transition process;
2. external source states are explicitly represented;
3. the claim is explicitly conditional on internal realised sources and does not pretend to cover external recruitment.

Observed sources are conditioning states, not inferred ancestors.

## 10. Response semantics

Define the actual observed target before outcome access.

For survey-recorded transitions, a zero may be used as a recorded negative target only under the declared survey interpretation. It is not automatically latent biological absence.

Raw EOG support is not occupancy/colonisation probability. A calibrated supervised learner may use frozen EOG features, but that calibration does not turn the latent world state into historical truth.

## 11. Dependence and validation units

Validation units must match the intended generalisation target.

Many site/species/patch rows do not create many independent years/islands/regions. Do not manufacture precision by resampling a very small number of outer units without prospectively justified operating characteristics.

Complementarity decisions are paired at the frozen outer-unit level. Row count does not substitute for outer-unit replication.

## 12. Required fresh independent sequence

### Gate 0 — source/schema/response semantics

Freeze immutable source, nodes, non-response inputs, response interpretation and holdout structure.

### Gate 1 — process/source closure

Freeze why the declared current-source system is scientifically admissible.

### Gate 2 — world scale

Freeze process-calibrated and/or analyst-choice structural worlds before response access.

### Gate 3 — structural adequacy

Run response-blind structural audit and stop if the prospectively declared gate fails.

### Gate 4 — latent/update state

Freeze rule IDs, source update policy, horizon, gates and falsification rule.

### Gate 5 — Layer-B representation

Freeze the Layer-B representation before response access.

Current default remains `symmetric_world_support_summary_v1`. Do not tune it on Daphnia heldout results and call the new interface prospective.

### Gate 6 — strong learner baseline

Freeze:

- learner/model family;
- preprocessing;
- hyperparameters/fit policy;
- conventional/external feature set;
- any calibration procedure.

This baseline is not weakened after outcomes merely to make EOG useful.

### Gate 7 — paired EOG augmentation

Freeze an augmented specification using:

- the **same learner and fit policy**;
- the same conventional/external features;
- the same response endpoint and split;
- plus the unchanged frozen EOG Layer-B feature block.

Fingerprint the learner, response endpoint, split, external feature set and EOG feature set separately.

### Gate 8 — complementarity metric and decision rule

Freeze before response access:

- primary metric;
- lower/higher-is-better direction;
- expected heldout outer-unit count;
- favourable minimum augmented wins;
- adverse minimum baseline wins;
- tie tolerance, if nonzero.

Use `PredictiveComplementarityDeclaration` and `evaluate_predictive_complementarity()` to preserve favourable/adverse/no-confirmed results without post-outcome threshold changes.

### Gate 9 — outcome opening once

Use the machine-checkable outcome-access freeze ledger. Run exact count/estimability checks first. If those fail, stop before model fitting/scoring. Otherwise fit/score the already frozen baseline and augmented learner once.

Do not retune worlds, source policy, Layer B, learner, conventional features, metrics or semantics after outcome access.

## 13. Complementarity execution contract

For each heldout outer unit `u` compute a paired score:

```text
S_base(u) = strong learner with frozen conventional features
S_aug(u)  = same learner + same conventional features + frozen Layer B
```

For lower-is-better metrics:

```text
Delta = mean_u S_aug(u) - mean_u S_base(u)
```

Favourable requires both:

- `Delta < 0` beyond the frozen tie tolerance; and
- at least the frozen minimum number of augmented outer-unit wins.

Adverse is the symmetric reverse condition. Conflicting macro/direction evidence remains:

`no_confirmed_complementary_added_value`

Higher-is-better metrics reverse score direction only.

The evaluator canonicalizes outer-unit order and requires exactly the prospectively declared number of unique finite paired scores.

## 14. Frozen earlier lessons

### STOC

Independent world universe falsified during calibration before heldout prediction. This motivated prospective scale/adequacy gates. STOC is not reused.

### SIVFLORA

Independent pre-outcome non-estimable. Not rescued.

### Azores

Independent pre-model non-estimable. Not rescued.

### A-Islands

Exploratory exact-world structural information; not independent. Earlier predictive extension adverse.

### Glanville

Completed independent forecast; exact world identity adverse as direct supervised encoding. Established the two-layer architecture.

### Daphnia

Completed fresh independent forecast; symmetric Layer B slightly favourable vs mean-only but clearly adverse vs strong RF. Established the paired complementarity endpoint as the next valid prediction question.

## 15. Prior-art / novelty boundary

Do not claim generic novelty for:

- threshold filtration, percolation, MST or critical connectivity;
- dynamic reachability;
- stepping stones, least-cost or circuit methods;
- suitable + accessible functional habitat;
- dynamic/mechanistic SDMs;
- ensembles/model averaging;
- permutation-invariant set functions, DeepSets or distributional summaries generally;
- generic feature augmentation, stacking or model comparison;
- Bayesian/credal/imprecise prediction;
- viability kernels;
- history matching/NROY;
- Pareto/minimum-relaxation frontiers;
- multiverse analysis;
- generic adaptive survey design.

The candidate EOG contribution is the domain-specific composition:

> **a prospectively source- and scale-certified finite world universe is conditioned by positive distribution evidence; exact world identities remain auditable sequential update state; a label-invariant representation exposes surviving world-set structure; later evidence contracts or falsifies the same frozen rule universe; and any predictive added-value claim is tested as a paired augmentation of a strong unchanged predictor without post-outcome retuning.**

## 16. Stop rules

- Do not add operators to rescue failed validation.
- Do not weaken comparators after outcomes.
- Do not retune graph scale after responses.
- Do not expose arbitrary world labels to the default prediction head after independent adverse evidence.
- Do not tune the symmetric summary on Daphnia heldout outcomes and relabel the result prospective.
- Do not change learner family, hyperparameters or conventional features between paired baseline and augmented fits.
- Do not rerun Daphnia and call the new complementarity endpoint independently confirmed.
- Do not sequentially shop datasets merely to overturn the adverse standalone external-prediction result.
- Do not call structural thresholds biological dispersal limits without calibration.
- Do not call survey zero latent biological absence without observation justification.
- Do not promote raw support to occupancy/colonisation probability.
- Do not equate propagation depth with physical time without calibration.
- Do not claim universal robustness outside the declared world certificate.
