# From open data to open inference: a prospective audit of ecological evidence pipelines

**Working target:** Ecological Informatics  
**Article type:** Research Article  
**Status:** cross-project draft v2

## Abstract

Open ecological data can be findable and reusable yet still fail to support a specific biological claim. We operationalize a narrower downstream property, **inferential openness**: whether a data–claim pairing preserves the source identity, opportunity registry, response linkage, observation semantics and calibration needed to authorize the target inference under a declared information-access order. We measured this property in two prospectively governed ecological programmes that retained terminal STOPs rather than repairing candidates after outcomes. In a prospectively governed predictive workflow, 34 scientific candidate attempts produced three scored predictive endpoints and 31 scientific/protocol STOPs. The 31 STOPs localized to transport or source identity (11), registry/geometry/time reconstruction (10), source separation/linkage/schema (8), and semantic or covariate validity (2). Twenty-nine STOPs occurred before any biological-response access, one after header-only access and one after a single full-response opening; thus 30/31 STOPs occurred before any biological-response row value was opened. A separate biological-relation audit tested a later inferential layer. Of 12 biological systems, two had prospectively identifiable relation/event/function source architectures, but neither had independent candidate-specific calibration sufficient to distinguish a true negative function state from non-detection or missingness. Consequently zero hard dependency endpoints were opened. These denominators are workflow-specific and are not prevalence estimates for ecology. Together, the audits show that public availability and inferential readiness are distinct: claim-ready reuse requires a reproducible chain from bytes and registries to the semantics and calibration of the biological state being inferred. Prospectively retaining terminal STOPs makes these usually hidden requirements measurable.

**Keywords:** data reuse; ecological informatics; FAIR; open data; preregistration; reproducibility; observation process; data provenance

## 1. Introduction

Ecology has invested heavily in making data more open and reusable. The FAIR principles formalize findability, accessibility, interoperability and reusability, while ecological data-management work increasingly translates those principles into concrete practices involving metadata, persistent storage, standards and structure. Recent guidance for ecologists makes that translation explicit and practical (Jantzen & Vriend 2026).

Yet reuse is always reuse **for something**. A file can be openly downloadable, richly described and technically interoperable while still lacking the particular information needed for a scientific claim. A camera-trap archive may contain observations but not a response-independent deployment registry. A survey may contain zeros without documenting whether a focal taxon was actually searched for. A biological monitoring system may record a required function positively, while non-detection remains impossible to interpret as functional absence.

These are not ordinary model-performance failures. They occur before, or logically upstream of, the point where predictive or biological evidence can be scored.

Open-science practice creates an opportunity to measure those barriers. Adaptive preregistration has recently been advocated for model-based ecology because ecological analyses often involve sequential decisions rather than a single fixed hypothesis test (Wintle & Rumpff 2026). If those decision points, information barriers and stopping rules are committed before focal outcomes are viewed, a terminal STOP becomes an observable state of the scientific workflow rather than an invisible abandoned attempt.

Data-quality and data-reuse scholarship already emphasizes that usefulness is context dependent: a resource may be FAIR or technically reusable without being fit for a particular scientific purpose. We therefore do not present claim-specific suitability itself as a new concept. We use **inferential openness** for a narrower, operational question: whether a data–claim pairing permits the required evidence chain to be reconstructed under a declared information-access order, without importing the outcome that the workflow is meant to evaluate. The novelty we test is prospective measurability of that boundary—whether precommitted STOP rules turn otherwise invisible abandoned reuse attempts into a finite empirical denominator. Inferential openness is not an additional FAIR principle or a permanent scalar quality score attached to a dataset.

We analyze two prospectively governed programmes. The first is a predictive ecological workflow that attempted to reconstruct structural ecological information before opening biological responses. It provides a finite denominator of candidate attempts and terminal STOP stages. The second is a biological-relation audit that begins further downstream: after relation and source architecture are plausible, can the negative biological state needed to falsify a hard dependency actually be identified?

Our objectives are to: (1) quantify where a finite predictive workflow stopped before scoring; (2) localize those STOPs relative to biological-response access; (3) identify the later observation-process barrier exposed by the biological-relation audit; and (4) propose a practical inferential-openness ladder connecting public availability to claim-ready evidence.

## 2. Methods

### 2.1 Prospective workflow principle

Both programmes used finite candidate denominators and staged information access. Candidate attempts were allowed to terminate when a prospectively declared requirement failed. A terminal STOP was retained as a workflow result and was not converted into adverse ecological evidence.

This distinction is essential. A failed transport route does not imply ecological absence. A response-independent registry mismatch does not imply poor prediction. An uncalibrated non-detection does not imply a biological negative.

The audit therefore classifies **where inference became unauthorized**, not whether the underlying ecological system was favorable or unfavorable.

### 2.2 Predictive-workflow scientific denominator

The manuscript-facing predictive-workflow candidate ledger contains:

- 3 scored predictive endpoints;
- 31 scientific/protocol STOPs;
- 3 administrative exclusions.

Administrative exclusions include placeholders, duplicate candidate records and one response-consumed output-capture failure that did not yield a recoverable scientific endpoint. They are excluded from the scientific denominator.

The resulting scientific denominator contains **34 candidate attempts**.

The three scored endpoints were Azores yellow eel telemetry, Southwest Louisiana King Rail passive acoustic monitoring and Tampa Bay seagrass transect monitoring. Their predictive signs are not the subject of the present paper; they establish that the workflow can reach and score an endpoint.

### 2.3 Predictive-workflow terminal-stage taxonomy

The 31 STOPs retain their original fine-grained terminal labels. For manuscript-level interpretation we group them into four operational layers without changing the underlying records.

**A. Transport or source identity**
- source_transport;
- bounded_archive_transport;
- metadata_identity_or_transport;
- metadata_identity_or_interface;
- response_blind_archive_range_transport;
- response_blind_zip_presign_transport;
- source_transport_dns.

**B. Registry, geometry or time**
- publication_registry_reproduction;
- geometry_registry;
- temporal_registry;
- response_independent_calendar_value;
- response_independent_geometry_registry;
- temporal_context_estimability.

**C. Separation, linkage or schema**
- physical_source_separation;
- response_linkage;
- response_header;
- response_blind_zip_inventory;
- response_blind_physical_header_schema;
- full_response_schema_or_linkage.

**D. Semantic or covariate validity**
- surveyed_negative_semantics;
- response_independent_baseline_covariate_value.

Counts are computed directly from the frozen candidate-flow table.

### 2.4 Localization relative to response access

For every scientific STOP, the ledger records whether biological-response information had been accessed.

We distinguish:
- no biological-response access;
- response-header only;
- one full-response opening before terminal schema/linkage failure.

The latter does not count as predictive evidence because no scored endpoint was recovered.

### 2.5 Biological-relation architecture and calibration audit

The predictive-workflow funnel asks whether a public system can become a valid scored predictive endpoint. The biological-relation audit asks a later question: after a biological dependency and source architecture are plausible, can the negative function state required for a hard relation be identified?

The biological-relation audit used a directional form

`E(k) -> F(k)`,

where `E(k)` is a dependent event at an exact biological opportunity and `F(k)` is the required biological function at the same key.

The source-architecture screen prospectively required:
- an external relation source `R`;
- an independent event-side observation stream `X`;
- an independent function-side observation stream `Y`.

Twelve candidate systems were screened under a finite cap. Two were architecture-qualified:
- *Cremastra appendiculata* var. *variabilis*;
- *Belonocnema treatae* / live-oak budbreak.

Before focal values were opened, a candidate-specific calibration audit asked whether function non-detection could be interpreted as `F(k)=false`. The frozen criteria required an independent calibration stream, known states, estimable detection performance, adequate temporal/window coverage, separation of failure/missingness states and no outcome-dependent tuning.

Neither retained candidate passed all calibration criteria.

### 2.6 Evidence boundary

The two programmes are not treated as random samples of ecological datasets. Their denominators are prospective workflow denominators created by scientific candidate-selection programmes.

Accordingly, quantities such as 31/34 describe **workflow yield under the declared contracts**, not the prevalence of unusable or insufficiently documented ecological data in the literature.

## 3. Results

### 3.1 Most predictive-workflow candidate attempts terminated before a scored endpoint

Of 34 scientific candidate attempts, **3 reached scored predictive endpoints and 31 reached scientific/protocol STOPs**.

Within this workflow, the scored-endpoint fraction was 3/34 (8.8%) and the STOP fraction was 31/34 (91.2%). These are denominator accounting quantities, not field-wide prevalence estimates.

### 3.2 STOPs were distributed across four operational layers

The 31 scientific STOPs grouped as:

- **11/31 (35.5%)** transport or source-identity barriers;
- **10/31 (32.3%)** registry, geometry or temporal-reconstruction barriers;
- **8/31 (25.8%)** separation, linkage or schema barriers;
- **2/31 (6.5%)** semantic or covariate-validity barriers.

No single failure label dominated. The largest individual fine-grained class was source transport (4), followed by publication-registry reproduction (3).

### 3.3 The dominant barriers preceded biological-response use

Among the 31 STOPs:

- **29/31 (93.5%)** occurred with no biological-response access;
- **1/31** stopped after response-header access only;
- **1/31** stopped after one full-response opening because the frozen deployment/response linkage failed.

Thus **30/31 STOPs occurred before any biological-response row value was opened**.

The dominant bottleneck observed in this workflow was therefore not poor predictive performance after fitting. It was failure to reconstruct a claim-ready source, registry or response architecture before scoring became authorized.

### 3.4 Later inferential layers remained even after source architecture succeeded

The biological-relation architecture screen retained **2 of 12** systems with distinct relation, event and function source channels.

Both then stopped at candidate-specific calibration.

For *Cremastra*, positive effective-pollinator detections were biologically meaningful, but no independent known-state calibration provided an estimate of the probability of detecting effective pollination when present. A zero sensor-camera detection could therefore not be interpreted as function absence.

For *Belonocnema*, budbreak was a biologically appropriate and separately measured resource state, but the available metadata did not calibrate false negatives or distinguish missing/unobserved budbreak from confirmed absence of usable new tissue.

Jointly:
- candidates passing all calibration criteria: **0/2**;
- hard negative authorized: **0/2**;
- focal value opening authorized: **0/2**.

Neither outcome is a biological negative.

## 4. Discussion

### 4.1 Open data and open inference are distinct

The central result is not that ecological data are generally unusable. It is that public availability is only the first requirement in a longer evidence chain.

A resource can be accessible but fail exact source identity. It can be transportable but lack a response-independent opportunity registry. It can contain response rows whose linkage to site/time units depends on the response itself. It can record zeros whose meaning as surveyed negatives is unspecified. Finally, even a biologically direct monitoring channel can fail to identify absence if its detection process is uncalibrated.

We refer to the ability to complete this claim-specific chain as **inferential openness**.

### 4.2 Relation to FAIR and fitness-for-purpose

FAIR concerns digital resource stewardship: findability, accessibility, interoperability and reusability. Recent ecology-specific guidance makes those aims operational through metadata, storage, standards and structure (Jantzen & Vriend 2026).

A separate literature on data quality and reuse has long stressed **fitness for use / fitness for purpose**: data adequacy depends on the intended application rather than on a universal dataset quality score. Environmental-data studies have likewise shown that researchers judge metadata and data in relation to the specific reuse task. Recent work in *Ecological Informatics* makes this distinction concrete by evaluating whether remote-sensing crop classifications are fit for a specific downstream landscape-heterogeneity calculation (Säurich et al. 2026).

Inferential openness is therefore downstream of, and narrower than, both FAIR and general fitness-for-purpose assessment.

A useful conceptual sequence is:

`FAIR / reusable -> fit for intended use -> inferentially authorized for claim C`.

Our added object is the **prospective terminal state of the evidence workflow**. A dataset can appear suitable in broad application terms while still lacking a response-independent opportunity registry, a stable response linkage, admissible negative-state semantics or observation-process calibration needed for one directional inference. When those requirements and information-access rules are precommitted, the point at which inference becomes unauthorized can be retained rather than silently repaired or abandoned.

We therefore do not propose an “I” to add to FAIR, did not measure FAIR compliance of the audited datasets, and do not claim to originate the general concept of data fitness-for-purpose.

### 4.3 The distinctive contribution is a prospective denominator of terminal states

The denominator exists because stopping rules were enforced.

If a failed archive route were silently replaced by a different download path, if a registry mismatch were repaired after reading the response, or if a zero were redefined after observing its consequences, those attempts would disappear from the visible scientific record.

Adaptive preregistration provides a natural framework for ecology because model-based research often contains conditional decisions (Wintle & Rumpff 2026). Our audits show a complementary benefit: when information-order rules are preserved, terminal states can be studied empirically.

This is the feature that distinguishes the present audit from a retrospective fitness-for-purpose checklist. The denominator contains not only resources that ultimately supported analysis, but also prospectively retained attempts that stopped before outcome scoring. Their terminal layer is therefore observable rather than reconstructed from memory after success or failure.

The STOP is not a failed study. It is a measurement of the point at which the requested inference ceased to be identified under the declared contract.

### 4.4 A five-layer inferential-openness ladder

The combined evidence suggests five practical layers.

**1. Transportable exact source.**  
Can the declared source/version be retrieved under a reproducible route?

**2. Reproducible response-independent registry.**  
Can the spatial units, geometry and temporal opportunity denominator be reconstructed without reading the outcome?

**3. Separated and linkable response architecture.**  
Can response records be linked to the declared units without forbidden mixed tables, ad hoc remapping or post-outcome schema repair?

**4. Semantically admissible observation state.**  
Does an observed zero or absence flag represent a surveyed negative rather than missingness, invalid metadata or an unobserved state?

**5. Calibrated inferential state.**  
When a negative observation is used to contradict a biological relation, is the observation process calibrated well enough to distinguish true absence from non-detection? This requirement is classical in ecological observation models: non-detection does not imply absence when detection probability is below one (MacKenzie et al. 2002).

The predictive workflow measured losses primarily across Layers 1–4. The biological-relation audit demonstrates Layer 5.

### 4.5 Practical data-publication implications

A conventional data-availability statement often certifies the existence of files and a persistent location. For reuse-intensive ecological inference, that is not enough to describe claim readiness.

We suggest that repositories and data papers make the following objects explicit when they exist:

- immutable source/version identifiers and direct file relationships;
- site/deployment/plot registries independent of biological response;
- explicit temporal survey/opportunity tables;
- stable keys connecting response rows to those registries;
- surveyed-negative versus missing/not-surveyed semantics;
- detector failure and incomplete-window states;
- calibration or repeat-observation information when non-detection is interpreted biologically.

These additions improve more than reproducibility. They determine which questions future researchers are allowed to ask without inventing states that were never measured.

### 4.6 Limitations

The predictive-workflow candidates were not randomly sampled from all ecological datasets. They were candidate systems selected for a particular structural-prediction programme. The stop fractions therefore cannot estimate the prevalence of data-access or metadata problems in ecology.

Some transport failures may be temporary. Some STOPs reflect deliberate strictness in our contracts rather than defects in the original data release. A dataset that is unresolved for our claim may be entirely adequate for the purpose for which it was collected.

The biological-relation audit contains only two retained architectures at the calibration stage. Its contribution is to expose a later class of inferential requirement, not to estimate how often negative-state calibration is absent across ecology.

## 5. Conclusion

Open ecological data do not become open inference merely by being downloadable.

In a finite prospective predictive workflow, 31 of 34 scientific candidate attempts stopped before a scored endpoint, and 30 of those 31 stopped before any biological-response row value was opened. In a separate biological-relation audit, two systems with plausible independent source architectures still could not support hard negative function states because candidate-specific detection calibration was unavailable.

The practical unit of openness for ecological inference is therefore a **reproducible evidence chain**, not a file.

By prospectively retaining STOPs rather than repairing them after outcomes, ecological workflows can make that chain — and its missing links — measurable.

## References

Bishop, B.W., Hank, C., Webster, J. & Howard, R. (2019). Scientists' data discovery and reuse behavior: (Meta)data fitness for use and the FAIR data principles. *Proceedings of the Association for Information Science and Technology*. https://doi.org/10.1002/pra2.4

Bokulich, A. & Parker, W. (2021). Data models, representation and adequacy-for-purpose. *European Journal for Philosophy of Science*, 11. https://doi.org/10.1007/s13194-020-00345-2

Jantzen, C.C. & Vriend, S.J.G. (2026). Putting FAIR into practice for ecologists: How to make ecological data more reusable. *Ecological Informatics*, 95, 103712. https://doi.org/10.1016/j.ecoinf.2026.103712

MacKenzie, D.I., Nichols, J.D., Lachman, G.B., Droege, S., Royle, J.A. & Langtimm, C.A. (2002). Estimating site occupancy rates when detection probabilities are less than one. *Ecology*, 83, 2248–2255. https://doi.org/10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2

Säurich, J., Schwieder, M., Preidl, S., Beyer, F. & Möller, M. (2026). Are remote sensing-based crop type classifications suitable for calculating a landscape heterogeneity metric? A data-fitness-for-purpose assessment. *Ecological Informatics*, 95, 103660. https://doi.org/10.1016/j.ecoinf.2026.103660

Wilkinson, M.D. et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, 3, 160018. https://doi.org/10.1038/sdata.2016.18

Wintle, B.C. & Rumpff, L. (2026). ‘But I can't preregister my research’: Improving the reproducibility and transparency of ecology and conservation with adaptive preregistration for model-based research. *Methods in Ecology and Evolution*, 17, 1768–1787. https://doi.org/10.1111/2041-210X.70311
