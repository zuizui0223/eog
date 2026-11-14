# Wetland duplicate-ID sensitivity: source-level descriptive detection bounds

## Scientific question and evidence source

This is a **post-exposure exploratory sensitivity audit**, not an independent validation or an occupancy analysis. Source: Mizsei, Edvárd & Wenner, Bálint (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, Zenodo 10.5281/zenodo.15044115 (CC BY 4.0). The immutable source is `zuizui0223/frogcs` commit `5e2f0a87c639df373fa2700b29403d2ab417a1cc`, verified by native CSV SHA256 in the existing duplicate gate.

The publication describes surveys at 13 restored sites, 6 nonrestored sites and 8 artificial ditches (**27**). The archived native site table has **29 site rows** (13 intervention, 7 control, 9 artificial). We cannot assign the two extra archive sites to an exclusion category or infer which were analyzed by the published MSOM without verifying the original R preparation code. The publication says that survey methods were treated as distinct replicates, but that does **not** adjudicate two source rows bearing the **same site, date, method, num, weather and `surv` ID** while having contradictory species counts. The native published code files are listed on Zenodo; their data-cleaning transformations were not independently verified in this audit.

## Computation

Source dimensions: 381 rows, 379 unique survey IDs, 29 site records, nine species. Two source-ID collisions are zero-species-count versus positive-species-count pairs. This is **not** a proposal to select one or discard a recorded observation.

Enumerate all four possible one-row-per-conflicting-ID *hypothetical* resolutions, leaving other rows unchanged. For each resolution, calculate positive observed detection indicators at three nested grains, without equating non-detection to ecological absence:

1. wetland site × species;
2. wetland site × survey method × species;
3. native survey ID × species.

Report only indicators that can change across the four conditional interpretations. Do not fit an occupancy or count likelihood. The four resolutions do not include every possible real sampling process (e.g. two physically distinct traps), so invariance is strictly conditional.

## Actual source computation (four row-resolution scenarios)

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

Original field sampling records or the source authors' R cleaning semantics must establish whether the duplicated `surv` rows are independently sampled traps, overwritten/corrected rows, or transcription artifacts. The published 27 versus archived 29 site roster must also be reconciled before interpreting the original occupancy/management contrasts. After identity and roster resolution, verify repeated-visit effort, closure, method-specific detection and independently measured ecological axes before considering an EOG×BAM field test.
