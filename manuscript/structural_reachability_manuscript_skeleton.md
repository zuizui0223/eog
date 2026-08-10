# When does landscape configuration add to pointwise distribution support?

## Alternative titles

1. **When does landscape configuration add to pointwise distribution support? An auditable reachability framework across islands and forest fragments**
2. **Environmental suitability is not structural reachability: contrasting evidence from 886 island plants and 60 forest birds**
3. **Auditable structural reachability as a conditional extension to species-distribution support**

## Provisional title

**When does landscape configuration add to pointwise distribution support? An auditable reachability framework across islands and forest fragments**

## Target article type

Original Research Paper, with *Ecological Informatics* as the first target. The paper should present a computational ecological framework, a positive confirmatory benchmark, a deliberately strong competitor benchmark, a negative external boundary result, and complete reproducibility contracts.

## Abstract

Species-distribution models commonly estimate local environmental support, while spatial cross-validation improves evaluation across structured landscapes. Neither operation alone represents how candidate locations are configured relative to observed populations through intermediate patches. We developed Environmental Occupancy Geometry (EOG), an auditable structural layer that converts frozen pointwise support and training occurrences into occurrence-anchored reachability and bottleneck features under predeclared graph scenarios. We evaluated incremental information rather than claiming replacement of species-distribution or connectivity models. In an A-Islands benchmark of 886 plant taxa across 842 islands, held-out islands were compared within strata matched for pointwise climatic support and distance to the nearest training occurrence. Structural connected frequency remained informative for 845 taxa (conditional concordance 0.618, species-bootstrap 95% interval 0.609–0.627). We then tested a stronger non-island reference using 60 bird species across 14 Tanzanian forest fragments. For every outer fold, one of 512 matrix-aware current-flow resistance combinations was selected from training labels only. Adding EOG connected frequency to patch area, current flow, their interaction, and nearest-occurrence distance increased held-out log loss by 0.032 (95% interval 0.017–0.049). Spatial-block sensitivity was weaker and uncertain. Structural reachability can therefore add information omitted by pointwise support and direct distance, but it is not a universally beneficial add-on once a strong landscape-specific connectivity model is present. Frozen positive and negative results define the framework’s current scope.

## Highlights

Each final highlight must remain within the journal character limit.

- EOG separates local environmental support from occurrence-anchored configuration.
- Island reachability added information after controlling support and source distance.
- EOG did not improve a strong matrix-aware forest-fragment reference.
- Positive and negative benchmarks define when structural features are informative.
- All graph choices, folds, failures, and result fingerprints are auditable.

## 1. Introduction

### 1.1 The gap between local support and realised configuration

A pointwise model can assign the same environmental support to two locations even when one lies within an occurrence-anchored patch chain and the other is detached by unavailable or low-support space. This is a genuine estimand gap, not simply a cross-validation problem.

Spatial blocks reduce optimistic evaluation caused by nearby training and test data. Spatial random effects represent residual dependence. Dynamic, mechanistic, diffusion, occupancy, circuit-theory, and resistance models can represent additional processes. The manuscript must therefore avoid the blanket claim that SDMs ignore space or dispersal.

The narrower problem is:

> When the available prediction is a frozen pointwise support surface, does occurrence-anchored landscape configuration retain information about held-out incidence after local support and simple source proximity are controlled?

### 1.2 Existing structural approaches

The related-work section must explicitly compare EOG with:

- spatial block cross-validation;
- spatial random effects and barrier SPDE models;
- dynamic occupancy and mechanistic spread models;
- habitat-patch networks;
- least-cost paths;
- circuit theory and current flow;
- graph centrality and metapopulation connectivity;
- support-component and superlevel-set topology.

EOG does not claim invention of graph connectivity, minimum spanning trees, minimax paths, current flow, or occurrence-distance predictors. Its contribution is an executable separation of local support, direct source distance, occurrence-anchored graph configuration, and stronger landscape-specific connectivity competitors under frozen held-out contracts.

### 1.3 Study questions

1. Does structural reachability distinguish held-out occupied and unoccupied islands after conditioning on pointwise support and nearest training occurrence distance?
2. Is the signal attributable only to environment-constrained edges, or does geography-only patch configuration retain information?
3. Does the same generic structural feature improve a non-island benchmark after matrix-aware current flow and source distance are already included?
4. What empirical boundary follows if the two systems give different incremental results?

## 2. Methods

### 2.1 Framework

Define three non-interchangeable quantities:

1. **local support** \(S_x\): a pointwise output from an independently specified model;
2. **direct source proximity** \(D_x\): distance to an outer-training occurrence anchor;
3. **structural reachability** \(R_x\): a graph quantity determined by all declared landscape nodes, edges, scenarios, and outer-training anchors.

A generic representation is:

\[
S_x=f(X_x),
\qquad
R_x=g(G, A_{\mathrm{train}}, x),
\]

where \(G\) is the frozen landscape graph and \(A_{\mathrm{train}}\) is the training-presence anchor set. Held-out labels never enter graph construction, parameter selection, scaling, or model fitting.

Connected frequency is the fraction of predeclared graph scenarios in which the target is connected to at least one training anchor. It is an assumption-robust structural diagnostic, not a colonisation probability.

### 2.2 A-Islands confirmatory benchmark

Report the complete frozen contract:

- A-Islands v1.0;
- 842-island universe;
- 886 APC-native taxa;
- five CHELSA variables;
- deterministic L2 logistic pointwise support;
- shared five-fold 5-degree spatial partition;
- 12 scenarios formed from four distance radii and declared environmental edge restrictions;
- training presences only as anchors;
- 5 × 5 pointwise-support × nearest-distance conditioning strata;
- species as the replication unit;
- 10,000 species bootstrap and 100,000 sign-flip diagnostic.

The primary endpoint is conditional concordance: within matched support-distance strata, how often does an occupied island have higher connected frequency than an unoccupied island?

Secondary analyses separate geography-only and environmentally constrained connected frequency. Median normalized geographic bottleneck is a direction-frozen secondary quantity.

### 2.3 Tanzania forest-fragment benchmark

Report:

- 14 surveyed fragments: nine East and five West Usambara;
- 89 source species and the predeclared 60-species eligible cohort;
- 42 structural forest-patch nodes in each region;
- official matrix rasters and source scripts;
- 512 resistance combinations for eucalyptus, tea, and other agriculture;
- 14-fold leave-one-fragment-out primary validation;
- geometry-only MST spatial-block sensitivity;
- source-code repairs frozen before outcomes;
- current-flow resistance selection using outer-training labels only;
- self-anchor exclusion for training structural features;
- identical L2 probability engine and training-only standardization in both tiers.

Strict reference:

`patch area + selected current flow + area × current flow + nearest training occurrence`

Candidate:

`reference + EOG connected frequency`

The primary endpoint is candidate-minus-reference paired Bernoulli log loss on exactly matched valid predictions. Negative differences favour EOG. Brier score is secondary. Species are averaged internally and then weighted equally.

### 2.4 Reproducibility and outcome boundary

For both benchmarks report:

- source identities and accepted hashes;
- cohort and fold fingerprints;
- graph and scenario declarations;
- training-only anchor and selection rules;
- explicit non-estimable groups and failure reasons;
- complete result fingerprints;
- whether each choice was frozen before or after outcome inspection.

Do not hide failed protocol proposals. Document the pre-outcome removal of conflicting A-Islands contracts, the geometry-only correction of degenerate Tanzania graph radii, and the post-result numerical fingerprint tolerance correction that did not alter raw model inputs.

## 3. Results

### 3.1 A-Islands: structural information beyond support and distance

Primary result:

- 845 estimable species;
- conditional connected-frequency concordance **0.6177466**;
- 95% interval **0.6086806–0.6269445**;
- sign-flip diagnostic approximately **1 × 10⁻⁵**.

Report the proportion of species above, equal to, and below 0.5, all failure categories, and the full-five-fold sensitivity subset.

### 3.2 Structural decomposition

- geography-only concordance **0.6147456**, 95% CI **0.6059505–0.6235729**;
- environmentally constrained concordance **0.6063727**, 95% CI **0.5974871–0.6154186**;
- bottleneck secondary approximately **0.5288**, 95% CI approximately **0.5177–0.5396**.

Interpret geography-only versus environment-constrained differences descriptively unless a contrast was frozen in advance.

### 3.3 Tanzania: no incremental gain beyond strong current flow

Primary LOSO result:

- 826 matched held-out predictions;
- 60 species;
- log-loss difference **+0.0321131**;
- 95% interval **+0.0174580 to +0.0486750**;
- sign-flip **p = 0.000030**;
- Brier difference **+0.0047993**;
- Brier 95% interval **+0.0022813 to +0.0073149**.

The inverse-area sensitivity retained the same direction. Spatial-block contrasts were smaller and intervals included zero.

### 3.4 Reproducibility

Report the A-Islands input fingerprints and the Tanzania verified result fingerprint:

`6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`

The result should be framed as independently reproduced, including the negative direction.

## 4. Discussion

### 4.1 Main finding

Environmental support, direct occurrence proximity, and structural reachability are distinct quantities. A-Islands demonstrates that graph configuration can remain informative after controlling the first two. Tanzania demonstrates that the same generic feature need not add value once a strong landscape-specific connectivity model has already represented matrix structure.

### 4.2 Why the negative result strengthens the method paper

The Tanzania outcome prevents a universal-superiority story. It shows that EOG must be justified as a conditional structural layer and benchmarked against the strongest available reference, not appended automatically to every distribution model.

The manuscript should state plainly:

> EOG identifies a potentially missing estimand; it does not guarantee a predictive gain.

### 4.3 What can explain the cross-system difference

Discuss only as hypotheses:

- taxon mobility and dispersal syndrome;
- island-chain versus terrestrial-matrix structure;
- information already captured by current flow;
- graph granularity and directionality;
- small training sets in a 14-fragment design;
- feature redundancy and variance inflation.

Do not select a preferred explanation from the observed outcome without new prospective evidence.

### 4.4 Limitations

- Neither benchmark directly observes dispersal or colonisation.
- A-Islands uses incidence patterns rather than temporal transitions.
- Tanzania has only 14 surveyed fragments.
- Connected frequency depends on a declared graph ensemble.
- The two endpoints and model hierarchies differ.
- Detection, abundance, demographic connectivity, and genetic isolation are not estimated.
- External generalisation beyond these systems remains open.

### 4.5 Prospective development

Trait-informed radii, directed wind/current edges, dynamic occupancy transitions, uncertainty propagation, and shrinkage may be valuable. Each must be treated as a new preregistered model, and the frozen Tanzania result must remain visible.

## 5. Claim matrix for the paper

| Evidence | Supported wording | Prohibited wording |
|---|---|---|
| A-Islands primary | Structural reachability retained held-out incidence information conditional on pointwise support and nearest-source distance | EOG is superior to SDM; connected frequency is dispersal probability |
| A-Islands secondary | Geography-only and environment-constrained structures were both informative under the frozen scenarios | Geography caused occupancy; one mode universally dominates |
| Tanzania primary | The tested generic EOG feature worsened LOSO prediction beyond current flow and distance | EOG is generally harmful; current flow universally dominates |
| Cross-system synthesis | Incremental structural value depends on the reference model and landscape representation | The two datasets identify the causal reason for their different outcomes |
| Reproducibility | Results were regenerated under frozen source, fold, feature, and inference contracts | Fingerprints prove ecological truth or preregistration when created after outcomes |

## 6. Figure plan

**Figure 1 — Distinct spatial roles.** Pointwise support, spatial block evaluation, direct occurrence distance, matrix-aware connectivity, and occurrence-anchored graph configuration.

**Figure 2 — A-Islands conditional benchmark.** Study design, support-distance conditioning, species-level concordance distribution, and primary/secondary estimates.

**Figure 3 — Tanzania strong-competitor benchmark.** Training-only current-flow selection, paired tiers, species-level log-loss differences, and spatial-block sensitivity.

**Figure 4 — Cross-system evidence boundary.** A matrix showing what each reference contains, what EOG adds, result direction, and permitted claim.

**Figure 5 — Audit trail.** Source hashes, pre-outcome contracts, corrected-but-outcome-independent protocol decisions, result fingerprints, and explicit non-estimable cases.

## 7. Table plan

**Table 1 — Existing spatial methods and EOG estimand.** Fit/evaluation role, local support, spatial dependence, matrix resistance, occurrence anchoring, intermediate configuration, and output interpretation.

**Table 2 — Benchmark contracts.** Units, taxa, predictors, folds, graph ensemble, reference model, endpoint, inference, and fingerprint.

**Table 3 — Main and sensitivity results.** A-Islands primary/decomposition/bottleneck and Tanzania LOSO/spatial-block/source-weight sensitivity.

**Table 4 — Claim boundary and prospective tests.** Supported claim, unresolved mechanism, required future data, and preregistration rule.

## 8. Evidence map

- A-Islands authoritative contracts: `docs/aislands_authoritative_contracts.md`;
- A-Islands primary execution: PR #89 and `benchmarks/run_aislands_authoritative_benchmark.py`;
- A-Islands mode decomposition: PR #90 and `benchmarks/run_aislands_predeclared_secondary.py`;
- A-Islands bottleneck secondary: PR #92;
- Tanzania geometry/formula contract: `docs/tanzania_geometry_formula_contract.md`;
- Tanzania selection contract: `docs/tanzania_current_flow_selection_contract.md`;
- Tanzania verified result: `docs/tanzania_heldout_result.md`;
- Cross-system synthesis: `docs/structural_validation_synthesis.md`.

## 9. Statements that must not appear as conclusions

- SDMs do not account for space or dispersal.
- Spatial block cross-validation is a dispersal model.
- EOG replaces SDM, occupancy, dynamic, mechanistic, resistance, or circuit models.
- Connected frequency is colonisation or dispersal probability.
- A graph component proves historical or demographic connectivity.
- EOG universally improves prediction.
- Tanzania invalidates the A-Islands result.
- A-Islands rescues the negative Tanzania result.
- The cross-system contrast identifies a causal taxonomic or landscape mechanism.
- Post-outcome trait or directional tuning is confirmatory evidence.
