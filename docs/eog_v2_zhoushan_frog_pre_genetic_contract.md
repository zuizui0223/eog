# EOG v2 Zhoushan pond-frog independent genetic validation contract

## Status

**Prospective analysis freeze — exact pairwise genetic response access prohibited until Stage 2 predictors are archived and fingerprinted.**

Candidate study: Wang et al. (2014), *Population size and time since island isolation determine genetic diversity loss in insular frog populations*, Molecular Ecology 23:637–648, DOI `10.1111/mec.12634`.

Public non-genetic/genetic mirror: Zenodo record `5012316`, corresponding to Dryad DOI `10.5061/dryad.dq4g5`.

Relevant released files are deliberately separated by stage:

- `Raw transects .xlsx` — response-free field-survey metadata;
- Wiley Supporting Information `Table S1` (`mec12634-sup-0001-TableS1.xlsx`) — **primary exact pairwise FST response, forbidden until Stage 2 is frozen**;
- `Microsatellite data.xls` — optional later raw-genotype replication, also forbidden until Stage 2 is frozen.

The published article-level narrative is already known, so this is not claimed to be publication-blinded. The critical prospective firewall is that the **exact pairwise response values are not opened until nodes, coordinates, graph, EOG predictors, reference model and inference rule are frozen**.

## Declared biological nodes

Exactly 27 sampled population/site nodes are fixed from the source paper.

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

No node may be merged, dropped, renamed or moved in response to FST values.

## Stage 1 — response-free geography

### 1A. Released transect metadata

Only `Raw transects .xlsx` was accessed. Run `31654548790` passed the access firewall and showed:

- all 24 island names are present;
- no coordinate/GPS field exists;
- the three mainland sites are not represented in the workbook;
- no microsatellite/genetic file was accessed.

The negative result is frozen in `docs/eog_v2_zhoushan_frog_pre_genetic_metadata_result.md`.

### 1B. Response-free gazetteer geography

Public geographic candidates were queried without genetic access in Nominatim run `31654792433`. Missing/ambiguous island entities were resolved only with independent GeoNames-backed geography.

The final coordinate-selection hierarchy and all 27 selected representative points are now frozen in:

- `docs/eog_v2_zhoushan_frog_coordinate_freeze.md`;
- `benchmarks/frozen/zhoushan_frog_response_free/population_coordinates.csv`.

The nodes represent population/site locations at island/site scale, not asserted individual frog capture coordinates. The source paper states that transects covered accessible habitat across each island/site.

## Stage 2 — response-free predictor freeze

Before any exact FST value is opened, the repository must generate and archive a complete 351-pair predictor table from the frozen coordinate CSV.

### Geographic predictors

- great-circle geographic distance in km;
- a parameter-free Gabriel graph in a local tangent plane;
- edge support `exp(-d / median_Gabriel_edge_length)`;
- `loss_support = 0.5`;
- effective-resistance/current-flow distance on the same response-free conductance graph.

### EOG predictor

Use the already-confirmed exact-eventual genetic construction on the same sub-stochastic operator:

- reciprocal eventual support averaged in support space;
- continuous connected-pair distance `-log(exchange support)`;
- explicit disconnection indicator;
- no finite propagation horizon;
- no numerical support-floor hyperparameter;
- no fitted symmetrisation parameter.

### IBE boundary

No environmental predictor is invented. `environmental_distance = 0` for all pairs and IBE is explicitly **non-applicable** in this candidate unless a separately frozen, response-independent environmental state is added before Stage 2 closes.

### Predictor/inference fingerprints

Stage 2 must archive before response access:

- population-coordinate CSV SHA-256;
- complete predictor CSV SHA-256;
- coordinate-selection manifest/fingerprint;
- Gabriel edge set and support scale;
- transition-operator fingerprint;
- exact-eventual connectivity fingerprint;
- validation settings and contract SHA-256.

The Stage-2 artifact is the immutable predictor source for the one-time genetic response run. It may not be regenerated after exact FST values become visible merely because floating-point or implementation changes alter results.

## Stage 3 — exact genetic response attachment

### Primary response

After Stage 2 is committed/fingerprinted, download the Wiley Supporting Information **Table S1** for DOI `10.1111/mec.12634` and record its SHA-256.

The primary response is the published symmetric pairwise FST value for each frozen population pair.

Response transform is frozen as:

`linearized_FST = FST / (1 - FST)`.

If an exact pair is missing in Table S1 it remains missing. Values are not reconstructed from figures, allele frequencies or genetic clustering.

### Optional replication

`Microsatellite data.xls` may be downloaded only after the primary Stage-2 freeze and primary Table-S1 response attachment. It is a replication/provenance check, not a source for choosing graph topology or reference models.

## Validation and promotion rule

Use deterministic leave-one-population-out validation. All genetic pairs containing the held-out population are test pairs; no pair containing that population enters training.

Common ridge penalty: `1.0`.

Models retained regardless of outcome:

1. IBD;
2. IBD + EOG;
3. Gabriel current flow;
4. Gabriel current flow + EOG.

Primary contrast:

`(current flow + EOG) − current flow` held-out MSE; negative favours EOG.

Secondary contrast:

`(IBD + EOG) − IBD` held-out MSE.

The inferential replication unit for the promotion gate is the held-out population, not the individual pair. Compute the paired per-population MSE difference for current-flow+EOG versus current-flow.

Fixed bootstrap:

- exactly `10,000` population resamples;
- seed `20260813`;
- 95% percentile interval of the equal-weight mean held-out-population MSE difference.

This dataset is a **GO for independent empirical genetic added information** only if all are true:

1. all 27 nodes are represented or any missing-response exclusions are mechanically required without node/graph changes;
2. pooled LOPO MSE for current flow is `<=` pooled IBD MSE, establishing an operational strong reference;
3. equal-weight mean held-out-population `(current flow + EOG) − current flow` MSE is `< 0`;
4. the upper bound of the fixed 95% population-bootstrap interval is `< 0`.

If condition 2 fails, status is `indeterminate_strong_reference_failure`; current flow is not dropped. If conditions 3–4 fail, the exact independent result is retained as null/adverse. No threshold/reference/graph rescue is permitted after Table S1 is opened.

## Coordinate sensitivity

Primary results always use the frozen coordinates.

A predeclared sensitivity may perturb one node at a time to the eight compass directions at the frozen radius recorded in `population_coordinates.csv`:

- ordinary island centroid: 5 km;
- mainland town centroid: 3 km;
- large-island/archipelago representative: 10 km.

No perturbation replaces the primary coordinate set, and no perturbation is selected based on better genetic fit.

## Claim boundary

This candidate tests whether the exact-eventual EOG construction adds held-out information beyond geography/current-flow in an independent land-bridge archipelago system with exact published pairwise FST.

Pairwise FST is symmetric and cannot validate migration direction. A null/adverse/indeterminate result remains visible and blocks a strong empirical-genetic promotion claim from this dataset.
