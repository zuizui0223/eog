# Open ecological data are not necessarily inferentially open: a prospective audit of ecological data access and observation-state identifiability

**Working target:** Ecological Informatics  
**Status:** manuscript spine v1

## Abstract

Open ecological data are increasingly abundant, but public availability does not imply that a predeclared ecological inference can actually be reconstructed. We quantified this gap using a prospective candidate-flow audit in which public monitoring systems were screened before biological outcomes were inspected. Among 34 scientific candidate systems, only 3 reached a scored predictive endpoint; 31 stopped under frozen protocol gates. Twenty-nine of 31 stops occurred before any biological-response access, and 30/31 occurred before response rows were opened. The 31 stops separated into four recurrent barrier families: transport/interface/identity (11), registry/geometry/temporal-frame reconstruction (9), response linkage/separation/semantics (7), and physical schema integrity at the response boundary (4). A complementary relation-inference programme showed a deeper boundary. Of 12 source architectures screened, two systems had independently separated relation, event and function streams, yet neither could identify a hard biological negative because false-negative and detection-completeness calibration was unavailable; reconstruction of existing raw and supplementary sources recovered such calibration for 0/2 systems. These results distinguish **data openness** from **inferential openness**. For reproducible ecological inference, repositories must expose not only response values, but also reconstructable sampling frames, stable identifiers, explicit linkage, surveyed-negative semantics, failure states and observation-process calibration.

## 1. Introduction

Ecology has invested heavily in making data findable and downloadable. Open repositories, long-term monitoring programmes and standardized biodiversity infrastructures now make many datasets publicly accessible. Yet a reproducible ecological analysis requires more than obtaining a file.

A predictive or relational endpoint may depend on a sampling-frame registry, spatial geometry, survey calendar, source separation, stable identifiers, response linkage, the meaning of zero or non-detection, and explicit distinction between missing observations and confirmed biological absence. If any of those elements is unavailable, an apparently open dataset can remain unusable for the intended inference.

Most discussions of data availability are retrospective. Analysts report datasets they successfully obtained and analysed, while systems that could not be reconstructed disappear from the denominator. This makes it difficult to estimate where ecological inference actually fails.

Here we use a prospective, response-blind candidate-flow design. Candidate systems were admitted under frozen rules and stopped when a required data or semantic layer could not be reconstructed. A STOP was not interpreted as adverse biological evidence. It recorded the stage at which the requested inference ceased to be identifiable.

We ask two questions.

1. Across a finite set of public ecological monitoring candidates, how often does an apparently suitable system reach an actual predictive endpoint, and where do non-scientific barriers occur?
2. After source architecture is adequate, can biological negative states still remain unidentifiable because the observation process is not calibrated?

The first question is answered by a 34-system EOG candidate denominator. The second is illustrated independently by the 284b Level-C relation programme. We do not pool the two programmes statistically; together they define successive layers of inferential openness.

## 2. Methods

### 2.1 Prospective EOG candidate denominator

The EOG candidate-flow ledger was frozen as part of a once-only predictive-complementarity programme. Administrative placeholders and duplicate entries were excluded from the scientific denominator.

The resulting scientific denominator comprised:
- 3 systems that reached scored predictive endpoints;
- 31 systems that stopped under a prospectively frozen protocol rule.

STOPs were not counted as null or adverse predictive results.

### 2.2 Response-access boundary

For each STOP we retained the highest level of biological-response access:
- none;
- header only;
- full response once.

This distinguishes failures of data architecture from failures discovered only after biological response opening.

### 2.3 Barrier taxonomy

Exact frozen terminal stages were retained in the source ledger. For manuscript synthesis we group them into four descriptive families without changing any terminal label.

**Transport/interface/identity**
includes source transport failures, bounded-range transport, metadata-identity mismatches and interface failures.

**Registry/geometry/temporal frame**
includes failure to reconstruct the published sampling universe, spatial registry, temporal registry or sufficient response-independent contexts.

**Linkage/separation/semantics**
includes inability to link response to sampling units, failure to separate response from design information, surveyed-negative ambiguity, and missing baseline/calendar semantics.

**Physical schema boundary**
includes header/schema failures, incomplete response-blind archive inventory and full-response schema/linkage failure.

The grouped taxonomy is descriptive and post hoc; the underlying terminal stages remain the authoritative evidence.

### 2.4 Deeper relation-identifiability case

We use the 284b Level-C programme as a separate case study, not as additional EOG denominator units.

A response-blind architecture screen evaluated 12 candidate cross-role ecological dependencies. Two candidates qualified for source-level follow-up:

- a *Cremastra* pollination system with independently separated breeding-system, fruit and pollinia-transfer streams;
- a *Belonocnema*–live-oak system with independently separated host-specificity, emergence and budbreak streams.

The hard endpoint required a directional implication E(k) -> F(k). A contradiction therefore required not merely failure to observe F, but an identifiable F=false state at the same key.

Candidate-specific calibration and raw-source reconstruction were then audited without opening focal cross-role outcome values.

## 3. Results

### 3.1 Only 3 of 34 scientific candidates reached predictive scoring

Of 34 scientific candidate systems, 3 reached a scored predictive endpoint and 31 stopped before predictive evaluation.

Thus:
- scored endpoints: **3/34 = 8.8%**;
- protocol STOPs: **31/34 = 91.2%**.

The three scored systems were not uniformly favorable, demonstrating that the pipeline was capable of producing favorable and adverse scientific outcomes once a system was inferentially open.

### 3.2 Most STOPs occurred before biological response access

Among 31 protocol STOPs:
- **29/31** opened no biological response;
- **1/31** opened only a response header;
- **1/31** reached the full response before a schema/linkage inconsistency terminated the endpoint.

Therefore **30/31** stopped before any response data row was opened.

The dominant losses were consequently not failed ecological hypotheses. They were failures to reconstruct the information architecture required to test those hypotheses.

### 3.3 Barriers occurred at several distinct layers

The 31 STOPs grouped into:

- transport/interface/identity: **11**;
- registry/geometry/temporal frame: **9**;
- linkage/separation/semantics: **7**;
- physical schema boundary: **4**.

No single technical problem dominated the entire denominator. Inferential openness depends on a chain of distinct data properties.

### 3.4 Open architecture did not guarantee identifiable biological absence

The 284b architecture screen retained 2 of 12 candidates with sufficiently separated source architecture for deeper evaluation.

Both retained systems supported biologically meaningful **positive** observations. However, neither supported a prospectively calibrated **negative** state.

For both candidates:
- detection completeness adequate for hard absence: **0/2**;
- candidate-specific calibration passing all required criteria: **0/2**;
- existing raw/supplementary data capable of reconstructing the missing calibration: **0/2**.

No focal cross-role value was opened and no non-detection was converted into F=false.

Thus data can remain inferentially closed even after the relevant response streams are public, separated and biologically meaningful.

## 4. Discussion

### 4.1 Public availability is only the first layer of openness

The EOG denominator shows that downloadability is a poor proxy for inferential readiness. A study can fail before response access because the published sampling frame cannot be reconstructed, geometry is incomplete, identifiers drift, transport interfaces do not support bounded inspection, or design and response are physically inseparable.

These are not cosmetic reproducibility problems. They determine which ecological estimand exists.

### 4.2 Sampling frames should be treated as first-class data products

Several STOPs arose because the paper-defined site, camera, patch or temporal universe could not be reproduced independently of the biological response.

A response table without a reconstructable denominator cannot support many absence, occupancy, connectivity or temporal-holdout analyses.

Repositories should therefore publish stable sampling-frame registries alongside observations.

### 4.3 Zero requires semantics

The Level-C case exposes a deeper problem. Even when positive event/function streams exist independently, a missing or zero observation cannot automatically be interpreted as biological absence.

Hard negative inference requires:
- known observation windows;
- explicit failure/missingness states;
- a prespecified negative rule;
- evidence about false-negative performance.

Without those components, the scientifically correct state is unresolved.

### 4.4 Toward an inferential-openness checklist

The combined evidence suggests a layered checklist:

1. **Transport openness** — can exact frozen resources be retrieved?
2. **Registry openness** — can the sampling units, geometry and temporal frame be reconstructed?
3. **Linkage openness** — can design, covariates and responses be joined without using forbidden response information?
4. **Semantic openness** — are surveyed negatives, missing values and failure states explicit?
5. **Calibration openness** — can non-detection or absence be interpreted with known observation performance?
6. **Endpoint openness** — can the predeclared ecological contrast be scored without post-outcome repair?

A dataset can be open at one layer and closed at the next.

### 4.5 Limitations

The EOG denominator is not a random sample of all ecological datasets. It is a finite set of systems selected for a particular predictive-complementarity programme, so the 8.8% endpoint rate should not be generalized as a global prevalence estimate.

The barrier-family grouping is descriptive and was created after the exact terminal stages were frozen.

The 284b case is a separate programme with a different scientific target and is not pooled into the EOG denominator.

The value of the study is therefore not a universal failure rate. It is the direct measurement of where a prospectively declared ecological inference becomes impossible, while preserving the denominator and preventing unsuccessful systems from disappearing from the record.

## 5. Conclusion

**Open data are not necessarily inferentially open.**

In a finite prospective audit, most candidate ecological monitoring systems stopped before biological response rows were accessed, and the barriers spanned transport, sampling-frame reconstruction, linkage, schema and semantics. Even after source architecture was adequate, hard biological absence could remain unidentified without calibrated detection.

Reproducible ecological data infrastructure should therefore publish the information required to reconstruct an inference, not only the values eventually analysed.

## Data and provenance

The quantitative EOG denominator is derived from the frozen candidate-flow ledger. The Level-C case study is pinned to frozen 284b result objects by commit and blob identity in the accompanying provenance receipt.

No STOP is treated as an adverse biological result.
