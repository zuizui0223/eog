# Inferential openness — literature positioning v2

## FAIR

Wilkinson et al. (2016) define FAIR around findability, accessibility, interoperability and reusability of digital resources.

Jantzen & Vriend (2026), *Ecological Informatics* 95:103712, translate FAIR into practical ecological data components: metadata, storage, standards and structure.

Positioning:
- do not criticize FAIR for failing to answer a question it was not designed to answer;
- place inferential openness downstream of reusable data;
- emphasize that claim-specific registry, negative-state semantics and detection calibration may be required even when a resource is reusable.

Preferred sentence:

> FAIR describes properties that enable digital resources to be found and reused; inferential openness describes whether a particular data–claim pairing preserves the states required to authorize that inference.

## Adaptive preregistration

Gould et al. (2026), *Methods in Ecology and Evolution* 17:1768–1787, argue that model-based ecological research can use adaptive preregistration to preserve transparency across conditional analytical decisions.

Citation audit: The version of record is Gould, Jones, Yen, Fraser, Wootton, Good, Duncan, Hauser, Wintle & Rumpff (2026), DOI 10.1111/2041-210X.70311; the former last-two-author citation was incorrect.

Connection:
- preregistration is the governance mechanism that makes terminal workflow states auditable;
- our paper's empirical object is the distribution of those terminal states;
- do not claim we invented adaptive preregistration.

## Novelty

The manuscript's novelty is **not**:
- another FAIR metric;
- a survey of whether datasets are publicly available;
- a catalog of broken URLs;
- an argument that open data are poor quality.

The novelty is the finite, prospectively governed denominator and localization of where claim authorization stops before outcome scoring.

## Strong distinction

Data availability question:
> Can I obtain and understand the resource?

Inferential-openness question:
> Can I reconstruct, without outcome leakage, the exact opportunity units and observation states needed to support or contradict claim C?

## Target fit

Primary: **Ecological Informatics** — direct fit with ecological data management, data integration, reproducibility and information architecture.

Secondary: **Methods in Ecology and Evolution** — viable if framed as a general prospective audit method rather than as a data-management paper.

Avoid Scientific Data as first choice: the manuscript is not a Data Descriptor for a newly released dataset.


## Fitness-for-purpose / fitness-for-use

This literature is a **direct conceptual neighbor** and must be cited explicitly.

Bishop et al. (2019) studied environmental scientists' data discovery and reuse in terms
of metadata fitness-for-use alongside FAIR.

Bokulich & Parker (2021) give a general philosophical account of data adequacy-for-purpose:
the suitability of data is context-sensitive and depends on the purpose of reuse.

FAIRagro work in 2026 explicitly states that FAIR compliance does not guarantee
fitness-for-purpose and develops application-specific quality reasoning.

Therefore do not claim:

> inferential openness is the first claim-specific view of data reuse.

The narrower novelty is:

> **prospectively governed information-access rules convert otherwise hidden abandoned
> reuse attempts into a finite denominator of terminal inferential states.**

Fitness-for-purpose asks whether data are adequate for an intended use. The present audit
adds an outcome-blind workflow question:

> At which predeclared evidence layer did authorization of claim C become impossible,
> and can that terminal state be retained without post-outcome repair?

## Observation-process calibration

MacKenzie et al. (2002) is the classical ecological anchor for Layer 5: non-detection does
not imply absence when detection probability is below one.

The Level-C contribution is not the discovery of imperfect detection. It is showing that
even after relation, event and function source architectures are independently
identifiable, the workflow can still STOP because the negative biological state required
by the proposed dependency is uncalibrated.
