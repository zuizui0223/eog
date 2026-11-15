# Wetland source-to-matrix parity: native counts, original ylist binarization, and duplicated pseudo-occasions

## Purpose and evidence grain

This is a **post-exposure source-method audit** extending EOG Draft PR #697, not a new prospective ecological test or an EOG-WF fourth prediction endpoint. It tests exactly how observed raw amphibian counts are transported from the original survey CSV into the 20 pseudo-repeat matrices in the published R analysis.

Original study: Mizsei & Wenner (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, data and published R scripts at [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. Raw surveys and sites are pinned by SHA256 to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`; original Q1/Q2 R scripts were independently MD5 authenticated.

The model-stage reproduction uses R 4.4.3, seed=123, and *exact source* `edvardmizsei/hunviphab@25d4c64da289ffcc14679619bb3b18bd494de872`, including `survreps` blob `ae7de0753faa1660b9e1ce1bc81b8cdb39a9c670` and `nmixmatrix` blob `40e0f5547cd67729e1c6d46d29a0ce2b75712a3a`. These pinned sources are public and authentic; authors' actual historical R installation is not yet verified.

## Exact stage-by-stage transformation

1. The Q1 script excludes `kis-banyato` and `vadasz-turjan` (27 sites), while Q2 selects only `ci == intervention` (13 sites).
2. Both set `season=1`, `X0=1`, `reps=20`, then use `survreps` to select source rows with replacement at 26/27 Q1 sites and 12/13 Q2 sites.
3. The published R code constructs nine species-specific site×20 count matrices using `nmixmatrix`.
4. **Verified original model-input transformation:** Q1 lines 65–73 and Q2 lines 68–76 set every species count above 1 to 1; both then create `ylist` and pass it to `unmarkedFrameOccuMulti` (Q1 line 95; Q2 line 94). Therefore raw counts greater than one are *not* used as numerical counts in the final binary occupancy detection input.

The new R stage replays `nmixmatrix` from authenticated original source and writes every site×pseudo-repeat×species raw count, source-row ID, method and date to an auditable long table. An independent Python gate checks each matrix entry against the exact source CSV and the frozen seed123 row mapping.

## Verified Q1/Q2 matrix properties

| Quantity | Q1 (27 sites) | Q2 (13 intervention sites) |
| --- | ---: | ---: |
| Source survey rows | 351 | 188 |
| R pseudo-occasion rows | 540 | 260 |
| R 9-species matrix cells verified | **4,860** | **2,340** |
| Positive raw count matrix cells | 750 | 440 |
| Original count cells above 1, binary-clipped for `ylist` | **445** | **294** |
| Source-count-to-R-`nmixmatrix` mismatches | **0** | **0** |
| Distinct native source rows selected | 287 | 153 |
| Repeated positions of already-selected native rows | **253** | **107** |
| Native-positive site×species pairs lost after sampling | **3** | **6** |

Model matrices have been audited at the preparation stage only. `unmarked` itself has not been fit in this EOG experiment.

### Row repetition concentration is not independently measured survey effort

The number of times an original row was selected at a site is `w_i`. The descriptive concentration-equivalent row count is

`N_Kish = (sum_i w_i)^2 / sum_i(w_i^2)`.

| Duplicate-weight diagnostic | Q1 | Q2 |
| --- | ---: | ---: |
| Site-average Kish concentration equivalent | **8.6544** | **9.8967** |
| Sum of site values | 233.6682 | 128.6567 |
| Ratio of sum to nominal pseudo rows | 0.4327 | 0.4948 |

This is **not** an estimated inferential effective sample size or a real number of independently surveyed traps/dates. It reflects only repeated weights of identical *CSV source rows* and does not include temporal, field-method or spatial dependence. A count of 20 output rows is not evidence of 20 independent field observations.

### Observation-method representation after sampling

| Recorded method | Q1 pseudo-row positions | Q2 pseudo-row positions |
| --- | ---: | ---: |
| Acoustic | 167 | 66 |
| Visual | 188 | 95 |
| Dipnet | 95 | 40 |
| Bottletrap | 90 | 59 |

Method and weather/date covariates follow the selected rows. The same native observation may therefore appear repeatedly with identical covariates and detection outcome.

## Strongest supported conclusion

The observed *binary detection label* passed into the original R `ylist` can be reproduced exactly at the source-processing stage: first, the choice of input cohort changes the R RNG draw stream and can change the selected source rows; then the `nmixmatrix` output retains native count values without a mismatch, and the original code converts all nine species to 0/1 before `unmarkedFrameOccuMulti`.

The avoidable ambiguity is **not a count-versus-binary coding error**. It is that *the 20 pseudo-repeat rows are not established as 20 independent actual field occasions, and rare original positives can be absent from one particular resample*. In the seed123 replay, 3 source-positive site×species pairs are omitted in Q1 and 6 in Q2. Across the common 13 sites, 7 pseudo-detection labels differ between the Q1 and Q2 preparation streams despite unchanged original observations.

## Claims explicitly withheld

- The historical R/package runtime, realized published row selections, and all original fitted coefficients have not been independently reproduced.
- The per-site mixture of multiple methods and within-site trap/date effort cannot be treated as verified exchangeable independent sampling occasions from the CSV alone.
- The `surv` key is exactly `site:method:day-of-year` in 381/381 original rows and is not a physical unique trap ID; two same-key bottletrap rows do not by themselves prove data corruption.
- No estimation of the magnitude or sign of bias in `unmarked::occuMulti` likelihood, management association or ecological A/B/M mechanisms follows without an appropriately justified field-observation unit and model refit.
- The EOG-WF mainline remains scientifically closed at the original three scored predictive endpoints, unaffected by this source-method audit.

## Reproduce

- Protocol: `validation/wetland_nmixmatrix_stage_v1/protocol.json`
- R matrix audit: `benchmarks/wetland_nmixmatrix_stage_v1.R`
- Independent Python parity/weighting: `benchmarks/wetland_nmixmatrix_stage_v1.py`
- Negative-control tests: `tests/test_wetland_nmixmatrix_stage_v1.py`
- Source-only nine-species binary ylist verification: `benchmarks/wetland_original_code_preflight_v1.py`
- Success run [#43673410145](https://github.com/zuizui0223/eog/actions/runs/43673410145), artifact 14144844219, ZIP digest `sha256:65ebbb9e7127c419262c558b1ec5e7147fbed5d353ac9384745759d10c2b437d`. This run certifies the R `nmixmatrix` stage; later source code verification separately certifies the original binary ylist conversion.
