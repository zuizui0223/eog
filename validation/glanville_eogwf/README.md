# Glanville fritillary independent EOG-WF validation

## Final status

> **`completed_independent_heldout_prediction`**
>
> **exact world identity prediction: adverse**  
> **external predictive added value of the exact-identity head: adverse**

This is the first independent EOG-WF system to pass source/process, response-blind world-scale, structural-adequacy, temporal-split and response-estimability gates and then complete genuinely heldout ecological prediction.

The result does **not** support the product hypothesis that feeding exact world identity directly into a supervised forecast head improves prediction.

It does support a narrower architectural boundary:

> exact world identity remains useful as the latent state required for sequential rule contraction/falsification, while a predictive head should not assume that arbitrary world labels themselves are useful predictive features.

A future permutation-invariant/compressed predictive head must be validated on a **fresh independent system**. Glanville is frozen and must not be retuned to rescue that claim.

## Source

- taxon: *Melitaea cinxia* (Glanville fritillary);
- region: Åland Islands, Finland;
- Dryad DOI: `10.5061/dryad.ksn02v707`;
- stable transport mirror: Zenodo record `4987060`;
- archive: `ECOG-04799.zip`;
- archive MD5: `69122a1d82b1fb970fb6638b02da3db4`;
- archive SHA-256: `c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9`;
- frozen patch universe: **4,656 patches**.

The prediction target is **survey-recorded annual colonisation transition**. Survey zero is not promoted to latent biological absence.

## Gate 0 — source/schema/process closure PASS

Before population responses were opened, the source archive, schema and process interpretation were frozen.

The bundle separates:

- `patch_network.tsv` — patch ID, centroid coordinates and area;
- `patch_area.tsv` — annual patch area;
- `survey_data.tsv` — annual survey state including `population`.

The system passed the process/source-closure screen for a conditional regional patch-metapopulation forecast: annual local extinction and recolonisation are the scientific transition process, while complete closure to every possible immigrant outside Åland is not claimed.

Canonical evidence:

- `gate0_source_process_contract.json`
- `gate0_result.json`

## Gate 1 — response-blind world scale and structural adequacy PASS

The frozen node geometry was examined before population responses.

Externally supported process reference:

- `process_mean_dispersal_1km` — 1 km mean-dispersal reference, not a hard maximum;
- largest weak component at 1 km: **35.9966%**.

Response-blind analyst-choice structural ladder:

| world | threshold | LCC |
|---|---:|---:|
| `geo_lcc250` | 0.8413 km | 26.20% |
| `geo_lcc500` | 1.1528 km | 50.04% |
| `geo_lcc750` | 1.6080 km | 76.93% |
| `geo_lcc900` | 6.4184 km | 95.21% |

The 90% structural world had zero isolated nodes and passed the prospectively frozen structural gate.

Canonical evidence:

- `gate1_scale_adequacy_declaration.json`
- `gate1_result.json`

## Sequential source-state correction before response

Annual metapopulation prediction requires current sources to change each year while the transition rule remains frozen.

Before response access, EOG therefore added `src/eog/v2/sequential_world_forecast.py`, which separates:

- frozen transition-rule identity;
- current realised source state;
- cumulative surviving-rule state.

Past positive evidence is not incorrectly re-tested from later source states. Rule worlds can only remain or contract/falsify. Known-truth tests are in `tests/test_sequential_world_forecast.py`.

## Gate 2 — temporal and comparison contract PASS

Response-free metadata fixed the complete survey sequence at 1999–2018.

Calibration transitions:

`1999→2000` through `2011→2012` — **13 transitions**.

Heldout transitions:

`2012→2013` through `2017→2018` — **6 transitions**.

No prediction model is refit during heldout evaluation. Rule state may contract only after a heldout transition outcome has occurred.

Five frozen EOG rule worlds were used:

1. full exponential process world, raw support `exp(-d/1 km)`;
2. the same kernel truncated at 0.8413 km;
3. truncated at 1.1528 km;
4. truncated at 1.6080 km;
5. truncated at 6.4184 km.

External comparators were frozen before response access:

- IFM-style logistic model using target `area^0.2` and metapopulation connectivity `S_i`;
- fixed random forest using area, IFM connectivity, nearest occupied-source distance and occupied-source counts within 1 and 2 km.

The exact-identity model and the compressed-world model shared the same ecological baseline and each received 10 EOG-specific dimensions. Identity estimability was tested prospectively rather than assumed.

Canonical contracts:

- `gate2_temporal_prediction_contract.json`
- `gate2_amendment_v1_1.json`
- `gate2_temporal_metadata_result.json`
- `runtime_lock.txt`

## Pre-response runner validation PASS

The frozen runner was compiled and exercised on synthetic data before the population response was opened.

The first smoke run exposed only a dynamic-import harness problem; the scientific runner compiled successfully. The harness alone was corrected, and the repeated smoke plus package regression passed.

Evidence: `pre_response_runner_smoke_result.json`.

## Response-opening technical mapping stop and correction

The first response-opening workflow (`32017396835`) downloaded the exact source and stopped before transition/model/statistic evaluation because `survey_data.tsv` contained historical patch IDs outside the frozen 4,656-node `patch_network`.

A response-free ID-only audit then showed:

- survey rows outside frozen network: **755**;
- unique outside IDs: **417**;
- outside IDs with any `patch_area` record: **0**.

The already-frozen eligibility rule required finite positive source-year patch area. Therefore every outside survey ID was structurally ineligible independent of its population value.

The correction did **not** expand the node universe. A deterministic adapter filtered rows only by patch membership in the frozen network and copied retained rows verbatim. Unit tests verify that changing an excluded row's population value does not change the filtered dataset or audit.

Evidence:

- `postopen_id_mapping_audit_result.json`
- `postopen_mapping_correction_v1.json`
- `node_filter_audit.json`
- `tests/test_glanville_survey_node_filter.py`

## Authoritative independent result

Authoritative workflow run: **`32017872743`**  
Artifact ID: **`9284217174`**  
Artifact ZIP SHA-256: `2a1676ed04638bec8a92049d614b79f270a914480bd8c6194c5e66551a575572`  
Result fingerprint: **`628511ac3f42fe108d334a6458428bbf56f3c3fea1e753b2bee8d980b3d84c33`**

Calibration:

- rows: **35,217**;
- positive recorded colonisations: **3,287**;
- negatives: **31,930**.

Heldout:

- rows: **18,918**;
- positive recorded colonisations: **900**;
- negatives: **18,018**;
- all six heldout transitions contained both classes.

Identity beyond the declared compression was **estimable** in calibration (`max residual SD = 0.81584`). Thus the adverse result is not explained by a mathematically redundant identity design.

### Primary macro-year binary log loss

| model | macro-year log loss |
|---|---:|
| **world-set compression** | **0.187983** |
| random forest | 0.191725 |
| IFM logistic | 0.200242 |
| **exact world identity** | **0.230197** |

Exact identity minus compression:

`+0.042214` log-loss units — **worse**.

Exact identity beat compression in **0/6 heldout transitions**.

Exact identity beat the better external comparator in **1/6 transitions**.

Frozen decision statuses:

- `adverse_identity_predictive_value`
- `adverse_external_predictive_added_value`

Exact annual metrics are in `glanville_eogwf_annual_metrics.csv`.

## World-rule contraction result

The structural worlds were useful as falsifiable alternatives even though identity labels harmed prediction.

During calibration:

- `1999→2000` eliminated the 0.841, 1.153 and 1.608 km truncated worlds;
- `2010→2011` eliminated the 6.418 km truncated world;
- the full exponential process world survived;
- all six heldout forecasts therefore began with only `process_full_exp_alpha1` surviving.

This is the key architectural distinction:

> **exact world identities remain scientifically meaningful for rule survival/falsification, but their labels should not automatically be exposed as supervised predictive covariates.**

## What the result does and does not establish

Supported:

- the prospective gate sequence can reach an independent heldout forecast without post-outcome world retuning;
- frozen world alternatives can be sequentially falsified while a process world survives;
- exact identity contains information beyond the declared compression in calibration;
- nevertheless, the exact-identity predictive head is independently adverse on this system.

Not supported:

- exact world identity as a generally superior predictive representation;
- EOG-WF exact identity outperforming IFM/RF;
- historical route identification;
- calibrated colonisation probability from raw EOG support.

The compressed same-world representation had the best descriptive macro log loss among the frozen tested models, but **external superiority of compression was not the prospectively declared external endpoint**. It must not be retroactively promoted to a confirmed claim.

## Mainline consequence

The product architecture is narrowed prospectively:

1. **latent epistemic/update layer** — preserve exact frozen world/rule identity for compatibility filtering, contraction and finite-universe falsification;
2. **predictive layer** — use a world-label-invariant representation of the surviving support set rather than arbitrary exact world labels.

This two-layer architecture is a revision prompted by adverse independent evidence. It is **not yet independently validated** and must be tested on a fresh system without reusing Glanville as confirmation.

## No-rescue boundary

Do not:

- refit Glanville with new world thresholds or extra operators;
- replace the frozen temporal split;
- tune compression features on heldout results and call the rerun independent;
- remove the adverse identity result;
- claim that the descriptive superiority of compression confirms EOG vs external methods;
- reuse Glanville as the independent confirmation for the revised predictive head.

Glanville is now frozen evidence for narrowing EOG-WF's prediction architecture.
