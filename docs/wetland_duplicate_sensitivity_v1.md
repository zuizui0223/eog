# Wetland duplicate-ID sensitivity: source-level descriptive detection bounds

## Scientific question and evidence source

This is a **post-exposure exploratory sensitivity audit**, not an independent validation or an occupancy analysis. Source: Mizsei, Edvárd & Wenner, Bálint (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, Zenodo 10.5281/zenodo.15044115 (CC BY 4.0). The immutable source is `zuizui0223/frogcs` commit `5e2f0a87c639df373fa2700b29403d2ab417a1cc`, verified by native CSV SHA256 in the existing duplicate gate.

The paper describes **27** analyzed wetland sites (13 restoration, 6 controls, 8 artificial) while the source CSV contains **29** (13 intervention, 7 control, 9 artificial). **This roster discrepancy is now resolved from the author's actual MD5-verified R scripts**: the Q1 script removes `kis-banyato` and `vadasz-turjan` (27 sites; 351 raw survey rows); the Q2 script keeps only `ci == "intervention"` (13 sites; 188 rows). Both scripts set `reps <- 20`, call `hunviphab::survreps` to construct their detection matrices, and renumber retained rows within each site as `n`. This documents the published processing, **not** whether the two same-ID raw rows are truly independent field replicates. The source itself does not establish that duplicated `surv` keys correspond to two physical traps, a corrected record or another process.

## Computation

Source dimensions: 381 rows, 379 unique survey IDs, 29 site records, nine species. Two source-ID collisions are zero-species-count versus positive-species-count pairs. This is **not** a proposal to select one or discard a recorded observation.

Enumerate all four possible one-row-per-conflicting-ID *hypothetical* resolutions, leaving other rows unchanged. For each resolution, calculate positive observed detection indicators at three nested grains, without equating non-detection to ecological absence:

1. wetland site × species;
2. wetland site × survey method × species;
3. native survey ID × species.

Report only indicators that can change across the four conditional interpretations. Do not fit an occupancy or count likelihood. The four resolutions do not include every possible real sampling process (e.g. two physically distinct traps), so invariance is strictly conditional.

## Actual source computation (four row-resolution scenarios)

Author-script cohort sensitivity:

| Cohort | Sites | Raw survey rows | Ambiguous site×species | Ambiguous site×method×species | Ambiguous survey×species |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archived source | 29 | 381 | 0 | 1 | 5 |
| Original Q1 analysis | 27 | 351 | 0 | 1 | 5 |
| Original Q2 analysis | 13 | 188 | 0 | 1 | 5 |

These are derived under the same two explicit one-row-per-conflict interpretations; they are *not* evidence of actual independent detector units, nor estimates of latent site occupancy.

## Original 29-site archive

| Grain | Number of ambiguous observed positive indicators |
| --- | ---: |
| Site × species | **0** |
| Site × method × species | **1** |
| Native survey ID × species | **5** |

The single site×method ambiguity is `feneketlen-turjan|bottletrap|Pelobates fuscus`. The five survey×species ambiguities occur at the two preidentified survey IDs; they cover four species at `feneketlen-turjan:bottletrap:89` and `Pelobates fuscus` at `tengelyut-2:bottletrap:118`.

**Defensible positive:** Site-level *recorded detection presence* among the 29 archived sites for nine named amphibians is invariant to the two conflicting native survey-ID resolutions. This does not resolve the published 27-site roster or validate site-level ecological/management effects.

**Still blocked:** A rowwise repeated-detection likelihood, constant effort, seasonal closure, treatment effects, latent occupancy, and identification of independently observed abiotic A / biotic B / movement M remain unsupported. Site-level invariance cannot be extended to the detection process or to historical connectivity.

## Reproduction and certification

The executable is `benchmarks/wetland_duplicate_bounds_v1.py`, with synthetic fail-closed tests in `tests/test_wetland_duplicate_bounds_v1.py`. The updated wetland PR workflow retrieves the pinned source files, authenticates both SHA256 values, executes the pre-existing identity block and the new four-scenario sensitivity, checks **0/1/5**, and uploads both machine-readable outputs. This is an exact enumeration of four *declared* row-resolution scenarios, **not** a universal all-process certificate.

An existing earlier result receipt continues to describe the prior duplicate-source gate and is not rewritten with post-exposure findings. The workflow artifact for this extension has its own fingerprint.

## Next external dependency

Original field sampling records or the source authors' R cleaning semantics must establish whether the duplicated `surv` rows are independently sampled traps, overwritten/corrected rows, or transcription artifacts. The published Q1/Q2 site rosters have been identified from the official R scripts, but independent field sampling-unit documentation remains needed before treating same-ID rows as independent occasions. The original script's 20-replicate preparation also needs methodological verification before any EOG occupancy refit. After identity and roster resolution, verify repeated-visit effort, closure, method-specific detection and independently measured ecological axes before considering an EOG×BAM field test.


## Source-code readback receipt

Two original R scripts were acquired directly from Zenodo 15044115 on GitHub Actions run 43584093845, with full MD5 equality against the official record (Q1 `fcab406cd8a192a07cc97582c19011ad`; Q2 `a2b2f6a30b7243c4b9ece3b5eb75dba6`). Neither script was executed. The row exclusion/selection, `reps=20` and `survreps` calls are visible in source lines 23–33. R-code readback is a source-provenance result, not field-method adjudication; the main substantive 0/1/5 sensitivity was subsequently verified on the two published cohorts under the fixed frozen-source inputs.
