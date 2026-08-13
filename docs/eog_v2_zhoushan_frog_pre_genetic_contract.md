# EOG v2 Zhoushan pond-frog independent genetic validation contract

## Status

**Stage-2 predictors are irreversibly frozen. Exact genetic-response access is now permitted only through the predeclared routes below.**

Candidate study: Wang et al. (2014), *Population size and time since island isolation determine genetic diversity loss in insular frog populations*, Molecular Ecology 23:637–648, DOI `10.1111/mec.12634`.

Public non-genetic/genetic mirror: Zenodo record `5012316`, corresponding to Dryad DOI `10.5061/dryad.dq4g5`.

Relevant released files are deliberately separated by stage:

- `Raw transects .xlsx` — response-free field-survey metadata;
- Wiley Supporting Information `Table S1` (`mec12634-sup-0001-TableS1.xlsx`) — published exact pairwise FST response;
- Zenodo/Dryad `Microsatellite data.xls` — raw nine-locus genotype fallback/replication source.

The published article-level narrative was already known, so this is not claimed to be publication-blinded. The prospective firewall is narrower and auditable: **exact pairwise FST values and raw genotypes were not accessed until nodes, coordinates, graph, EOG predictors, reference model, response transform and promotion rule were frozen and byte-archived.**

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

The final coordinate-selection hierarchy and all 27 selected representative points are frozen in:

- `docs/eog_v2_zhoushan_frog_coordinate_freeze.md`;
- `benchmarks/frozen/zhoushan_frog_response_free/population_coordinates.csv`.

The nodes represent population/site locations at island/site scale, not asserted individual frog capture coordinates. The source paper states that transects covered accessible habitat across each island/site.

## Stage 2 — response-free predictor freeze — COMPLETE

A complete 351-pair predictor table was generated and archived before any exact FST value or raw genotype was opened.

Authoritative pre-response artifact:

- workflow run `31655358037`;
- workflow head `4e604d86f60e0815c7d39e78b31d137ad5689206`;
- artifact ID `9164198982`;
- artifact digest `sha256:60f0cb0eff61a0af15a2e2d0a8d107c0f334a5597d73ea3de2c4691f04f6dcb1`;
- predictor-manifest fingerprint `e0a18112d9adfd197958b3e0e1cd1043485055425371b073f2cb74ad917ead70`.

The artifact was then committed byte-for-byte to `benchmarks/frozen/zhoushan_frog_response_free/` by one-time archival workflow `31655603171`; it is not regenerated after response visibility.

### Geographic predictors

- great-circle geographic distance in km;
- parameter-free Gabriel graph in a local tangent plane;
- edge support `exp(-d / median_Gabriel_edge_length)`;
- `loss_support = 0.5`;
- effective-resistance/current-flow distance on the same response-free conductance graph.

### EOG predictor

The already-confirmed exact-eventual genetic construction is frozen on the same sub-stochastic operator:

- reciprocal eventual support averaged in support space;
- continuous connected-pair distance `-log(exchange support)`;
- explicit disconnection indicator;
- no finite propagation horizon;
- no numerical support-floor hyperparameter;
- no fitted symmetrisation parameter.

### IBE boundary

No environmental predictor is invented. `environmental_distance = 0` for all pairs and IBE is explicitly **non-applicable**.

Frozen identities include:

- populations CSV SHA-256 `a540a3d2ec6dd9b74a2ed80bc040d649cb179ec89e0e60ad87f3e529e96cf6f5`;
- predictors CSV SHA-256 `dd14cacf10ce39442977b6b68ae7fc45ced7ae78e458e4feb8338fadd138d7d9`;
- coordinate fingerprint `decfa791f879c38dd6168240684383b01e2f2ab730de8c36575291c622a4e794`;
- operator fingerprint `242d251353d1180d9a39a8698969246264e65a3ba9b6ad3c0a5a3fc3259369df`;
- exact-eventual connectivity fingerprint `2822fbd07b22d4a6f77123077f49f660e99a9641da6cecbf44203b45b5ffefb9`.

## Stage 3 — exact genetic response attachment

### Route A — published Wiley Table S1

The preferred response source is Wiley Supporting Information `mec12634-sup-0001-TableS1.xlsx`, described by Wiley as pairwise FST for all studied populations.

After Stage 2 was byte-frozen, two automated requests to the official Wiley supplement endpoint returned HTTP 403. The first used an incorrectly inferred supplement filename and the second used the corrected official filename. The corrected failure is a publisher transport failure, not a response/admission result.

No Table S1 numeric FST value has been read by EOG through this route.

### Route B — predeclared raw-genotype fallback

Because Route A is transport-blocked, `Microsatellite data.xls` from Zenodo/Dryad is now permitted **only after this contract amendment is committed and before that raw file is opened**.

The raw-genotype fallback must reproduce the estimator declared in the source paper:

- pairwise FST is Weir & Cockerham (1984) `theta`;
- the source paper used FSTAT version 2.9.3.2;
- all nine released microsatellite loci are retained;
- all 27 frozen populations are retained;
- no locus or population is selected from observed FST magnitude;
- missing diploid genotypes are excluded locus-wise/pair-wise rather than imputed;
- empty strings, explicit `NA`/`N/A`/`.` tokens, or non-positive allele codes are treated as missing only if the released schema uses them as missing codes;
- allele values are otherwise treated as categorical microsatellite alleles, not metric values;
- the across-locus pairwise Weir–Cockerham estimator is calculated from the released diploid genotypes without significance-based filtering;
- Bonferroni/permutation significance is not an EOG validation response;
- negative or `>=1` raw pairwise FST is **not clipped**. If any primary pair is outside `[0,1)`, the predeclared `FST/(1-FST)` response transform is non-admissible for that pair and the exact reason is retained rather than repaired post hoc.

Before FST is computed, a separate raw-file schema audit must record:

- raw file SHA-256 and released MD5 identity;
- workbook/sheet dimensions;
- row count and population labels/codes;
- the nine locus column groups / allele-pair encoding;
- missing-value tokens;
- whether all 27 frozen population identities can be mapped mechanically;
- total individual count, with the published study total of 810 used only as a provenance/integrity check.

The schema audit must not report pairwise FST values. If the genotype schema cannot be mapped mechanically to the 27 frozen nodes and nine loci, the raw fallback is a provenance NO-GO; mapping may not use clustering, FST, migration or allele similarity.

### Primary response identity under the fallback

If Route B passes the schema/provenance gate, the primary EOG response is the raw-genotype-derived Weir–Cockerham pairwise FST matrix. The unavailable Wiley Table S1 remains the preferred published cross-check if it later becomes lawfully retrievable; it does not become a tuning source.

Response transform remains frozen as:

`linearized_FST = FST / (1 - FST)`.

No response-model or graph setting changes because the response provenance changed from published table to source-paper-equivalent raw recomputation.

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

If condition 2 fails, status is `indeterminate_strong_reference_failure`; current flow is not dropped. If conditions 3–4 fail, the exact independent result is retained as null/adverse. No threshold/reference/graph rescue is permitted after raw genotypes are opened.

## Coordinate sensitivity

Primary results always use the frozen coordinates.

A predeclared sensitivity may perturb one node at a time to the eight compass directions at the frozen radius recorded in `population_coordinates.csv`:

- ordinary island centroid: 5 km;
- mainland town centroid: 3 km;
- large-island/archipelago representative: 10 km.

No perturbation replaces the primary coordinate set, and no perturbation is selected based on better genetic fit.

## Claim boundary

This candidate tests whether the exact-eventual EOG construction adds held-out information beyond geography/current-flow in an independent land-bridge archipelago system with exact neutral microsatellite FST.

Pairwise FST is symmetric and cannot validate migration direction. Table S2 asymmetric migration estimates remain out of scope. A null/adverse/indeterminate result remains visible and blocks a strong empirical-genetic promotion claim from this dataset.
