# Tanzania benchmark: geometry and formula contract

This contract is frozen after the official Dryad bytes, scripts, table semantics, coordinate reference systems, and source-eligible species cohort were verified, but **before** any Tanzania current-flow or EOG held-out performance is calculated.

## Verified source state

The benchmark contains:

- 14 surveyed forest fragments: 9 East and 5 West;
- 89 bird species with a complete 89 × 14 binary occurrence table;
- 60 species satisfying the pre-outcome source rule of at least 2 presences and 2 absences;
- 42 forest-patch nodes in each landscape;
- EPSG:4326 site/node coordinates aligned to the two verified matrix rasters;
- exact official scripts for the 512 resistance combinations and occurrence models.

The canonical source-eligible species-list SHA-256 is:

`4859178d155db2594a635896d794d1af4c4d655da924489d41ff64e8fc57f135`

Any drift in that cohort, source file digest, coordinate alignment, or formula evidence is a hard failure.

## Cross-validation

### Primary: leave one fragment out

The primary design has 14 folds. Every surveyed fragment is held out once. This maximizes training information in the very small site set while ensuring that the held-out occurrence label is never used in local-model fitting, current-flow resistance selection, occurrence anchoring, EOG features, or probability calibration.

The global 2/2 source rule guarantees that every eligible species retains both classes in every single-site training set. Method-specific numerical or graph failures are still reported rather than silently dropped.

### Spatial sensitivity: geometry-only MST blocks

A secondary spatial extrapolation audit is built independently within East and West from site coordinates alone.

For each region:

1. construct a deterministic site minimum spanning tree using great-circle distance;
2. choose the number of blocks as `round(sqrt(n_sites))`, with a minimum of two;
3. remove the largest `k−1` MST edges;
4. use the resulting connected components as held-out blocks;
5. resolve exact distance ties lexically, never using occurrence labels.

This creates three East blocks and two West blocks. Species/folds that lose one response class under block holdout are marked non-estimable for that sensitivity analysis.

## EOG graph

East and West are separate graphs. Cross-landscape edges are prohibited even if a numeric radius would connect them. Each graph contains all 42 verified forest-patch nodes, including unsurveyed structural stepping stones. The 14 survey fragments are exact subsets of those node tables.

The graph is deliberately geography-only in this benchmark. Matrix heterogeneity is represented by the strong current-flow comparator, so the EOG increment tests occurrence-anchored patch configuration without disguising another matrix-resistance model as EOG.

### Geometry-only scenario radii

Within each 42-node region, compute the deterministic node MST. The four edge radii are the q50, q75, q90, and q100 quantiles of that MST's edge lengths.

This rule is fixed entirely by verified geometry:

- no species label is used;
- no radius is selected by held-out performance;
- q100 is the minimum radius at which the whole regional node set is connected;
- lower quantiles provide increasingly restrictive fragmentation scenarios.

The primary EOG structural quantity is `connected_frequency`: the fraction of the four scenarios in which a candidate node is connected to at least one training-presence anchor. Median normalized geographic bottleneck is secondary.

These quantities remain assumption-dependent structural diagnostics, not colonization or dispersal probabilities.

## Controlling simple occurrence proximity

The strict EOG comparison includes `log10(1 + nearest training-presence distance in km)` in both the reference and candidate models.

Therefore the primary incremental question is not merely whether occupied fragments lie closer to known occurrences. It is whether graph configuration adds held-out information after controlling:

- patch area;
- the fold-safe matrix-aware current-flow quantity;
- the source area × isolation interaction;
- simple distance to the nearest training occurrence.

Training-site anchor-distance and EOG predictors are themselves cross-fitted inside each outer fold: each training site's own occurrence is excluded when constructing its structural predictor. The outer held-out fragment uses all outer-training occurrences. This prevents an occupied training fragment from trivially receiving zero distance and perfect anchor membership in the regression fit.

## Source formulas

The verified source scripts define:

- local predictor: `log10(area_ha)`;
- simple-isolation candidates: `distance1` and `distance2`, each linked to its named nearest fragment;
- relative resistance levels: `1, 2, 4, 8, 16, 32, 64, 128` for eucalyptus, tea, and other agriculture;
- intact forest resistance: 1;
- 512 current-flow resistance combinations per landscape;
- pairwise Circuitscape effective resistance;
- patch isolation as the sum, over all other source patches, of resistance distance divided by the source patch's `log10(area_ha)`;
- source occurrence model: `occur ~ log10(area_ha) * log10(isolation)`;
- source candidate selection by AIC among models passing the original convergence and pseudo-R² checks.

The source script refers to `raster_east3_new.tif`, while the sole verified East raster in the archive is `raster_east3.tif` and already contains the final four classes expected by the script. Execution may use a byte-identical alias only; raster values may not be altered or reconstructed.

## Reproduction versus held-out prediction

Two analyses remain separate.

### Source reproduction

The original full-data analysis is reproduced with the source unpenalized binomial GLM, AIC selection, convergence checks, and pseudo-R² summaries. This is a source-implementation sanity check and cannot be used as held-out evidence.

### Leakage-safe prediction

Within each outer fold:

1. select the current-flow resistance combination on training data only, using the source AIC/convergence procedure;
2. fix that selected current-flow quantity for both the structural reference and the EOG candidate;
3. refit every held-out comparison tier with the same deterministic L2 logistic engine, training-only standardization, unpenalized intercept, and λ = 1;
4. score the untouched held-out label with the already frozen paired log-loss framework.

The EOG candidate may not trigger a different current-flow resistance selection.

## Frozen probability tiers

The executable held-out tiers are:

1. `local`: log patch area;
2. `simple isolation`: area, selected simple isolation, and their interaction;
3. `current flow`: area, selected fold-safe current-flow isolation, and their interaction;
4. `current flow + anchor distance`;
5. `current flow + anchor distance + EOG connected frequency`.

The strict incremental contrast is tier 5 minus tier 4. Candidate-minus-reference log-loss differences below zero favor EOG.

## Inference and claim boundary

Species are the inferential replication unit. The equal-weight mean of species-level paired log-loss differences is primary, with a 10,000-replicate species bootstrap and a secondary 100,000-replicate species sign-flip diagnostic under the frozen seeds.

Success would show that occurrence-anchored patch-network configuration carries held-out information beyond patch area, conventional isolation, simple occurrence proximity, and a leakage-safe matrix-aware current-flow competitor in a non-island fragmented landscape. It would not establish a mechanistic colonization probability or universal superiority over connectivity models.
