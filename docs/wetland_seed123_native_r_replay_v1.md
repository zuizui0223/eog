# EOG wetland audit — native R seed-123 sampling and analyst-cohort dependence

## Main result

This is a **post-exposure methodological replication of the 20-row survey-preparation stage**, using original CC BY 4.0 survey/site CSVs and the pinned public `hunviphab::survreps` source. It is **not** a replication of the original `unmarked::occuMulti` fit, a field occupancy estimate, or an EOG-WF fourth endpoint.

**Scientific source:** Mizsei, Edvárd & Wenner, Bálint (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, Zenodo DOI [10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115). Source branch commit `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`. Original Q1 and Q2 R script MD5s `fcab406cd8a192a07cc97582c19011ad` and `a2b2f6a30b7243c4b9ece3b5eb75dba6` confirmed in previous source-only CI. The original scripts both call `set.seed(123)` at line 2.

**Replay environment:** R 4.4.3 (2025-02-28), `Mersenne-Twister / Inversion / Rejection`, `seed=123`, `survreps` from public `edvardmizsei/hunviphab@25d4c64da289ffcc14679619bb3b18bd494de872` (file Git blob `ae7de0753faa1660b9e1ce1bc81b8cdb39a9c670`). This upstream implementation dates from December 2022, preceding the 2025 dataset publication. The installed package and actual R runtime used in the published analysis have **not** been independently identified.

The replay follows the original pre-sampling steps: `read.csv`, original Q1/Q2 site filters, `season=1`, `X0=1` for every survey row, `reps=20`, then authentic `survreps(df,"X0","season","site",20)`. A new source-row ID column is metadata only; it consumes no random numbers or selection logic.

## Verified native-record versus sampled-record outcomes

| Metric | Published Q1 (27 sites) | Published Q2 (13 intervention sites) |
| --- | ---: | ---: |
| Original survey rows | 351 | 188 |
| Output 20-row positions | 540 | 260 |
| Distinct original survey rows actually represented | **287** | **153** |
| Repeated positions of an already represented original row | **253 (46.9%)** | **107 (41.2%)** |
| Native-positive site×species pairs | 144 | 77 |
| Seed-123 replay-positive site×species pairs | **141** | **71** |
| Native-positive site×species pairs lost completely | **3 (2.1%)** | **6 (7.8%)** |
| Analytical expectation across random draws (prior exact audit; not the realized outcome) | 9.475863 | 4.871441 |

Rows reused after their first selection are **not new independent field visits**. The fractions describe algorithmically duplicated source rows only; they do not estimate bias in the original fitted likelihood.

### Exact pairs lost after R sampling

**Q1 (3):** `alsopeszer_3` — *Pelobates fuscus*; `baracsi-csatorna` — *Bombina bombina* and *Lissotriton vulgaris*.

**Q2 (6):** `alsopeszer_2` — *Bufotes viridis* and *Pelophylax ridibundus*; `hancsik-also` — *Bufotes viridis*; `hancsik-felso` — *Bombina bombina* and *Bufotes viridis*; `lato-hegy` — *Bombina bombina*.

These are losses from one deterministic replayed preprocessing representation, **not evidence that the species were absent**.

## Cohort-only processing changes the same site's apparent detection

All Q2 sites are contained within Q1. The native source evidence for those 13 sites is identical in both original subsets. Despite `set.seed(123)` in both scripts, filtering to the Q2 cohort changes the sequence of R random-number draws.

- **0/13 shared sites** retain the exact same ordered 20-row selection.
- **0/13 shared sites** retain even the same *set* of unique selected native source rows.
- **7 site×species detection indicators differ** after the two replay representations, despite unchanged native source-positive evidence.

| Original site | Species | Q1 sampled detection | Q2 sampled detection |
| --- | --- | --- | --- |
| alsopeszer_2 | *Bufotes viridis* | Present | Not detected |
| alsopeszer_2 | *Pelophylax ridibundus* | Present | Not detected |
| alsopeszer_3 | *Pelobates fuscus* | Not detected | Present |
| hancsik-also | *Bufotes viridis* | Present | Not detected |
| hancsik-felso | *Bombina bombina* | Present | Not detected |
| hancsik-felso | *Bufotes viridis* | Present | Not detected |
| lato-hegy | *Bombina bombina* | Present | Not detected |

**Interpretation:** Changing the analyst's cohort filter can change pseudo-detection evidence for the **same place, same species, same original field records, and same seed**. This is representation dependence, not species turnover, changing ecology or a novel population-level process.

## Independent execution check

- First source-authenticated R execution: [Actions #43671471822](https://github.com/zuizui0223/eog/actions/runs/43671471822) — **SUCCESS**; artifact 14144356728; ZIP digest `sha256:166bb71adb6e921508b496c4e5ca1fe454db3d6d766bd2cc9c517ea9ee671442`.
- Second R execution, adding post-result cross-cohort regression auditing: [Actions #43671749950](https://github.com/zuizui0223/eog/actions/runs/43671749950) — **SUCCESS**; artifact 14144014887; ZIP digest `sha256:2e477412063c4fbf98abe8108a547aa9ce20964d59933eba36af61ad1b9dc1dd`.
- **All four R-authored data outputs were byte-identical** across the two executions: both Q1/Q2 source-row mapping CSVs and both R runtime metadata files.
- Q1 mapping SHA256 `06554191c02c94d1f08a0d0bf88b1383db633de2785e59e295f69ee6e01821ff`; Q2 `bb2c6cd855ab9bb1d72c0380a86edd90a78c8e02cf466208fce6cd392398dc26`.
- Final machine-readable result fingerprint `0eae2061fc082031402122759c5ef1b9a76d6373839a86132d8ad71ef60983f0`.

Protocol: `validation/wetland_survreps_seed123_replay_v1/protocol.json`. Exact native R runner: `benchmarks/wetland_survreps_seed123_replay_v1.R`. Strict mapping reconciliation: `benchmarks/wetland_survreps_seed123_evaluate_v1.py`. Synthetic negative-control tests: `tests/test_wetland_survreps_seed123_evaluate_v1.py`.

## Inference limits and next scientific dependency

1. **The historical published R installation is not verified.** This is a *pinned public package stage* replay, not proof of the actual original realized draws, final occupancy coefficients, treatment contrasts or AIC.
2. **The two conflicting native `surv` identifiers remain unadjudicated.** Both conflicting source rows are preserved in this replay to reproduce the archived CSV; no one-row reconciliation was imposed.
3. **The row-multiplicity problem may invalidate an independence assumption if a downstream likelihood treats pseudo-rows as independent visits.** This audit has not executed or evaluated the historical occupancy model, so it does not establish the magnitude/direction of any coefficient bias.
4. **For EOG**, source-positive evidence should be audited at its original observation grain. The same native-positive source site may be incorrectly treated as unobserved (or, still worse, as a false absence) after arbitrary sampling. Finite-world elimination strength must never exceed authentic evidence strength.
5. **No causal A/B/M result, external independent biogeographic forecast validation or reopened EOG-WF 3/31/3 evidence** is implied.

A faithful biological reanalysis would require adjudicated physical observation units, method-specific effort and closure metadata, and the historical R/package environment, before fitting any occupancy model. Until these are available, the defensible output is a source-verified descriptive detection/processing sensitivity result with exact code and provenance.
