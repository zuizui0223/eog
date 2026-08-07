# A-Islands benchmark screening protocol

## Why A-Islands is the primary multi-species island benchmark

A-Islands is an Australia-wide curated database of comprehensive vascular-plant floras for more than 800 continental islands spanning tropical to cool-temperate climates, broad variation in island area and mainland isolation, and multiple substrate types. The published database contains three linked CSV tables (`island_data`, `species_data`, `reference_data`) and island polygons. Because included surveys are intended to represent complete island floras rather than partial plots, non-recorded species can be treated more defensibly as island-level non-occurrences than in opportunistic occurrence databases.

Raja Ampat remains useful as a standardized small-island stress test, but its islands occupy a small geographic region and are extremely small. It is therefore not the primary benchmark for asking whether spatial topology adds predictive information beyond a conventional environmental support surface across broad environmental gradients.

## Pre-outcome screening

Species are screened before any EOG comparison is calculated. The screening script is `benchmarks/aislands_species_screen.py`.

The primary distributional eligibility rule is frozen as:

- present on at least 10 unique surveyed islands;
- absent from at least 10 unique surveyed islands;
- island prevalence between 0.10 and 0.90 inclusive.

Repeated flora lists for one island do not count as independent islands. A species recorded in any list for an island is counted as present on that island.

The screen reports `Native` and `Naturalised` values when supplied by A-Islands but does not silently decide ambiguous status records. The confirmatory benchmark will exclude taxa with evidence of naturalisation or unresolved taxonomic/status problems only through a separately frozen status-cleaning table created before EOG outcomes are inspected.

## Why 10 islands rather than the published minimum of six

Published A-Islands analyses have used native species occurring on at least six islands because six has been discussed as a lower bound for island SDMs. EOG uses a stricter primary screen of 10 present islands and also requires 10 surveyed absences. This is intended to avoid evaluating topology on taxa whose apparent performance is driven by extremely sparse incidence. Sensitivity analyses can later repeat the full benchmark at 6 and 20 present islands, but those are secondary and must not replace the primary rule after outcomes are known.

## Confirmatory analysis boundary

Passing this screen does not make a species a confirmed benchmark taxon. Before model fitting, each retained taxon still needs:

1. a frozen taxonomic and native-status decision;
2. a training-only occurrence set for producing the pointwise support field;
3. a declared geographic domain and hard availability mask;
4. fixed raster resolution, thresholds, neighbourhood and persistence settings;
5. island or region holdout assignments frozen without consulting EOG outcomes;
6. comparison against the existing five rules: support only, nearest-anchor distance, support plus distance, single-threshold detached membership, and multi-threshold persistent topology.

The primary manuscript quantity should be the paired improvement of multi-threshold topology over local support for the same held-out units, with distance-only and support-plus-distance retained as required baselines. A positive result would show added predictive information under the frozen benchmark; it would not estimate dispersal probability, colonisation history, demographic connectivity, or a causal barrier.

## Literature basis

- Schrader et al. (2025), *Journal of Vegetation Science*, A-Islands data paper, DOI: 10.1111/jvs.70019.
- Coleman et al. (2025), *Ecology Letters*, island versus mainland climatic-range analysis using A-Islands, DOI: 10.1111/ele.70099.
- Coleman et al. (2025), *Global Change Biology*, future climate shifts for Australian coastal-island vegetation, DOI: 10.1111/gcb.70220.
- Schrader et al. (2020), *Biodiversity Data Journal*, standardized Raja Ampat woody-plant dataset, DOI: 10.3897/BDJ.8.e55275.
