# When does landscape configuration add to pointwise distribution support?

**An auditable reachability framework across islands and forest fragments**

## Abstract

Species-distribution models commonly estimate local environmental support, while spatial cross-validation improves evaluation across structured landscapes. Neither operation alone represents how candidate locations are configured relative to observed populations through intermediate patches. We developed Environmental Occupancy Geometry (EOG), an auditable structural layer that converts frozen pointwise support and training occurrences into occurrence-anchored reachability and bottleneck features under predeclared graph scenarios. We evaluated incremental information rather than claiming replacement of species-distribution or connectivity models. In an A-Islands benchmark of 886 plant taxa across 842 islands, held-out islands were compared within strata matched for pointwise climatic support and distance to the nearest training occurrence. Structural connected frequency remained informative for 845 taxa (conditional concordance 0.618, species-bootstrap 95% interval 0.609–0.627). We then tested a stronger non-island reference using 60 bird species across 14 Tanzanian forest fragments. For every outer fold, one of 512 matrix-aware current-flow resistance combinations was selected from training labels only. Adding EOG connected frequency to patch area, current flow, their interaction, and nearest-occurrence distance increased held-out log loss by 0.032 (95% interval 0.017–0.049). Spatial-block sensitivity was weaker and uncertain. Structural reachability can therefore add information omitted by pointwise support and direct distance, but it is not a universally beneficial add-on once a strong landscape-specific connectivity model is present. Frozen positive and negative results define the framework’s current scope.

## Highlights

- EOG separates local environmental support from occurrence-anchored configuration.
- Island reachability added information after controlling support and source distance.
- EOG did not improve a strong matrix-aware forest-fragment reference.
- Positive and negative benchmarks define when structural features are informative.
- All graph choices, folds, failures, and result fingerprints are auditable.

## 1. Introduction

Species-distribution analyses turn environmental observations into spatial statements about where a species is supported by measured conditions. In their common pointwise form, those statements are functions of the predictors at a target location. That representation is useful and often exactly what is required, but the word *spatial* can refer to several different inferential problems that should not be conflated. A model can be evaluated spatially, can include spatially correlated latent effects, can incorporate a dispersal process, or can encode resistance and connectivity among habitat patches. These operations answer different questions. Our starting point is narrower: when a pointwise support prediction is already fixed, does the geographic configuration of candidate locations relative to observed training populations retain held-out information that is not contained in local support or simple distance to the nearest known occurrence?

This question is not solved by changing cross-validation alone. Random cross-validation can underestimate prediction error when spatial structure places highly similar observations in training and test sets, motivating spatially separated folds and related evaluation strategies (Valavi et al. 2019). Distance-aware schemes such as nearest-neighbour distance matching further align train–test separation with the spatial geometry of the prediction domain (Milà et al. 2022). These methods are essential for credible evaluation, but they alter which observations are used for training and testing rather than defining a biological route between source and target locations. We therefore treat spatial validation as an evaluation layer, not as a connectivity or dispersal model.

Spatial dependence models address a second problem. Gaussian random fields and related spatial effects can represent residual dependence left after measured covariates are included. Barrier formulations of the Matérn/SPDE framework can prevent inappropriate smoothing across coastlines or other physical discontinuities (Bakka et al. 2019). Such models can substantially improve spatial inference, but correlation or interpolation across a latent field is not identical to asking whether a target is embedded in an occurrence-anchored sequence of intermediate patches. In particular, two targets can have similar local environmental support and comparable spatial correlation with observed data while differing in the configuration of available stepping-stone locations between them.

A third class of methods represents movement or colonisation more explicitly. Dynamic occupancy models can make colonisation depend on neighbouring occupancy, local habitat conditions and long-distance dispersal while accounting for imperfect detection (Broms et al. 2016). Dynamic mechanistic species-distribution models can combine population growth with local and long-distance dispersal through heterogeneous landscapes (Merow et al. 2011). These are process models and are conceptually richer than the structural diagnostic developed here. EOG is not proposed as a substitute for them, and the present benchmarks do not observe temporal colonisation or individual movement. Where data support a mechanistic or dynamic model, such a model may be the more appropriate scientific tool.

Landscape-connectivity methods address yet another component of the problem. Least-cost models define effective distances through resistance surfaces (Adriaensen et al. 2003), while circuit theory integrates multiple pathways across heterogeneous landscapes (McRae et al. 2008). Habitat-network models can combine habitat suitability, resistance-based links and patch-network quantities to predict occurrence (Ortiz-Rodríguez et al. 2019). These precedents mean that neither graph construction, thresholding, shortest or minimax paths, nor the use of resistance surfaces is itself a novel contribution of EOG. Instead, they provide important competitors. A structural feature is informative only relative to what the reference model already contains: an occurrence-anchored graph may add information beyond pointwise support and source distance, yet become redundant or harmful once a strong matrix-specific connectivity model is already included.

We call the framework Environmental Occupancy Geometry because it describes how declared locations occupied by observed records are arranged relative to candidate locations in a specified landscape graph. Here *occupancy* does not denote the latent ecological state estimated by occupancy models, and EOG does not estimate detection probability. The framework takes a frozen pointwise support representation and a set of outer-training occurrences as inputs. It then evaluates structural quantities under a predeclared ensemble of graph scenarios. The principal quantity used in this paper, **connected frequency**, is the fraction of declared graph scenarios in which a target belongs to a component containing at least one outer-training occurrence. This fraction expresses robustness of a structural statement to declared graph assumptions; it is not a colonisation or dispersal probability.

The methodological contribution is therefore an executable separation of estimands and evidence boundaries. Local environmental support, direct occurrence proximity, generic occurrence-anchored configuration, and landscape-specific connectivity are stored and evaluated separately. Graph scenarios, folds, source identities, training-only transformations, non-estimable cases and output fingerprints are declared so that apparently favourable results cannot silently change the reference model or discard failed cases. The framework is designed to permit a negative incremental result. That feature is important because a structural layer that is useful only when compared with a weak reference would not justify a general method claim.

We evaluated this logic in two deliberately different ecological systems. The first uses A-Islands, an Australia-wide vascular-plant occurrence database (Schrader et al. 2025), together with CHELSA climate data (Karger et al. 2017). It asks whether island-chain configuration adds held-out incidence information after pointwise climate support and nearest-training-occurrence distance are controlled. The second uses the Tanzanian forest-fragment data of Brodie and Newmark (2019), for which a matrix-aware current-flow model is a biologically relevant and substantially stronger connectivity reference. It asks whether the same generic EOG connected-frequency feature remains useful after patch area, current flow, their interaction and nearest-occurrence distance are already represented.

We addressed four questions. First, does occurrence-anchored structural reachability distinguish held-out occupied and unoccupied islands after conditioning on pointwise environmental support and direct source distance? Second, is any A-Islands signal confined to environment-constrained edges, or does geography-only patch configuration also retain information? Third, does a generic occurrence-anchored structural feature improve prediction in a non-island system after matrix-specific current flow and source distance are included? Fourth, what empirical claim boundary follows if the two benchmarks give different incremental results? By designing the paper around both a positive benchmark and an adverse strong-competitor benchmark, we evaluate when a structural layer is informative rather than whether EOG can be made to win a universal comparison.

## 2. Methods

### 2.1 Estimands and framework

We separated three quantities that are often blended in spatial distribution analyses. For a candidate location or patch \(x\), **local support** \(S_x\) is the pointwise output of an independently specified environmental or habitat model. **Direct source proximity** \(D_x\) is the geographic distance from \(x\) to the nearest occurrence in the outer-training data. **Structural reachability** \(R_x\) is determined by a declared landscape graph, a set of graph scenarios and the outer-training occurrence anchors. In generic notation,

\[
S_x=f(X_x),
\qquad
D_x=\min_{a\in A_{\mathrm{train}}} d(x,a),
\qquad
R_x=g(G_{1:K},A_{\mathrm{train}},x),
\]

where \(X_x\) is the local predictor vector, \(A_{\mathrm{train}}\) is the training-presence anchor set and \(G_{1:K}\) is a predeclared set of \(K\) graph scenarios. The three quantities were not allowed to substitute for one another. In particular, spatial cross-validation modified the evaluation partition but was not treated as \(R_x\), and a current-flow quantity was treated as a landscape-specific connectivity predictor rather than as generic EOG structure.

For each graph scenario \(k\), we recorded whether target \(x\) belonged to the same connected component as at least one training occurrence. The primary structural summary was

\[
C_x=\frac{1}{K}\sum_{k=1}^{K}
I\{x\leftrightarrow A_{\mathrm{train}}\text{ in }G_k\},
\]

which we call **connected frequency**. All declared scenarios remain in the denominator, including scenarios in which the target is disconnected. Thus \(C_x\) is a robustness frequency over analysis assumptions. No probabilistic calibration to colonisation, dispersal, movement or latent occupancy was applied. EOG also includes minimax/bottleneck diagnostics, but these were treated as separate structural quantities and were not used to redefine connected frequency after outcomes were observed.

### 2.2 Common held-out and audit principles

Both empirical benchmarks followed the same leakage boundary. Outer-test responses were unavailable to graph construction, anchor assignment, predictor scaling, parameter selection and model fitting. Occurrence anchors were always derived from outer-training presences. When structural features were needed for training rows, the focal row could not serve as its own occurrence anchor. Any group lacking a valid training configuration was recorded as non-estimable rather than imputed or silently removed.

All scientifically meaningful choices were represented by machine-readable contracts or frozen inputs before the corresponding outcome was evaluated. These included source identities, cohort rules, fold assignments, environmental variables, graph scenarios, predictor definitions, scoring rules and resampling seeds. Cryptographic hashes were used to detect source or generated-artifact drift. A fingerprint verifies identity and provenance only; it does not supply evidence for ecological causation or preregistration when the fingerprint itself was created after an outcome.

The two benchmarks intentionally used different reference models. A-Islands tested whether generic structural configuration added information beyond pointwise climate support and nearest-source distance. Tanzania tested a stricter incremental question in which a matrix-aware current-flow quantity and its interaction with patch area were already present. We did not compare the numerical magnitude of effect estimates across the two systems because their endpoints differ: A-Islands uses conditional concordance, whereas Tanzania uses paired held-out prediction loss.

### 2.3 A-Islands confirmatory benchmark

#### 2.3.1 Source data and frozen cohort

We used A-Islands version 1.0, a curated database of vascular-plant occurrences on Australian continental islands (Schrader et al. 2025; Zenodo record 10775809). The repository workflow reacquired the archived source and verified its expected source identity before analysis. After deterministic source, taxonomy and geometry audits, the benchmark universe comprised 842 model-linked surveyed islands and a frozen cohort of 886 Australian Plant Census-native taxa. Cohort membership was fixed before the authoritative species-level outcome execution.

For each island we extracted five CHELSA bioclimatic variables at the audited island centroid: annual mean temperature (BIO1), maximum temperature of the warmest month (BIO5), minimum temperature of the coldest month (BIO6), annual precipitation (BIO12) and precipitation seasonality (BIO15). CHELSA provides high-resolution temperature and precipitation climatologies suitable for ecological analyses (Karger et al. 2017). The resulting island-by-climate table was frozen by SHA-256 and reused unchanged across species.

#### 2.3.2 Spatial folds and pointwise support

All species shared a five-fold geographic evaluation partition constructed from frozen 5-degree spatial blocks. Within each outer fold, pointwise climatic support was fitted using only outer-training rows. The support model was a deterministic L2-regularised logistic regression with penalty parameter \(\lambda=1\), no class weighting and training-only standardisation. The same fixed implementation was used for every taxon; no species-specific hyperparameter search was permitted. Held-out island support values therefore depended on the same declared five climatic predictors and the outer-training fit but not on held-out incidence labels.

Nearest-source proximity was computed from each held-out island to the nearest outer-training presence. This quantity was stored separately from the graph features. The primary comparison therefore could not attribute to EOG an advantage that was merely a consequence of being geographically closer to an observed occurrence.

#### 2.3.3 Frozen island graph ensemble

All 842 model-linked islands were retained as structural nodes, including islands without a training occurrence for the focal taxon. We evaluated 12 predeclared graph scenarios formed by crossing four geographic connection radii (25, 50, 125 and 250 km) with three environmental-edge policies: no environmental restriction, a training-derived 90th-percentile environmental threshold and a training-derived 75th-percentile threshold. The four geography-only scenarios and eight environment-constrained scenarios had equal status within their declared summaries. Training presences were the only occurrence anchors.

For each held-out island, connected frequency was the proportion of the 12 scenarios in which the island shared a component with at least one training anchor. Predeclared secondary summaries separately evaluated geography-only connected frequency and environmentally constrained connected frequency. A further secondary analysis used the frozen median normalized geographic bottleneck. Its evaluation direction was fixed before bottleneck outcomes as the negative of the bottleneck quantity, so a smaller required bottleneck counted as more favourable structural support.

#### 2.3.4 Conditional concordance endpoint

The A-Islands estimand was incremental structural information conditional on pointwise support and nearest-source distance, not overall species-distribution accuracy. Within each outer fold, held-out islands were assigned to the frozen 5 × 5 pointwise-support × nearest-anchor-distance strata. Occupied and unoccupied held-out islands contributed a pairwise comparison only when they occurred in the same stratum. For a structural score \(Z\), conditional concordance is the probability, over comparable occupied–unoccupied pairs, that the occupied island has the more favourable \(Z\), with ties receiving their standard half contribution. A value of 0.5 is the null of no conditional ordering information.

Fold-level statistics were averaged without weighting within species, and the primary across-species statistic was the unweighted mean of species statistics. Species, rather than individual island pairs, were the replication unit for uncertainty. We used 10,000 species-cluster bootstrap replicates with seed 20260808 for the 95% percentile interval. A two-sided species sign-flip diagnostic used 100,000 replicates and the same seed. Non-estimability remained explicit. For the primary combined statistic, the frozen applicability table distinguishes evaluable folds, folds with no comparable occupied–unoccupied pairs within the conditioning strata, and folds with insufficient training classes. The bottleneck analysis additionally distinguishes cases with no *finite* comparable bottleneck pairs.

### 2.4 Tanzania forest-fragment strong-competitor benchmark

#### 2.4.1 Source package and pre-outcome repairs

The non-island benchmark used the archived source package for Brodie and Newmark’s analysis of bird occurrence in fragmented East and West Usambara forest landscapes in Tanzania (Brodie & Newmark 2019; Dryad DOI 10.5061/dryad.p042h0c). The workflow reacquired Dryad version 23134 and verified all nine archived files by declared size and digest before analysis. The package contained 14 surveyed forest fragments, nine in East Usambara and five in West Usambara, a complete occurrence table containing 89 species, 42 structural forest-patch nodes per region, regional land-cover rasters and the original analysis scripts. A pre-outcome requirement of at least two presences and two absences across the 14 fragments yielded 60 eligible species.

Source auditing identified three ambiguities that were resolved before any current-flow versus EOG outcome was calculated. First, the released R workflow rasterized focal nodes using implicit row indices while a downstream step addressed resistance-matrix columns by `patch_number`; because both node tables were permuted relative to patch number, the benchmark explicitly rasterized the declared patch identifiers. Second, the released cumulative-isolation weight \(1/\log_{10}(\mathrm{area}_{ha})\) becomes non-positive for sub-hectare source patches and is singular at one hectare. We therefore froze \(1/\log_{10}(1+\mathrm{area}_{ha})\) as the primary positive monotone source weight and \(1/\mathrm{area}_{ha}\) as a sensitivity rule. Third, the released script referred to `raster_east3_new.tif`, whereas the digest-verified archive contains `raster_east3.tif`; the benchmark used the verified archived raster. These choices were documented as source repairs rather than post-outcome model tuning.

#### 2.4.2 Matrix-aware current-flow candidate library

We reproduced a matrix-specific current-flow competitor rather than comparing EOG only with pointwise support. Forest resistance was fixed at 1. Eucalyptus, tea and other agriculture each took values in \(\{1,2,4,8,16,32,64,128\}\), producing \(8^3=512\) resistance combinations separately for East and West Usambara under their verified land-cover mappings. Candidate generation did not use species responses.

Pairwise effective resistance was computed on an eight-neighbour raster graph. Cell values were interpreted as resistance; conductance for an edge was derived from the mean of adjacent cell conductances, with diagonal conductance divided by \(\sqrt{2}\). To make the 512-candidate library reproducible in CI while retaining focal identity, categorical rasters were aggregated by a factor of eight using deterministic block mode and explicit preservation of the fine-resolution class at every focal patch. This factor was selected using geometry alone: factor 16 collapsed East Usambara from 42 to 40 distinct focal cells, whereas factor 8 preserved all 42 focal identities in both regions.

For each species and outer fold, one current-flow candidate was selected using outer-training responses only. Candidate ranking reproduced the released source-model form, `occur ~ log10(area_ha) * log10(current_flow_isolation)`, and selected the converged finite-AIC fit with minimum training AIC. Numerical ties at the frozen comparison precision were resolved by the lower predeclared candidate index. If every candidate was invalid for an outer fold, the group remained explicitly non-estimable. The selected candidate was then reused unchanged in both the reference and EOG probability tiers; EOG could not receive a different or more favourable current-flow surface.

#### 2.4.3 Geography-only EOG graph and direct source distance

East and West Usambara were kept as separate EOG graphs, each containing all 42 verified structural forest-patch nodes. Before species outcomes were calculated, an initial radius proposal based on broad MST-edge quantiles was rejected because all surveyed fragments in each region were already connected at the smallest proposed threshold. That proposal would have reduced connected frequency to a same-region-anchor indicator. It was replaced, using geometry only, by a four-scenario survey-component ladder: the smallest distinct MST thresholds at which surveyed nodes occupied exactly four, three, two and one components.

The frozen East Usambara radii were 0.511808, 0.913522, 2.654323 and 2.678215 km; the West Usambara radii were 0.417907, 0.854101, 1.585589 and 3.038021 km. Every scenario had to induce a distinct surveyed-node partition. The Tanzania EOG feature used in the strict comparison was the fraction of these four geography-only scenarios in which a target patch was connected to at least one outer-training presence in its region.

Nearest-source distance was kept as a separate predictor. It was the great-circle distance to the nearest remaining outer-training presence across both regions, transformed as \(\log_{10}(1+\mathrm{km})\). For a held-out row, all outer-training presences were eligible anchors. For a training row, the row itself was removed from its anchor set before both nearest-distance and EOG features were constructed. If anchors existed only in the other region, nearest distance could remain finite while same-region EOG connected frequency was zero; thus the two predictors could not collapse deterministically to one another.

#### 2.4.4 Held-out probability tiers and validation partitions

The primary evaluation was 14-fold leave-one-fragment-out (LOSO), so every surveyed fragment served once as the held-out unit. A sensitivity analysis used geometry-only within-region MST blocks, with three blocks in East Usambara and two in West Usambara. Fold construction preceded species-level outcome inspection; single-class training sets and other non-estimable cases were retained in the audit.

After training-only current-flow selection and structural-feature construction, both probability tiers used the same deterministic L2 logistic engine with \(\lambda=1\) and training-only standardisation. Training-constant columns were dropped and recorded. The strict reference model contained

`patch area + selected current flow + patch area × selected current flow + nearest training occurrence`,

and the candidate model contained

`reference + EOG connected frequency`.

Consequently the tested contrast asks whether generic occurrence-anchored configuration adds predictive information beyond a strong matrix-aware connectivity model and simple source proximity. It does not compare EOG with a weak pointwise-only baseline.

#### 2.4.5 Tanzania endpoint and uncertainty

The primary Tanzania endpoint was paired held-out Bernoulli log loss on the exact intersection of valid candidate and reference predictions. We defined the contrast as candidate minus reference, so negative values favour EOG and positive values are adverse. Brier-score difference was a predeclared secondary endpoint. AUC was not used as the primary statistic because many species-fold test sets are too small or single-class for stable discrimination summaries.

Loss differences were first averaged within each species. The inferential point estimate was then the equal-weight mean of the 60 species means; an observation-weighted micro mean was descriptive only. The 95% interval used 10,000 species-cluster percentile bootstrap replicates with seed 20260810. A secondary two-sided species sign-flip diagnostic used 100,000 replicates with the same seed and a finite-Monte-Carlo +1 correction. This hierarchy prevents species with more executable folds from receiving greater inferential weight. Non-estimable predictions remained in the declared-row accounting, including single-class model failures and training-only current-flow-selection failures.

### 2.5 Reproducibility, timing and claim boundary

The repository separates scientific-design decisions from numerical reproducibility policies. Each benchmark stores source identities, cohort and fold fingerprints, graph declarations, training-only rules, applicability records and result projections. Figure and table builders consume frozen machine-readable artifacts and fail if expected fingerprints, sample counts, effect directions or declared failure counts drift. The manuscript result tables are themselves rebuilt in CI and compared byte-for-byte with their committed versions.

Protocol changes were retained rather than erased from the audit history. For A-Islands, mutually conflicting early analysis contracts were explicitly revoked before the first authoritative species-level outcome, leaving one authoritative contract. For Tanzania, the degenerate graph-radius proposal was replaced using geometry only before predictive outcomes, and source-code repairs were frozen before current-flow selection or scoring. A later adjustment to cross-run numerical fingerprint quantisation addressed solver-level variation in current-flow arrays; it did not alter raw float64 inputs, model predictions or the frozen biological result. Post-outcome fingerprints are therefore described as archival reproducibility records, not as evidence that a choice was preregistered.

The resulting claim boundary is deliberately restricted. A positive A-Islands concordance supports added held-out incidence information conditional on pointwise climate support and nearest-source distance. A negative Tanzania loss difference supports no incremental predictive benefit for the tested generic EOG feature beyond the specified current-flow-plus-distance reference. Neither benchmark observes individual movement, colonisation events, detection probability, gene flow or demographic connectivity. Accordingly, connected frequency and bottleneck diagnostics are structural quantities, not estimates of realised dispersal or colonisation probability.

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

## 10. References

Adriaensen, F., Chardon, J.P., De Blust, G., Swinnen, E., Villalba, S., Gulinck, H. & Matthysen, E. (2003). The application of ‘least-cost’ modelling as a functional landscape model. *Landscape and Urban Planning* 64: 233–247. https://doi.org/10.1016/S0169-2046(02)00242-6

Bakka, H., Vanhatalo, J., Illian, J.B., Simpson, D. & Rue, H. (2019). Non-stationary Gaussian models with physical barriers. *Spatial Statistics* 29: 268–288. https://doi.org/10.1016/j.spasta.2019.01.002

Brodie, J.F. & Newmark, W.D. (2019). Heterogeneous matrix habitat drives species occurrences in complex, fragmented landscapes. *The American Naturalist* 193: 748–754. https://doi.org/10.1086/702589

Broms, K.M., Hooten, M.B., Johnson, D.S., Altwegg, R. & Conquest, L.L. (2016). Dynamic occupancy models for explicit colonization processes. *Ecology* 97: 194–204. https://doi.org/10.1890/15-0416.1

Karger, D.N. et al. (2017). Climatologies at high resolution for the earth’s land surface areas. *Scientific Data* 4: 170122. https://doi.org/10.1038/sdata.2017.122

McRae, B.H., Dickson, B.G., Keitt, T.H. & Shah, V.B. (2008). Using circuit theory to model connectivity in ecology, evolution, and conservation. *Ecology* 89: 2712–2724. https://doi.org/10.1890/07-1861.1

Merow, C., LaFleur, N., Silander, J.A. Jr., Wilson, A.M. & Rubega, M. (2011). Developing dynamic mechanistic species distribution models: Predicting bird-mediated spread of invasive plants across northeastern North America. *The American Naturalist* 178: 30–43. https://doi.org/10.1086/660295

Milà, C., Mateu, J., Pebesma, E. & Meyer, H. (2022). Nearest neighbour distance matching Leave-One-Out Cross-Validation for map validation. *Methods in Ecology and Evolution* 13: 1304–1316. https://doi.org/10.1111/2041-210X.13851

Ortiz-Rodríguez, D.O., Guisan, A., Holderegger, R. & van Strien, M.J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution* 9: 10457–10471. https://doi.org/10.1002/ece3.5567

Schrader, J. et al. (2025). A-Islands: A Vascular Plant Dataset for Biodiversity Research and Species Monitoring on Australian Continental Islands. *Journal of Vegetation Science* 36: e70019. https://doi.org/10.1111/jvs.70019

Valavi, R., Elith, J., Lahoz-Monfort, J.J. & Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods in Ecology and Evolution* 10: 225–232. https://doi.org/10.1111/2041-210X.13107
