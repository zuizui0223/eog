# Open data are not necessarily inferentially open: a prospective audit of ecological endpoint accessibility

**Working target:** Ecological Informatics  
**Status:** manuscript v1 from frozen ledgers only  
**Scientific boundary:** no new candidate search, no new biological-response opening, no reinterpretation of terminal STOPs

## Abstract

Public availability does not guarantee that an ecological dataset can support a prospectively specified inferential endpoint. We examined this gap using two independently frozen ecological workflows that retained candidates terminating before endpoint evaluation instead of repairing or replacing them after outcome access. In the Environmental Occupancy Geometry (EOG) validation programme, 34 scientific candidate systems entered the frozen workflow. Three reached valid scored predictive endpoints and 31 terminated at scientific or protocol STOPs, giving an endpoint-conversion fraction of 3/34 (8.82%) within this deliberately selected workflow. Of the 31 STOPs, 29 occurred without biological-response access, one after response-header access only, and one after a single full-response opening that exposed an unrecoverable frozen linkage violation. STOPs arose from source transport, source/version identity, sampling registries, geometry, temporal denominators, physical response separation, linkage, negative semantics, baseline covariates and estimability. They were not treated as adverse ecological results. A second workflow, the 284b Level-C programme, screened 12 biological systems for a harder dependency endpoint. Two passed source-architecture qualification and had materializable relation, event and positive-function streams, but neither authorized a hard endpoint because the negative functional state was not independently calibrated. Candidate-specific calibration passed 0/2 systems, and existing raw or supplementary sources reconstructed adequate absence calibration in 0/2. These results motivate **inferential accessibility** as an endpoint-relative property: whether the released evidence exposes the source identity, sampling universe, linkage, semantics and state calibration required to evaluate a declared ecological claim without post-inspection repair. The observed fractions are workflow-specific, not field-wide prevalence estimates. We propose an inferential-accessibility manifest that records the information states needed to make public ecological data claim-ready.

## Introduction

Ecological data are increasingly discoverable and reusable, but a public file is not automatically a valid endpoint. A model-ready analysis may require more than downloadable bytes: the exact source version must be identifiable, the sampling universe must be reconstructable, response records must link to declared units, survey effort and missingness must have defensible semantics, and the biological state required by the claim must be observable with adequate calibration.

This distinction is downstream of FAIR data practice rather than a replacement for it. FAIR-oriented workflows ask whether resources are findable, accessible, interoperable and reusable. Ecological observation frameworks likewise recognize latency, identifiability, effort and scale as major determinants of what can be inferred from recorded data. The unresolved practical question is narrower: **given a public ecological system and a prospectively declared endpoint, does the released evidence contain every information state required to evaluate that endpoint without changing the question after inspection?**

Most published examples make this denominator difficult to see. Candidate datasets that cannot be transported, joined, reconstructed or interpreted may disappear before analysis, while studies that reach a valid endpoint remain visible. If the endpoint, parser, registry, negative-state rule or candidate itself can be repaired after biological outcomes are inspected, the resulting denominator no longer represents the original inferential process.

We use two prospectively governed programmes to expose this hidden denominator. The first is the EOG fresh validation funnel, which attempted to convert public ecological monitoring systems into frozen held-out predictive endpoints under response-blind source, registry, geometry, effort and semantic gates. The second is the 284b Level-C programme, which asked a later question: once independent relation, event and function channels are materially available, is the negative biological state required to falsify a hard dependency itself identifiable?

The two programmes therefore probe different depths of the same source-to-claim chain. EOG primarily exposes whether a public system can be transformed into a valid endpoint at all. Level C shows that even after positive relation/event/function channels exist, the observation process may still be insufficient to interpret a non-detection as biological absence.

We call this property **inferential accessibility**. It is endpoint-relative and does not grade a repository or dataset as globally good or bad. A dataset can be highly reusable for one question and insufficient for another. Our aims are to (1) quantify the retained EOG source-to-endpoint denominator, (2) identify where that pipeline stopped before scoring, (3) test whether a deeper absence-identification barrier remained in the independently frozen Level-C workflow, and (4) translate the combined evidence into a reusable manifest for ecological data intended to support prospective inference.

## Materials and Methods

### Study design and non-repair rule

Both programmes used finite candidate ledgers and terminal-state rules defined before the focal biological values needed for the intended endpoint were used. A terminal STOP meant that the prospectively declared endpoint could not be evaluated under the frozen information boundary. STOPs were retained in the denominator rather than repaired and converted into valid endpoints after response inspection.

Three distinctions were enforced throughout.

First, **STOP was not an adverse ecological result**. It indicated endpoint unavailability under the declared contract.

Second, **administrative exclusions were not scientific candidates** and were excluded from the scientific denominator.

Third, unresolved or uncalibrated negative states were not converted into biological absence.

No new candidate search or biological-response opening was performed for the present synthesis. All counts and classifications were read from frozen ledgers.

### EOG prospective endpoint funnel

The EOG programme evaluated public ecological systems for a paired predictive endpoint comparing an unchanged conventional learner with the same learner augmented by a frozen EOG representation. Before scored fitting, candidate systems passed response-blind checks covering source identity, transport, sampling registry, geometry, temporal structure, response separation, linkage, survey-negative semantics, baseline covariates and endpoint estimability.

The frozen candidate-flow ledger contains 37 records. Three were administrative exclusions and therefore lie outside the scientific denominator. The remaining 34 scientific candidates consist of three scored predictive endpoints and 31 scientific/protocol STOPs.

For each scientific STOP we retained the original terminal-stage label and biological-response-access state. We summarized terminal stages without changing their original classifications.

### EOG response-access localization

To distinguish source-to-endpoint failures from post-model performance failures, we classified every scientific/protocol STOP according to the biological response accessed before termination:

- no biological response access;
- response-header access only;
- one full-response opening followed by terminal STOP.

Scored predictive endpoints were not included in this STOP localization.

### Level-C source-architecture screen

The independent 284b Level-C v3 programme screened a finite set of 12 biological candidate systems. The architecture screen asked whether three conceptually distinct evidence channels could be materialized without opening focal endpoint values:

1. an independent biological relation;
2. an event or outcome stream;
3. a function or resource stream relevant to the relation.

Two candidates passed architecture qualification: *Cremastra appendiculata* var. *variabilis* and *Belonocnema treatae* / live-oak budbreak.

For *Cremastra*, the retained architecture consisted of external breeding-system evidence plus distinct same-key fruit and pollinia-carrying camera streams. For *Belonocnema*, it consisted of independent host-specificity evidence plus distinct natural adult-emergence and live-oak budbreak streams.

### Negative-state qualification

Architecture qualification did not authorize a hard dependency endpoint. The next gate asked whether the negative function state could be interpreted prospectively.

For *Cremastra*, positive effective-pollinator detections were biologically meaningful, but a sensor-camera non-detection could not be promoted to absence of effective pollination without candidate-specific detection-completeness calibration.

For *Belonocnema*, budbreak and adult-emergence streams were separately materializable, but missing or unobserved budbreak could not be promoted to true absence of usable new tissue without calibration distinguishing observational failure from biological absence.

Both systems therefore terminated as unresolved absence adequacy rather than biological negatives.

### Candidate-specific calibration audit

The subsequent v5 calibration audit required an independent calibration stream, known-state support, estimable detection performance, adequate window coverage, separation of failure/missingness states and no outcome tuning.

For *Cremastra*, no overlapping gold-standard observation stream was located that could estimate detection sensitivity for effective visits independently of fruit outcome. The source itself noted the need for quantitative validation against continuous recording.

For *Belonocnema*, no candidate-specific budbreak detection validation, repeated same-tree cross-observer validation or known-state sensitivity/specificity estimate was available for the required resource-state rule.

Neither candidate passed all calibration gates.

### Existing-source reconstruction audit

A final audit asked whether currently identified raw or supplementary sources could reconstruct the missing calibration without new measurement.

For *Cremastra*, supplementary camera-operation information and limited scheduled-camera trials did not provide a same-unit, same-window gold standard sufficient to estimate effective-visit detection completeness.

For *Belonocnema*, the available budbreak and emergence files confirmed separate positive streams but did not provide an independent calibration stream that distinguished missing records from confirmed absence of usable resource.

Thus 0/2 retained candidates could be rescued by existing identified material.

### Definition of inferential accessibility

We define inferential accessibility as an endpoint-relative property of a public ecological system:

> A system is inferentially accessible for a declared endpoint when the released evidence permits the source identity, sampling universe, linkage, observation semantics and any biological states required by that endpoint to be reconstructed without post-inspection repair.

The definition does not require every dataset to support every possible claim.

## Results

### Only 3 of 34 EOG scientific candidates reached a valid scored endpoint

The frozen EOG scientific denominator contained 34 candidate systems. Three reached valid scored predictive endpoints and 31 terminated at scientific or protocol STOPs. The endpoint-conversion fraction within this workflow was therefore 3/34 = 8.82%.

The three scored endpoints included both favorable and adverse predictive outcomes in the parent EOG study. Endpoint accessibility therefore did not mean success in the biological or predictive sense; it meant that the declared endpoint was validly evaluable.

The 31 STOPs included failures in source transport, bounded archive transport, DNS transport, source/version identity, publication-registry reproduction, geometry registries, temporal registries, physical source separation, response linkage, response headers, response-independent baseline covariates, surveyed-negative semantics and temporal-context estimability.

### Most EOG STOPs occurred before biological response values were opened

Of the 31 scientific/protocol STOPs, 29 occurred with no biological-response access. One stopped after response-header access only. One stopped after a single full-response opening because the frozen parser detected a focal event outside the raw deployment interval; post-response repair and rerun were forbidden.

Thus 30/31 STOPs occurred before any biological response row value could be used for a scored endpoint.

The dominant observed bottleneck was therefore not weak model performance after fitting. It was failure to instantiate the frozen source, registry, geometry, linkage, semantic or estimability requirements needed to make model fitting scientifically interpretable.

### Level C moved the bottleneck from source architecture to negative-state identification

The Level-C v3 architecture screen evaluated 12 candidates and qualified two. Both qualified systems materialized their intended relation, event and positive-function channels.

However, 0/2 authorized a hard dependency endpoint because negative-state adequacy remained unresolved.

For *Cremastra*, camera non-detection could not establish absence of effective pollination function.

For *Belonocnema*, missing or unobserved budbreak could not establish absence of the required resource state.

Neither unresolved state was recoded as a biological negative.

### Candidate-specific calibration passed 0/2 systems

The v5 audit found no independent candidate-specific calibration stream for either retained system. Known-positive detection sensitivity and negative specificity were not estimable under the frozen rules. Candidate-specific calibration therefore passed 0/2 systems, and focal value opening remained unauthorized.

The terminal requirement was additional calibration measurement rather than relaxed interpretation.

### Existing raw and supplementary sources rescued 0/2 systems

The v6 reconstruction audit did not identify sufficient existing material to replace the missing calibration.

*Cremastra* would require overlapping same-inflorescence continuous or prespecified scheduled reference observation across the relevant flowering window, with effective-pollinator labels independent of fruit outcome and explicit camera-failure accounting.

*Belonocnema* would require repeated within-tree resource observations across the relevant opportunity window, an independent or cross-observer reference, a prespecified usable-resource threshold and explicit separation of missing records from confirmed absence.

Accordingly, both systems remained unresolved and required new measurement.

### A layered accessibility stack emerged across the two programmes

The combined ledgers distinguish at least six operational layers:

1. transport and version identity;
2. sampling registry and geometry;
3. relational linkage across units, time and effort;
4. semantic identification of missingness and surveyed negatives;
5. endpoint estimability;
6. state identification and calibration when hard negative inference is required.

Failure at an earlier layer prevents later endpoint evaluation. Passing earlier layers does not guarantee later inferential accessibility, as the Level-C systems demonstrate.

## Discussion

### Public availability and claim readiness are different properties

The empirical pattern is not simply that some public datasets were difficult to use. The stronger result is that the source-to-claim chain contains multiple explicit information states, each of which can be necessary for a valid endpoint.

A file can be openly downloadable while the sampling registry is not reproducible. A registry can be complete while the response cannot be linked to the declared unit. A positive function stream can be materialized while a non-detection remains biologically uninterpretable. These are different failure modes and require different remedies.

Inferential accessibility is therefore conditional on the intended claim. The same dataset may be entirely adequate for descriptive use while being insufficient for a held-out predictive endpoint or a hard-negative mechanistic test.

### The retained denominator changes what is visible

The EOG ledger makes the pre-endpoint denominator explicit. Only three scientific candidates reached scoring, whereas 31 terminated under frozen source or protocol gates. Because 29 of those STOPs occurred without biological-response access and one more occurred at the header stage, the observed attrition cannot be summarized as poor predictive performance.

This distinction matters because candidate replacement after inspection can hide the cost of constructing a valid endpoint. A workflow that silently drops irreconcilable sources and reports only analyzable systems answers a different question from a workflow that retains every prospectively admitted terminal state.

The 8.82% conversion fraction must not be generalized beyond this workflow. The EOG candidate set was deliberately assembled under demanding endpoint requirements and was not a random sample of ecological repositories.

### Negative evidence requires a stronger observation contract than positive evidence

The Level-C programme shows a deeper asymmetry. Positive observations can be biologically informative even when absence is not.

In *Cremastra*, observing a pollinia-carrying visitor is meaningful evidence that the function occurred. Failing to observe such a visit is not equivalent to evidence that the function did not occur unless detection completeness is calibrated.

Likewise, a recorded budbreak event in the *Belonocnema* system is a direct positive resource observation, whereas an unobserved resource state cannot become a hard absence without a known observation process.

This asymmetry is especially important for claims built around contradiction, necessity or dependency. A hard negative endpoint requires not only a source architecture but a defensible mapping from non-observation to biological absence.

### Inferential accessibility complements FAIR and observation-process frameworks

The proposed concept should not be interpreted as a competing FAIR score or a replacement for observation-process theory. FAIR-oriented practice concerns the broader reusability of digital resources, while observation-process frameworks explain how latency, identifiability, effort and scale shape ecological inference.

Inferential accessibility is narrower and operational: for a declared endpoint, can the released evidence instantiate the exact units, links, semantics and calibrated states required to evaluate that endpoint prospectively?

Its empirical contribution is the retained denominator and the explicit terminal boundary between endpoint unavailability and biological evidence.

### A practical inferential-accessibility manifest

For datasets intended to support prospective ecological inference, the release record should, where relevant, expose:

- immutable source and version identity;
- checksums or equivalent physical entity identity;
- sampling-unit registry;
- site and geometry registry;
- survey or effort calendar;
- response-to-unit linkage keys;
- explicit missingness states;
- surveyed-negative definition;
- observation-failure states;
- detection or absence calibration when the intended inference relies on hard negatives.

Not every project needs every field. The manifest is claim-relative: its purpose is to state which inferential operations the released evidence can support.

### Limitations

The EOG candidate denominator is prospective but not randomly sampled. Its 3/34 conversion fraction is therefore not an estimate of the fraction of ecological datasets that are inferentially accessible.

The Level-C result contains only two architecture-qualified systems. The 0/2 calibration result demonstrates a possible binding constraint, not its prevalence across ecology.

Several EOG STOPs reflect the intentionally strict frozen workflow and may have been resolvable under a different predeclared endpoint or source contract. We therefore interpret STOPs as endpoint-specific incompatibility states, not as defects of the data producer.

Finally, inferential accessibility does not establish biological truth. It establishes whether a declared endpoint is licensed by the available evidence under a specified information contract.

## Conclusion

Open ecological data become claim-ready only through a reproducible chain from source identity to the biological state required by the intended inference. In the frozen EOG workflow, most candidate systems terminated before biological response values could support a scored endpoint. In the independent Level-C workflow, even systems with materializable relation, event and positive-function channels remained unable to support hard-negative inference because absence was not calibrated. Retaining these terminal states reveals a hidden denominator that is normally lost between data publication and ecological analysis.

**Public availability is therefore not equivalent to inferential openness. Inferential accessibility is endpoint-relative, and it should be documented as part of the data-to-claim contract rather than inferred from file availability alone.**

## Frozen claim boundary

Supported: the EOG 34-candidate denominator and 3/31 split; the response-access localization of the 31 STOPs; the Level-C 12→2→0 architecture/calibration funnel; the endpoint-relative inferential-accessibility synthesis.

Not supported: a field-wide ecological failure rate; a claim that STOP systems are low-quality or non-FAIR; treating STOP as adverse biology; interpreting 0/2 Level-C systems as a prevalence estimate; or claiming that either retained Level-C biological dependency was falsified.
