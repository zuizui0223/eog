# EOG v2 SW Finland archipelago colonization pre-outcome contract

## Status

**Prospective independent empirical occurrence candidate. Outcome scoring is not yet authorized.**

This contract is frozen before EOG v2 is scored against the released `outcome` column. The published paper and Dryad metadata necessarily describe the original colonization results, but this dataset has not been used to design EOG v2, choose the fixed-source EOG-R estimator, select the source-expansion policy, or set the synthetic promotion gates.

The benchmark may proceed only after the response-free admission checks below pass. A failed admission check is a dataset NO-GO for graph-native EOG confirmation and must not be repaired using the colonization outcomes.

## Authoritative source

- Study: Aikio, Ramula, Muola & von Numers (2020), *Island properties dominate species traits in determining plant colonizations in an archipelago system*, Ecography, DOI `10.1111/ecog.05013`.
- Dataset: von Numers, Aikio, Ramula & Muola (2020), Dryad DOI `10.5061/dryad.ffbg79cr6`.
- Released file: `colonization_select.csv`.
- Dryad landing-page size: `129.16 MB`.
- Study universe: paired historical/recent vascular-plant inventories on `471` islands; historical surveys were mainly in 1925–1946 and recent surveys in 1996–2017.

The raw file SHA-256 must be computed immediately after lawful retrieval and committed before the EOG score is evaluated. Retrieval failure does not authorize a mirror with altered contents unless the mirror is independently provenance-verified and byte identity is demonstrated.

## Released columns relevant to this benchmark

The Dryad metadata declares, among others:

- `outcome` — colonization failure/success (`0/1`); **forbidden during admission and feature freeze**;
- `holmkod` — focal island code;
- `spp.name` — focal species;
- `Euref_X_original`, `Euref_Y_original` — original EUREF-FIN island coordinates;
- `Dist_to_historical_log` — distance to the nearest island historically occupied by the focal species;
- `Historical_total_log` — number of islands historically occupied by the focal species;
- island area, surrounding land, shoreline, limestone, habitat-diversity and CORINE habitat variables.

## Biological unit and source definition

The evaluated unit is a species–island **potential colonization event**: the focal species was absent from that island in the historical inventory and may or may not occur in the recent inventory.

For a focal species, the intended fixed sources are the islands occupied in the historical inventory. The released long table does not expose a dedicated historical-source-ID column. Therefore source membership may be reconstructed as the complement of the released potential-target island set **only if all response-free consistency checks pass**.

No recent successful colonization is ever admitted as a source in this benchmark. This is the already-confirmed fixed-source EOG-R estimand; the separately tested expanded-source policy failed its frozen confirmation and is prohibited here.

Species with no occurrence in the historical inventory have no defined fixed source. The source paper reports such cases through missing nearest-historical distance. They are legitimate biological records but are outside this fixed-source EOG-R estimand and must be declared non-applicable before `outcome` is read.

## Response-free admission gates

The admission program must never parse, summarize, count, stratify or model the `outcome` values.

It must verify:

1. exactly `471` unique `holmkod` values form the island universe;
2. each island has one invariant pair of finite `Euref_X_original`/`Euref_Y_original` coordinates across species rows;
3. a historical-source complement is reconstructed for every species; zero-source species are explicitly counted as fixed-source non-applicable, and at least `100` species have one or more reconstructed historical sources;
4. among sourceful species, reconstructed historical source count is consistent with `Historical_total_log` up to one of a small frozen set of monotone release transforms (`raw`, `log10(n)`, `log10(n+1)`, `ln(n)`, `ln(n+1)`) followed by an affine standardization; required `R^2 >= 0.999999` across finite rows;
5. among sourceful species, Euclidean distance from each target island to the nearest reconstructed historical source is consistent with `Dist_to_historical_log` under the analogous frozen transform family followed by affine standardization; required `R^2 >= 0.999999` across finite rows;
6. for zero-source species, released nearest-historical distance must be missing wherever it is represented in the admission projection rather than silently imputed from recent outcomes;
7. no island coordinate or source-reconstruction decision depends on `outcome`;
8. the raw-file SHA-256 and a response-free projection fingerprint are archived before scoring.

If gates 1–6 fail, do not infer missing historical source identities from the EOG outcome or optimize a graph to improve prediction.

## Primary island graph

The graph is built once from the `471` island locations and island habitat states, without species outcomes.

### Geographic adjacency

Use the undirected **Gabriel graph** on original EUREF-FIN island-centre coordinates. Gabriel adjacency is parameter-free and contains the Euclidean minimum spanning tree, avoiding an outcome-tuned distance radius or k-nearest-neighbour choice.

For Gabriel edge `i-j`, let `d_geo(i,j)` be Euclidean coordinate distance. Define

`K_geo(i,j) = exp(-d_geo(i,j) / median_Gabriel_edge_distance)`.

### Environmental transition support

Use island habitat state only; island area is not folded into reachability because target size/persistence is a separate EOG layer.

Habitat-state columns are predeclared as:

- `Buildings`;
- `Meadow_or_pasture`;
- `Deciduous_forest`;
- `Coniferous_forest`;
- `Mixed_forest`;
- `Sand`;
- `Open_rock_or_bare_ground`;
- `Marsh`;
- `Shore_meadow`;
- `Limestone`.

`Scrub` is omitted because the habitat proportions are compositional and the source study likewise removed one habitat class to avoid the deterministic sum constraint.

Standardize each continuous habitat column across the 471 islands without outcome data. Let `d_env(i,j)` be Euclidean distance in this standardized habitat space. On Gabriel edges,

`K_env(i,j) = exp(-d_env(i,j) / median_nonzero_Gabriel_environment_distance)`.

Primary raw directed support is symmetric:

`W_ij = K_geo(i,j) * K_env(i,j)`.

No directional wind/current modifier is introduced because the released dataset does not justify one.

### Frozen EOG-R propagation

Use the already-confirmed fixed-source occurrence settings rather than retuning them to Finland:

- `loss_support = 0.55`;
- `max_steps = 5`;
- equal initial weights over the focal species' historical sources;
- no source reinjection after step zero;
- target predictor = finite-depth integrated node reachability support.

A geography-only Gabriel-graph EOG-R is retained as a sensitivity output, not a replacement primary chosen after outcome inspection.

## Conventional predictor ladder

No predictor selection is outcome-driven. Numeric standardization is training-fold-only.

### R0 — local island reference

Predeclared local island predictors:

- `Residents_per_area_log`;
- `Area_log`;
- `Buffer_2_km_log`;
- `Buffer_5_km_log`;
- `Shannon_habitats`;
- `Convolution`;
- `Limestone`;
- `Buildings`;
- `Meadow_or_pasture`;
- `Deciduous_forest`;
- `Coniferous_forest`;
- `Mixed_forest`;
- `Sand`;
- `Open_rock_or_bare_ground`;
- `Marsh`;
- `Shore_meadow`;
- `Euref_X`;
- `Euref_Y`.

`Scrub` is omitted for the same compositional constraint noted above.

### R1 — published historical-source summaries

R0 plus:

- `Dist_to_historical_log`;
- `Historical_total_log`.

### R2 — stronger source/network reference

R1 plus two response-free reconstructed-source features:

- source pressure = sum of `exp(-distance / median_Gabriel_edge_distance)` over historical sources;
- minimum effective-resistance distance from target to any historical source on the symmetric primary Gabriel conductance graph.

The effective-resistance matrix is computed once from the frozen island graph; no resistance surface is tuned to `outcome`.

### C — fixed-source dynamic EOG-R candidate

R2 plus the primary finite-depth EOG-R reachability support.

Primary empirical contrast:

`C - R2` held-out log loss; negative favours EOG.

R0/R1/R2 are all retained regardless of direction so the result shows whether the source/network references themselves are informative.

## Validation folds

All rows for an island must belong to the same outer fold.

Before reading `outcome`, construct `5` deterministic contiguous spatial folds from original island coordinates using a response-free farthest-point-seeded k-means rule implemented in the benchmark code. The exact island-to-fold assignment and its SHA-256 fingerprint must be archived before scoring.

No species–island row from a held-out island may enter model fitting for that fold.

## Fitting engine

Use one common deterministic L2 logistic engine for R0, R1, R2 and C:

- L2 penalty `1.0`;
- intercept unpenalized;
- numeric scaling learned on the outer training fold only;
- no AIC/drop-one/VIF or post-outcome feature selection;
- categorical species traits are not used in the primary benchmark.

The benchmark is deliberately focused on whether source-conditioned graph structure adds to local island properties and strong historical/source-network references, not on reproducing the source paper's trait-selection model.

Rows with non-finite required predictors are excluded by a response-free completeness mask. The mask and counts must be frozen before scoring.

## Inference and promotion rule

The inferential replication unit is species, not the individual species–island row.

For each eligible species, compute its paired held-out mean log-loss difference `C - R2`. Report:

- equal-weight mean species difference;
- median species difference;
- fraction of species with negative difference;
- 95% percentile bootstrap interval over species using `10,000` fixed resamples;
- pooled row-level log-loss and Brier differences as descriptive sensitivities.

The dataset is a **GO for empirical added information** only if all of the following predeclared conditions hold:

1. at least `100` species are evaluable under the response-free source/completeness gates;
2. R2 is not worse than R0 in pooled held-out log loss, establishing that the strong historical/source reference is operationally meaningful;
3. equal-weight mean species `C - R2 < 0`;
4. the upper bound of the 95% species-bootstrap interval for `C - R2` is `< 0`.

If R2 is adverse to R0, the EOG incremental test is retained but the dataset-level promotion decision is **indeterminate strong-reference failure**, not rescued by dropping R2.

If EOG is null or adverse, that outcome is retained and EOG v2 does not gain an empirical occurrence superiority claim from this dataset.

## Outcome firewall

Before the response-free admission projection, graph, folds, reference set, EOG settings and promotion rule above are fingerprinted, no EOG code may:

- count successful colonizations;
- inspect success rates by species or island;
- choose taxa by observed colonization frequency;
- alter graph topology, support scales, propagation depth or loss support;
- change R0/R1/R2 predictors;
- change folds;
- lower the promotion threshold.

The published source-paper results remain useful prior context but may not be used to retune EOG after its held-out result is known.
