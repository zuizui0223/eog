# EOG method-validation protocol

## Status

This document defines how the active EOG method and the EOG-WF forecast algorithm are to be validated after the 2026-08 methodological audit.

The audit does **not** reopen or retune any frozen empirical result. In particular, the A-Islands strong-reference result, the SIVFLORA climate block, and the Azores pre-model taxon-scope block remain unchanged historical evidence.

Current verdict:

> **EOG's finite world-set inference is coherent conditionally, and EOG-WF is now an implemented inverse-conditioned world-set forecasting algorithm. Independent identity-preserving forecast value and predictive superiority remain unconfirmed and must be tested separately.**

The active contribution claim is therefore narrower than a new generic SDM, dispersal algorithm, ensemble method, credal classifier, or universal forecasting mathematics.

## 1. Inferential and predictive objects

EOG keeps four scientific objects distinct:

1. **local possibility** — locally supported under a declared environmental/process representation;
2. **reachability** — reachable from a declared anchor/source set under a declared transition rule;
3. **distributional realizability** — compatible with the observed positive occurrence configuration inside a declared world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate, or demographic process in nature.

For a declared finite world universe `W`, observations `O`, and compatibility predicate `C(w, O)`, the inverse object is

```text
W(O) = {w in W : C(w, O)}
```

This is an **unranked compatible set** unless an independently justified ranking model was declared.

EOG-WF adds a forward object. For each retained world `w`, node `x`, and horizon `h`, it computes cumulative first-passage support `S_w(x,h)` and retains the full world-indexed forecast state rather than averaging the worlds before prediction.

The canonical prediction object is therefore

```text
compatible world × horizon × node
```

plus robust/contingent/excluded projections derived from that cube.

Observed occurrences are positive realized constraints. Unobserved locations are not biological absences without an explicit observation/detection interpretation.

## 2. What is methodologically valid now

### 2.1 Conditional world reconstruction

The finite core explicitly conditions on declared source/anchor policy and declared transition operators. It does not infer one true historical route. This is a valid conditional inverse question.

### 2.2 World identity preservation

If two admissible worlds imply different structures or forecasts, EOG may retain them separately rather than average, union, or select them before interpretation. An aggregate is allowed only when the scientific estimand itself is the aggregate.

### 2.3 Finite-universe forecast classes

At each forecast horizon, EOG-WF may classify a node as:

- `robustly_supported` — supported by every compatible world;
- `contingent` — supported by some but not every compatible world;
- `excluded_in_all_worlds` — supported by none of the compatible worlds.

These statements are exact only over the enumerated, certified universe. They are conditional finite-world statements, not universal ecological certainty.

### 2.4 Underidentification is forecast state

If several worlds remain compatible, EOG-WF carries those alternatives into the forecast. Failure to identify one history is not an algorithmic failure.

### 2.5 Sequential update without retuning

When new positive evidence is added, the same frozen world universe is re-evaluated. Under the declared positive-constraint logic,

```text
W(O ∪ O+) ⊆ W(O)
```

The compatible set may remain equal, contract, or become empty. An empty set is reported as finite-universe falsification rather than repaired by changing thresholds/world definitions after seeing the evidence.

## 3. What the method must not claim

EOG/EOG-WF must not claim novelty for, or superiority simply by containing:

- dynamic/time-respecting reachability;
- critical connection thresholds or stepping stones;
- least-cost/minimum-exposure paths;
- circuit-style redundancy;
- suitability + accessibility / functional habitat;
- dynamic/mechanistic SDMs;
- ensemble/consensus prediction or model averaging;
- Bayesian/credal/imprecise-probability classification in general;
- viability kernels or generic robust reachability;
- history matching / NROY filtering;
- minimum-relaxation/Pareto/falsification-frontier mathematics;
- multiverse analysis;
- generic adaptive survey design.

Likewise, a probability-like reachability support is not called occupancy probability, colonisation probability, migration rate, ancestry probability, or demographic connectivity unless a calibrated stochastic model supports that interpretation.

A forecast horizon is propagation depth, not physical time, unless independently calibrated.

## 4. Validation estimands must remain separate

### A. Algorithmic correctness

Question:

> **Does the inverse-filter → forward-propagate → update/falsify algorithm obey its declared finite-world invariants?**

Required known-truth tests include:

- exact reproduction of compatible-world filtering;
- monotone cumulative first-passage support through horizon;
- preservation of exact supporting-world identity;
- monotone contraction of compatible worlds after added positive evidence;
- finite-universe falsification when all worlds are contradicted;
- local viability/persistence gates applied separately from reachability;
- deterministic fingerprints for frozen worlds, gates and forecast state.

Current state: supported by `tests/test_world_forecast.py` plus package-wide regression.

### B. Identity-preserving forecast value

Question:

> **Does retaining exact world identity preserve a scientifically actionable forecast distinction that is erased by a predeclared compression of the same world universe, and can independent evidence discriminate that distinction?**

A valid test requires a predeclared collision/equivalence class in which two targets have the same compressed summary but differ in exact supporting-world identity or decomposition.

Independent evidence must then test a consequence that differs between those worlds.

Examples include:

- a later positive occurrence at a site supported by only a subset of colliding worlds;
- time-stamped colonisation/recolonisation evidence;
- an independently surveyed intermediate site with explicit detection semantics;
- genetic or movement evidence whose interpretation was frozen before inspecting the EOG forecast.

Success validates the identity-preserving forecast state, not historical truth.

### C. Predictive added value

Question:

> **Does EOG-WF improve genuinely held-out ecological prediction beyond strong predeclared comparators?**

At minimum distinguish:

1. **same-world compression comparators** — scalar frequency, union, mean/envelope summaries that use the same frozen world universe but erase identity;
2. **external ecological comparators** — strong SDM, dynamic-SDM, accessibility/dispersal, occupancy or other process models appropriate to the scientific system.

A same-world comparison isolates value of identity retention. It is not automatically a state-of-the-art ecological-method comparison.

Predictive failure does not by itself invalidate a correctly implemented uncertainty/identifiability representation. Predictive success does not establish historical truth.

### D. Historical identification

Actual routes, ancestry or colonisation sequence require stronger independent evidence and are not implied by the first three estimands.

## 5. World-universe adequacy is part of the method

A mathematically exact finite-world forecast can still be ecologically weak if the declared universe is poorly justified.

Every future world dimension must be typed as one of:

- **natural/process uncertainty** — biologically plausible processes or parameter regimes;
- **analyst-choice uncertainty** — products, thresholds, preprocessing choices, graph constructions or other defensible analytical alternatives.

For each dimension record:

1. provenance or external rationale;
2. whether values are biologically calibrated or only sensitivity-grid levels;
3. why the enumerated levels are admissible;
4. which plausible alternatives remain outside the certificate;
5. how forecast classes change when admissible worlds are added.

Quantile-based geographic/environmental thresholds are acceptable analyst-choice sensitivity worlds. They are **not** automatically species-specific dispersal limits or biological tolerance thresholds.

No `robust`, `excluded`, `impossible`, or high-confidence wording may exceed this adequacy record.

## 6. Anchor/source conditionality

Training or observed occurrences may be used as realized anchors under an explicit policy, including fixed-source or self-excluded evaluation.

They must not silently become inferred ancestral sources.

Every empirical forecast must state the conditioning explicitly, for example:

> reachable from the outer-training realized occurrences under the declared world universe

rather than:

> the species historically dispersed from these locations.

Held-out targets must not contribute to their own anchor set.

## 7. Local viability and persistence gates

EOG-WF may consume local-state information from SDMs, mechanistic models, or independently declared support layers.

If used, viability and persistence must remain separately inspectable. The default forecast algorithm must not manufacture an occupancy-like probability by multiplying reachability × viability × persistence unless a calibrated generative model justifies that operation.

A locally suitable node can remain all-world excluded through accessibility constraints. A reachable node can fail a predeclared viability gate. These are different failure modes and must remain distinguishable.

## 8. Response and absence semantics

A catalogue non-record may be used as a negative class only when the prediction target is explicitly **catalogue-record status under the frozen catalogue rule**.

It is not biological absence by default.

Claims about occupancy, extinction, failed colonisation, unsuitable habitat or calibrated binary forecast skill require an observation/detection or survey-completeness model appropriate to that claim.

Positive-only sequential forecast validation is permitted when the endpoint is world contraction/discrimination rather than binary absence prediction.

## 9. Pre-outcome eligibility screen

Before freezing an EOG-WF empirical contract, a candidate dataset must pass a **generic eligibility screen** that does not inspect the forecast outcome.

The screen may inspect source/schema metadata and non-response vocabularies needed for deterministic semantic mappings. It must establish:

1. immutable source identity and licence/provenance;
2. unambiguous node/spatial-unit mapping;
3. environmental/local-state input coverage;
4. taxonomic/rank/establishment vocabulary sufficient for the intended semantic population;
5. response semantics and whether non-records can support the planned target;
6. enough genuinely independent held-out spatial or temporal units;
7. no dependence of eligibility on EOG-WF forecast results.

This preserves the Azores lesson prospectively without reopening its frozen stop result.

## 10. Dependence and uncertainty

Validation units must match the intended generalisation target.

For a claim that generalises to new islands, island-level holdout remains the primary independence unit; thousands of species-island rows must not be treated as thousands of independent island replicates.

A large number of bootstrap draws does not create additional independent units. Therefore:

- a percentile bootstrap over very few outer units is descriptive unless design-specific operating characteristics were justified pre-outcome;
- confirmatory interval/test language requires pre-outcome simulation or another design-specific justification;
- otherwise report paired outer-unit effects, direction counts and uncertainty descriptively.

The frozen nine-island Azores contract remains historical and is not retuned.

## 11. Required EOG-WF empirical validation sequence

### Gate 0 — generic eligibility

Pass source/schema/node/input/taxonomy/response/independent-unit checks before EOG-specific outcome design.

### Gate 1 — world-universe adequacy freeze

Freeze world IDs, natural versus analyst-choice dimensions, provenance, parameter/threshold rationale, anchor policy, coverage boundary, horizon interpretation and universe-expansion sensitivity.

### Gate 2 — forecast-state freeze

Freeze:

- local viability/persistence inputs when used;
- reachability/viability/persistence gates;
- forecast horizon;
- output classes and fingerprints;
- rule for handling full universe falsification.

### Gate 3 — identity-preserving comparison freeze

Predeclare:

- a compression of the same world universe;
- the collision/disagreement object erased by that compression;
- the later independent evidence that can discriminate the alternatives;
- the result that counts as no added identity-preserving forecast value.

### Gate 4 — predictive-comparator freeze

Only when calibrated prediction is itself a claim, predeclare:

- same-world compression comparator(s);
- external ecological comparator(s);
- holdout structure;
- prediction target and loss/score;
- dependence-aware inference;
- no-added-value rule.

### Gate 5 — run once

Open the frozen outcome/evidence once. Do not retune worlds, gates, horizons, comparators or semantic population after seeing forecast results.

## 12. Decision rules

The following statements remain separate:

- **algorithmic correctness** — EOG-WF performs its declared inverse/forward/update operations;
- **ecological interpretability** — world/gate/response semantics correspond to stated ecological concepts;
- **independent identity-preserving value** — independent evidence discriminates world-identity forecast distinctions erased by a frozen compression;
- **predictive added value** — held-out predictive loss/score improves over stated comparators;
- **historical identification** — actual history is identified.

Current EOG-WF status:

- algorithmic correctness: **supported by known-truth and package tests**;
- ecological interpretability: **conditional on explicit world/anchor/gate/response contracts**;
- independent identity-preserving value: **unconfirmed**;
- predictive added value: **not established; earlier frozen strong-reference extensions include adverse evidence**;
- historical identification: **not claimed**.

## 13. Stop rules

- Do not add an operator to rescue a failed forecast validation.
- Do not weaken a comparator after outcome inspection.
- Do not call analyst-choice quantiles biological dispersal limits.
- Do not call catalogue non-record biological absence without an observation model.
- Do not fuse support layers into an occupancy probability without calibration.
- Do not equate propagation steps with physical time without calibration.
- Do not use small-cluster resampling to manufacture apparent replication.
- Do not broaden a frozen blocked contract on the same opened dataset and call it independent confirmation.
- Do not require predictive superiority as proof of algorithmic correctness.
- Do not use known-truth algorithmic success as proof of ecological superiority.
- Do not claim universal robustness outside the declared adequacy certificate.

## 14. Literature anchors for the methodological boundary

These sources motivate boundaries EOG adopts; they are not novelty claims for EOG.

- Soberón & Peterson (2005), *Interpretation of Models of Fundamental Ecological Niches and Species' Distributional Areas*, DOI `10.17161/bi.v2i0.4` — distinguishes ecological niche/distributional interpretations and motivates explicit conceptual boundaries.
- Barve et al. (2011), *The crucial role of the accessible area in ecological niche modeling and species distribution modeling*, DOI `10.1016/j.ecolmodel.2011.02.011` — accessibility is already central to distribution-model calibration/testing logic.
- Araújo & New (2007), *Ensemble forecasting of species distributions*, DOI `10.1016/j.tree.2006.09.010` — multiple model projections and their disagreement/aggregation are established SDM concerns.
- Merow et al. (2011), *Developing Dynamic Mechanistic Species Distribution Models*, DOI `10.1086/660295` — dynamic, dispersal-explicit links between potential and realized distributions are established process-model territory.
- Steegen et al. (2016), *Increasing Transparency Through a Multiverse Analysis*, DOI `10.1177/1745691616658637` — retaining outcomes across defensible analytical choices is an established transparency/sensitivity principle.
- Roberts et al. (2017), *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*, DOI `10.1111/ecog.02881` — held-out design must respect dependence and intended generalisation.
- Cameron, Gelbach & Miller (2008), *Bootstrap-Based Improvements for Inference with Clustered Errors*, DOI `10.1162/rest.90.3.414` — bootstrap repetition does not remove the need to respect the number of independent clusters.

Accordingly, EOG-WF's candidate distinct contribution is **not** “adding accessibility”, “using several models”, “adding dispersal”, “returning prediction sets”, or generic multiverse mathematics. It is the biogeographic inverse-to-forward composition in which occurrence-conditioned structural worlds retain identity as sequential forecast state, underidentification remains explicit, and later positive evidence contracts or falsifies the frozen finite world universe.
