# Environmental Occupancy Geometry separates structural falsification from context-dependent predictive complementarity

**Target journal:** Methods in Ecology and Evolution  
**Article status:** scientific-content draft from frozen repository evidence; live journal formatting and author metadata remain to be completed immediately before submission.  
**Author list:** to be completed by the authors.  
**Corresponding author:** to be completed by the authors.

## Abstract

1. Ecological prediction often requires reasoning about both local environmental support and whether sites are mutually accessible through a landscape or observation history. Accessibility, connectivity, dynamic occupancy and dispersal are not new ideas, and many existing methods represent them explicitly. A remaining methodological problem is how to preserve uncertainty over several plausible accessibility structures without selecting a preferred structure from the same held-out outcomes later used to claim predictive success.

2. We developed **Environmental Occupancy Geometry (EOG)** as a two-layer framework. **Layer A** retains the exact finite set of declared accessibility or continuity worlds still compatible with accumulated occurrence evidence, including their contraction, provenance and falsification. **Layer B** compresses that surviving world set into the fixed, world-label-invariant ten-feature representation `symmetric_world_support_summary_v1`. Predictive value is then tested by comparing the same strong conventional learner with and without the Layer-B summary under prospectively frozen held-out evaluation. Source, registry, geometry, effort and estimability failures are terminal protocol outcomes rather than negative predictive results.

3. Three genuinely fresh heterogeneous endpoints reached valid paired predictive terminals. Layer B reduced macro log loss for Azores yellow eel telemetry from 0.142273 to 0.132287 and won 5/5 held-out blocks, and for Southwest Louisiana King Rail passive acoustics from 0.246317 to 0.245346 and won 7/8 occasions. In contrast, Tampa Bay seagrass monitoring was adverse: macro log loss increased from 0.337735 to 0.438764 and the augmented arm won only 1/5 folds. A predeclared ten-feature placebo control did not rescue the Tampa augmentation. Across the prospective validation funnel, 31 additional scientific candidates stopped under frozen data-contract gates and three records were administrative exclusions.

4. EOG therefore does not support universal predictive superiority. Its supported boundary is a **structural diagnostic plus a context-dependent predictive complement**: Layer A provides an auditable way to retain and falsify possible accessibility worlds, while Layer B can contain non-redundant predictive information in some systems and harmful information in another. The framework is intended for transparent structural inference and prospectively validated augmentation, not for recovering a unique dispersal history or identifying a causal movement mechanism.

**Keywords:** accessibility; connectivity; occurrence data; occupancy; species distribution modelling; structural uncertainty; prospective validation; falsification; reproducibility

---

## 1. Introduction

Observed species distributions reflect more than local environmental compatibility. Whether a species is recorded at a site can also depend on accessibility, dispersal, colonisation, landscape structure and the spatial configuration of occupied source populations. These ideas are well established. Accessible area is a central component of BAM-style ecological niche reasoning (Barve et al., 2011); dynamic occupancy models can represent colonisation and dispersal explicitly (Broms et al., 2016); mechanistic distribution models can couple demography and dispersal through heterogeneous landscapes (Merow et al., 2011); and least-cost, circuit-theory and habitat-network approaches provide mature representations of landscape connectivity (McRae et al., 2008; Ortiz-Rodríguez et al., 2019; Van Moorter et al., 2023). Source-conditioned proximity and occupied-neighbour information are also established predictors rather than novel ingredients (Prugh, 2009; Berlow et al., 2013).

The methodological gap addressed here is consequently narrower than “adding connectivity to a species distribution model”. Connectivity predictions can depend strongly on modelling choices such as resistance, source points, thresholds and functional form, and contemporary frameworks increasingly make that model-choice uncertainty explicit (Prima et al., 2024). Yet an ecological analysis still needs to distinguish at least three questions that can otherwise be conflated. First, **structural inference** asks which declared accessibility worlds remain compatible with the evidence. Second, **predictive complementarity** asks whether information derived from those surviving worlds improves held-out prediction beyond a conventional reference learner. Third, **mechanistic interpretation** asks whether a particular movement or connectivity process generated the observed pattern. Evidence for one of these questions does not automatically answer the others.

This separation matters whenever several accessibility structures are plausible. Choosing the world that best predicts held-out data and then using the same held-out data to argue that the selected world carries independent predictive information creates a selection problem. Collapsing several worlds to a single averaged probability can avoid explicit selection but loses the exact identity of what has been ruled out, which can be the scientifically important output. Conversely, retaining all worlds as labelled features makes prediction depend on arbitrary member identities and can invite world-specific supervision. We therefore sought a representation in which exact world identity remains available for structural auditing while the predictive interface remains invariant to world labels.

We developed **Environmental Occupancy Geometry (EOG)** around this separation. Layer A is an exact finite possible-world state: occurrence evidence sequentially contracts a declared world ensemble and records which worlds survive or are falsified. Layer B is a fixed symmetric compression of the current world set. The compression is not interpreted as a posterior probability over mechanisms and the surviving world set is not claimed to contain the true historical route. Instead, Layer B is treated as a candidate source of additional predictive information whose value must be assessed against a strong same-learner baseline.

The evaluation design was as important as the representation. We used prospectively staged response access, frozen candidate rules, deterministic splits and explicit terminal outcomes. A dataset could end in a source, registry, geometry, effort, schema or estimability STOP before prediction, and such STOPs were retained in the manuscript denominator as methods-integrity evidence. A valid predictive endpoint could be favorable, null or adverse, all of which were accepted without redesigning the world family after observing the outcome. Candidate hunting was prospectively hard-stopped after the first valid third predictive endpoint.

We ask two main questions. **(1)** Can the label-invariant summary of an exact compatible-world set contain non-redundant held-out predictive information beyond a strong conventional learner? **(2)** Is that contribution stable enough across heterogeneous ecological observation systems to justify a general predictive claim? The answer to the second question is deliberately allowed to be negative. The final method boundary is determined by the complete prospective sequence, including adverse results and failed data contracts, rather than by the most favorable example.

---

## 2. Materials and Methods

### 2.1 Two-layer EOG estimand

EOG separates the state used for structural inference from the representation used for supervised prediction.

**Layer A: exact compatible-world state.** A “world” is a prospectively declared accessibility, continuity or reachability structure under which occurrence evidence can be evaluated for compatibility. The finite world ensemble is not treated as a sample from a known posterior distribution. Instead, Layer A stores exact membership of the current compatible set together with sequential update and falsification provenance. As new positive evidence is incorporated, worlds that cannot support the required compatibility relation are excluded. A finite local universe can therefore be exhausted, in which case the structural result is falsification of all declared local worlds rather than selection of the least-bad member. A permissive `external_open` world may remain as an explicit statement that the frozen local family is insufficient.

**Layer B: symmetric predictive compression.** For prediction, the current Layer-A state is transformed using the unchanged ten-feature `symmetric_world_support_summary_v1`. The transformation is invariant to labels and ordering of world members. Thus prediction can use properties of the surviving ensemble without assigning supervised meaning to a world identifier. Exact member identity remains available in Layer A for structural interpretation and auditing, but member labels are not exposed as ordinary predictor columns.

The method therefore estimates neither a unique dispersal history nor a causal probability that a particular landscape path generated an occurrence. A compatible world is a world not yet excluded by the declared evidence and rules.

### 2.2 Leakage-safe paired prediction

For each fresh endpoint, conventional predictors and the learning algorithm were frozen before the once-only biological outcome was used for scoring. The primary comparison used the **same learner in both arms**:

- **baseline arm:** the prospectively frozen conventional/site/observation predictors;
- **augmented arm:** the same predictors plus the ten unchanged Layer-B features.

Layer-B construction for training rows excluded the row's own target information where required by the endpoint contract, and held-out labels did not enter Layer A before that held-out prediction was scored. Split assignment, world construction and endpoint eligibility were not changed in response to favorable or adverse results.

The primary loss was binary log loss. For each endpoint we report macro log loss for baseline and augmented arms, their difference

`delta = augmented macro log loss - baseline macro log loss`,

and the number of held-out units in which the augmented arm had lower loss. Negative delta favors Layer B; positive delta favors the conventional baseline. The ecosystem/endpoint, not the individual row, is the unit of fresh replication. We do not pool rows across systems, estimate a common cross-system effect, or report a pooled significance test.

### 2.3 Prospective outcome firewall and terminal states

Fresh candidates passed through staged gates before biological response access. Depending on the dataset, these gates established public source identity and byte transport, response-independent site or node registry, geometry, effort and surveyed-negative semantics, structural-scale adequacy, temporal or spatial holdout feasibility, and physical response linkage. Rules were content-addressed and audited before later stages.

Terminal outcomes were separated prospectively:

- **favorable predictive result:** the frozen augmented arm showed the predeclared complementary improvement;
- **null predictive result:** no confirmed complementary improvement under the predeclared decision rule;
- **adverse predictive result:** the augmented arm was materially worse under the predeclared decision rule;
- **scientific/protocol STOP:** the endpoint could not satisfy a frozen source, registry, geometry, effort, schema or estimability contract without prohibited repair;
- **administrative exclusion:** a record such as a duplicate or execution bookkeeping failure that did not constitute an additional scientific denominator unit.

Scientific STOPs were never reinterpreted as adverse Layer-B results. Conversely, once a full response had been consumed under a once-only rule, the same endpoint was not rerun to obtain a more favorable classification.

The final candidate-flow ledger contains three scored predictive endpoints, 31 scientific/protocol STOPs and three administrative exclusions. Candidate search was hard-stopped after the valid Tampa endpoint supplied the third predictive terminal.

### 2.4 Fresh ecological endpoints

#### 2.4.1 Azores yellow eel acoustic telemetry

The first fresh endpoint predicted receiver-week recorded detection for yellow eel telemetry in the Azores. The observation process was acoustic telemetry. Evaluation used five held-out blocks under the endpoint-specific prospectively frozen baseline and the unchanged Layer-B representation. The authoritative once-only predictive run was `32807155541`.

#### 2.4.2 Southwest Louisiana King Rail passive acoustics

The second endpoint predicted site-occasion recorded detection of King Rail from passive acoustic monitoring in southwest Louisiana. Eight held-out occasions were evaluated using the same paired logic. This endpoint also provides the clearest demonstration that structural and predictive conclusions are distinct: all six frozen local Layer-A worlds were eventually falsified, whereas the permissive `external_open` world survived. The authoritative once-only predictive run was `32812052801`.

#### 2.4.3 Tampa Bay seagrass transect monitoring

The third valid predictive endpoint used long-term fixed-transect seagrass monitoring in Tampa Bay. A candidate unit was an eligible parent Transect visit crossed with whether *Thalassia testudinum* was recorded among linked child Point events. The frozen endpoint comprised 1,497 candidate units on 71 nodes, including 927 positive and 570 negative candidate units. Five held-out folds contained both classes. The authoritative once-only predictive run was `34028447227`.

The third endpoint additionally included a secondary, predeclared feature-count placebo. Twenty placebo replicates supplied ten response-independent columns each. This control asked whether a result could be explained merely by adding ten dimensions. It was explicitly secondary and was not allowed to change the primary favorable/null/adverse classification.

### 2.5 Cross-ecosystem synthesis

The synthesis rule was frozen before endpoint 3 was observed. Each fresh endpoint is displayed separately. We report absolute and relative changes in log loss and held-out-unit wins but do not pool the observations or suppress endpoint heterogeneity behind a single average.

The decision mapping specified that an adverse third endpoint would narrow the method from a candidate general predictive complement to **`structural_diagnostic_plus_context_dependent_predictive_complement`**. This mapping was applied after Tampa without rescue tuning. A fourth fresh dataset is prohibited by the same hard-stop rule.

### 2.6 Software generality and source adapters

The current software separates source-specific ingestion from the EOG core through a dataset-neutral pre-response problem contract. Dataset adapters are responsible for normalising stable nodes, contexts, effort and zero semantics, geometry and conventional predictor roles. Structural identity, geometry and effort remain fail-closed when they cannot be reproduced. Optional ordinary baseline covariates can use prospectively defined calibration-only missing-data handling rather than converting every missing environmental value into a source-registry failure.

This software boundary is an engineering generalisation, not extra empirical evidence. The scientific claims in this paper remain those supported by the three frozen fresh predictive endpoints and their candidate-flow ledger.

### 2.7 Reproducibility and manuscript projection

All manuscript-facing numerical tables and the four principal schematic/result figures are generated deterministically from frozen repository certificates and the candidate-flow ledger. The committed `manuscript/paper_ready/` assets are regression-tested against a fresh rebuild byte for byte. This projection step performs no biological response retrieval and no model fitting; it only verifies that the manuscript reflects the already frozen evidence direction.

---

## 3. Results

### 3.1 Prospective candidate funnel

The complete fresh validation programme contains **37 handled records**: 34 scientific denominator units and three administrative exclusions. The scientific denominator consists of **three scored predictive endpoints and 31 scientific/protocol STOPs**. Frequent STOP stages included source transport (4), publication-registry reproduction (3), geometry registry (2), metadata identity or transport (2), physical source separation (2), response linkage (2) and temporal registry (2). STOPs document where a candidate could not satisfy its frozen contract without prohibited post hoc repair; they are not evidence that Layer B is predictive or non-predictive.

### 3.2 Azores: favorable complementary information

For Azores yellow eel telemetry, baseline macro log loss was **0.1422727** and augmented macro log loss was **0.1322871**, giving `delta = -0.0099856`, approximately a **7.0% reduction** relative to baseline loss. The augmented arm won **5/5** held-out blocks. This endpoint therefore reached the frozen favorable terminal classification.

### 3.3 Louisiana: small favorable gain despite local-world falsification

For Southwest Louisiana King Rail passive acoustics, baseline macro log loss was **0.2463173** and augmented macro log loss was **0.2453455**, giving `delta = -0.0009718`, approximately a **0.39% reduction**. The augmented arm won **7/8** held-out occasions.

Independently of this predictive comparison, sequential Layer-A evidence eventually falsified **all six frozen local worlds**, leaving only `external_open`. The coexistence of these results is central to the method interpretation. A Layer-B gain does not confirm one of the local worlds as a true dispersal or connectivity mechanism; predictive complementarity and structural compatibility are different estimands.

### 3.4 Tampa: adverse augmentation and secondary placebo

The third valid predictive endpoint was adverse. Tampa Bay seagrass baseline macro log loss was **0.3377354**, whereas augmented macro log loss was **0.4387640**, giving `delta = +0.1010287`, a **29.9% increase** relative to baseline loss. The baseline arm was better in four folds and the augmented arm in only **1/5**.

The secondary ten-feature placebo distribution had median macro log loss **0.3361758** (interquartile range 0.3353363–0.3373586). The real Layer-B augmented model was **0.1025883** log-loss units worse than the placebo median and beat **0% of the 20 placebo replicates**. The placebo therefore does not rescue the real augmentation and, by design, does not alter the adverse primary classification.

### 3.5 Cross-ecosystem result

The endpoint pattern is **favorable / favorable / adverse** under the unchanged Layer-B representation. The programme therefore rejects a uniform-benefit interpretation. The prospectively mapped supported boundary is:

> **Layer A is an auditable structural compatibility and falsification framework; Layer B is a context-dependent predictive complement whose incremental value must be demonstrated for the system at hand.**

No fourth fresh endpoint is permitted to change this pattern.

---

## 4. Discussion

### 4.1 The main contribution is separation, not a universally better predictor

The strongest conclusion from the completed programme is not that structural world-set information always improves ecological prediction. It demonstrably did not. Instead, EOG supplies a disciplined separation between an exact structural state and a predictive summary of that state. Two fresh systems showed favorable incremental held-out information; the third showed substantial degradation. This heterogeneity turns what could have been framed as a generic predictor into an applicability boundary.

That boundary is scientifically useful. When Layer B improves prediction, the gain can be reported without converting a surviving world into a mechanistic truth claim. When Layer B harms prediction, Layer A can still retain its separate structural role: tracking which declared worlds remain compatible, which have been falsified and whether the local world universe has been exhausted. The method can therefore fail predictively without becoming uninterpretable structurally.

### 4.2 Louisiana demonstrates why structural and predictive claims must remain distinct

The Louisiana endpoint makes the distinction concrete. A conventional reading of a “connectivity model” often encourages an analyst to interpret better prediction as support for the fitted connectivity representation. Here, all six frozen local worlds were eventually falsified, yet the symmetric world-set summary still produced a small held-out gain. The result is not paradoxical once the two estimands are separated. The predictive summary encodes the configuration and contraction state of a candidate-world ensemble; it is not a supervised label for a surviving local mechanism.

This also illustrates why the permissive `external_open` state is useful. Exhaustion of the local world family becomes an explicit diagnostic rather than a reason to silently widen a threshold or substitute a new resistance surface. The correct inference is that the declared local family was insufficient under the frozen compatibility rules.

### 4.3 Tampa establishes the predictive applicability boundary

Tampa is not a failed replication to be hidden or repaired. It is the observation that closes the predictive claim. The same fixed Layer-B representation that added information in telemetry and passive acoustic monitoring materially worsened seagrass prediction. Moreover, its loss was worse than every replicate of the secondary ten-feature placebo control. Thus the adverse result cannot be softened into a generic “extra features did not help” statement; under the frozen Tampa design, the real world-set summary actively degraded the paired learner relative to the conventional baseline.

We do not infer from this endpoint why the degradation occurred mechanistically. Possible causes such as mismatch between the declared world family and the ecological process, redundancy with strong conventional features, temporal structure, observation architecture or information loss in the ten-feature compression would require new prospectively designed tests. Post hoc identification of one explanation would violate the discipline of the present programme.

### 4.4 Relation to existing accessibility and connectivity methods

EOG does not introduce accessibility to ecological niche modelling (Barve et al., 2011), source-conditioned connectivity (Prugh, 2009), explicit colonisation in occupancy models (Broms et al., 2016), mechanistic dispersal in distribution models (Merow et al., 2011), circuit connectivity (McRae et al., 2008), habitat-network occurrence prediction (Ortiz-Rodríguez et al., 2019), or integrated environmental and geographic habitat functionality (Van Moorter et al., 2023). Nor is uncertainty across connectivity constructions itself novel (Prima et al., 2024).

The narrower contribution is an auditable workflow for **retaining exact candidate-world identity for structural falsification while exposing only a label-invariant world-set representation to a matched predictive test**, coupled to a prospective response-access protocol that treats adverse results and data-contract STOPs as first-class outcomes. The novelty therefore lies in the combination of estimand separation, world-set compression, matched held-out evaluation and execution discipline rather than any one graph or dispersal operator.

### 4.5 The candidate funnel is part of the method result

Only three endpoints reached a valid predictive terminal, while 31 scientific candidates stopped earlier. That imbalance is not presented as evidence that ecological data are generally unusable for EOG. It instead reveals where a stringent prospective workflow encounters practical constraints: stable public transport, response-independent registries, explicit effort, defensible survey negatives, physical response separation and schema identity.

Retaining these STOPs makes endpoint selection auditable. Had the pipeline silently repaired header mismatches, averaged inconsistent coordinates, changed minimum counts after observing data or retried consumed outcomes, the final three-endpoint sequence would be difficult to distinguish from candidate hunting. The funnel therefore functions as methods-integrity evidence, not as an ecological meta-analysis of failure rates.

### 4.6 Generality is an interface property, not a claim of uniform ecological benefit

The three scored systems differ strongly in observation process: acoustic telemetry, passive acoustic monitoring and fixed-transect plant monitoring. This supports portability of the two-layer evaluation architecture across data types. It does not establish that one set of worlds is ecologically meaningful everywhere. In the software, source-specific details terminate at a normalised problem interface; the EOG core receives stable nodes, contexts, effort/zero semantics, geometry and frozen baseline roles.

This is the appropriate sense in which the method is general. A new dataset can implement the interface without adding dataset-specific branches to Layer A or changing `symmetric_world_support_summary_v1`. But predictive benefit remains an empirical property of the system and must be tested rather than assumed.

### 4.7 Limitations

Several limitations bound interpretation.

First, Layer A is conditional on a finite **declared** world universe. Surviving worlds are not guaranteed to include the true process, and complete falsification can mean that the universe was inadequate rather than that accessibility itself was irrelevant.

Second, occurrence compatibility is not unique-history reconstruction. Multiple rules may support the same observations, and positive records alone generally do not identify direction, timing or causal movement mechanisms.

Third, Layer B is a deliberately compressed ten-feature representation. Its invariance prevents arbitrary world-label supervision but necessarily discards information. Tampa shows that the fixed compression can be harmful in at least one system.

Fourth, three valid predictive endpoints are sufficient to establish heterogeneity but not to characterise the full distribution of contexts in which Layer B helps. The prospective hard stop prevents us from expanding the dataset count merely to estimate a more favorable average.

Fifth, the 31 STOPs arise from a deliberately strict data-contract workflow and should not be interpreted as a representative estimate of failure across ecological repositories.

Finally, the present evidence is predictive and structural rather than causal. Any mechanistic explanation for why a world is retained, excluded or predictively useful requires independent directional, experimental, demographic or movement evidence appropriate to that system.

### 4.8 Recommended use

We recommend using EOG in two modes.

1. **Structural diagnostic mode.** Declare a scientifically defensible finite family of accessibility or continuity worlds, update it with occurrence evidence, and report surviving and falsified worlds with provenance. This use does not require a claim that Layer B will improve prediction.

2. **Predictive-complement mode.** If prediction is desired, freeze the Layer-B representation and compare the same conventional learner with and without it under leakage-safe held-out evaluation. Retain favorable, null and adverse results. Do not redesign the world family after observing held-out performance.

Under the evidence reported here, the first mode is the method's stable core and the second is context dependent.

---

## 5. Conclusions

EOG turns uncertainty about accessibility structure into two deliberately separate objects: an exact, auditable compatible-world state for structural inference and a label-invariant summary whose predictive value can be tested. The completed prospective programme yielded two favorable and one adverse predictive endpoints, alongside 31 protocol STOPs that document the cost of enforcing response-independent data contracts. These results support EOG as a **structural diagnostic with a context-dependent predictive complement**, not as a universally superior species-distribution model or a recovered movement history.

The practical implication is simple: preserve impossibility and falsification explicitly, and make predictive augmentation earn its place through prospectively matched validation.

---

## Data and code availability

All EOG source code, frozen contracts, endpoint certificates, candidate-flow ledger and reproducible manuscript projections are maintained in the public `zuizui0223/eog` repository. The paper-ready manuscript tables and figures are generated from frozen repository evidence by `manuscript/build_paper_ready_eogwf.py` and guarded against manual drift by automated tests. Original biological datasets remain governed by their source repositories and licences; endpoint-specific source identities and access boundaries are recorded in the corresponding validation contracts.

Before submission, replace this paragraph's repository-only citation with the final archived release DOI and immutable release tag/commit. No new biological outcome should be generated for that release step.

## Author contributions

To be completed after the final author list is fixed. Contribution roles should describe conceptualisation, methodology, software, validation, formal analysis, data curation, visualisation, writing and supervision as applicable; do not infer roles from repository activity alone.

## Funding

To be completed by the authors.

## Competing interests

To be completed by the authors.

## Acknowledgements

To be completed by the authors. Dataset creators should be credited according to the requirements of the original data releases and publications.

---

## References cited in this scientific-content draft

Barve, N., Barve, V., Jiménez-Valverde, A., Lira-Noriega, A., Maher, S.P., Peterson, A.T., Soberón, J. & Villalobos, F. (2011). The crucial role of the accessible area in ecological niche modeling and species distribution modeling. *Ecological Modelling*, 222, 1810–1819. https://doi.org/10.1016/j.ecolmodel.2011.02.011

Berlow, E.L. et al. (2013). A Network Extension of Species Occupancy Models in a Patchy Environment Applied to the Yosemite Toad (*Anaxyrus canorus*). *PLoS ONE*, 8, e72200. https://doi.org/10.1371/journal.pone.0072200

Broms, K.M., Hooten, M.B., Johnson, D.S., Altwegg, R. & Conquest, L.L. (2016). Dynamic occupancy models for explicit colonization processes. *Ecology*, 97, 194–204. https://doi.org/10.1890/15-0416.1

McRae, B.H., Dickson, B.G., Keitt, T.H. & Shah, V.B. (2008). Using circuit theory to model connectivity in ecology, evolution, and conservation. *Ecology*, 89, 2712–2724. https://doi.org/10.1890/07-1861.1

Merow, C., LaFleur, N., Silander, J.A. Jr., Wilson, A.M. & Rubega, M. (2011). Developing dynamic mechanistic species distribution models: Predicting bird-mediated spread of invasive plants across northeastern North America. *The American Naturalist*, 178, 30–43. https://doi.org/10.1086/660295

Ortiz-Rodríguez, D.O., Guisan, A., Holderegger, R. & van Strien, M.J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution*, 9, 10457–10471. https://doi.org/10.1002/ece3.5567

Prima, M.-C. et al. (2024). A comprehensive framework to assess multi-species landscape connectivity. *Methods in Ecology and Evolution*, 15, 2385–2399. https://doi.org/10.1111/2041-210X.14444

Prugh, L.R. (2009). An evaluation of patch connectivity measures. *Ecological Applications*, 19, 1300–1310. https://doi.org/10.1890/08-1524.1

Valavi, R., Elith, J., Lahoz-Monfort, J.J. & Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods in Ecology and Evolution*, 10, 225–232. https://doi.org/10.1111/2041-210X.13107

Van Moorter, B. et al. (2023). Habitat functionality: Integrating environmental and geographic space in niche modeling for conservation planning. *Ecology*, 104, e4105. https://doi.org/10.1002/ecy.4105
