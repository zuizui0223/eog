# Structural-reachability novelty audit and submission strategy

Audit date: **2026-08-12**

Status: **scientifically submission-worthy after a required novelty-framing revision; no new outcome analysis is required before first submission.**

This audit distinguishes (1) whether the frozen empirical results are sufficiently strong to support a paper, (2) whether the manuscript fills a defensible gap in the existing literature, and (3) how the paper should be submitted without claiming novelty for components that already exist.

## 1. Submission verdict

### Scientific result gate: PASS

The paper already contains two complementary held-out empirical outcomes.

**A-Islands positive benchmark**

- 842 model-linked surveyed islands;
- 886 frozen APC-native plant taxa;
- 845 taxa with an estimable primary species statistic;
- mean conditional connected-frequency concordance = **0.6177466**;
- species-bootstrap 95% interval = **0.6086806–0.6269445**;
- 672/845 estimable taxa above the 0.5 null, 42 equal, 131 below;
- positive information is evaluated only within frozen pointwise-support × nearest-training-source-distance strata;
- geography-only and environmentally constrained connected-frequency decompositions retain the same direction;
- all non-estimable species-folds remain visible.

The effect is not merely a small p-value: relative to the 0.5 null, the average ordering gain is about **0.118**, and the direction is broad across species rather than concentrated in a few taxa. The supported interpretation is nevertheless conditional ordering information, not a colonisation probability or effect of realised dispersal.

**Tanzania strong-reference boundary benchmark**

- 60 predeclared eligible bird species across 14 surveyed fragments;
- species- and fold-specific current-flow resistance selected from 512 candidates using outer-training responses only;
- strict reference = patch area + selected matrix-aware current flow + interaction + nearest-training-occurrence distance;
- candidate = the same reference + EOG connected frequency;
- 826 matched LOSO held-out predictions;
- species-macro candidate-minus-reference log-loss difference = **+0.0321131**;
- 95% interval = **+0.0174580 to +0.0486750**;
- 17 species favourable to EOG and 43 adverse;
- inverse-area LOSO sensitivity retains the adverse direction;
- spatial-block sensitivity is smaller and uncertain rather than treated as confirmation.

This negative benchmark is scientifically useful because it rejects a universal-superiority story and identifies the dependence of an incremental structural claim on the reference-model content.

### Reproducibility gate: PASS for manuscript-facing evidence

The repository has a complete manuscript, frozen result tables, Figure 1–5 builders, machine-readable sidecars, explicit non-estimability accounting, source/result fingerprints, an offline submission-package builder, and CI tests that rebuild manuscript-facing scientific assets from frozen repository inputs. Stale generated-artifact drift discovered during manuscript preparation was corrected and converted into a regression test rather than hidden.

### Human/release gate: NOT YET COMPLETE

Submission is still blocked by author/declaration approval, live journal-policy confirmation, final visual inspection at journal size, and the DOI/tag/archive sequence tracked in Issue #131. These are submission-production gates, not missing scientific results.

## 2. Closest prior literature: what is already established

The literature audit shows that the broad idea “environmental suitability is not enough; add connectivity or accessibility” is **not new** and must not be presented as the paper's novelty.

### Accessible-area / BAM reasoning

Barve et al. (2011), *Ecological Modelling*, DOI `10.1016/j.ecolmodel.2011.02.011`, formalized the importance of the movement-accessible region M for niche/distribution modelling. EOG therefore does not introduce the idea that accessibility constrains realised distributions.

### Occupancy plus occupied-neighbour / network information

Berlow et al. (2013), *PLoS ONE*, DOI `10.1371/journal.pone.0072200`, extended static occupancy prediction by blending environmental patch quality and network structure. The paper explicitly notes existing predictors such as distance to the nearest occupied patch and density of occupied patches. EOG therefore does not introduce source-conditioned spatial predictors or environmental-quality-plus-network occupancy models.

### Habitat suitability plus topology/connectivity

Ortiz-Rodríguez et al. (2019), *Ecology and Evolution*, DOI `10.1002/ece3.5567`, predicted occurrence-state from local habitat suitability, weighted connectivity and habitat-network topology. EOG therefore does not introduce habitat-network occurrence prediction.

### Sensitivity to graph/dispersal assumptions

Ortiz-Rodríguez et al. (2023), *PLoS ONE*, DOI `10.1371/journal.pone.0293966`, repeated habitat-network occurrence models across alternative maximum-dispersal thresholds and showed that topology and predictive performance were sensitive to that choice. EOG therefore does not introduce threshold sensitivity analysis.

### Formal integration of environmental, geographic and topological space

Van Moorter et al. (2023), *Ecology*, DOI `10.1002/ecy.4105`, proposed the functional-habitat framework integrating environmental-space suitability, geographic-space accessibility and topological-space connectivity using network/metapopulation theory. EOG therefore must not claim to be the first formal integration of local suitability and landscape connectivity.

### Patch effects within SDMs

Riva et al. (2024), *Journal of Ecology*, DOI `10.1111/1365-2745.14403`, reviewed how patch area, configuration and diversity can be incorporated into SDMs and argued that such effects have been used sporadically but deserve systematic testing. EOG should be placed as one explicit incremental-validation strategy within this broader agenda, not as a discovery that patches matter.

### Connectivity plus metapopulation/SDM modelling

Kim et al. (2024), *Ecological Informatics*, DOI `10.1016/j.ecoinf.2024.102464`, combined landscape connectivity with incidence-function and species-distribution modelling. This is particularly important because it appeared in the planned target journal.

Felin et al. (2025), *Science of the Total Environment*, DOI `10.1016/j.scitotenv.2024.178204`, added barrier- and mobility-informed river-connectivity indices to SDMs for 33 fish species while accounting for habitat suitability. EOG therefore cannot claim that connectivity covariates have not been tested conditionally on habitat-related predictors.

### Connectivity-model uncertainty and ensembles

Prima et al. (2024), *Methods in Ecology and Evolution*, DOI `10.1111/2041-210X.14444`, integrated uncertainty in modelling choices in a multi-species connectivity framework. Cushman et al. (2026), *Ecological Informatics*, DOI `10.1016/j.ecoinf.2026.103740`, compared 171 connectivity-model combinations and showed strong dependence on method, source points and dispersal thresholds. EOG therefore does not introduce the general principle that connectivity estimates require sensitivity/uncertainty analysis or ensembles.

## 3. The gap that remains defensible

After accounting for those precedents, the defensible gap is **not a new graph primitive and not the first suitability-connectivity integration**.

The gap addressed by the present paper is the lack of a clearly separated, leakage-safe and reference-conditioned empirical test of the following question:

> **Given an independently frozen local-support representation, does occurrence-conditioned landscape configuration retain held-out incidence information after direct source proximity is controlled, and does any such structural increment persist when a strong landscape-specific connectivity model is already present?**

The searched literature contains many integrations of habitat quality, accessibility, occupied-neighbour information, graph topology, resistance/current flow, dispersal thresholds and uncertainty. In the literature reviewed for this audit, we did not identify a directly equivalent design combining all of the following as the object of inference; this is an audit conclusion, not a claim of exhaustive priority:

1. **estimand separation** — local support, direct source proximity, generic graph configuration and landscape-specific connectivity are represented as non-interchangeable quantities;
2. **outer-training-only occurrence conditioning** — held-out occurrence labels cannot define structural anchors, tune graph choices or leak into structural predictors;
3. **predeclared scenario aggregation without winner selection** — the structural summary asks how robust a target-to-training-anchor connection is across a frozen graph ensemble rather than selecting the graph that best fits the held-out outcome;
4. **matched incremental evaluation** — the structural addition is evaluated on the same valid held-out rows against an explicitly declared reference;
5. **strong-reference falsification opportunity** — where a matrix-aware connectivity model is available, EOG is required to compete after that information is already in the reference rather than only against a weak local-only model;
6. **explicit applicability/failure accounting** — non-estimable taxa, folds, pair strata and parameter-selection failures are retained;
7. **positive and adverse evidence in one scope claim** — a large multi-species positive benchmark and an adverse strong-reference benchmark are preserved together to define where the generic structural term earns and fails to earn an incremental claim;
8. **source-to-manuscript auditability** — scientific-design timing, result fingerprints and generated manuscript assets are linked so that post-outcome corrections can be distinguished from scientific retuning.

Items 1–8 are strongest as a **combined validation/informatics contribution**. Several pieces have precedents individually; the paper should not claim otherwise.

## 4. The main contribution sentence to use

Preferred formulation:

> **EOG is an auditable framework for testing whether occurrence-conditioned landscape configuration earns an incremental held-out claim beyond a frozen local-support model, direct source proximity, and—where available—a stronger landscape-specific connectivity reference.**

Secondary formulation:

> **The contribution is not a new connectivity algorithm; it is a leakage-safe, reference-conditioned validation design that makes the incremental value and failure boundary of structural landscape information explicit.**

Do not use:

- “EOG integrates environmental and geographic space for the first time.”
- “SDMs ignore dispersal/connectivity.”
- “Existing occurrence models use only local habitat.”
- “Occurrence anchoring is novel.”
- “Scenario robustness or sensitivity analysis is novel.”
- “EOG outperforms SDM.”
- “Connected frequency estimates dispersal or colonisation probability.”

## 5. Is the empirical evidence enough for a first submission?

**Yes. Do not reopen the frozen outcome analyses merely to manufacture a stronger positive story.**

Reasons:

1. A-Islands supplies unusually broad taxonomic replication (845 estimable species) and the signal remains positive after the two simplest competing explanations in that design—local climatic support and nearest-source distance—are controlled.
2. The species-direction distribution (672 above versus 131 below the null, with 42 ties) demonstrates breadth beyond a single aggregate estimate.
3. The Tanzania benchmark is deliberately harder and tests the generic term after species-adaptive matrix-aware current flow. Its adverse result establishes a real boundary rather than a second cherry-picked positive case.
4. The spatial-block Tanzania sensitivity becoming uncertain is reported rather than suppressed, which accurately exposes the limits of a 14-fragment design.
5. The scientific direction is frozen and independently reproducible at the manuscript-facing level.

A new analysis before first submission would be justified only if the literature audit reveals a **fatal missing comparator that can be specified independently of the observed outcomes**. The present audit identifies important missing citations and framing, but not a comparator whose absence invalidates the existing estimands. A-Islands must simply be described as evidence beyond local support + nearest source, not beyond every connectivity model.

## 6. Reviewer risks and planned answers

### Risk 1 — “This is functional habitat / habitat-network modelling under a new name.”

**Severity: high if the current literature framing is left unchanged; manageable after revision.**

Response strategy: cite Berlow 2013, Ortiz-Rodríguez 2019/2023, Van Moorter 2023, Riva 2024 and Kim 2024 prominently in the Introduction. State explicitly that EOG is not presented as the first integration. Focus the contribution on held-out incremental validation, training-only anchors, strong-reference testing and the positive/adverse evidence boundary.

### Risk 2 — “A-Islands does not beat a matrix-aware connectivity model.”

**Severity: expected, not fatal.**

Response strategy: agree. The A-Islands estimand is conditional on pointwise CHELSA support and nearest source only. Do not generalize its positive result to current flow. Tanzania supplies the strong-reference test and is adverse.

### Risk 3 — “Connected frequency averages arbitrary graph assumptions.”

**Severity: moderate.**

Response strategy: call it an assumption-robust structural diagnostic, not biological probability. Cite threshold/uncertainty literature and explain that scenarios were frozen before outcome evaluation. The paper tests the ensemble-defined quantity; it does not infer the true movement threshold.

### Risk 4 — “Tanzania is too small and its validation design changes the result.”

**Severity: moderate and already visible.**

Response strategy: treat primary LOSO as the frozen primary design and spatial blocks as a sensitivity boundary. Explicitly report the jump in non-estimability and avoid claiming general harm or current-flow superiority.

### Risk 5 — “The two benchmarks use different endpoints.”

**Severity: moderate.**

Response strategy: never compare effect magnitudes. The synthesis is logical—whether an incremental structural claim is earned relative to each dataset's frozen reference—not a meta-analysis of one common effect.

### Risk 6 — “The method is a workflow composed of existing tools.”

**Severity: decisive for some methods journals.**

Response strategy: do not target a journal whose novelty rule requires a genuinely new algorithm unless the method is expanded prospectively. For the current paper, emphasize computational validation, evidence contracts and empirical applicability boundaries.

## 7. Journal strategy

### First target — *Ecological Informatics*: GO

Recommended article type: **Original Research Paper**.

Why this is the best first target:

- the journal explicitly covers computational ecology/ecological data science, ecological data modelling, uncertainty analysis and species-distribution modelling;
- the manuscript contains a tested computational framework, two real-data benchmarks, explicit uncertainty/applicability accounting and reproducibility infrastructure;
- recent *Ecological Informatics* papers already engage directly with landscape connectivity + species occurrence/modelling, including Kim et al. 2024 and Cushman et al. 2026, so the topic is clearly in scope;
- the paper's distinguishing value for this journal is the reference-conditioned validation and audit architecture, not a claim to have invented connectivity modelling.

**Submission pitch:**

> Existing ecological models already combine habitat suitability, patch structure and connectivity. We ask a different validation question: when does occurrence-conditioned graph configuration add held-out information after local support, source distance and, where available, a strong matrix-aware connectivity model are already represented? Across 845 estimable island-plant taxa the structural term retained information, whereas in a 60-species forest-bird benchmark it worsened primary prediction beyond current flow. The paired positive/adverse result defines an auditable applicability boundary rather than a universal-superiority claim.

### *Methods in Ecology and Evolution*: NO-GO for the current version

Current author guidance states that Research Articles should describe new methods and that descriptions of workflows linking existing methods generally are not considered new methods; computational methods normally should include simulation/benchmark testing. The journal now has a Workflow article type, but it expects broadly useful pipelines with substantial and quantifiable methodological improvement, uncertainty/error-propagation analysis and extensive sensitivity/benchmark evaluation.

The current EOG paper is stronger as an empirical computational-informatics validation framework than as a claim of a new method primitive. Submitting the current manuscript to MEE would create unnecessary desk-reject risk. MEE becomes reasonable only after a prospective second paper adds a genuinely general methodological development, simulations with known truth, formal ablation/error propagation, and benchmark evidence that cannot be reduced to assembling established connectivity tools.

### Backup — *Ecological Modelling*: CONDITIONAL

Use as a backup if *Ecological Informatics* rejects on fit/novelty rather than a scientific flaw. *Ecological Modelling* explicitly welcomes new mathematical models and systems analysis as well as innovative applications of existing models, but its process/mechanistic emphasis makes it less natural than *Ecological Informatics* for the current static structural validation paper.

A landscape-ecology journal can be considered if reviews indicate that the informatics contribution is less compelling than the landscape-configuration result, but that route will likely increase demands for biological movement interpretation and additional landscape-specific comparators.

## 8. Submission sequence

1. **Before DOI reservation:** revise the Introduction/Discussion and reference ledger to include the closest prior work identified above and narrow the novelty statement.
2. Run the full manuscript/figure/table CI. No frozen result may change.
3. Complete author/declaration approvals in `author_metadata.template.json` or its approved replacement.
4. Complete the live *Ecological Informatics* Guide-for-Authors check and final visual QA.
5. Reserve the Zenodo DOI, insert `<ARCHIVE_DOI>` and `v0.1.0` in an identifier-only release PR, then follow Issue #131 exactly.
6. Submit to *Ecological Informatics* as an Original Research Paper.
7. In the cover letter, lead with the **question and empirical boundary**, not with the EOG acronym: structural configuration adds information in one high-replication system and fails after a strong connectivity reference in another.
8. If editorial rejection says “integration already exists,” do not add favourable analyses. Reply internally by checking whether the paper adequately foregrounded the reference-conditioned held-out validation gap. Retarget to *Ecological Modelling* or a landscape-ecology outlet depending on the editor's reason.

## 9. Stop/go rule after this audit

**GO to submission preparation; HOLD actual submission until the closest-prior framing revision is merged and the existing human/release gates are complete.**

Do not reopen A-Islands/Tanzania outcome analyses to improve the story. The strongest publishable story is precisely that the same generic structural idea has a broad positive increment under a relatively weak structural reference and an adverse increment under a strong matrix-aware reference.