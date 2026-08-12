# When does landscape configuration add held-out information?

**An auditable reference-conditioned framework across islands and forest fragments**

## Abstract

Ecological models increasingly combine local environmental support, source proximity, patch context and landscape connectivity, but the incremental value assigned to a structural predictor depends on what the declared reference already contains. We developed Environmental Occupancy Geometry (EOG) as an auditable framework for testing that reference-conditioned increment with outer-training-only occurrence anchors and predeclared graph assumptions. In an initial A-Islands benchmark of 886 plant taxa across 842 islands, connected frequency retained held-out incidence ordering after matching on climatic support and nearest-source distance (845 estimable taxa; mean conditional concordance 0.618, 95% species-bootstrap interval 0.609–0.627). We then prospectively froze a stronger island reference containing climate, island area, mainland distance, direct and area-weighted source pressure, surrounding landmass, generic stepping-stone accessibility and network position. Adding species-conditioned EOG to this reference increased held-out log loss by 0.00349 (95% interval 0.00247–0.00451; 341 species favourable, 545 adverse). In 60 Tanzanian forest birds, adding EOG after patch area, training-selected matrix-aware current flow and nearest source also increased primary log loss by 0.032 (0.017–0.049), while spatial-block sensitivity was uncertain. Structural ordering under limited conditioning therefore does not imply predictive gain beyond a richer reference. EOG is best treated as a falsifiable structural-adequacy diagnostic, not a universal connectivity correction or a dispersal probability.

**Keywords:** species distribution model; landscape connectivity; spatial cross-validation; island biogeography; habitat fragmentation; current flow; reproducible ecology

## 1. Introduction

Species-distribution analyses turn environmental observations into spatial statements about where measured conditions support a species. In their common pointwise form, those statements are functions of predictors at a target location. That representation can be useful and sufficient, but the word *spatial* covers several distinct inferential problems. A model can be evaluated with spatially separated data, can contain a spatial random field, can represent movement or colonisation explicitly, or can encode resistance and connectivity among habitat patches. These operations answer different questions. Our concern is narrower: **after a declared reference model has already represented some combination of local support and landscape context, does an occurrence-conditioned structural feature retain additional held-out information?**

This question is not solved by spatial cross-validation alone. Random cross-validation can underestimate prediction error when nearby observations are split across training and test sets, motivating blockCV and related spatially separated designs (Valavi et al. 2019). Nearest-neighbour distance matching further targets the geometry of train–test separation (Milà et al. 2022). These methods improve evaluation but do not themselves define a dispersal process or a landscape-connectivity estimand. We therefore treat spatial validation as an evaluation layer rather than as evidence that source-to-target structure has been represented.

Likewise, spatial dependence models address a different problem. Gaussian random fields and related spatial effects can absorb residual autocorrelation, and barrier SPDE formulations can reduce inappropriate smoothing across coastlines or other discontinuities (Bakka et al. 2019). Dynamic occupancy models can make colonisation depend on neighbouring occupancy and habitat while accounting for imperfect detection (Broms et al. 2016), and dynamic mechanistic species-distribution models can represent population growth and local or long-distance dispersal explicitly (Merow et al. 2011). EOG is not proposed as a substitute for these process models. The present benchmarks contain cross-sectional incidence rather than observed colonisation events, so their graph summaries cannot be interpreted as realised movement.

Landscape-connectivity methods already provide a rich vocabulary for the structural part of the problem. Least-cost models quantify effective distance through resistance surfaces (Adriaensen et al. 2003), circuit theory integrates multiple possible pathways (McRae et al. 2008), and habitat-network models combine local suitability, weighted connectivity and network topology to predict occurrence (Ortiz-Rodríguez et al. 2019). Nearest occupied patches and occupied-neighbour density have long been used as predictors in patch-occupancy analyses (Prugh 2009; Berlow et al. 2013), and source-patch quality or size can be incorporated into connectivity measures (Schooley & Branch 2011). Suitability-derived resistance and circuit connectivity are also established (Nelli et al. 2022). More recent work has formalised environmental, geographic and topological spaces within a common habitat-functionality framework (Van Moorter et al. 2023), reviewed incorporation of patch effects into species-distribution models (Riva et al. 2024), combined connectivity with incidence-function and species-distribution modelling (Kim et al. 2024), and quantified uncertainty caused by connectivity-model, source and threshold choices (Prima et al. 2024; Cushman et al. 2026). These precedents mean that EOG cannot claim novelty simply for adding connectivity, using occurrence anchors, or averaging across graph scenarios.

Island biogeography makes this boundary especially important. Isolation has never been only one geometric distance. Stepping-stone effects have long been recognised (Long et al. 2009), surrounding land area can outperform simple mainland distance as an isolation representation (Weigelt & Kreft 2013), and graph-theoretic island connectivity has been analysed directly (Sillero et al. 2018). Carter et al. (2020) compared 16 measures across New Zealand offshore islands and identified major axes corresponding to mainland distance, stepping stones and insular network position. Graph-derived connectivity has also been validated against independent ecological and genetic data (Daniel et al. 2023). Thus the scientific opportunity is not to rediscover multidimensional island isolation, but to ask whether **species-conditioned source-network configuration contributes held-out information after those generic isolation dimensions and simpler source terms are already represented**.

We call the framework Environmental Occupancy Geometry because it describes how locations occupied by observed training records are arranged relative to candidate locations in a declared graph. Here *occupancy* refers only to observed occurrence support in the declared analysis; it is not the latent state of an occupancy model. The principal feature used here, **connected frequency**, is the fraction of predeclared graph scenarios in which a target belongs to a component containing at least one outer-training occurrence. It is a robustness summary over declared structural assumptions, **not a colonisation or dispersal probability**.

The central methodological claim is therefore about **reference-conditioned structural adequacy**. Local support, direct source proximity, generic island or patch context, species-conditioned graph configuration and landscape-specific connectivity are kept as separate quantities. Held-out labels cannot define structural anchors. Graph scenarios and reference tiers are declared before the outcome to which they apply. The structural addition is scored on the same held-out rows as its reference. Non-estimable cases are retained. A negative result is permitted and preserved. This architecture makes the question falsifiable: a structural feature may be informative under a limited reference but redundant or harmful under a richer one.

We evaluated that logic in two ecological systems and, crucially, at two reference depths within A-Islands. The original A-Islands analysis asked whether connected frequency retained **conditional ordering information** after matching held-out islands on pointwise climate support and nearest outer-training source distance. After a closest-prior audit, but before inspecting the new outcome, we froze a second A-Islands analysis with a stronger reference containing recipient area, mainland distance, multi-source pressure, source-island area, surrounding landmass, generic stepping-stone accessibility and generic network position. This prospective extension asked a different question: whether species-conditioned EOG improved **held-out predictive loss** beyond that reference. Tanzania supplied an external strong-reference test in which matrix-aware current flow was selected from outer-training responses only.

We therefore addressed five questions. First, does occurrence-anchored graph configuration retain held-out incidence ordering beyond pointwise climate support and nearest-source distance? Second, is that original signal robust across geography-only and environmentally constrained graph summaries? Third, after a substantially richer island-isolation reference is frozen prospectively, does species-conditioned EOG still improve held-out prediction? Fourth, does EOG improve a matrix-aware strong reference in a non-island fragmented landscape? Fifth, what claim boundary follows when the answer depends on both the reference and the endpoint? The goal is not to make EOG win every comparison, but to determine when a structural claim is actually earned.

## 2. Methods

### 2.1 Estimands and framework

For a candidate location or patch \(x\), we distinguished local support, source proximity and graph structure. Let \(S_x\) denote the pointwise output of an independently specified environmental model, \(D_x\) the geographic distance to the nearest occurrence in the outer-training data, and \(G_{1:K}\) a predeclared family of landscape graphs. For outer-training occurrence anchors \(A_{\mathrm{train}}\), connected frequency was

\[
C_x=\frac{1}{K}\sum_{k=1}^{K} I\{x\leftrightarrow A_{\mathrm{train}}\text{ in }G_k\}.
\]

All declared scenarios remain in the denominator. No calibration converts \(C_x\) to a probability of occupancy, migration, dispersal or colonisation. Other EOG quantities such as bottleneck summaries are separate estimands and cannot be substituted for connected frequency after inspecting an outcome.

The key inferential object is not \(C_x\) in isolation but its contribution **conditional on a declared reference**. We use two endpoint types. The original A-Islands benchmark uses conditional concordance within strata defined by reference quantities. The strong-reference A-Islands and Tanzania benchmarks use paired held-out predictive-loss differences between a reference \(R\) and a candidate \(R+C\). These endpoint types answer related but non-identical questions and are never treated as one common effect-size scale.

### 2.2 Common leakage, fitting and audit principles

Outer-test responses were unavailable to graph construction, occurrence anchoring, predictor scaling, parameter selection and model fitting. Response-derived source features were reconstructed inside each outer-training set. For training rows used to fit a probability tier, a training presence could not use itself as an occurrence source. Held-out rows were unlabelled during feature construction. This cross-fitting rule prevents a target response from helping to construct the predictor later evaluated against that response.

All probability tiers used the same deterministic L2-penalised logistic implementation where such a model was required. Predictor standardisation used outer-training rows only, the intercept was unpenalised, \(\lambda=1\), class weighting was absent, and no hyperparameter tuning used held-out outcomes. The A-Islands strong-reference extension required at least five outer-training presences and five absences. Columns constant within the outer-training tier were dropped and recorded, with the retained indices applied unchanged to held-out rows.

Scientific choices were represented by machine-readable contracts or frozen input fingerprints before the corresponding outcome was evaluated. The repository records source identities, cohort definitions, spatial folds, graph assumptions, feature formulas, resampling seeds, non-estimability states and result fingerprints. Cryptographic hashes establish data or result identity, not biological truth. When a new comparison was developed after an earlier result existed, its timing was recorded explicitly rather than relabelling it as part of the earlier confirmatory design.

### 2.3 A-Islands source, cohort and original conditional-ordering benchmark

#### 2.3.1 Data and frozen cohort

We used A-Islands version 1.0, a curated database of vascular-plant occurrences on Australian continental islands (Schrader et al. 2025). The source was reacquired from the immutable archive and verified before analysis. The model-linked surveyed universe contained 842 islands. A taxonomy/status audit produced a frozen cohort of 886 Australian Plant Census-native taxa. The cohort file contains a broader candidate audit, but exactly 886 rows were marked `primary_cohort_included=1`; that flag, rather than post-outcome filtering, defines the cohort.

Species records are linked to islands through the source `List_ID` field. The authoritative pipeline therefore maps `species_data.List_ID` through `island_data.List_ID → Island_ID` before constructing species-by-island incidence. The same join was used by the prospective extension.

For each island, we used five CHELSA v2.1 bioclimatic variables sampled at the frozen WGS84 island centroid: annual mean temperature (BIO1), maximum temperature of the warmest month (BIO5), minimum temperature of the coldest month (BIO6), annual precipitation (BIO12) and precipitation seasonality (BIO15) (Karger et al. 2017). The resulting 842-island climate table was frozen by SHA-256.

#### 2.3.2 Spatial folds and pointwise climatic support

All species shared a five-fold geographic partition derived from frozen 5-degree blocks. Within each outer fold, pointwise climatic support was fitted with deterministic L2 logistic regression using the five CHELSA predictors, \(\lambda=1\), no class weighting and training-only standardisation. Nearest-source distance was computed from every target island to the nearest outer-training presence and kept separate from graph features.

#### 2.3.3 Original graph ensemble and conditional concordance

The original benchmark used 12 predeclared graph scenarios crossing four geographic radii (25, 50, 125 and 250 km) with three environmental-edge policies: no environmental restriction, an outer-training-derived 90th-percentile environmental threshold and an outer-training-derived 75th-percentile threshold. All 842 islands remained graph nodes, and only outer-training presences were occurrence anchors.

Held-out islands were assigned to frozen 5 × 5 pointwise-support × nearest-source-distance strata. An occupied and an unoccupied held-out island contributed a pair only when they occurred within the same stratum. For a structural score \(Z\), conditional concordance is the fraction of comparable pairs in which the occupied island has the more favourable \(Z\), with ties contributing one half. The null is 0.5. Fold statistics were averaged equally within species and species equally across the cohort. The 95% interval used 10,000 species bootstrap replicates; a two-sided species sign-flip diagnostic used 100,000 replicates. Non-estimable folds were retained explicitly.

Predeclared secondary summaries separated geography-only and environmentally constrained connected frequency. A further secondary evaluated the median normalised geographic bottleneck under a direction frozen before that outcome, so smaller required bottlenecks were more favourable.

### 2.4 Prospective A-Islands strong-reference island-isolation test

#### 2.4.1 Why a second A-Islands test was frozen

After the original A-Islands result was known, a literature audit identified a legitimate stronger-comparator question. Island area, mainland distance, surrounding landmass, stepping stones, source-area weighting and generic network position all have clear precedents and therefore could not be treated as EOG novelty (Long et al. 2009; Weigelt & Kreft 2013; Sillero et al. 2018; Carter et al. 2020). Before calculating any outcome for the extension, we froze a new reference hierarchy to ask whether species-conditioned archipelago configuration retained predictive information after those quantities were represented. This extension did not replace or reanalyse the original conditional-concordance estimand.

#### 2.4.2 Outcome-free island area and mainland geometry

The downloadable A-Islands v1.0 attribute table lacks the area field described in the data paper, but the already-frozen shapefile contains polygon geometry. We therefore recovered area only from those exact polygon bytes, using a deterministic spherical equal-area calculation. All 842 model-linked islands yielded finite positive area. The derived area table was frozen with SHA-256 `496789783a98e55e1b9552f6f6d28e7b4567ef0f52c795657c7e2fea9c60aae2`; no external area database or outcome-guided correction was permitted.

Continental-mainland distance was derived independently of species outcomes from Natural Earth 1:10m Admin-0 Countries v5.1.1. We selected the unique country feature satisfying `ADMIN=Australia` and `ADM0_A3=AUS`, split its polygon geometry into rings, and defined continental Australia mechanically as the ring with the largest absolute spherical area. This excluded Tasmania and smaller islands without a hand-curated name list. Minimum spherical centroid-to-mainland-coastline distance was computed for all 842 islands. The Natural Earth archive, mainland ring and 842-row distance table were fingerprinted before the species outcome; the distance table SHA-256 is `7d6f52f03702dd0cfae061023a1b2f405e39397de73eaad21b97d24176c4f869`.

#### 2.4.3 Frozen reference hierarchy

The hierarchy was closed at five tiers before extension outcomes:

- **R0:** BIO1, BIO5, BIO6, BIO12 and BIO15.
- **R1:** R0 + log island area + continental-mainland distance + nearest outer-training species source.
- **R2:** R1 + unweighted multi-source pressure + area-weighted source pressure.
- **R3:** R2 + nearest-other-island distance + surrounding-island pressure + surrounding-landmass pressure + unanchored component exposure + species-independent mainland stepping-stone frequency.
- **C:** R3 + geography-only species-conditioned EOG connected frequency.

Source-pressure terms were averaged over the already-declared 25, 50, 125 and 250 km scales. For scale \(s\), unweighted pressure was \(\log[1+\sum_a \exp(-d_{ia}/s)]\) over outer-training presences other than the focal row, while area-weighted pressure additionally multiplied each source by source-island area. Surrounding-island and surrounding-landmass pressure used the same scale ensemble but summed over all other surveyed islands rather than species sources.

Unanchored component exposure was species-independent: at each radius it measured the fraction of other surveyed islands contained in the target's connected component. Species-independent mainland stepping-stone frequency was the fraction of the four radius graphs in which the target's component contained at least one island whose fixed distance to the mainland coastline was no greater than that radius. These quantities were deliberately placed in R3 so generic island density, landmass and network embedding could not be credited to EOG.

The candidate EOG term used the same four geography-only radius graphs but was species-conditioned: it was the fraction of radii in which the target component contained at least one outer-training presence of the focal species. The graph universe remained exactly the 842 surveyed/model-linked islands; shapefile-only unsurveyed polygons were not added post hoc as neutral stepping stones.

#### 2.4.4 Endpoint, inference and one-time execution

The primary extension contrast was paired held-out Bernoulli log loss, **C minus R3**, on identical held-out rows. Negative values were predeclared as favourable to EOG. Brier-score difference was secondary. Fold differences were averaged equally within species, then species means equally across estimable taxa. The 95% interval used 10,000 species bootstrap replicates and the two-sided sign-flip diagnostic used 100,000 replicates, both with seed 20260812.

Before biological scoring, an outcome-free smoke workflow reacquired the source, regenerated the frozen 886-taxon cohort, 842-island audit, five folds, CHELSA table, polygon area and Natural Earth mainland distance, and hard-matched all fingerprints. It then verified 842 islands, 886 taxa and five folds with zero models fitted, zero held-out predictions scored and `C−R3` uninspected. The authoritative extension was subsequently executed once at commit `a9329d929933c919fe6c1c03934f0314c40f5c50`, workflow run `31564146592`, attempt 1. Its raw predictions, fold applicability, species summaries, uncertainty and output checksums were archived. The one-time workflow was removed after successful execution so a more favourable rerun cannot be produced from the current repository state.

### 2.5 Tanzania forest-fragment strong-reference benchmark

#### 2.5.1 Source data and pre-outcome repairs

The non-island benchmark used the archived source package for Brodie and Newmark's analysis of bird occurrence in fragmented East and West Usambara landscapes in Tanzania (Brodie & Newmark 2019; Dryad DOI 10.5061/dryad.p042h0c). Fourteen surveyed forest fragments were represented, nine in East and five in West Usambara. A pre-outcome requirement of at least two presences and two absences yielded 60 eligible bird species.

Source auditing identified three ambiguities that were resolved before current-flow versus EOG outcomes. The workflow rasterised declared patch identifiers rather than implicit row indices; replaced a non-positive/singular source-weight expression with the frozen positive monotone rule \(1/\log_{10}(1+\mathrm{area}_{ha})\), retaining inverse area as sensitivity; and used the digest-verified archived East Usambara raster filename rather than a nonexistent filename referenced in the released script. These were source repairs, not post-outcome tuning.

#### 2.5.2 Current-flow reference and EOG candidate

Forest resistance was fixed at 1. Eucalyptus, tea and other agriculture each took values in \(\{1,2,4,8,16,32,64,128\}\), producing 512 resistance combinations per region. Pairwise effective resistance was computed on an eight-neighbour raster graph. A factor-eight deterministic block-mode coarsening was selected using geometry alone because it preserved all 42 focal identities in each region, whereas factor 16 did not.

For every species and outer fold, one current-flow candidate was selected using outer-training responses only by minimum finite training AIC under the declared source-model form. The selected current-flow quantity was shared by the reference and candidate tiers. The strict reference contained patch area, selected current flow, their interaction and log-transformed nearest outer-training occurrence distance. The candidate added only geography-only EOG connected frequency.

The EOG graph was frozen separately for East and West Usambara using the smallest distinct MST thresholds at which surveyed nodes occupied four, three, two and one components. East radii were 0.511808, 0.913522, 2.654323 and 2.678215 km; West radii were 0.417907, 0.854101, 1.585589 and 3.038021 km. The original broader radius proposal had been rejected before outcomes because it collapsed connected frequency into a nearly trivial same-region indicator.

#### 2.5.3 Validation and endpoint

Primary evaluation used 14-fold leave-one-fragment-out (LOSO). A sensitivity analysis used geometry-only within-region MST blocks. Both probability tiers used deterministic L2 logistic regression with training-only standardisation. Training-constant predictors were dropped and recorded. The primary endpoint was paired candidate-minus-reference held-out log loss; negative values favoured EOG. Brier difference was secondary. Species were the replication unit for 10,000 bootstrap and 100,000 sign-flip replicates. All selection and single-class failures remained in the applicability accounting.

### 2.6 Reproducibility and claim boundary

The repository separates scientific design from manuscript projection. Source identities, cohort and fold fingerprints, graph declarations, feature formulas, training-only rules, applicability states and biological result fingerprints are stored independently of figures and prose. Figure and table builders consume frozen machine-readable inputs and fail if expected fingerprints or result values drift. The prospective A-Islands strong-reference result is frozen under fingerprint `5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a`; the Tanzania result remains frozen under `6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4`.

The claim boundary follows the estimand. A positive original A-Islands conditional concordance supports added **ordering information** conditional on pointwise support and nearest-source distance. It does not by itself imply improved probability prediction under a richer island model. A positive candidate-minus-reference loss difference is adverse because lower loss is favourable. Neither A-Islands endpoint nor the Tanzania endpoint estimates individual movement, realised dispersal, colonisation, detection probability, gene flow or demographic connectivity.

## 3. Results

### 3.1 Original A-Islands analysis: structural ordering remained beyond support and nearest source

Of the 886 declared A-Islands taxa, 845 yielded an estimable original species-level conditional concordance and 41 did not. Mean concordance for combined connected frequency was **0.6177466**, with species-bootstrap 95% interval **0.6086806–0.6269445** and a two-sided sign-flip diagnostic of approximately \(1\times10^{-5}\) (Table 3). Because comparisons were restricted to occupied and unoccupied held-out islands within the same pointwise-support × nearest-source-distance strata, the result is evidence of structural **ordering information** beyond those two controlled quantities rather than a claim of overall probability improvement.

The species distribution was broad: **672 had concordance above 0.5**, **42 equalled 0.5**, and **131 were below 0.5**. At the species-fold level, 3,041 primary rows were evaluable, 1,190 had no comparable occupied–unoccupied pairs within the frozen conditioning strata, and 199 had insufficient training classes. Failed or non-comparable cases were not converted to neutral values.

### 3.2 Original A-Islands structural decompositions

Both predeclared connected-frequency decompositions retained the same original conditional-ordering direction. Geography-only connected frequency had mean concordance 0.6147456 (95% interval 0.6059505–0.6235729; \(n=845\)), while environmentally constrained connected frequency had mean 0.6063727 (0.5974871–0.6154186; \(n=845\)). Their descriptive difference was not a predeclared superiority comparison.

The normalised geographic bottleneck secondary was weaker but remained above the 0.5 null: mean concordance 0.528772 (95% interval 0.517726–0.539568) across 793 taxa. Bottleneck applicability included **2,591** evaluable species-fold rows, **1,640** with no finite comparable occupied–unoccupied bottleneck pair within the frozen strata, and 199 with insufficient training classes. These results show that connected frequency and bottleneck describe related but non-identical aspects of the graph.

### 3.3 Prospective A-Islands strong reference: EOG did not add predictive value

The prospectively frozen strong-reference extension was estimable for all **886** taxa at the species level. Of **4,430** declared species-folds, **4,231** were evaluable and 199 failed only the predeclared 5-presence/5-absence training-class gate. The evaluable folds produced **712,515** held-out predictions. No predictor was dropped as training-constant in an evaluable fold.

The primary C-minus-R3 log-loss difference was **+0.0034852**. Because negative values were predeclared as favourable to EOG, this was adverse. The species-bootstrap 95% interval was **+0.0024664 to +0.0045082**, excluding zero, and the two-sided sign-flip diagnostic was approximately \(1\times10^{-5}\). At the species level, **341** taxa had a negative mean difference favouring EOG, none had exactly zero, and **545** had a positive adverse difference. The Brier endpoint agreed: C minus R3 was **+0.00026825** (95% interval **+0.00007891 to +0.00045700**; sign-flip \(p=0.00562\)). Thus the species-conditioned EOG term did not earn an incremental predictive claim after the predeclared R3 reference.

The predeclared reference ladder is informative only as a post-outcome explanatory decomposition; it cannot replace C−R3 as the primary extension endpoint. Species-macro log loss decreased from R0 to R1 (R1−R0 = −0.01405; 95% interval −0.01584 to −0.01215), but additional tiers were adverse: R2−R1 = +0.00315 (0.00130–0.00491), R3−R2 = +0.00831 (0.00685–0.00992), and C−R3 = +0.00349. R1 therefore had the lowest descriptive species-macro log loss among the five tiers. This pattern is important because it rules out a simplistic explanation in which R3 is merely a superior model that “absorbs” an otherwise beneficial EOG signal. Instead, the frozen result establishes only the narrower point that **adding EOG on top of the declared R3 worsened held-out prediction on average**.

The extension is archived under result fingerprint `5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a`. An independent calculation from the archived species and fold outputs reproduced the species-macro effect, confidence interval, 341/545 direction counts, 4,231 evaluable folds and 712,515 prediction rows.

### 3.4 Tanzania: EOG did not improve the current-flow strong reference

The Tanzania benchmark gave an adverse primary direction under leave-one-fragment-out validation. Across 60 predeclared species, **826** of 840 held-out predictions were valid in both tiers; 14 were non-estimable because training data contained a single response class. **Seventeen species** had a negative mean candidate-minus-reference log-loss difference, while **43 had a positive difference**.

Adding EOG increased species-macro held-out log loss by **+0.0321131** relative to patch area, selected matrix-aware current flow, their interaction and nearest source. The species-bootstrap 95% interval was **+0.0174580 to +0.0486750**, and the sign-flip diagnostic was \(p=0.000030\). Brier difference was also adverse: +0.0047993 (0.0022813–0.0073149). The prespecified inverse-area source weighting retained the direction: log-loss difference **+0.0306296** (0.0162138–0.0469375), with Brier +0.0046676.

### 3.5 Tanzania spatial-block sensitivity was uncertain

Under geometry-only spatial MST blocks, the Tanzania contrast weakened. Primary-weighting log-loss difference was **+0.0109538**, with 95% interval −0.0121714 to +0.0334313. Under inverse-area weighting it was **+0.0057016** (−0.0155325 to +0.0258239). Brier intervals also crossed zero. For each weighting, 718 of 840 declared spatial-block predictions were matched and 122 were non-estimable. The 122 failures comprised **66 single-class training cases** and **56 folds** in which training-only current-flow selection failed. We therefore treat this analysis as a sensitivity boundary, **not as confirmation of the adverse primary LOSO effect**.

### 3.6 Evidence boundary across references and endpoints

The empirical pattern is no longer a simple positive-islands versus negative-fragments contrast. Within A-Islands itself, the original limited-reference endpoint was positive while the later prospectively frozen strong-reference predictive endpoint was adverse. These results are not contradictory because they do not estimate the same quantity. The first asks whether a structural score orders incidence within support × nearest-source strata; the second asks whether adding one EOG predictor to a multivariable penalised probability reference improves held-out loss. The extension therefore prevents the original 0.618 concordance from being elevated into a general claim that EOG improves island occurrence prediction beyond multidimensional isolation.

Tanzania independently reinforces the same methodological boundary under a different strong reference: a generic EOG term did not improve primary prediction once matrix-aware current flow and source distance were present. The Tanzania spatial-block result remains uncertain. The joint evidence supports a reference-conditioned framework in which **structural information can be detectable under one restricted comparison without earning predictive value under a richer or differently parameterised reference**.

## 4. Discussion

### 4.1 Reference content and endpoint are part of the estimand

The central result is not that graph structure is universally useful or universally redundant. It is that statements such as “connectivity adds information” are incomplete unless the reference and the scoring endpoint are specified. The original A-Islands analysis found clear conditional ordering beyond climatic support and nearest-source distance. A later, prospectively frozen test in the same biological system found that adding geography-only species-conditioned EOG to R3 worsened held-out log loss. Tanzania likewise produced an adverse primary increment beyond a matrix-aware reference. These outcomes define the role of EOG more sharply than another positive benchmark would have: **EOG is a structural-adequacy diagnostic whose output may be residual information, adverse/redundant increment, or indeterminate applicability.**

This framing places EOG alongside established spatial methods rather than above them. Spatial CV improves evaluation; random fields model residual dependence; dynamic occupancy and mechanistic models represent processes; and least-cost, circuit-theory and habitat-network models encode connectivity in different ways. EOG asks what remains after the analyst declares which of those information classes belong in the reference. The reference is therefore part of the scientific claim, not merely a technical baseline.

### 4.2 What the two A-Islands endpoints tell us—and what they do not

The original A-Islands result remains valid within its frozen estimand. Matching on pointwise climatic support and nearest-source distance did not remove all association between incidence and connected frequency. With 672 of 845 taxa above the concordance null, the signal was broad. This supports the narrow statement that reducing the original comparison to local climate plus one endpoint distance missed an occurrence-conditioned structural ordering.

The strong-reference extension places a firm ceiling on how far that statement can be generalised. Once the analysis moved to a predictive probability endpoint and a reference containing area, mainland distance, multiple-source pressure, source area, surrounding landmass, generic stepping-stone accessibility and generic network position, adding species-conditioned EOG was adverse on average. Therefore the original concordance cannot be used to claim that EOG captures a generally predictive “archipelagic isolation” dimension beyond established island context.

At the same time, the extension does **not** prove that R3 causally explains the original concordance. The endpoints and model forms differ, and the explanatory tier ladder shows that R3 itself was not the best predictive tier: R1 had lower species-macro log loss, while R2 and R3 successively worsened it. Additional covariates can increase variance or encode noisy/redundant information in a penalised model even when their ecological concepts are meaningful. The supported conclusion is therefore narrower: **under the exact frozen C−R3 predictive test, EOG did not provide incremental predictive benefit**.

This within-system result is methodologically valuable because it removes one weakness of the earlier manuscript. Previously, the only strong-reference adverse result came from Tanzania, so reference strength was confounded with taxonomic group, landscape, sample size and graph construction. The new A-Islands extension does not eliminate endpoint differences, but it shows within the same source system that a positive restricted-reference structural association does not automatically survive as a richer-reference predictive increment.

### 4.3 The island result is not a failure of island biogeography

Island isolation is already known to be multidimensional. Mainland distance, stepping stones, surrounding land area and insular network position can carry different information (Long et al. 2009; Weigelt & Kreft 2013; Carter et al. 2020). Graph-theoretic island connectivity is also established (Sillero et al. 2018), and graph predictions can be evaluated with independent ecological or genetic evidence (Daniel et al. 2023). The adverse C−R3 result therefore should not be read as evidence that stepping stones or network context are unimportant.

Instead, it answers a model-comparison question about the specific species-conditioned connected-frequency feature. R3 was deliberately constructed to deny EOG novelty credit for generic isolation dimensions. The result says that, after this declared reference was fitted with the common L2 engine, adding EOG did not lower held-out loss. That is exactly the type of falsification the pre-outcome design was intended to permit. We consequently close the stronger island-specific novelty route rather than weakening R3 or selecting a favourable subset of taxa.

### 4.4 Tanzania provides an external strong-reference boundary

The Tanzania primary LOSO result is qualitatively compatible with the new A-Islands extension: both strong-reference tests produced adverse candidate-minus-reference log loss. In Tanzania, the reference is biologically different because it includes a training-selected matrix-aware current-flow predictor. The adverse result may reflect redundancy with current flow, the coarseness of the four-rung EOG graph, variance introduced by a new predictor in small folds, or other factors. The data do not identify which mechanism dominates.

The spatial-block Tanzania sensitivity remains important because it became smaller and uncertain while non-estimability increased sharply. Thus neither Tanzania nor A-Islands warrants the broad claim that EOG is always harmful. The supported principle is simply that a generic graph feature must demonstrate incremental held-out value relative to the reference actually used; it cannot inherit credibility from a positive result obtained under a different endpoint or weaker conditioning set.

### 4.5 Response-derived spatial features require an explicit train/test boundary

A broader informatics lesson concerns leakage. Nearest occupied-source distance, occupied-source density, source-weighted pressure and occurrence-conditioned graph summaries all derive predictor values from observed responses. Spatially separated folds do not prevent leakage if such predictors are constructed once from all occurrences before the split. In our benchmarks, every response-derived structural quantity was rebuilt from outer-training presences, and training presences were prevented from acting as their own source.

Cross-fitting is not a novel statistical idea, and source-conditioned connectivity is not a novel ecological idea. The contribution is making that boundary executable and auditable for graph-derived ecological predictors. The prospective A-Islands extension is especially useful here because the design survived an adverse result without changing its source definitions, scales or taxon set. That behaviour is part of what distinguishes a diagnostic framework from an outcome-seeking feature-engineering exercise.

### 4.6 Auditability changes what a negative result means

The scientific value of the adverse island extension depends on its timing. Island area and mainland distance were fixed before extension species outcomes. The R0–R3–C hierarchy, 25/50/125/250 km scales, 5/5 class gate, self-anchor exclusion, L2 engine, endpoint and resampling rules were all closed before the one-time execution. A zero-outcome smoke gate verified source identities, the 886-taxon cohort, 842-island universe, folds, CHELSA bytes, area and mainland fingerprints while fitting no models and inspecting no C−R3 outcome.

The subsequent authoritative run was executed once and produced a complete raw prediction archive, fold table, species summary, aggregate result and checksums. Its direction was then retained, and the one-time workflow was removed. This sequence matters because a negative benchmark that can be silently rerun after radius, source or taxon adjustments does not provide the same evidence boundary.

The repository also retains a prior manuscript-generation correction in which a stale generated results table was found to be internally self-consistent with stale metadata. That problem was converted into a rebuild-equality test. Together, these examples illustrate two distinct reproducibility requirements: the scientific analysis must resist post-outcome adaptation, and the manuscript projection must resist drift away from frozen evidence.

### 4.7 Limitations

Several limitations remain. First, none of the benchmarks observes dispersal, colonisation or individual movement directly. Connected frequency is not an estimate of realised movement. Dynamic occupancy, telemetry, mark–recapture, demographic models or genetic analyses are required when the target is an actual movement process.

Second, the original and strong-reference A-Islands endpoints differ. Conditional concordance within discretised strata is not equivalent to incremental Bernoulli log loss in a penalised multivariable model. Their contrast is scientifically useful for limiting claims, but it is not a controlled one-factor ablation of reference content under one common endpoint. Third, R3 contains several correlated predictors. The common L2 penalty stabilises estimation but does not guarantee that every ecological concept receives an optimally specified representation. The explanatory tier ladder showed deterioration as predictors were added; interpreting those steps mechanistically would require a separately prospectively designed study.

Fourth, the graph radii are assumption scales, not fitted dispersal kernels. Fifth, the A-Islands graph includes the 842 surveyed/model-linked islands only; unsurveyed polygons were not inserted as post-hoc neutral stepping stones. Sixth, Tanzania has only 14 surveyed fragments, leading to substantial non-estimability under spatial blocks. Seventh, detection probability, abundance, genetic isolation and demographic connectivity are outside the current estimands.

Finally, auditability does not make a model biologically correct. A predeclared feature can still be poorly specified. Freezing choices protects the interpretation of the test, not the truth of the assumptions.

### 4.8 Prospective development

The next methodological work should be separated from the present empirical paper. A controlled simulation study with known generating mechanisms could test when a cross-fitted EOG feature detects genuinely transitive structural information, when a nearest-source or multi-source reference is sufficient, and how a deliberately leaky response-derived feature inflates apparent gain. Such work would be appropriate for a later general-method contribution and should not be added now to rescue the adverse island result.

Likewise, trait-informed radii, directional edges, historical colonisation hypotheses, support topology, path redundancy or bottleneck variants may be ecologically useful, but each changes the estimand. They should be frozen prospectively and benchmarked against references containing the information already shown here. The current paper's contribution is complete without a new favourable dataset: it demonstrates how a structural claim can be earned under one restricted comparison and rejected under stronger predictive references while preserving both results.

## 5. Conclusions

Occurrence-conditioned landscape configuration retained conditional incidence-ordering information beyond pointwise climatic support and nearest-source distance in the original A-Islands analysis. That positive result did not translate into a general predictive advantage. In a separately prospectively frozen A-Islands test, adding species-conditioned EOG to a richer island reference increased held-out log loss, and a Tanzanian matrix-aware current-flow benchmark independently showed an adverse primary increment. Because these endpoints and references differ, the results are not one common effect size; together they establish the framework's central rule: **structural information must earn its claim relative to an explicitly declared reference and endpoint**. EOG should therefore be used as an auditable, falsifiable structural-adequacy layer—not as a universal correction to species-distribution models, not as evidence that island connectivity is newly discovered, and not as an estimate of realised dispersal or colonisation probability.

## References

Adriaensen, F., Chardon, J.P., De Blust, G., Swinnen, E., Villalba, S., Gulinck, H. & Matthysen, E. (2003). The application of ‘least-cost’ modelling as a functional landscape model. *Landscape and Urban Planning* 64: 233–247. https://doi.org/10.1016/S0169-2046(02)00242-6

Bakka, H., Vanhatalo, J., Illian, J.B., Simpson, D. & Rue, H. (2019). Non-stationary Gaussian models with physical barriers. *Spatial Statistics* 29: 268–288. https://doi.org/10.1016/j.spasta.2019.01.002

Barve, N., Barve, V., Jiménez-Valverde, A., Lira-Noriega, A., Maher, S.P., Peterson, A.T., Soberón, J. & Villalobos, F. (2011). The crucial role of the accessible area in ecological niche modeling and species distribution modeling. *Ecological Modelling* 222: 1810–1819. https://doi.org/10.1016/j.ecolmodel.2011.02.011

Berlow, E.L. et al. (2013). A network extension of species occupancy models in a patchy environment applied to the Yosemite toad (*Anaxyrus canorus*). *PLoS ONE* 8: e72200. https://doi.org/10.1371/journal.pone.0072200

Brodie, J.F. & Newmark, W.D. (2019). Heterogeneous matrix habitat drives species occurrences in complex, fragmented landscapes. *The American Naturalist* 193: 748–754. https://doi.org/10.1086/702589

Broms, K.M., Hooten, M.B., Johnson, D.S., Altwegg, R. & Conquest, L.L. (2016). Dynamic occupancy models for explicit colonization processes. *Ecology* 97: 194–204. https://doi.org/10.1890/15-0416.1

Carter, Z.T., Perry, G.L.W. & Russell, J.C. (2020). Determining the underlying structure of insular isolation measures. *Journal of Biogeography* 47: 955–967. https://doi.org/10.1111/jbi.13778

Cushman, S.A. et al. (2026). One-hundred seventy-one models of connectivity across Scotland: Influences of method, source points, dispersal threshold, and functional shape on connectivity predictions. *Ecological Informatics* 95: 103740. https://doi.org/10.1016/j.ecoinf.2026.103740

Daniel, J. et al. (2023). [Graph-connectivity validation study]. *Conservation Biology*. https://doi.org/10.1111/cobi.14047

Felin, A. et al. (2025). The role of river connectivity in the distribution of fish in an anthropized watershed. *Science of the Total Environment* 959: 178204. https://doi.org/10.1016/j.scitotenv.2024.178204

Karger, D.N. et al. (2017). Climatologies at high resolution for the earth’s land surface areas. *Scientific Data* 4: 170122. https://doi.org/10.1038/sdata.2017.122

Kim, E.S. et al. (2024). Metapopulation models using landscape connectivity can better reflect landscape heterogeneity. *Ecological Informatics* 80: 102464. https://doi.org/10.1016/j.ecoinf.2024.102464

Long, J.D. et al. (2009). [Stepping-stone island isolation study]. *Ecological Applications*. https://doi.org/10.1890/08-1337.1

McRae, B.H., Dickson, B.G., Keitt, T.H. & Shah, V.B. (2008). Using circuit theory to model connectivity in ecology, evolution, and conservation. *Ecology* 89: 2712–2724. https://doi.org/10.1890/07-1861.1

Merow, C., LaFleur, N., Silander, J.A. Jr., Wilson, A.M. & Rubega, M. (2011). Developing dynamic mechanistic species distribution models: Predicting bird-mediated spread of invasive plants across northeastern North America. *The American Naturalist* 178: 30–43. https://doi.org/10.1086/660295

Milà, C., Mateu, J., Pebesma, E. & Meyer, H. (2022). Nearest neighbour distance matching Leave-One-Out Cross-Validation for map validation. *Methods in Ecology and Evolution* 13: 1304–1316. https://doi.org/10.1111/2041-210X.13851

Nelli, L. et al. (2022). Predicting habitat suitability and connectivity for management and conservation of urban wildlife: A real-time web application for grassland water voles. *Journal of Applied Ecology* 59: 1072–1085. https://doi.org/10.1111/1365-2664.14118

Ortiz-Rodríguez, D.O., Guisan, A., Holderegger, R. & van Strien, M.J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution* 9: 10457–10471. https://doi.org/10.1002/ece3.5567

Ortiz-Rodríguez, D.O., Guisan, A. & van Strien, M.J. (2023). Sensitivity of habitat network models to changes in maximum dispersal distance. *PLoS ONE* 18: e0293966. https://doi.org/10.1371/journal.pone.0293966

Prima, M.-C. et al. (2024). A comprehensive framework to assess multi-species landscape connectivity. *Methods in Ecology and Evolution* 15: 2385–2399. https://doi.org/10.1111/2041-210X.14444

Prugh, L.R. (2009). An evaluation of patch connectivity measures. *Ecological Applications* 19: 1300–1310. https://doi.org/10.1890/08-1524.1

Riva, F. et al. (2024). Incorporating effects of habitat patches into species distribution models. *Journal of Ecology* 112: 2162–2182. https://doi.org/10.1111/1365-2745.14403

Schooley, R.L. & Branch, L.C. (2011). Habitat quality of source patches and connectivity in fragmented landscapes. *Biodiversity and Conservation* 20: 1611–1623. https://doi.org/10.1007/s10531-011-0049-5

Schrader, J. et al. (2025). A-Islands: A Vascular Plant Dataset for Biodiversity Research and Species Monitoring on Australian Continental Islands. *Journal of Vegetation Science* 36: e70019. https://doi.org/10.1111/jvs.70019

Sillero, N. et al. (2018). [Graph-theoretic structural connectivity among islands]. *Biological Journal of the Linnean Society*. https://doi.org/10.1093/biolinnean/bly033

Valavi, R., Elith, J., Lahoz-Monfort, J.J. & Guillera-Arroita, G. (2019). blockCV: An R package for generating spatially or environmentally separated folds for k-fold cross-validation of species distribution models. *Methods in Ecology and Evolution* 10: 225–232. https://doi.org/10.1111/2041-210X.13107

Van Moorter, B. et al. (2023). Habitat functionality: Integrating environmental and geographic space in niche modeling for conservation planning. *Ecology* 104: e4105. https://doi.org/10.1002/ecy.4105

Weigelt, P. & Kreft, H. (2013). Quantifying island isolation—insights from global patterns of insular plant species richness. *Ecography* 36: 417–429. https://doi.org/10.1111/j.1600-0587.2012.07669.x
