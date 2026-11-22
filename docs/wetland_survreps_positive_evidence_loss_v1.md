# Wetland amphibian monitoring: exact survey-row resampling and positive-evidence loss

## Result and scope

**Post-exposure methodological diagnostic, not a new independent biological result.** The original wetland study's Q1 and Q2 scripts were verified directly from Zenodo 10.5281/zenodo.15044115 (Mizsei & Wenner 2025; CC BY 4.0). Those scripts load the archived survey CSV, set `df$season <- 1`, set `df$X0 <- 1` for every source row, and pass `reps <- 20` into `survreps(df,"X0","season","site",reps)`. The Q1 script removes `kis-banyato` and `vadasz-turjan`; Q2 keeps `ci == "intervention"`.

Public upstream `edvardmizsei/hunviphab` at commit `25d4c64da289ffcc14679619bb3b18bd494de872`, blob `ae7de0753faa1660b9e1ce1bc81b8cdb39a9c670`, has the following `survreps` behavior under **constant X0=1**:

- If a site's native survey-row count `n <= 20`, sample **20 rows with replacement**.
- If `n > 20`, sample **20 rows without replacement**, since every row is a positive X0 row.
- Downstream `nmixmatrix` reads the resulting resampled row order and species counts into site×repeat matrices. This creates a 20-column input per site but not 20 independent physical survey occasions.

The original Q1 and Q2 R scripts each explicitly call **`set.seed(123)` on line 2** (MD5-authenticated source readback). This corrects a possible concern about an unstated script seed. The public package git object is pinned and audited in CI, but **the exact historical hunviphab installation and R version used by the authors have not been verified**, so the specific realized selection cannot yet be claimed as reproduced from the publication environment. No original R analysis or `unmarked` model was executed.

## Quantitative result with original unmodified data

| Source subset | Sites | Native rows | 20-row matrix rows | Sites sampled with replacement | Raw positive site×species pairs | Expected positive pairs lost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Q1 (all study wetlands) | 27 | 351 | 540 | **26/27** | **144** | **9.475863** |
| Q2 (intervention wetlands) | 13 | 188 | 260 | **12/13** | **77** | **4.871441** |
| Full archived CSV (not paper Q1/Q2) | 29 | 381 | 580 | 28/29 | 153 | 11.125239 |

Among the original study cohorts, **11 Q1** and **9 Q2** native-positive site×species pairs have a conditional probability at least 25% of losing all recorded positive survey rows during normalization. The greatest individual probability is **31.8807%** (one detected `Triturus dobrogicus` row out of 18 at `tengelyut-1`). This is *selection loss*, not a biological absence or field detection probability.

## Exact calculation

For one source site, let `n` be the number of native recorded survey rows and `k>=1` the number of rows with a positive observation of the target species. The source uses `r=20` normalized rows.

**When n <= 20, with replacement:**

`P(drop all k positive rows | n,k,r) = ((n-k)/n)^r`.

**When n > 20, without replacement:**

`P(drop all k positive rows | n,k,r) = C(n-k,r)/C(n,r)`, or zero if `n-k < r`.

The sum of these probabilities over native-positive site×species pairs is the expected number of lost positive indicators, not the number observed to be lost in the authors' actual random execution. Indicator losses across species at the same site are dependent because they share one row selection; the sum of expectations remains mathematically valid without independence.

### Source ambiguity does not explain the full effect

Two native survey identifiers have conflicting zero/nonzero count rows. Keeping just one hypothetical row from each conflict and enumerating the four cases (which is **not** field-source adjudication) gives:

| Cohort | Baseline original CSV | Four hypothetical source-row choices |
| --- | ---: | ---: |
| Q1 | 9.475863 | 9.403519–9.421496 |
| Q2 | 4.871441 | 4.799097–4.817074 |

The site×species *raw recorded presence* classification is invariant to these two native conflicts, as established in the earlier gate. The 20-row resampling can still drop raw positive rows under **every** scenario. The two issues are separate.

## What follows and what does not

**Supported source and algorithm finding:** Under the pinned public `survreps` implementation and the source-published preprocessing calls, randomly resampling uneven numbers of real records into 20 pseudo-occasions risks omitting recorded species detections. Models that interpret 20 resampled rows as 20 independent detection occasions do not automatically have the actual independent effort represented by those rows. In particular, an algorithmic zero after sampling cannot be read as a verified ecological absence.

**Not established:** The realized row selection from the authors' execution despite the declared `set.seed(123)` (R/runtime and package not independently reproduced), its exact `hunviphab` installation, any original occupancy coefficients, AIC, or significance changes; whether authors modeled resampled rows as statistically independent rather than describing a bootstrap-like approximation; whether treatment/habitat results change under a faithful raw-occasion analysis; or the true biological A/B/M mechanism.

For EOG, **positive-only world compatibility** must be conditioned on the native source evidence, not exclusively on a potentially lossy normalized table. Missing positive evidence weakens elimination of false worlds; incorrectly interpreting the resulting zeros as genuine negative evidence could instead cause unjustified world elimination. These are different error modes.

## Reproducibility

- Fixed-source original species/site inputs: `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, raw survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.
- Official published Q1/Q2 R MD5: `fcab406cd8a192a07cc97582c19011ad` and `a2b2f6a30b7243c4b9ece3b5eb75dba6`.
- Public `hunviphab::survreps` blob SHA-1: `ae7de0753faa1660b9e1ce1bc81b8cdb39a9c670`, commit `25d4c64da289ffcc14679619bb3b18bd494de872`.
- Protocol: `validation/wetland_survreps_evidence_v1/protocol.json` (post-exposure, expressly not preregistration).
- Executable: `benchmarks/wetland_survreps_evidence_loss_v1.py` and `tests/test_wetland_survreps_evidence_loss_v1.py`.
- Verified GitHub Actions: [run #43585874262](https://github.com/zuizui0223/eog/actions/runs/43585874262); output fingerprint `bf2fb6753860313b80c7241812d9eaa847a1415e9a1f654d30ee07f167fdc078`; artifact ID 14110067074; ZIP SHA256 `6758b47c5ea996448dd5d077435cacd2085cd9aeb1feee882a3ac04974505033`.
- A second [seed-audit workflow run #43586181277](https://github.com/zuizui0223/eog/actions/runs/43586181277) verified `set.seed(123)` at line 2 in **both** MD5-authenticated original scripts; artifact ID 14110482262 (ZIP SHA256 `f0d34d02c9ce0d910c77e8d22411121cfedafb4e3c3c8c92856cb13c0d21f2af`).
- Live original published and public package source **not** used as biological independent data or fourth EOG-WF endpoint.

## Correct next inferential test

An independent source-backed reanalysis would keep each genuinely distinct site×date×method×effort occasion once, handle within-visit method dependence, report effort and season closure, and compare the unaltered native observations against the publication sampling representation. Before doing so, resolve the two ambiguous same-ID sampling units and identify the author's actual package version and random seed. Restrict any new inference to source-justified A and/or measured habitat associations; movement M is not independently observed here. Do **not** use algorithmic resampling as evidence for a novel EOG prediction advantage.
