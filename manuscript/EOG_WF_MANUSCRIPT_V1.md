# Environmental Occupancy Geometry as a two-layer structural and predictive framework

**Manuscript status:** first closed-boundary draft for Methods in Ecology and Evolution fit audit.

**Scientific boundary:** this manuscript must remain consistent with `manuscript/paper_ready/submission_boundary.json`. It does not authorize a fourth fresh endpoint, row-level pooled effects, a general predictive-superiority claim, causal identification, unique historical-route recovery, or truth claims about surviving Layer-A worlds.

## Abstract

Ecological distribution data can support two different inferential tasks: constraining which declared distribution-forming worlds remain compatible with accumulated evidence, and improving prediction of future observations. Treating these tasks as interchangeable risks confusing structural interpretation with predictive performance. We present Environmental Occupancy Geometry (EOG) as a two-layer framework that keeps them separate. Layer A retains exact, auditable world identities for sequential compatibility, contraction and finite-universe falsification. Layer B projects the surviving world set into a frozen ten-feature summary that is invariant to world labels and member order, and can be tested as an augmentation to an unchanged strong conventional predictor. We evaluated Layer-B added value prospectively across three fresh ecological endpoints under response-blind data, geometry and estimability gates and once-only outcome access. The augmented model improved macro log loss for Azores yellow eel telemetry (0.1423 to 0.1323; 5/5 heldout blocks) and Southwest Louisiana King Rail passive acoustics (0.2463 to 0.2453; 7/8 occasions), but degraded performance for Tampa Bay seagrass monitoring (0.3377 to 0.4388; 1/5 folds). A secondary feature-count placebo did not rescue the Tampa result. We therefore retain Layer A as an auditable structural falsification framework and Layer B as a context-dependent predictive complement rather than a universally beneficial prediction product. EOG formalizes a separation between what distribution evidence can structurally rule out and what derived world-set information can add to heldout prediction.

## Introduction

Ecological prediction and ecological explanation are often asked to operate on the same spatial observations, but success at one task does not guarantee success at the other. A model can predict heldout observations well while leaving the underlying distribution-forming process weakly identified; conversely, evidence can eliminate mechanistic or structural hypotheses without producing a superior forecasting representation. This distinction is familiar across statistical and ecological modelling, but it becomes especially important when distributions are represented by multiple plausible reachability or accessibility rules rather than by a single fitted mechanism. [REF]

EOG was developed around a finite declared universe of candidate worlds. Each world specifies a particular reachability or support rule, and accumulated occurrence evidence contracts the set of worlds that remain compatible with the observations. The exact identities of those surviving and eliminated worlds are scientifically useful because they make structural updating auditable: the analyst can state which declared rules were contradicted and which remain compatible. However, exact world identity is not equivalent to historical truth. Multiple worlds may remain observationally compatible, and their arbitrary labels need not be useful supervised features.

This distinction became empirical rather than merely conceptual during EOG development. In the Glanville fritillary system, exact world identity performed worse as a supervised predictive representation than a symmetric same-world compression across all six heldout transitions, while exact world contraction remained informative for structural updating. In Tvärminne Daphnia, a world-label-invariant Layer-B summary contained a small amount of non-redundant information beyond mean support but remained substantially worse than a strong frozen random forest. These results rejected a simple product interpretation in which exact or compressed EOG state should replace a conventional predictor. Instead, they motivated a narrower paired question: does a frozen summary of surviving-world structure add heldout information **on top of the same unchanged strong learner**?

We therefore formalized EOG as a two-layer method. **Layer A** is the exact scientific state: world identities, fingerprints, per-world support, surviving compatible rules, sequential contraction and finite-universe falsification. **Layer B** is a prediction-facing projection: the unchanged `symmetric_world_support_summary_v1`, containing ten permutation-invariant features of the surviving world support distribution. The two layers answer different questions. Layer A asks which declared structural explanations remain compatible with the evidence. Layer B asks whether the residual structure of that surviving world set contains predictive information not already captured by a strong conventional model.

A second methodological problem is that such an added-value question is easy to overstate when candidate systems, parsers, thresholds, data linkages or model specifications are repeatedly repaired after outcome access. Flexible endpoint search can transform ordinary data incompatibilities into an unrecorded selection process. We therefore coupled the two-layer estimand to a prospective validation funnel: source identity, response-independent registries, geometry, response semantics, structural adequacy, learner specification, heldout units, scoring rules and stopping conditions were frozen before row-level biological outcomes were used for model fitting. Endpoints that failed these contracts were retained as STOPs rather than repaired and relabelled as independent evidence.

The aim of this study was not to show that EOG universally improves ecological prediction. We instead tested a narrower, falsifiable claim across fresh ecological systems: **can the frozen Layer-B representation provide added heldout information beyond the same strong baseline predictor, while Layer A remains separately interpretable as a structural compatibility and falsification state?** We prospectively closed this question after three valid scored endpoints, accepting favorable, null or adverse outcomes under the same decision framework and prohibiting a fourth endpoint selected to improve the observed result pattern.

## Methods

### Two-layer estimand

Environmental Occupancy Geometry (EOG) separates exact structural inference from predictive compression. **Layer A** retains the auditable set of declared worlds compatible with the accumulated positive evidence, including world contraction and finite-universe falsification. **Layer B** maps the surviving world ensemble to the unchanged ten-feature `symmetric_world_support_summary_v1`, which is invariant to world labels and member order. Exact world identities are therefore retained for structural interpretation but are not exposed as supervised feature labels.

The predictive question was deliberately narrower than a claim of general superiority: for a fresh ecological endpoint, does the frozen Layer-B summary contain heldout information beyond the same strong conventional learner? Each paired comparison used the same learner and conventional baseline features in both arms; the augmented arm differed only by the ten frozen Layer-B columns. Primary performance was binary log loss, evaluated on prospectively frozen heldout units. Favorable, null and adverse terminal outcomes were accepted under rules fixed before the relevant response was opened.

### Prospective endpoint funnel and outcome firewall

Fresh endpoints were advanced through response-blind source, registry, geometry, effort/negative-semantics and estimability gates before biological response access. Terminal pre-response and pre-model STOPs were retained as methods-integrity evidence and were never reclassified as adverse Layer-B results. The final ledger contains **3 scored predictive endpoints, 31 scientific/protocol STOPs and 3 administrative exclusions**. The most frequent STOP classes included source transport (4), publication registry reproduction (3), geometry registry (2), metadata identity or transport (2), physical source separation (2), and response linkage (2). Candidate hunting was prospectively hard-stopped after the first valid third predictive endpoint; a fourth endpoint is not permitted to improve the apparent result.

### Cross-ecosystem synthesis

The ecosystem/endpoint, not the individual row, was the unit of fresh replication. The preregistered synthesis reports each endpoint separately using baseline and augmented macro log loss, their paired difference, the relative log-loss change and heldout-unit wins. No row-level pooling, common-effect estimate or pooled significance test is used. The preregistered adverse mapping narrows the supported product boundary to `structural_diagnostic_plus_context_dependent_predictive_complement`.

### Feature-count placebo

For the third endpoint only, a secondary response-independent ten-feature placebo control tested whether adding any ten columns could explain an apparent gain. The placebo was explicitly secondary and could not alter the primary favorable/null/adverse classification. Tampa used 20 placebo replicates with 10 features each.

## Results

### Fresh paired predictive endpoints

**Azores yellow eel telemetry.** The augmented arm reduced macro log loss from 0.1422727 to 0.1322871, a difference of -0.0099856 (-7.0%). It won all 5 heldout blocks, giving a favorable terminal result.

**Southwest Louisiana King Rail passive acoustics.** Macro log loss changed from 0.2463173 to 0.2453455, a difference of -0.0009718 (-0.39%). The augmented arm won 7/8 heldout occasions. Independently, all six frozen local Layer-A worlds were eventually falsified and only `external_open` survived. Thus a small favorable Layer-B gain can coexist with strong Layer-A structural falsification; the predictive result does not identify a local movement mechanism.

**Tampa Bay seagrass monitoring.** The valid third endpoint was adverse. Baseline macro log loss was 0.3377354, whereas the augmented arm reached 0.4387640; the difference was +0.1010287 (+29.9%). The augmented arm won only 1/5 folds. The secondary placebo median log loss was 0.3361758; the real augmented arm beat 0% of placebo replicates. The placebo therefore does not rescue the real Layer-B augmentation and does not change the adverse primary classification.

### Cross-ecosystem interpretation

The three fresh endpoints are heterogeneous rather than uniformly favorable: two systems show non-redundant heldout information in the frozen Layer-B representation, whereas one shows substantial degradation. The evidence therefore supports **Layer A as an auditable structural compatibility/falsification framework and Layer B as a context-dependent predictive complement**. It does not support universal predictive superiority, a standalone Layer-B predictor, causal identification, a recovered dispersal history, or the truth of an exact Layer-A world.

### Candidate funnel

The 31 scientific/protocol STOPs document where a prospective endpoint could not satisfy its frozen data contract without post-outcome repair. Three additional records were administrative exclusions and remain outside the scientific denominator. These STOPs support the integrity of the validation design but provide no evidence for or against Layer-B predictive value.

## Discussion

### Structural falsification and predictive complementarity are distinct estimands

The central result is not the count of favorable endpoints in isolation. It is the empirical separation of two claims that could otherwise be conflated. Layer A can remain scientifically informative when Layer B adds little or even harmful predictive information, because Layer A records which declared structural worlds remain compatible with evidence rather than optimizing a forecast score. Conversely, a favorable Layer-B comparison does not validate a particular surviving Layer-A world or identify a distribution-forming mechanism.

The Louisiana endpoint provides the clearest example. The augmented predictor achieved a small favorable heldout difference, yet all six frozen local Layer-A worlds were falsified and only `external_open` survived. These observations are compatible because the two layers estimate different objects. The Layer-B gain indicates that the surviving world-set representation retained some predictive information beyond the conventional baseline in that endpoint. It does not imply that any tested local movement rule was correct. This decoupling is the methodological reason to preserve exact Layer-A state behind, rather than inside, the supervised prediction interface.

### Predictive added value is context dependent

The three fresh endpoints do not support a universal predictive-product claim. Azores showed a clear favorable difference and wins in all five heldout blocks. Louisiana showed a much smaller favorable difference with seven wins across eight heldout occasions. Tampa showed substantial degradation, with the augmented model losing on four of five folds and performing worse than every secondary feature-count placebo replicate. The adverse result is therefore not plausibly summarized as a minor variance around a generally positive effect.

This heterogeneity fixes the appropriate product boundary. Layer B should be treated as a candidate complementary representation whose value must be established in the target application under a strong unchanged baseline, not as a mandatory feature set or standalone EOG predictor. The practical consequence is conservative: users can retain Layer A for auditable structural updating even when they choose not to use Layer B for prediction.

### Why exact world identities remain scientifically useful

The rejection of exact identity as a default supervised feature does not make exact worlds disposable. Exact identities are required for deterministic provenance and for statements such as which declared rule was eliminated after a particular evidence update. Replacing the exact state by a symmetric summary would destroy that audit trail. The two-layer architecture therefore resolves a tension exposed by the empirical program: prediction benefits from label invariance, whereas structural falsification requires identity preservation.

This distinction also constrains interpretation. A surviving exact world is a member of the declared rule universe that has not yet been contradicted by the available evidence. It is not a recovered historical truth. EOG therefore supports conditional statements about compatibility and falsification under a declared finite universe rather than unique-history reconstruction.

### Prospective stopping is part of the inferential design

The candidate funnel is unusually visible because failed source, registry, geometry, response-semantics and estimability gates were retained rather than silently replaced by repaired analyses. The 31 scientific/protocol STOPs are not negative biological results and should not enter a predictive meta-analysis. Their role is different: they show where a candidate could not reach the frozen scientific endpoint without violating the prospective contract.

This distinction matters because endpoint selection is itself a source of flexibility. If an adverse or technically incompatible system can simply be replaced until a favorable result appears, the apparent replication count ceases to describe the original decision process. The hard stop after the first valid third endpoint prevents that form of candidate hunting here. It also means that the observed favorable/favorable/adverse sequence must be interpreted as the closed empirical result rather than as an interim state awaiting one more system.

### Relationship to existing ecological prediction methods

EOG-WF should not be read as a replacement for species distribution models, dynamic occupancy models, mechanistic range models, landscape connectivity methods or generic ensemble learning. [REF] Those approaches may estimate local occurrence support, dynamic occupancy, dispersal processes, connectivity or predictive combinations directly. EOG-WF instead addresses a narrower interface problem: how to retain an exact, auditable finite-world structural state while exposing a label-invariant representation of that state to an external predictor, and how to test the added value of that representation without changing the baseline learner.

Similarly, the novelty claim does not rest on generic threshold graphs, percolation, minimum-cost paths, stacking, permutation-invariant summaries, model averaging, credal prediction or adaptive survey design. Those components have established precedents. [REF] The contribution evaluated here is their domain-specific separation into an exact structural update state and a prediction-facing projection, coupled to prospective paired complementarity tests in which favorable and adverse outcomes are both terminally admissible.

### Limitations

First, three fresh scored endpoints establish heterogeneity but do not characterize the full distribution of Layer-B effects across ecological systems. The hard stop intentionally prevents extending the denominator after observing the third valid result, so broader generalization requires future independent work rather than continuation of this closed series.

Second, Layer-A conclusions are conditional on the declared finite world universe. A world outside that universe may provide an explanation not represented in the analysis. EOG therefore supports falsification only relative to the declared certificate and does not establish biological impossibility in an unrestricted sense.

Third, Layer-B summaries compress exact world-state information. Their label invariance is desirable for prediction, but different symmetric summaries could retain different information. The present ten-feature representation was frozen prospectively; the current study does not establish it as uniquely optimal.

Fourth, the prospective validation machinery is demanding. Many candidate datasets failed before scientific scoring because identifiers, physical response files, geometry, effort semantics or source separation were insufficiently reproducible under the frozen contract. This reduces opportunistic flexibility but also limits where the full validation design can presently be applied.

Finally, predictive complementarity is not causal evidence. A favorable paired log-loss difference means only that the frozen Layer-B columns improved heldout prediction for that endpoint under the declared baseline and split. It does not identify why the information was useful or which ecological mechanism generated it.

### Conclusion

EOG-WF separates two inferential roles that should not be collapsed into one score. Exact world identities remain useful as an auditable state for sequential compatibility, contraction and finite-universe falsification, while a label-invariant summary can be exposed to prediction without treating arbitrary world labels as supervised features. Across three prospectively closed fresh endpoints, that predictive complement was favorable twice and substantially adverse once. The supported product is therefore neither a universal predictor nor a purely descriptive diagnostic. It is a **structural diagnostic with a context-dependent predictive complement**, with claim strength constrained by the declared world universe and by the prospective validation contract.

## Submission-boundary checklist

Before submission, confirm that the manuscript still satisfies all of the following:

- [ ] exactly 3 fresh scored endpoints;
- [ ] endpoint pattern remains favorable / favorable / adverse;
- [ ] no fourth fresh endpoint;
- [ ] 31 scientific/protocol STOPs and 3 administrative exclusions remain correctly separated;
- [ ] no row-level pooled effect or common-effect significance claim;
- [ ] no claim of universal Layer-B superiority;
- [ ] no standalone Layer-B predictor claim;
- [ ] no unique historical-route or surviving-world truth claim;
- [ ] Louisiana decoupling is described as structural falsification plus small predictive complement, not mechanistic validation;
- [ ] Tampa placebo is secondary and does not alter the primary adverse classification;
- [ ] references are added for general literature-positioning statements marked `[REF]`;
- [ ] journal-specific format is checked on the submission date.
