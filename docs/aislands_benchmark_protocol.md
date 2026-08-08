# A-Islands benchmark screening protocol

## Why A-Islands is the primary multi-species island benchmark

A-Islands is an Australia-wide curated database of comprehensive vascular-plant floras for more than 800 continental islands spanning tropical to cool-temperate climates, broad variation in island area and mainland isolation, and multiple substrate types. The published database contains three linked CSV tables (`island_data`, `species_data`, `reference_data`) and island polygons. Because included surveys are intended to represent complete island floras rather than partial plots, non-recorded species can be treated more defensibly as island-level non-occurrences than in opportunistic occurrence databases.

Raja Ampat remains useful as a standardized small-island stress test, but its islands occupy a small geographic region and are extremely small. It is therefore not the primary benchmark for asking whether EOG adds structural information beyond a conventional pointwise environmental support surface across broad environmental gradients.

## Frozen source before EOG outcomes

The primary A-Islands source is frozen to Zenodo record `10775809`, cited by the data paper as A-Islands version 1.0. The pre-outcome acquisition workflow downloads that exact record, verifies any checksums declared by Zenodo, records SHA-256 digests for the resolved `island_data` and `species_data` tables, and only then performs species screening.

The acquisition and screening stage must not fit an SDM, calculate EOG topology or bridge outputs, inspect held-out performance, or select species using model outcomes. Its purpose is to establish the eligible taxon universe before any EOG result exists.

## Pre-outcome distribution screen

Species are screened before any EOG comparison is calculated. The screening script is `benchmarks/aislands_species_screen.py`.

The **primary** distributional eligibility rule is frozen as:

- present on at least 10 unique surveyed islands;
- absent from at least 10 unique surveyed islands;
- **no primary prevalence exclusion beyond the full 0–1 range**.

Repeated flora lists for one island do not count as independent islands. A species recorded in any list for an island is counted as present on that island.

The earlier 0.10–0.90 prevalence rule is retired from the primary screen because, with roughly 844 surveyed islands, a 0.10 minimum would silently require presence on roughly 84 islands and thereby exclude the small-range, dispersal-limited taxa that motivate this benchmark. Optional prevalence bounds may be used only as explicitly labelled sensitivity analyses after the count-based primary screen remains fixed.

The screen reports `Native` and `Naturalised` values when supplied by A-Islands but does not silently decide ambiguous status records. The confirmatory benchmark will exclude taxa with evidence of naturalisation or unresolved taxonomic/status problems only through a separately frozen status-cleaning table created before EOG outcomes are inspected.

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

## Confirmatory analysis boundary

Passing the distribution screen does not make a species a confirmed benchmark taxon. Before model fitting, each retained taxon still needs:

1. a frozen taxonomic and native-status decision;
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
