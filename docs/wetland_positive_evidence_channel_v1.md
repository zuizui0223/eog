# EOG: source-anchored positive evidence through an imperfect preprocessing channel

## Verified outcome (2026-11-15)

This is a **retrospective observation-process/data-provenance audit**, not a new independent biological result. It asks how reliably the original recorded positive evidence survives the published wetland amphibian data-preparation algorithm, and what can legitimately be claimed by EOG's **positive-only, fixed-support world-compatibility rule**.

Original 2024 Hungary wetland source: Mizsei & Wenner (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, [Zenodo DOI 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0; original survey and site files pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

The processing evidence is the **complete 256-seed result** from fixed integers `1..256`, authentic public `hunviphab::survreps` (Git commit `25d4c64da289ffcc14679619bb3b18bd494de872`), R 4.4.3. The paired source-positive record table `seed_ensemble_native_positive_pairs.csv` contains **56,576 observations of algorithmic outcomes** (256 × (144 Q1 + 77 Q2)); it is not 56,576 ecological field observations or statistically independent replicates. Its independently authenticated SHA256 is `3ba582b5fbbdaa0e6c6f89cb70bb640cba9e56e50bc0ca187a223f81c0a45ae6`.

## What remains when 256 different preprocessing seeds are used?

Define a site×species pair as source-positive when at least one original recorded survey row has a positive species count. The original native positives are `O_raw`. After source-row selection under seed `r`, the remaining positive mask is `S_r`.

| Source-confirmed positive site×species evidence | Original Q1: 27 sites | Original Q2: 13 intervention sites |
| --- | ---: | ---: |
| Original recorded positive pairs | **144** | **77** |
| Detected after *every* one of 256 preprocessing seeds | **59 (41.0%)** | **35 (45.5%)** |
| Lost in ≥1 seed and detected in ≥1 other seed | **85 (59.0%)** | **42 (54.5%)** |
| Lost in *all* 256 seeds | **0** | **0** |
| Seeds with ≥1 source-positive pair lost | **256/256** | **254/256** |

The intersection over 256 seeds is a **finite-grid stability summary**, not a universal guarantee for arbitrary unseen seeds. The union of these 256 pseudo-positive masks happened to cover all source-positive pairs, but must **not** replace checking actual native source evidence.

### Species-level sensitivity (post-exposure descriptive)

| Species | Q1 source-positive sites | Q1 variable sites | Q2 source-positive sites | Q2 variable sites |
| --- | ---: | ---: | ---: | ---: |
| *Triturus dobrogicus* | 7 | 6 | 4 | 3 |
| *Bufotes viridis* | 11 | 10 | 7 | 6 |
| *Pelophylax ridibundus* | 18 | 15 | 10 | 9 |
| *Bombina bombina* | 18 | 15 | 12 | 10 |
| *Hyla arborea* | 24 | 4 | 12 | 0 |

The comparisons reflect species-specific **source-record detection frequency and data preparation**, not differences in true distribution, ecological suitability, extinction, species interactions, or the biological meaning of island/continental occupancy. For example, a recorded positive occurring in only one native row can disappear under source-row resampling even if the species really occurred at the site.

## What EOG can prove without inventing ecological worlds

Let `U` be a finite declared universe of worlds with **fixed** world-positive-support sets, **fixed** sources, and rules unchanged as evidence is processed. For an observed positive set `O`:

`W(O) = {w in U : O is contained in the positive-support set of w}`.

Because every sampled selected source row comes from the original table:

`S_r subseteq O_raw` for each of the 256 tested seeds.

Therefore **under this fixed-support compatibility policy**:

`W(O_raw) subseteq W(S_r)`.

Losing positive observations **weakens positive-only world exclusion**: a sampled dataset cannot rule out more of the fixed worlds solely by omitting native-positive constraints. A source-anchored registry restores `O_raw = S_r union (O_raw minus S_r)` exactly in all 256 checked seeds.

### Different, equally important, invalid procedure

If a downstream analyst instead interprets the processed zero at a *native source-positive* site×species as confirmed ecological absence, each member of `O_raw minus S_r` becomes a direct contradiction of recorded source evidence. The number of such potential contradictions is the number of omitted positive pairs (Q1: 3–19, Q2: 0–11 in the fixed 256 seeds). **These are not counts of real ecological worlds incorrectly eliminated**: that would require a predeclared and independently defensible ecological world universe and a validated absence-observation model.

The positive-set inclusion is **not automatically valid** if the inference operator changes its sources, support masks, calibration, world universe or fit when input occurrences change, for example under EOG's self-excluded source diagnostics. This audit does not certify those evidence-dependent operators.

## Claim boundary and why it matters

The native `surv` string is a `site:method:day-of-year` grouping key, not a validated unique physical trap or independent repeat identifier. The published Q1/Q2 R scripts clip each species' count `>1` to binary 1 before `unmarkedFrameOccuMulti`; the source problem **is not** a count-versus-binary coding mistake. Rather, a separately sampled 20-row pseudo-occasion representation can omit source-positive detections and reproduce certain original rows repeatedly.

The analysis does **not** identify:

- an independently observed abiotic/biotic/movement (`A/B/M`) world family or the historical route of any amphibian;
- verified absence, a true number of compatible ecological worlds, or a quantitative field-occurrence probability;
- physical trap identity/effort, season closure, the historical installed R+`hunviphab` version or original fitted occupancy coefficients;
- any fourth EOG-WF predictive endpoint or generic forecasting superiority.

## Executable source contract and evidence

- Fixed post-exposure protocol: `validation/wetland_positive_evidence_channel_v1/protocol.json`
- Source-anchored deterministic reanalysis: `benchmarks/wetland_positive_evidence_channel_v1.py`
- Unit tests, including a tiny **mathematical** positive-world example and fail-closed source table controls: `tests/test_wetland_positive_evidence_channel_v1.py`
- Machine-readable receipt: `validation/wetland_positive_evidence_channel_v1/result_receipt.json`
- Pre-existing source-pinned R/seed data generator: `benchmarks/wetland_seed_ensemble_v1.R`, independent source adjudication of the complete seed roster via `benchmarks/wetland_seed_ensemble_v1.py`

Reproducible run: [GitHub Actions #43675880722](https://github.com/zuizui0223/eog/actions/runs/43675880722), **SUCCESS**. Result fingerprint `2920331b3510e48cffb5420bf17984cd3c6d67bf8bb46af8c32cac54f74f062b`; GitHub artifact ID **14146397548**, ZIP SHA256 `5832468923bb8c1243b88850e47e02bba1135ee974d260e94cfeeaa1a02f1974`. Original complete 256-seed fixed-data run [#43674891349](https://github.com/zuizui0223/eog/actions/runs/43674891349) is retained separately.

**Decision:** Retain source-positive occurrence evidence as an immutable constraint registry, never let a resampling or standardization output overwrite confirmed source positives, and maintain explicit `unknown` versus `observed absent` states. The source evidence can support compatibility checks but not field occupancy or mechanisms without additional measurements.
