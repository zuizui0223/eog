# EOG v2 Zhoushan pond-frog independent exact genetic validation result

## Status

**Independent exact genetic validation — COMPLETED, INDETERMINATE STRONG-REFERENCE FAILURE.**

This is the first Zhoushan run that computed empirical pairwise genetic responses after the full 27-node / 351-pair response-free EOG predictor artifact, node coordinates, reference ladder, response transform and promotion rule had been frozen and byte-archived.

The result is retained exactly as observed. The predeclared current-flow reference is not dropped or replaced after seeing the result.

## One-time execution provenance

Authoritative run:

- workflow: `Zhoushan frog one-time independent genetic validation`;
- workflow run: `31656924070`;
- workflow head: `44839bdec13c7ea315079a2ece5728b7efbf5fe5`;
- result artifact ID: `9164737355`;
- artifact digest: `sha256:0dce3020b616a00c08ee602d5f1b44d5bc59f08ad753e8a989b51802d612633c`;
- result fingerprint: `585b4b6c3a616d353e3abcfd95b5c341cb4e022da012a8d72ad310ddb9ae48cd`.

Every workflow step passed:

1. Weir–Cockerham estimator boundary tests;
2. immutable pre-response predictor SHA/fingerprint verification;
3. raw-to-article mainland identity adapter verification;
4. raw workbook MD5/SHA verification;
5. exact raw FST calculation and frozen LOPO ladder;
6. result-contract verification;
7. raw genotype deletion before artifact upload.

An earlier workflow attempt stopped at Python module import before any pairwise FST was computed. It is not an empirical result.

## Frozen pre-response predictor provenance

The one-time run used the byte-identical Stage-2 artifact created before exact FST computation:

- pre-response workflow run `31655358037`;
- artifact ID `9164198982`;
- artifact digest `sha256:60f0cb0eff61a0af15a2e2d0a8d107c0f334a5597d73ea3de2c4691f04f6dcb1`;
- populations CSV SHA-256 `a540a3d2ec6dd9b74a2ed80bc040d649cb179ec89e0e60ad87f3e529e96cf6f5`;
- predictors CSV SHA-256 `dd14cacf10ce39442977b6b68ae7fc45ced7ae78e458e4feb8338fadd138d7d9`;
- predictor-manifest fingerprint `e0a18112d9adfd197958b3e0e1cd1043485055425371b073f2cb74ad917ead70`;
- coordinate fingerprint `decfa791f879c38dd6168240684383b01e2f2ab730de8c36575291c622a4e794`;
- operator fingerprint `242d251353d1180d9a39a8698969246264e65a3ba9b6ad3c0a5a3fc3259369df`;
- exact-eventual connectivity fingerprint `2822fbd07b22d4a6f77123077f49f660e99a9641da6cecbf44203b45b5ffefb9`.

These predictors were not regenerated after the raw genetic response was computed.

## Raw genetic response

Source: Zenodo/Dryad `Microsatellite data.xls`, Wang et al. (2014), DOI `10.1111/mec.12634`.

- raw MD5 `0f9d9b36bb0c481f41170ad2d6cc6344`;
- raw SHA-256 `52ee37e431aff3303d58685cfef064a7ee34cf0117f52eaca3889e21eacebb17`;
- 27 populations;
- 30 individuals per population;
- 810 individuals total;
- 9 microsatellite loci;
- `7290 = 810 × 9` complete diploid genotypes;
- zero missing diploid genotypes after parsing;
- zero partially missing allele pairs.

The mainland raw prefixes were mapped using the administrative identity adapter frozen before pairwise FST calculation:

- `Haining -> Yuanhua`;
- `Zhenhai -> Xiepu`;
- `Beilun -> Guoju`.

The 24 island prefixes map directly to the frozen island nodes.

## FST estimator and response admissibility

Pairwise neutral differentiation was recomputed from all nine loci using the predeclared Weir & Cockerham (1984) multilocus `theta` construction, matching the estimator family declared by the source paper.

No FST value was clipped.

All `351` unordered population pairs were finite and inside the predeclared linearization domain `[0,1)`:

- minimum FST: `0.02440864510`;
- maximum FST: `0.39484455318`;
- invalid/non-finite/out-of-domain pairs: `0`.

Therefore the frozen response transform

`linearized_FST = FST / (1 - FST)`

was admissible for the complete pair set.

## Frozen leave-one-population-out results

All pairs involving one held-out population were excluded from training for that fold. Lower MSE/MAE is better.

Because environmental distance was predeclared non-applicable and fixed to zero, `IBD+IBE` is numerically identical to IBD and `IBD+IBE+EOG` is the predeclared IBD+EOG secondary model.

| Model | Pooled LOPO MSE | Pooled LOPO MAE |
|---|---:|---:|
| IBD | `0.00996365409` | `0.07906704096` |
| IBD + EOG | `0.00965827101` | `0.07684598138` |
| Gabriel current flow | `0.30863559327` | `0.18357305484` |
| Gabriel current flow + EOG | `0.71358430966` | `0.23413989151` |

### Secondary IBD contrast

`IBD + EOG − IBD = -0.00030538308` pooled MSE.

The corresponding MAE difference is `-0.00222105958`.

IBD + EOG improved held-out-population MSE in `17/27` folds. This is retained as a descriptive secondary signal only; it does **not** satisfy or replace the predeclared strong-reference promotion gate.

### Primary strong-reference contrast

`current flow + EOG − current flow = +0.40494871639` pooled MSE.

The corresponding MAE difference is `+0.05056683667`.

Although current-flow + EOG improved MSE in `19/27` individual held-out-population folds, the effect was strongly heterogeneous and adverse in the equal-weight mean because of large failures in a small number of folds. In particular the Yuanhua-held-out MSE difference was approximately `+10.9550`.

The predeclared per-population primary inference was:

- mean MSE difference: `+0.40494871639`;
- median MSE difference: `-0.00125883087`;
- fraction of populations with negative difference: `0.7037037` (`19/27`);
- fixed bootstrap seed: `20260813`;
- bootstrap resamples: `10000`;
- 95% percentile interval: `[-0.00167662905, +1.21712400848]`.

## Predeclared decision checks

1. all 27 populations / 351 pairs represented — **PASS**;
2. current-flow strong-reference pooled MSE <= IBD pooled MSE — **FAIL** (`0.30864` vs `0.00996`);
3. mean population `(current flow + EOG) − current flow` MSE < 0 — **FAIL** (`+0.40495`);
4. bootstrap upper 95% bound < 0 — **FAIL** (`+1.21712`).

Therefore:

**`status = indeterminate_strong_reference_failure`**

**`promotion_go = false`**

## Interpretation

This dataset does **not** give EOG v2 a strong empirical-genetic added-information claim under the predeclared reference ladder.

The most important result is not that EOG simply failed everywhere. It is reference-dependent:

- adding exact-eventual EOG to straight-line IBD produced a small pooled predictive improvement;
- the predeclared Gabriel effective-resistance/current-flow reference performed dramatically worse than simple IBD;
- adding EOG to that failed strong reference was adverse in pooled error despite improving a majority of held-out populations;
- one or a few extrapolative mainland folds dominate the mean, which is visible rather than hidden by changing the reference after response access.

This is exactly the situation covered by the frozen contract: when the supposed strong conventional reference is not operationally competitive with IBD, the dataset-level promotion decision is **indeterminate strong-reference failure**, not a rescued EOG success against the weaker or better-performing alternative chosen after the fact.

The secondary IBD+EOG improvement can motivate a future independently frozen reference redesign, but it cannot be used to alter or rerun this confirmation result.

Symmetric FST remains invalid for testing migration direction.

## Consequence for EOG v2

The independent exact-genetic validation **execution gate is complete**, but the empirical-genetic **promotion gate is not passed**.

Any next genetic dataset or next-generation reference must be designed and frozen independently of this result. In particular, current-flow resistance scaling, graph topology, loss support, or the Yuanhua coordinate cannot be retuned on this dataset to convert the result into a GO.
