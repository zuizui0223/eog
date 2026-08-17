# EOG method-validation protocol

## Status

This document defines how the active EOG method and EOG-WF forecast algorithm are validated after the 2026-08 methodological audit and the first independent STOC attempt.

Current verdict:

> **EOG-WF is an implemented inverse-conditioned world-set forecast/update algorithm with known-truth support. Independent ecological value remains unconfirmed. Future independent tests must pass source/process semantics, response-blind world-scale construction, and structural adequacy before outcomes are opened.**

Frozen empirical results are not reopened or retuned under this improved protocol.

## 1. Inferential and predictive objects

EOG keeps four objects distinct:

1. **local possibility** — locally supported under a declared environmental/process representation;
2. **reachability** — reachable from a declared source/anchor set under a declared transition rule;
3. **distributional realizability** — compatible with observed positive states inside a declared world;
4. **historical truth** — the actual route, sequence, ancestry, movement rate, or demographic process in nature.

For finite world universe `W`, observations `O`, and compatibility predicate `C(w,O)`:

```text
W(O) = {w in W : C(w,O)}
```

This is an unranked compatible set unless an independently justified ranking model was prospectively declared.

EOG-WF propagates each retained world separately. The canonical forecast object is:

```text
compatible world × horizon × node
```

plus robust/contingent/excluded projections.

Unobserved locations are not biological absences without an explicit observation/detection interpretation.

## 2. What is methodologically valid now

### 2.1 Conditional world reconstruction

The finite core conditions on declared sources and transitions. It does not infer one true historical route.

### 2.2 World identity preservation

Mutually exclusive worlds may remain separate rather than being averaged/unioned before interpretation or update.

### 2.3 Finite-universe forecast classes

At any forecast horizon a node may be:

- `robustly_supported` — supported by every compatible world;
- `contingent` — supported by some but not all compatible worlds;
- `excluded_in_all_worlds` — supported by no compatible world.

These are exact only over the enumerated certified universe.

### 2.4 Sequential update

Under positive-constraint logic:

```text
W(O ∪ O+) ⊆ W(O)
```

New positive evidence may leave the world set unchanged, contract it, or falsify the entire finite universe. World definitions are not altered after evidence is opened.

## 3. Prior-art / claim boundary

Do not claim generic novelty for:

- graph threshold filtration, critical connectivity, percolation or minimum spanning trees;
- dynamic/time-respecting reachability;
- stepping stones, least-cost paths, circuit redundancy;
- suitable + accessible functional habitat;
- dynamic/mechanistic SDMs;
- ensemble/model averaging;
- Bayesian/credal/imprecise prediction generally;
- viability kernels;
- history matching/NROY;
- minimum-relaxation/Pareto frontiers;
- multiverse analysis;
- generic adaptive survey design.

Uncalibrated support is not occupancy, colonisation, migration or ancestry probability. Propagation depth is not physical time without calibration.

## 4. Validation estimands remain separate

### A. Algorithmic correctness

Does inverse-filter → forward-propagate → update/falsify obey its declared invariants?

Known-truth tests require:

- compatible-world filtering;
- monotone cumulative first-passage support;
- exact supporting-world identity preservation;
- monotone contraction after added positive evidence;
- finite-universe falsification;
- separate viability/persistence gates;
- deterministic fingerprints.

Current state: supported by package tests.

### B. World-universe adequacy

Was the declared world set structurally capable of representing the intended forecast scale **before species outcomes were opened**?

This is now a first-class estimand because STOC showed that a response-blind threshold rule can still occupy the wrong graph scale.

### C. Identity-preserving forecast value

Does exact world identity preserve a scientifically actionable forecast distinction erased by a frozen compression of the same worlds, and does independent evidence discriminate it?

### D. Predictive added value

Does EOG-WF improve genuinely heldout prediction over:

1. matched same-world compression; and
2. strong external ecological comparators appropriate to the system?

### E. Historical identification

Actual routes/ancestry/colonisation sequence require stronger evidence and are not implied by A–D.

## 5. World scale construction

World-universe construction must precede response access.

### 5.1 Externally calibrated process scale

When defensible movement/dispersal/transport/barrier evidence exists, use it prospectively and document provenance and uncertainty.

### 5.2 Response-blind structural scale ladder

When no defensible biological scale exists, analyst-choice structural worlds may be generated using `src/eog/v2/world_scale_ladder.py`.

For prospectively declared largest-component targets `c1 < ... < ck`, choose the minimum metric threshold reaching each regime. Targets are study declarations, not universal constants. The resulting thresholds are not biological dispersal limits without external calibration.

Primary-only structural worlds should be retained when secondary geography×environment/barrier intersections would otherwise force the entire universe into a narrower fragmented regime.

## 6. Structural adequacy gate

After world axes are composed, audit the candidate universe using `src/eog/v2/world_adequacy.py` before species response access.

The response-blind audit may include:

- weak component count;
- largest-component fraction;
- isolated-node fraction;
- degree summaries;
- directed horizon-reachable fractions.

Pass/fail criteria must be declared prospectively and justified relative to the forecast claim. EOG embeds no universal structural cutoff.

Fragmented worlds are allowed when fragmentation is scientifically intended. The universe as a whole must nevertheless include structural regimes capable of expressing the forecast domain claimed by the study.

## 7. Process closure and source semantics

Before response access, the study must answer:

> **Can future/unsampled positive states reasonably be conditioned on propagation from the declared internal source/anchor system, or are important source states located outside the declared node universe?**

This is separate from graph connectivity.

A candidate system is eligible only if one of the following is prospectively justified:

1. the node universe approximately closes the relevant distribution-forming process over the forecast interval;
2. external source states are represented explicitly in the declared worlds;
3. the scientific target is explicitly conditional on internal realized sources and does not pretend to cover external recruitment.

Do not silently treat observed training sites as ancestral sources. Do not use an anchor-conditioned spread model for a system dominated by unconstrained external immigration and then interpret failure as evidence about EOG-WF prediction quality.

The process-closure check is conceptual and evidence-based rather than a universal numerical gate.

## 8. Anchor/source conditionality

Training occurrences may be realized anchors under an explicit policy, including fixed-source or self-excluded evaluation. Heldout targets must never contribute to their own anchor set.

Use wording such as:

> reachable from declared training-period realized anchors under the certified world universe

rather than asserting historical dispersal from those anchors.

## 9. Local viability and persistence gates

EOG-WF may consume SDM/mechanistic/local-state layers, but viability and persistence must remain separately inspectable. Do not multiply support layers into an occupancy-like probability without a calibrated generative model.

## 10. Response and absence semantics

Catalogue/non-record data may be a negative class only for an explicitly stated record/detection target. It is not biological absence by default.

Claims about occupancy, failed colonisation, extinction or calibrated binary skill require appropriate detection/survey-completeness interpretation.

Positive-only sequential validation is valid when the endpoint is world contraction/discrimination rather than binary absence prediction.

## 11. Dependence and validation units

Validation units must match intended generalisation. Many site/species/year rows do not automatically create independent spatial or temporal replicates.

Small-cluster confirmatory inference requires prospectively justified operating characteristics; bootstrap repetition does not create new independent units.

## 12. Required independent EOG-WF sequence

### Gate 0 — immutable source and semantic eligibility

Freeze source identity, licence/provenance, nodes, non-response inputs, taxonomic/response vocabulary and independent holdout structure.

### Gate 1 — process closure/source semantics

Freeze why internal anchors are an appropriate conditional source system, or explicitly declare external source states / narrower conditional claim.

### Gate 2 — response-blind world-scale construction

Freeze process-calibrated distances or analyst-choice structural target regimes and all secondary world axes.

### Gate 3 — response-blind structural adequacy

Run and freeze the world-universe structural audit. Stop before response access if the prospectively declared gate fails.

### Gate 4 — forecast state and comparator contract

Freeze:

- anchor rule;
- horizon and interpretation;
- viability/persistence gates if any;
- same-world compression comparator;
- strong external comparator;
- identity-discrimination endpoint;
- predictive target/metric when appropriate;
- dependence-aware analysis;
- favourable/null/adverse/non-estimable rules.

### Gate 5 — open response once

Run once. Do not retune world scales, anchors, horizon, models or semantics after outcome access.

## 13. STOC lesson remains frozen

STOC's first independent EOG-WF universe was falsified during calibration for 20/20 response-estimable species before heldout prediction.

Post-hoc structural diagnosis showed the most permissive frozen geography world had a largest component of only 8.67% of 1,003 sites; 8,702 positive targets were disconnected from fixed anchors versus 48 that were connected but beyond the eight-hop horizon.

A later response-blind method diagnostic demonstrated broader structural regimes, but those thresholds do not replace the frozen STOC universe. STOC remains:

`independent_world_universe_falsified_on_calibration`

## 14. Stop rules

- Do not add an operator to rescue a failed validation.
- Do not weaken comparators after outcome inspection.
- Do not retune graph scale after species responses are seen.
- Do not call structural thresholds biological dispersal limits without calibration.
- Do not treat internal anchors as a closed source process when important external recruitment is unrepresented.
- Do not call non-detection biological absence without an observation model.
- Do not fuse support layers into occupancy probability without calibration.
- Do not equate propagation depth with physical time without calibration.
- Do not reuse a failed opened dataset as a fresh independent confirmation after redesign.
- Do not claim universal robustness outside the declared certificate.

## 15. Literature anchors

These sources define boundaries; they are not EOG novelty claims.

- Soberón & Peterson (2005), DOI `10.17161/bi.v2i0.4`.
- Barve et al. (2011), DOI `10.1016/j.ecolmodel.2011.02.011`.
- Urban & Keitt (2001), DOI `10.1890/0012-9658(2001)082[1205:LCAGTP]2.0.CO;2`.
- Metzger & Décamps (1997), DOI `10.1016/S1146-609X(97)80075-6`.
- Moilanen (2011), DOI `10.1111/j.1365-2664.2011.02062.x`.
- Araújo & New (2007), DOI `10.1016/j.tree.2006.09.010`.
- Merow et al. (2011), DOI `10.1086/660295`.
- Roberts et al. (2017), DOI `10.1111/ecog.02881`.

The candidate EOG-WF contribution is the biogeographic composition in which a prospectively source- and scale-certified finite world universe is occurrence-conditioned, world identity is retained as sequential forecast state, and later evidence contracts or falsifies that frozen universe without post-outcome retuning.
