# EOG method-validation protocol

## Status

This document defines how the active EOG method and the EOG-WF forecast algorithm are to be validated after the 2026-08 methodological audit.

The audit does **not** reopen or retune frozen empirical results. A-Islands, SIVFLORA, Azores, and the independent STOC attempt remain historical evidence under the contracts with which they were run.

Current verdict:

> **EOG's finite world-set inference is coherent conditionally, and EOG-WF is an implemented inverse-conditioned world-set forecasting algorithm. The first independent EOG-WF attempt (STOC) exposed a world-universe structural-adequacy failure before heldout prediction. Independent identity-preserving forecast value and predictive superiority therefore remain unconfirmed.**

The active contribution claim remains narrower than a new generic SDM, dispersal algorithm, ensemble method, credal classifier, or universal forecasting mathematics.

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

The finite core explicitly conditions on declared source/anchor policy and declared transition operators. It does not infer one true historical route.

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

The compatible set may remain equal, contract, or become empty. An empty set is finite-universe falsification rather than a licence to change thresholds after seeing the evidence.

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

Likewise, reachability support is not called occupancy probability, colonisation probability, migration rate, ancestry probability, or demographic connectivity unless a calibrated stochastic model supports that interpretation. A forecast horizon is propagation depth, not physical time, unless independently calibrated.

## 4. Validation estimands must remain separate

### A. Algorithmic correctness

Question:

> **Does the inverse-filter → forward-propagate → update/falsify algorithm obey its declared finite-world invariants?**

Required known-truth tests include exact compatible-world filtering, cumulative-support monotonicity, world-identity preservation, monotone world contraction, finite-universe falsification, separately declared local gates, and deterministic fingerprints.

Current state: supported by `tests/test_world_forecast.py` plus package-wide regression.

### B. Identity-preserving forecast value

Question:

> **Does retaining exact world identity preserve a scientifically actionable forecast distinction that is erased by a predeclared compression of the same world universe, and can independent evidence discriminate that distinction?**

A valid test requires a predeclared collision/equivalence class in which targets have the same compressed summary but differ in exact supporting-world identity or decomposition. Independent evidence must then test a consequence that differs between those worlds.

Success validates the identity-preserving forecast state, not historical truth.

### C. Predictive added value

Question:

> **Does EOG-WF improve genuinely held-out ecological prediction beyond strong predeclared comparators?**

At minimum distinguish:

1. **same-world compression comparators** — scalar frequency, union, mean/envelope summaries using the same frozen world universe but erasing identity;
2. **external ecological comparators** — strong SDM, dynamic-SDM, accessibility/dispersal, occupancy or other process models appropriate to the system.

A same-world comparison isolates value of identity retention. It is not automatically a state-of-the-art ecological-method comparison.

### D. Historical identification

Actual routes, ancestry or colonisation sequence require stronger independent evidence and are not implied by the first three estimands.

## 5. World-universe adequacy is part of the method

A mathematically exact finite-world forecast can still be ecologically or structurally useless if the declared universe is poorly justified.

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

### 5.1 Response-blind structural adequacy is mandatory

The STOC independent attempt showed that a response-blind threshold rule can still be structurally inappropriate for the prediction scale. Its most permissive frozen geography-only world used an 18.11 km threshold across 1,003 country-scale sites and produced 231 connected components, 101 isolated sites, and a largest component containing only 8.67% of sites. All 20 species then falsified the world universe during calibration before heldout prediction.

Therefore, **before species/response outcomes are opened**, every future candidate world universe must pass a structural adequacy screen using only node geometry, non-response environmental inputs, externally justified process constraints, and the predeclared forecast horizon.

The screen must freeze and report, as appropriate to the representation:

- component count and largest-component fraction for graph worlds;
- isolated-node fraction;
- degree/edge-density summaries;
- whether the declared horizon can traverse the intended spatial support in the graph topology;
- which worlds are structurally local versus system-spanning;
- whether intersection of geography/environment/barrier rules fragments the universe beyond the intended estimand;
- why at least one declared world is capable of representing the spatial scale to which the forecast is intended to generalise.

Crucially, this screen **must not inspect species occurrences, heldout responses, world-identity forecast results, or predictive scores**. It is a design-admissibility gate, not a post-outcome tuning mechanism.

There is no universal numerical connectivity cutoff. Adequacy thresholds must be justified prospectively from the prediction target, external ecological knowledge, or a generic design rule applicable before responses are seen. A rule may legitimately allow fragmented worlds when fragmentation itself is the intended process hypothesis; the certificate must then say so.

No `robust`, `excluded`, `impossible`, or high-confidence wording may exceed both the ecological adequacy record and this structural certificate.

## 6. Anchor/source conditionality

Training or observed occurrences may be used as realized anchors under an explicit policy. They must not silently become inferred ancestral sources.

Every empirical forecast must state the conditioning explicitly, for example:

> reachable from the declared training anchors under the declared world universe

rather than:

> the species historically dispersed from these locations.

Heldout targets must not contribute to their own anchor set.

## 7. Local viability and persistence gates

EOG-WF may consume local-state information from SDMs, mechanistic models, or independently declared support layers.

If used, viability and persistence must remain separately inspectable. The default forecast algorithm must not manufacture an occupancy-like probability by multiplying reachability × viability × persistence unless a calibrated generative model justifies that operation.

## 8. Response and absence semantics

A catalogue non-record may be used as a negative class only when the prediction target is explicitly catalogue-record status under the frozen rule. It is not biological absence by default.

Claims about occupancy, extinction, failed colonisation, unsuitable habitat or calibrated binary forecast skill require an observation/detection or survey-completeness interpretation appropriate to that claim.

Positive-only sequential forecast validation is permitted when the endpoint is world contraction/discrimination rather than binary absence prediction.

## 9. Pre-outcome eligibility screen

Before freezing an EOG-WF empirical contract, a candidate dataset must pass a generic eligibility screen that does not inspect the forecast outcome.

The screen may inspect source/schema metadata and non-response vocabularies needed for deterministic semantic mappings. It must establish:

1. immutable source identity and licence/provenance;
2. unambiguous node/spatial-unit mapping;
3. environmental/local-state input coverage;
4. taxonomic/rank/establishment vocabulary sufficient for the intended semantic population;
5. response semantics and whether non-records can support the planned target;
6. enough genuinely independent heldout spatial or temporal units;
7. **response-blind structural adequacy of the proposed world universe for the intended spatial/horizon scale**;
8. no dependence of eligibility on EOG-WF forecast results.

The Azores lesson concerns semantic/schema eligibility; the STOC lesson concerns world-structure eligibility. Neither blocked system is reopened or rescued by this prospective rule.

## 10. Dependence and uncertainty

Validation units must match the intended generalisation target. A large number of rows or bootstrap draws does not create additional independent spatial/temporal units.

Confirmatory interval/test language with few independent units requires pre-outcome design-specific justification; otherwise report paired outer-unit effects and uncertainty descriptively.

## 11. Required EOG-WF empirical validation sequence

### Gate 0 — generic source/schema eligibility

Pass source/schema/node/input/taxonomy/response/independent-unit checks before EOG-specific outcome design.

### Gate 1 — response-blind structural world eligibility

Using no species responses, build the proposed world universe and freeze structural diagnostics. Reject or redesign the candidate **before response access** if the universe cannot represent the intended spatial/horizon scale under its prospectively declared adequacy rule.

### Gate 2 — world-universe adequacy freeze

Freeze world IDs, natural versus analyst-choice dimensions, provenance, parameter/threshold rationale, anchor policy, coverage boundary, horizon interpretation and universe-expansion sensitivity.

### Gate 3 — forecast-state freeze

Freeze local-state inputs, gates, horizon, output classes/fingerprints, and full-universe-falsification handling.

### Gate 4 — identity-preserving comparison freeze

Predeclare the same-world compression, the identity distinction it erases, the independent evidence that can discriminate it, and the no-added-value rule.

### Gate 5 — predictive-comparator freeze

When calibrated prediction is a claim, freeze same-world and external ecological comparators, holdout structure, prediction target/loss, dependence-aware inference and no-added-value rule.

### Gate 6 — run once

Open the frozen response/evidence once. Do not retune worlds, structural adequacy rule, gates, horizons, comparators or semantic population after seeing forecast results.

## 12. Decision rules

The following statements remain separate:

- **algorithmic correctness** — EOG-WF performs its declared inverse/forward/update operations;
- **world-universe adequacy** — the response-blind declared worlds can represent the intended design scale under a prospectively justified structural certificate;
- **ecological interpretability** — world/gate/response semantics correspond to stated ecological concepts;
- **independent identity-preserving value** — independent evidence discriminates world-identity forecast distinctions erased by a frozen compression;
- **predictive added value** — heldout predictive loss/score improves over stated comparators;
- **historical identification** — actual history is identified.

Current EOG-WF status:

- algorithmic correctness: **supported by known-truth and package tests**;
- world-universe adequacy: **not solved generically; first independent STOC universe failed before prediction**;
- ecological interpretability: **conditional on explicit world/anchor/gate/response contracts**;
- independent identity-preserving value: **unconfirmed**;
- predictive added value: **unconfirmed for EOG-WF; STOC did not reach comparison**;
- historical identification: **not claimed**.

## 13. Stop rules

- Do not add an operator to rescue a failed forecast validation.
- Do not retune a world universe on an opened dataset and call the rerun independent.
- Do not weaken a comparator after outcome inspection.
- Do not call analyst-choice quantiles biological dispersal limits.
- Do not call catalogue non-record biological absence without an observation model.
- Do not fuse support layers into an occupancy probability without calibration.
- Do not equate propagation steps with physical time without calibration.
- Do not use small-cluster resampling to manufacture apparent replication.
- Do not require predictive superiority as proof of algorithmic correctness.
- Do not use known-truth algorithmic success as proof of ecological superiority.
- Do not claim universal robustness outside the declared adequacy certificate.

## 14. Literature anchors for the methodological boundary

These sources motivate boundaries EOG adopts; they are not novelty claims for EOG.

- Soberón & Peterson (2005), *Interpretation of Models of Fundamental Ecological Niches and Species' Distributional Areas*, DOI `10.17161/bi.v2i0.4`.
- Barve et al. (2011), *The crucial role of the accessible area in ecological niche modeling and species distribution modeling*, DOI `10.1016/j.ecolmodel.2011.02.011`.
- Araújo & New (2007), *Ensemble forecasting of species distributions*, DOI `10.1016/j.tree.2006.09.010`.
- Merow et al. (2011), *Developing Dynamic Mechanistic Species Distribution Models*, DOI `10.1086/660295`.
- Steegen et al. (2016), *Increasing Transparency Through a Multiverse Analysis*, DOI `10.1177/1745691616658637`.
- Roberts et al. (2017), *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*, DOI `10.1111/ecog.02881`.
- Cameron, Gelbach & Miller (2008), *Bootstrap-Based Improvements for Inference with Clustered Errors*, DOI `10.1162/rest.90.3.414`.

Accordingly, EOG-WF's candidate distinct contribution is not “adding accessibility”, “using several models”, “adding dispersal”, “returning prediction sets”, or generic multiverse mathematics. It is the biogeographic inverse-to-forward composition in which occurrence-conditioned structural worlds retain identity as sequential forecast state, underidentification remains explicit, and later positive evidence contracts or falsifies the frozen finite world universe.
