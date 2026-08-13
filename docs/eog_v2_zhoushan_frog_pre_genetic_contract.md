# EOG v2 Zhoushan pond-frog pre-genetic metadata contract

## Status

**Prospective candidate — genetic response access prohibited until the response-free geography gate is frozen.**

Candidate study: Wang et al. (2014), *Population size and time since island isolation determine genetic diversity loss in insular frog populations*, Molecular Ecology 23:637–648, DOI `10.1111/mec.12634`.

Public data mirror: Zenodo record `5012316`, corresponding to Dryad DOI `10.5061/dryad.dq4g5`.

The archive exposes two separate files:

- `Raw transects .xlsx` — field-survey metadata; response-free stage only;
- `Microsatellite data.xls` — genetic response source; **forbidden before predictor freeze**.

This candidate is useful only if the geography and node identity can be established independently of the microsatellite outcomes.

## Declared biological nodes

The source paper predeclares 27 sampled populations: three mainland sites and 24 islands.

Mainland:

1. Guoju
2. Xiepu
3. Yuanhua

Islands:

1. Meishan
2. Fodu
3. Liuheng
4. Huni
5. Xiashi
6. Mayi
7. Taohua
8. Dengbu
9. Zhujiajian
10. Putuoshan
11. Zhoushan
12. Damao
13. Cezi
14. Jintang
15. Dapengshan
16. Changbai
17. Xiushan
18. Dayushan
19. Daishan
20. Dongji
21. Qushan
22. Sijiao
23. Shengshan
24. Huaniao

The primary validation unit will be the population/site node; population merging or deletion after genetic-response access is prohibited.

## Stage 1 — response-free metadata audit

Only `Raw transects .xlsx` may be downloaded or parsed.

The audit must archive:

- raw file SHA-256;
- workbook sheet names and dimensions;
- declared column headers;
- unique site/island identifiers found in non-genetic metadata;
- any explicit longitude/latitude or projected-coordinate fields;
- any GPS/transect-location fields;
- a canonical response-free metadata fingerprint.

The audit must not download, open, inspect, hash, or infer anything from `Microsatellite data.xls`.

### Geography admission

The candidate can proceed to predictor freeze only if one of these response-free routes succeeds:

A. explicit finite coordinates are present for all 27 declared nodes in the transect workbook; or

B. each declared node maps unambiguously to one island/site and a separately documented, outcome-independent geographic point (e.g. declared island centroid/site coordinate) can be frozen before genetic access.

If multiple populations map to one island, using one island centroid for all of them is not permitted unless the population-level genetic response is first aggregated by a rule frozen before genetic access. No location may be inferred from allele patterns, FST, migration, clustering, or published genetic-result figures.

## Stage 2 — response-free EOG predictor freeze

Only after Stage 1 admission passes:

- freeze node IDs and coordinates;
- freeze straight-line IBD distance;
- freeze a parameter-free Gabriel geography graph;
- freeze current-flow/effective-resistance strong reference;
- freeze the already-confirmed exact-eventual EOG continuous distance and disconnection indicator;
- archive all pairwise predictor values and fingerprints before genetic access.

Environmental distance is not invented if a response-free, biologically justified environmental state is unavailable. In that case the empirical ladder is explicitly IBD -> current-flow -> current-flow + EOG, with IBE marked non-applicable.

## Stage 3 — genetic response attachment

Only after the Stage 2 artifact is committed/fingerprinted may `Microsatellite data.xls` be downloaded.

The genetic-response implementation must:

- record the genetic raw-file SHA-256;
- verify exactly the frozen 27 population labels or document response-free exclusions;
- calculate one predeclared symmetric neutral genetic-distance endpoint from the nine microsatellite loci;
- preserve missing data rather than inventing genotypes;
- use leave-one-population-out validation so every pair involving the held-out population is excluded from training.

Pairwise FST is symmetric and therefore cannot validate migration direction.

## Claim boundary

This candidate is intended to test whether the frozen exact-eventual EOG construction adds held-out information beyond geography/current-flow in an independent land-bridge archipelago dataset. A null or adverse result is retained. References, graph topology, nodes, response transform and eligibility rules cannot be changed after genetic access.
