# A-Islands benchmark screening protocol

## Why A-Islands is the primary multi-species island benchmark

A-Islands is an Australia-wide curated database of comprehensive vascular-plant floras for more than 800 continental islands spanning tropical to cool-temperate climates, broad variation in island area and mainland isolation, and multiple substrate types. The published database contains three linked CSV tables (`island_data`, `species_data`, `reference_data`) and island polygons. Because included surveys are intended to represent complete island floras rather than partial plots, non-recorded species can be treated more defensibly as island-level non-occurrences than in opportunistic occurrence databases, provided that the island has an actual species-list record in the frozen source.

Raja Ampat remains useful as a standardized small-island stress test, but its islands occupy a small geographic region and are extremely small. It is therefore not the primary benchmark for asking whether EOG adds structural information beyond a conventional pointwise environmental support surface across broad environmental gradients.

## Frozen source before EOG outcomes

The published A-Islands version reference `10775809` is a Zenodo concept identifier. The pre-outcome acquisition workflow resolves that concept while requiring the declared version to be exactly `1.0`; the immutable versioned record is Zenodo record `10775810` (DOI `10.5281/zenodo.10775810`). The workflow verifies Zenodo-declared checksums and records SHA-256 digests for `island_data`, `species_data`, and `reference_data` before any species screening or model outcome is calculated.

The acquisition and screening stage must not fit an SDM, calculate EOG topology or bridge outputs, inspect held-out performance, or select species using model outcomes. Its purpose is to establish the source, survey universe, and eligible taxon cohort before any EOG result exists.

The exact version-1.0 tables contain 1,349 `island_data` rows and 59,773 `species_data` rows. The source has 843 unique `Island_ID` values, but one metadata-only list (`List_ID=353`, `Island_ID=277`, `Ref_ID=38`) has no species row, no island name, no survey year, and no alternative list for that island. Because the frozen source does not establish that this row is a complete zero-species flora, the primary benchmark does **not** treat it as universal absence. The primary surveyed-island universe is therefore the 842 unique islands linked to at least one `species_data` row. This rule was fixed before any SDM or EOG outcome was inspected.

## Pre-outcome distribution screen

Species are screened before any EOG comparison is calculated. The screening script is `benchmarks/aislands_species_screen.py`, using the package implementation in `src/eog/aislands_species_screen.py`.

The **primary** distributional eligibility rule is frozen as:

- surveyed-island universe = unique islands linked to at least one `species_data` row;
- present on at least 10 unique surveyed islands;
- absent from at least 10 unique surveyed islands;
- **no primary prevalence exclusion beyond the full 0–1 range**.

Repeated flora lists for one island do not count as independent islands. A species recorded in any retained list for an island is counted as present on that island. An `island_data` row with no linked species row does not by itself establish absence of all species.

The earlier 0.10–0.90 prevalence rule is retired from the primary screen because, with roughly 842 surveyed islands, a 0.10 minimum would silently require presence on roughly 84 islands and thereby exclude the small-range, dispersal-limited taxa that motivate this benchmark. Optional prevalence bounds may be used only as explicitly labelled sensitivity analyses after the count-based primary screen remains fixed.

## Pre-outcome status freeze

The screen reports source-list `Native` values for audit, but those values are incomplete and heterogeneous across original flora lists. Primary taxon status is therefore frozen from `Status_APC`, the standardized Australian Plant Census status supplied in the A-Islands species table.

The primary status rule is:

- `Status_APC == native` → retain in the primary cohort;
- `Status_APC == introduced` → exclude from the primary cohort;
- source-list `Native` values and family are audit fields only and do not override `Status_APC`.

This status rule is applied after the distributional count screen and before any model outcome is inspected. Any future taxonomic exclusions require a separately frozen, source-documented rule and cannot be chosen from EOG or SDM performance.

## Why 10 islands rather than the published minimum of six

Published A-Islands analyses have used native species occurring on at least six islands. EOG uses a stricter primary screen of 10 present islands and also requires 10 surveyed absences. The count rule provides a minimum amount of incidence information while retaining genuinely restricted taxa. Sensitivity analyses can later repeat the full benchmark at 6 and 20 present islands, but those are secondary and must not replace the primary rule after outcomes are known.

## SDM relationship and confirmatory target

The benchmark is not designed to show that EOG is a superior SDM. The pointwise support producer is an upstream input and must be frozen independently of EOG evaluation. The key comparison asks whether a structural transformation of the same support information changes what can be said about spatial organization.

The primary confirmatory comparison must therefore separate:

1. **local support** — the upstream model quantity at a location;
2. **support structure** — occurrence-conditioned component identity and persistence under frozen thresholds;
3. **reachability assumptions** — bridge or barrier hypotheses, evaluated separately from topology;
4. **survey decisions** — any finite-site allocation, which remains downstream and can be delegated to ACSP.

A positive empirical result may show that frozen structural information adds discrimination beyond the upstream local-support score on the evaluated units. It must not be worded as universal EOG superiority over SDMs.

## Why the primary A-Islands test is reachability, not raster topology

Ocean masking would make separate islands disconnected raster components by construction. Using that fact as the primary topology benchmark would risk rewarding EOG for an island-specific triviality rather than testing the general problem of restricted movement across a fragmented landscape.

The primary A-Islands structural test therefore uses the **existing** `eog.bridge` and `eog.bridge_builder` graph implementation without adding an island class or a new reachability definition. Each surveyed island is a node. Geographic separation and environmental contrast define predeclared graph scenarios, and training-fold presence islands are the source nodes. The same machinery can be used for fragmented forests, mountain patches, river networks, or other discrete habitat systems by changing nodes and edge costs rather than changing the algorithm.

The frozen machine-readable contract is `validation/aislands_preoutcome_20260808/reachability_protocol.json`. The earlier CHELSA freeze in PR #83 is authoritative for climate inputs: CHELSA-bioclim v2.1, 1981–2010, `bio1`, `bio5`, `bio6`, `bio12`, and `bio15`, sampled directly at each frozen A-Islands WGS84 centroid with no nearby-cell substitution, interpolation, polygon averaging, or imputation. The accepted climate CSV SHA-256 is `6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285`. All 842 retained islands have finite values for all five variables.

Primary local support is climate-only so that area, coordinates, mainland distance, nearest-island distance, and bridge outputs cannot leak movement structure into the environmental baseline. Predictors are standardized inside each training fold only. The frozen statistical objective is class-balanced L2-regularized logistic regression with penalty 1.0; the implementation uses deterministic Newton updates to solve that objective. This correction was made before any species-level SDM or EOG outcome was computed, after detecting that the initial reachability protocol had accidentally drifted from the earlier frozen climate artifact.

The primary graph is an undirected 5-nearest-neighbour graph, with 3- and 8-neighbour graphs retained as declared sensitivities. No island-specific barrier term is added in the primary graph. The required paired comparators are local support only, nearest-training-presence geographic distance, local support plus distance, geographic-only bridge, and geographic-plus-environmental bridge. Bridge scores remain hypothesis scores rather than dispersal probabilities or reconstructed colonisation histories.

## Confirmatory analysis boundary

Passing the distribution and APC-native screens does not by itself validate a taxon-specific EOG result. Before model fitting, the benchmark still needs:

1. the frozen source and taxon cohort described above;
2. a training-only occurrence/incidence set for producing the pointwise support field;
3. a declared geographic domain and availability/barrier treatment;
4. fixed support-producer specification and predictor provenance;
5. fixed raster or node resolution, thresholds, neighbourhood and persistence settings where spatial support topology is used;
6. island or region holdout assignments frozen without consulting EOG outcomes;
7. comparison against predeclared rules that distinguish local support from structural and reachability information.

For support-topology analyses, required baselines remain support only, nearest-anchor distance, support plus distance, single-threshold detached membership, and multi-threshold persistent topology. Bridge/reachability analyses require their own predeclared graph-scenario baselines and must not be folded into a topology score after outcomes are seen.

The primary manuscript quantity should be a paired, held-out contrast defined before outcomes are inspected. A positive result would show added structural information under the frozen benchmark; it would not estimate dispersal probability, colonisation history, demographic connectivity, genetic isolation, or a causal barrier.

## Literature basis

- Schrader et al. (2025), *Journal of Vegetation Science*, A-Islands data paper, DOI: 10.1111/jvs.70019.
- Coleman et al. (2025), *Ecology Letters*, island versus mainland climatic-range analysis using A-Islands, DOI: 10.1111/ele.70099.
- Coleman et al. (2025), *Global Change Biology*, future climate shifts for Australian coastal-island vegetation, DOI: 10.1111/gcb.70220.
- Schrader et al. (2020), *Biodiversity Data Journal*, standardized Raja Ampat woody-plant dataset, DOI: 10.3897/BDJ.8.e55275.
