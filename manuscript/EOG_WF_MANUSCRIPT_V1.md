# Environmental Occupancy Geometry: auditable finite-world falsification with a prospectively stress-tested prediction interface

**Manuscript status:** closed-boundary draft for Methods in Ecology and Evolution.

**Scientific boundary:** this manuscript is subordinate to `manuscript/paper_ready/submission_boundary.json`. It does not authorize a fourth fresh predictive endpoint, row-level pooled effects, universal predictive superiority, causal identification, unique historical-route recovery, or truth claims about surviving Layer-A worlds.

## Abstract

**1.** Ecological distribution observations can constrain a declared set of distribution-forming hypotheses even when they do not identify one true history. A methodological difficulty is to keep that structural evidence distinct from a second question: whether a compressed representation of the remaining hypotheses improves heldout prediction. Conflating the two can turn an auditable falsification state into an unjustified prediction product.

**2.** We developed Environmental Occupancy Geometry (EOG) around two deliberately separated layers. **Layer A** retains exact identities and fingerprints for a finite declared world universe, updates the compatible set sequentially with positive distribution evidence, and permits finite-universe falsification. A response-blind prospective protocol freezes source identity, registries, geometry, response semantics, structural adequacy, learner specification, heldout units and terminal decision rules before scored outcome access. **Layer B** is a secondary prediction-facing projection: a fixed ten-feature, world-label-invariant summary tested only as an augmentation to the same unchanged strong conventional learner.

**3.** Layer-A falsification operated in real applications rather than remaining a formal possibility. In STOC, the predeclared 20-world universe was falsified during calibration for all 20 species before a heldout predictive comparison was reached. In Southwest Louisiana King Rail data, all six frozen local worlds were eventually falsified and only `external_open` survived. In the independent Glanville fritillary system, exact world identities remained useful for rule-specific updating but were adverse when directly exposed as supervised predictive features. The prospective fresh-complementarity funnel ended with **3 scored endpoints, 31 scientific/protocol STOPs and 3 administrative exclusions**. Layer-B augmentation changed macro log loss by −7.0% in Azores yellow eel telemetry, −0.39% in Louisiana, and **+29.9%** in Tampa Bay seagrass monitoring. The Tampa augmentation beat 0/20 matched feature-count placebo replicates.

**4.** The strongest supported result is therefore not general predictive benefit. EOG provides an auditable finite-world compatibility, contraction and falsification framework coupled to an explicit prospective validation denominator. The frozen Layer-B compression can contain additional heldout information in some systems but can also cause substantial predictive degradation; its usefulness must be established separately in each application. Structural compatibility and predictive value are distinct estimands and are allowed to disagree.

**Data and code for peer review:** all manuscript results are linked to immutable repository contracts, certificates, fingerprints and generated paper-ready assets. A review-ready release/archive should be fixed before submission. [FINAL ARCHIVE/DOI TO ADD]

**Keywords:** ecological forecasting; falsification; model uncertainty; prospective validation; reachability; reproducibility; species distributions

## Introduction

Ecological prediction and ecological explanation are often asked to operate on the same spatial observations, but success at one task does not guarantee success at the other. A model may predict heldout observations well while leaving the underlying distribution-forming process weakly identified; conversely, new evidence may eliminate structural or mechanistic hypotheses without yielding a better forecasting representation (Shmueli, 2010; Houlahan et al., 2017). This distinction becomes especially important when distributions are represented by several plausible reachability or accessibility rules rather than by one fitted mechanism.

EOG starts from a deliberately finite declared universe of candidate worlds. Each world encodes a frozen support or reachability rule. For evidence set `O`, Layer A retains the exact compatible subset `W(O)`. New positive evidence may leave that set unchanged, contract it by eliminating particular worlds, or falsify the entire declared universe. Exact identity matters here because a statement such as “rule X was eliminated by transition t” is impossible after identity has been discarded. At the same time, survival of a world does **not** establish that world as historical truth: several worlds can remain observationally compatible and the true process may lie outside the declared universe.

The first independent EOG applications made this distinction empirical rather than rhetorical. STOC did not reach the intended prediction comparison because calibration positives falsified the complete frozen 20-world universe for 20/20 species. That failure was retained rather than repaired by expanding the world set after outcome access. In the Glanville fritillary system, exact world identities continued to contract under evidence, yet using those identities directly as supervised features produced macro log loss 0.230197 versus 0.187983 for the predeclared symmetric compression and was worse in all six heldout transitions. These outcomes indicate that an exact structural state can be scientifically useful while being a poor predictive encoding.

We therefore separate the method into two layers rather than treating prediction as the criterion that validates the structural layer. **Layer A** is the exact scientific state: world identities, rule fingerprints, per-world support, compatible-world membership, sequential contraction and finite-universe falsification. **Layer B** is only a prediction-facing projection of that state: the frozen `symmetric_world_support_summary_v1`, consisting of ten statistics that are invariant to arbitrary world naming and member order. A deterministic known-truth benchmark verifies that Layer A can contract monotonically to complete universe falsification while the Layer-B matrix remains invariant to relabelling of the same exact worlds.

A second problem concerns validation itself. Added-value results are easy to overstate if candidate systems, parsers, thresholds, registries or model specifications can be repaired repeatedly after outcome access. Flexible candidate replacement can also hide the denominator behind an apparently successful set of examples. We therefore made the validation funnel explicit. Source identity, response-independent registries, geometry, response semantics, structural adequacy, learner specification, heldout units, metrics and terminal rules were frozen before row-level biological outcomes were used for scored fitting. Systems that failed the frozen contract remained STOPs rather than being repaired and relabelled as independent evidence.

The primary aim of this study is consequently twofold but asymmetric. First, we ask whether finite-world structural compatibility and falsification operate as an auditable ecological inference state in known-truth and real applications. Second, as a deliberately harder product test, we ask whether a frozen label-invariant compression of that state adds heldout information to an **unchanged strong conventional learner**. We did not require the second result to be favorable in order to retain the first. The fresh predictive series was prospectively closed after the third valid scored endpoint, and a fourth endpoint selected to improve the observed pattern is forbidden.

## Materials and Methods

### Layer A — exact finite-world compatibility and falsification

Let `W` denote a finite, prospectively declared set of worlds and `O` the accumulated positive distribution evidence. EOG retains

`W(O) = {w in W : w is compatible with O}`.

World identities and rule fingerprints remain exact so that sequential updates can attribute eliminations to particular declared rules. Positive evidence may contract `W(O)` monotonically. If no declared world remains compatible, the terminal state is finite-universe falsification. This is a statement about the declared universe, not unrestricted biological impossibility and not recovery of one true historical world.

### Deterministic known-truth method benchmark

Before ecological applications, the two-layer separation was checked in small deterministic world universes with known transition structure. In one construction, two exact rules initially explained an observed transition; later evidence eliminated one rule, and subsequent evidence contradicted the final survivor, yielding `universe_falsified`. The surviving set was required to be a subset of the preceding set at every update, and reusing an existing world ID after changing its operator was rejected.

In a second construction, two exact worlds connected the same source and endpoint through different intermediates. Renaming the worlds or reversing their member order was required to change exact latent provenance where appropriate but leave the complete Layer-B feature matrix and prediction-facing fingerprint unchanged. These tests establish representation contracts; they do not test predictive superiority.

### Layer B — secondary prediction-facing projection

Layer B maps the surviving exact world ensemble to the frozen ten-feature `symmetric_world_support_summary_v1`: surviving-world fraction; support mean, standard deviation, minimum and maximum; q25, q50 and q75; positive-support fraction; and support range. Exact world IDs remain available in Layer A but are not exposed as default supervised feature columns.

The closed predictive question is deliberately narrow: for a fresh ecological endpoint, does this frozen Layer-B block contain heldout information beyond the **same strong conventional learner**? Baseline and augmented arms use the same learner, preprocessing, hyperparameters and conventional features; the augmented arm differs only by the ten Layer-B columns. The endpoint unit, split, binary log-loss metric and favorable/adverse rules are frozen before relevant outcome access.

This paired augmentation is the product claim evaluated here. It should not be interpreted as a test that Layer B is a useful standalone predictor, nor as evidence that a surviving exact world is true.

### Prospective endpoint funnel and outcome firewall

Fresh systems advanced through response-blind source, registry, geometry, effort/negative-semantics and estimability gates before scored biological response access. Physical response-header identity, categorical response-token semantics, runtime identity and the once-only outcome-access contract were treated as part of the frozen response semantics. Terminal pre-response and pre-model STOPs were retained as methods-integrity evidence and never converted into adverse predictive results.

The final ledger contains **3 scored fresh predictive endpoints, 31 scientific/protocol STOPs and 3 administrative exclusions**. Candidate hunting was hard-stopped after the first valid third predictive endpoint; a fourth fresh endpoint is not permitted to improve the apparent result pattern.

### Cross-ecosystem synthesis

The ecosystem/endpoint, not the individual row, is the unit of fresh replication. Each endpoint is reported separately using baseline and augmented macro log loss, paired difference, relative change and heldout-unit wins. No row-level pooling, common-effect estimate or pooled significance test is used.

### Feature-count placebo

For Tampa Bay only, a secondary response-independent control tested whether degradation could be explained merely by adding ten columns. Twenty matched-count placebo replicates independently permuted the Layer-B columns within the frozen train/heldout structure. The placebo could not alter the primary favorable/null/adverse classification.

## Results

### Layer A falsification occurred in known-truth and ecological applications

The deterministic benchmark behaved as specified: the exact compatible set contracted from two rules to one and then to zero under successive incompatible positive observations. World renaming did not alter the Layer-B feature matrix, while exact latent fingerprints continued to preserve rule identity.

In **STOC**, the first independent EOG-WF attempt to reach calibration could not proceed to its intended heldout prediction comparison: the predeclared 20-world universe was falsified by calibration-period positive distributions for **20/20 species**. This result was retained as an adverse world-universe adequacy result rather than repaired by redefining worlds after response access.

In **Glanville fritillary**, exact rule history remained interpretable as Layer-A state while exact identity failed as a direct supervised representation. Macro log loss was 0.230197 for exact identity versus 0.187983 for the declared symmetric compression, and exact identity lost in all 6/6 heldout transitions. Thus identity preservation is justified by audit/falsification requirements, not by a prediction claim.

In **Southwest Louisiana King Rail**, all six frozen local Layer-A worlds were eventually falsified; only `external_open` survived. This structural conclusion coexisted with a small favorable Layer-B augmentation, illustrating directly that structural falsification and predictive complementarity are distinct outputs.

### The prospective denominator is 3 scored / 31 scientific STOP / 3 administrative

Thirty-one candidate attempts terminated at scientific or protocol gates before a valid scored endpoint. Three additional records were administrative exclusions and remain outside the scientific denominator. STOPs document where a candidate could not satisfy the frozen contract without post-outcome repair; they provide neither favorable nor adverse evidence for Layer-B predictive value.

### Fresh Layer-B paired augmentation was asymmetric

**Azores yellow eel telemetry.** Baseline macro log loss was 0.1422727 and augmented log loss 0.1322871, a difference of −0.0099856 (**−7.0%**). The augmented arm won 5/5 heldout blocks.

**Southwest Louisiana King Rail passive acoustics.** Baseline macro log loss was 0.2463173 and augmented log loss 0.2453455, a difference of −0.0009718 (**−0.39%**). The augmented arm won 7/8 heldout occasions. The magnitude is small and should not be treated as equivalent to the Azores effect.

**Tampa Bay seagrass monitoring.** Baseline macro log loss was 0.3377354, whereas augmented log loss was 0.4387640, a difference of +0.1010287 (**+29.9%**). The augmented arm won only 1/5 folds. The matched-count placebo median was 0.3361758, and the real augmentation beat **0/20** placebo replicates. Therefore the adverse result is not explained by the mere addition of ten columns.

The effect magnitudes are notably asymmetric: the largest observed degradation is more than four times the relative magnitude of the largest observed improvement, and each endpoint contains only 5–8 heldout outer units. The series therefore does not support summarizing the outcome as a simple “two wins versus one loss” predictive result.

### Closed interpretation

The evidence supports **Layer A as an auditable structural compatibility, contraction and finite-universe falsification framework, together with a prospective validation design that exposes its full candidate denominator**. Layer-B v1 is not supported as a generally beneficial prediction product. The three scored endpoints show that its added predictive value can be favorable, negligible-to-small, or substantially adverse under the frozen paired design.

The closed evidence does not establish universal predictive superiority, guaranteed Layer-B improvement, causal mechanism identification, unique historical-route recovery, or truth of a surviving exact Layer-A world.

## Discussion

### Layer A is the primary supported scientific object

The strongest result is that exact finite-world falsification is operational rather than decorative. STOC falsified its complete frozen universe before predictive comparison; Louisiana eliminated every frozen local world; and Glanville showed why exact identities must be retained even though those same identities were poor supervised features. These outcomes are especially informative because they are failures of declared explanations. A falsification framework that only records successful survivors would be difficult to distinguish from post-hoc model selection; here, incompatible worlds and even complete universes were allowed to fail terminally.

The appropriate interpretation remains conditional. Layer A can say which **declared** worlds survive or are eliminated under the frozen evidence contract. It cannot say that a surviving world is historical truth, nor that a falsified finite universe establishes unrestricted biological impossibility. Its value is auditable constraint and refutation within an explicitly declared model universe.

### The prospective denominator is part of the method result

The 31 scientific/protocol STOPs should not be pooled with predictive outcomes, but neither should they disappear from the paper. Their visibility describes the actual selection process through which the three scored endpoints were reached. A candidate that fails source transport, registry identity, geometry, effort semantics, response schema or estimability cannot be silently repaired after outcome access and still count as an independent predeclared test.

This is more than reproducibility bookkeeping. If technically incompatible or adverse systems can be replaced until a favorable example appears, the apparent replication count no longer represents the original inferential process. The hard stop after the third valid endpoint therefore protects the meaning of the denominator. It also means the current predictive series is closed rather than an interim search awaiting a more favorable fourth result.

### Layer B should be read as a stress test of productization, not the main contribution

The Layer-B results are valuable mainly because they prevent an overly broad product claim. Azores provides the clearest positive example, Louisiana adds only a 0.39% log-loss reduction, and Tampa produces a 29.9% degradation. The imbalance in magnitudes and small number of heldout outer units make it inappropriate to market Layer B as a generally useful predictive complement on the basis of “two favorable endpoints.”

A more defensible conclusion is that compressing a structurally meaningful world state into supervised features is a separate empirical problem. The same structural framework can remain useful when its prediction-facing compression adds no value or causes harm. That is exactly why Layer A and Layer B should not be collapsed into one score or one product claim.

The Tampa placebo sharpens but does not solve this problem. Randomized ten-column blocks perform near the baseline whereas the real aligned Layer-B block performs much worse, so feature count alone is not a sufficient explanation. The closed study does **not** identify the mechanism of that degradation. Explanations involving ecology, spatial blocking, feature redundancy, static representation or learner interaction would be post-outcome hypotheses unless tested in a separately frozen mechanism study.

### Prediction, non-identification and falsification are different statements

A favorable Layer-B comparison means only that the frozen augmented arm achieved lower heldout log loss than the unchanged baseline for that endpoint. It does not validate a surviving Layer-A world. Conversely, falsifying a Layer-A world does not imply that Layer B should improve prediction. Louisiana demonstrates both statements simultaneously: local structural worlds were eliminated while the compressed representation produced only a very small predictive gain.

This separation also clarifies what remains untested or unidentified. The closed paired series evaluates Layer B as an **augmentation** to an unchanged strong learner; it does not establish a generally useful standalone Layer-B product. The degradation mechanism in Tampa is unidentified by the closed endpoint. The fourth predictive endpoint is intentionally absent by hard stop, not missing by accident. Exact-world truth is not merely untested but non-identified by design.

### Relationship to existing ecological prediction methods

EOG-WF is not presented as a replacement for species distribution models, dynamic occupancy models, mechanistic range models, landscape connectivity methods or generic ensemble learning. Accessibility constraints, occupied-source proximity, habitat-network occurrence models and suitability-derived connectivity are already established components of ecological prediction (Prugh, 2009; Barve et al., 2011; Schooley & Branch, 2011; Ortiz-Rodríguez et al., 2019; Nelli et al., 2022). Those methods can estimate local occurrence support, occupancy dynamics, dispersal processes, connectivity or predictive combinations directly. EOG instead asks whether a declared finite set of structural worlds remains compatible with accumulating distribution evidence and preserves exact provenance when worlds are eliminated.

Nor does the novelty claim rest on any individual ingredient such as thresholded connectivity, path or network representations, permutation-invariant summaries, model combination or schema validation. Sensitivity of habitat-network predictions to dispersal thresholds is itself an established concern (Ortiz-Rodríguez et al., 2023). The contribution lies in the domain-specific combination of exact finite-world ecological falsification, strict separation of structural state from its prediction-facing compression, and a response-blind validation protocol that retains failed candidates in the denominator rather than repairing them away.

### Limitations

First, Layer-A claims are bounded by the declared finite universe. Unrepresented worlds can exist, so complete finite-universe falsification is not equivalent to proof of biological impossibility.

Second, the fresh predictive series contains only three scored endpoints and 5–8 heldout outer units per endpoint. It demonstrates heterogeneity and one substantial adverse case but cannot estimate a general distribution of Layer-B effects.

Third, the frozen ten-feature Layer-B representation is only one compression of exact state. Its invariance to world labels is a required representation property, not evidence that it is sufficient or optimal for prediction.

Fourth, the prospective protocol is demanding and excludes many otherwise interesting datasets. This is intentional for the current inferential claim, but it limits immediate application where response-independent registries, geometry, effort semantics or source separation cannot be reproduced.

Finally, neither favorable nor adverse predictive differences identify mechanism. The Tampa degradation mechanism in particular remains outside the closed study's identified results; only the feature-count explanation is directly weakened by the matched placebo.

### Conclusion

EOG's strongest supported contribution is an **auditable finite-world structural inference and falsification state whose validation history exposes both successful updates and terminal failures**. A prospective response-blind funnel makes the denominator of that evidence explicit. The prediction-facing Layer-B compression is intentionally subordinate to this claim: across three fresh paired endpoints it produced a moderate improvement, a very small improvement, and a much larger degradation. Rather than rescuing or averaging away that disagreement, EOG retains it as evidence that structural interpretability and predictive utility are separate empirical properties.

The resulting product boundary is conservative. Layer A can be used for declared-world compatibility, sequential contraction and finite-universe falsification without assuming that Layer B will improve a conventional predictor. Any predictive use of a compressed world-set representation requires its own prospective validation.

## References

Barve, N., Barve, V., Jiménez-Valverde, A., Lira-Noriega, A., Maher, S.P., Peterson, A.T., Soberón, J. & Villalobos, F. (2011). The crucial role of the accessible area in ecological niche modeling and species distribution modeling. *Ecological Modelling*, 222, 1810–1819. https://doi.org/10.1016/j.ecolmodel.2011.02.011

Houlahan, J.E., McKinney, S.T., Anderson, T.M. & McGill, B.J. (2017). The priority of prediction in ecological understanding. *Oikos*, 126, 1–7. https://doi.org/10.1111/oik.03726

Nelli, L., Schehl, B., Stewart, R.A., Scott, C., Ferguson, S., MacMillan, S. & McCafferty, D.J. (2022). Predicting habitat suitability and connectivity for management and conservation of urban wildlife: A real-time web application for grassland water voles. *Journal of Applied Ecology*, 59, 1072–1085. https://doi.org/10.1111/1365-2664.14118

Ortiz-Rodríguez, D.O., Guisan, A., Holderegger, R. & van Strien, M.J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution*, 9, 10457–10471. https://doi.org/10.1002/ece3.5567

Ortiz-Rodríguez, D.O., Guisan, A. & van Strien, M.J. (2023). Sensitivity of habitat network models to changes in maximum dispersal distance. *PLoS ONE*, 18, e0293966. https://doi.org/10.1371/journal.pone.0293966

Prugh, L.R. (2009). An evaluation of patch connectivity measures. *Ecological Applications*, 19, 1300–1310. https://doi.org/10.1890/08-1524.1

Schooley, R.L. & Branch, L.C. (2011). Habitat quality of source patches and connectivity in fragmented landscapes. *Biodiversity and Conservation*, 20, 1611–1623. https://doi.org/10.1007/s10531-011-0049-5

Shmueli, G. (2010). To explain or to predict? *Statistical Science*, 25, 289–310. https://doi.org/10.1214/10-STS330

## Submission-boundary checklist

Before submission, confirm that the manuscript still satisfies all of the following:

- [ ] exactly 3 fresh scored predictive endpoints;
- [ ] endpoint pattern remains favorable / favorable / adverse without being summarized as a vote count;
- [ ] no fourth fresh predictive endpoint;
- [ ] 31 scientific/protocol STOPs and 3 administrative exclusions remain correctly separated;
- [ ] STOC 20/20 universe falsification is described as Layer-A/world-universe adequacy evidence, not a predictive result;
- [ ] no row-level pooled effect or common-effect significance claim;
- [ ] no claim of universal Layer-B superiority or guaranteed improvement;
- [ ] no standalone Layer-B product claim from the closed paired series;
- [ ] no unique historical-route or surviving-world truth claim;
- [ ] Louisiana decoupling is described as structural falsification plus a very small predictive gain, not mechanistic validation;
- [ ] Tampa placebo is secondary and only weakens the feature-count explanation;
- [ ] Tampa degradation mechanism remains explicitly unidentified in the closed study;
- [x] literature-positioning statements are supported by verified references and no citation placeholders remain;
- [ ] final archive/DOI, title page, author contributions, AI-use disclosure and journal-specific format are checked on the submission date.
