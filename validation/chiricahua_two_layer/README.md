# Chiricahua leopard frog two-layer EOG-WF validation

## Final status

> **Gate 0 source/process/response semantics: PASS for a fixed-founder conditional design**
>
> **Gate 1 response-blind structural adequacy: PASS**
>
> **Gate 2 response-free implementation and synthetic smoke: PASS**
>
> **Once-only empirical outcome: `non_estimable_response_or_representation`**

The exact detection-history response was opened once under the prospectively frozen contract. The calibration risk set contained **8 positive first detections**, below the frozen minimum of **10**. Therefore no supervised model or dynamic-occupancy HMM was fit and no 2013–2017 heldout prediction was scored.

This result is neither favourable nor adverse evidence about the revised label-invariant Layer-B predictor. It is a prospectively valid non-estimability outcome and must not be rescued by lowering the positive-count threshold, changing the target, moving years, changing founders/worlds or reusing this system as fresh independent validation.

## Scientific target

The public release contains:

- a full response-free universe of **274 candidate wetlands**;
- response-free coordinates and hydroperiod for all 274;
- repeated detection histories for **47 surveyed wetlands**;
- three known 2003 reintroduction founders at 1-based indices `15, 33, 274`;
- explicit missing detection states and three subsequently destroyed sites.

Because annual occupancy is not observed over all 274 wetlands, the valid EOG target was narrowed before response access to:

> **multi-horizon first survey-recorded detection from the three known 2003 founders, evaluated on the 47 archived surveyed sites.**

Latent occupancy at the 227 unsurveyed wetlands was never imported as observed source state. Early positive detections could eliminate frozen rules but were not promoted to annual sources. The endpoint is survey-recorded detection, not latent colonisation probability or actual route reconstruction.

## Gate 0 source freeze

Source:

- Figshare article `5838189`, version `4`;
- DOI `10.6084/m9.figshare.5838189.v4`;
- title `Increasing connectivity between metapopulation ecology and landscape ecology`;
- CC0;
- 10 files, total 1,857,254 bytes;
- every published file size and MD5 verified.

Authoritative workflow run: `32030446500`  
Artifact: `9288678675`  
Artifact ZIP SHA-256: `0aaca661c0e86f650ec9eeb093b3fa0c818f51602513b567a2f92c51bcc19d6a`

The Gate-0 response firewall read only bounded physical headers. It did not open `y.wide.dryad.csv` rows or deserialize binary response objects.

Canonical files:

- `gate0_source_process_response_contract.json`
- `gate0_result.json`
- `gate0_amendment_v1_1.json`

## Gate 1 structural adequacy

Response-free 0.25 / 0.50 / 0.75 / 0.90 largest-component scales:

| world | threshold | achieved LCC | isolated fraction |
|---|---:|---:|---:|
| `geo_lcc250` | 2.5750 km | 0.2920 | 0.0401 |
| `geo_lcc500` | 2.5969 km | 0.5255 | 0.0328 |
| `geo_lcc750` | 3.0378 km | 0.8577 | 0.0109 |
| `geo_lcc900` | 3.3121 km | 0.9453 | 0.0000 |

All four thresholds are distinct and positive, edge sets are nested, and the 90% scale passes the frozen LCC/isolation criteria.

Authoritative workflow run: `32043150953`  
Artifact: `9292316766`  
Artifact ZIP SHA-256: `c73664e52e7849c2112d34e1d439c4376d859237d0a99c92ffbc01425d6c0985`  
Result fingerprint: `b4b8b0a1879aeac4c368630bc0bbf7f3b1052f37fa7b9d013335814c127b2d12`

The first Gate-1 run stopped on benchmark-only `zip(strict=True)` misuse. Removing strictness was the sole correction; node universe, bytes, thresholds, criteria and response firewall were unchanged. These thresholds remain analyst-choice structural scales rather than estimated frog dispersal limits.

Canonical files:

- `gate1_scale_adequacy_declaration.json`
- `gate1_result.json`

## Gate 2 pre-response freeze and smoke

Before response access, the branch froze:

- calibration years `2007–2012`;
- heldout years `2013–2017`;
- fixed founders and five Layer-A rules;
- unchanged Layer B `symmetric_world_support_summary_v1`;
- same-world mean-only comparator;
- founder-connectivity logistic baseline;
- repeated-detection dynamic-occupancy HMM;
- flexible random forest;
- response, missingness, estimability, metric and decision rules;
- all remaining preprocessing, HMM and runtime choices.

The response-free implementation established that the ten-feature Layer-B representation was computable and varied beyond shared covariates plus mean support (`max residual SD = 0.672556`).

The complete empirical runner was then exercised on deterministic synthetic detections while `y.wide.dryad.csv` was absent. All response parsing, first-detection risk-set, sequential contraction, logistic, RF, HMM, annual-metric and decision branches completed.

Synthetic-smoke workflow run: `32067855168`  
Artifact: `9300594060`  
Artifact ZIP SHA-256: `5f29876f6f244d43d2cf6a5aacfd9696cd15ed6ce11a72e650627a658b2815cc`  
Smoke result fingerprint: `e5d078b438225e16642b8cc897c42cab0354e989df8f97962f3849dd47bcd11f`

The smoke result is technical evidence only. Its favourable/adverse synthetic directions carry no scientific interpretation.

Canonical files:

- `gate2_prediction_comparator_contract.json`
- `gate2_amendment_v1_1.json`
- `gate2_amendment_v1_2.json`
- `gate2_nonresponse_result.json`
- `gate2_outcome_smoke_result.json`

## Once-only empirical outcome

The exact response object was:

- file: `y.wide.dryad.csv`;
- size: `5,859` bytes;
- MD5: `1a71e692356300fcf181fe77347da1b6`;
- SHA-256: `29f18ccaad9f9882bdb93e246ba12e58816c186b0833474c16fd8430ce566438`.

The empirical workflow verified the unchanged runner blob and the smoke-frozen numerical runtime before downloading the response.

Authoritative workflow run: `32068163306`  
Artifact: `9300697352`  
Artifact ZIP SHA-256: `034056d686cc66b4e092931ffea5d93118210218ed2c3ce58eae4316dbca6de1`  
Result fingerprint: `41a8a051d1ce8711caaa4325f1f9c563f64cc5da8a429b9b239361aa79708a95`

### Frozen response gate result

- calibration risk rows: **145**;
- calibration positive first detections: **8**;
- required positives: **10**;
- calibration negative candidate rows: **137**;
- required negatives: **40**;
- Layer-B variation beyond shared-plus-mean-only: **estimable**, maximum residual SD **0.684397**;
- models fit: **none**;
- heldout rows scored: **0**;
- annual metrics produced: **none**.

The positive sequence was `3, 2, 1, 1, 1, 0` across 2007–2012. No positive detection contradicted any frozen world, so all five Layer-A rules survived calibration. This does not validate the rules; it only means the sparse calibration positives did not falsify them under the support threshold.

Frozen status:

- Layer-B predictive value: `non_estimable_response_or_representation`;
- external predictive added value: `non_estimable_external_predictive_added_value`.

Canonical evidence:

- `gate2_outcome_result.json`
- `gate2_outcome_provenance.json`
- `gate2_annual_metrics.csv`
- `gate2_predictions.csv`
- `gate2_runtime_freeze.txt`

The empty CSV registries are intentional audit evidence that the prospectively frozen response gate stopped the analysis before model fitting and heldout scoring.

## Interpretation

What this candidate established:

1. a public metapopulation system can pass source/process, full-node-universe and response-blind structural gates;
2. the revised label-invariant Layer-B representation is technically computable and nontrivial on the frozen design;
3. the full comparator and HMM implementation can complete before response access on synthetic detections;
4. the real endpoint nevertheless lacks the prospectively required calibration-event count.

What it did **not** establish:

- predictive superiority of Layer B over same-world mean compression;
- predictive added value over founder connectivity, dynamic occupancy or RF;
- biological validity of any structural distance as a dispersal parameter;
- one actual colonisation route;
- annual occupancy of unsurveyed wetlands.

The correct conclusion is therefore:

> **Chiricahua is a structurally eligible but response-non-estimable fresh EOG-specific validation attempt.**

## Independence and no-rescue boundary

Published aggregate ecological findings were viewed during screening, so this was fresh EOG-specific validation rather than completely outcome-naive system validation. No EOG heldout score was viewed because the frozen response gate stopped before model fitting.

Do not:

- lower the minimum from 10 to 8 positives;
- change calibration or heldout years;
- switch to all detections, latent occupancy or a positive-only endpoint;
- promote unsurveyed latent states to observed sources;
- restrict the 274-node universe to detected sites;
- change founders, structural scales, kernel or support tolerance;
- expose exact world IDs as supervised features;
- retune `symmetric_world_support_summary_v1`;
- rerun this system and call it fresh independent validation;
- infer one actual colonisation route.

The one-time smoke and outcome workflows were removed after durable evidence preservation.
