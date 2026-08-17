# Chiricahua leopard frog two-layer EOG-WF validation

## Current status

> **Gate 0 source/process/response semantics: PASS for a fixed-founder conditional design**
>
> **Gate 1 response-blind structural adequacy: PASS**
>
> **Detection-history response rows opened: false**

This branch is the first post-Glanville candidate to pass both source/process eligibility and the prospectively reused structural-scale gate without response access.

It has **not** yet produced a Layer-B predictive result.

## Scientific target after Gate 0 adjudication

The public release contains:

- a full response-free universe of **274 candidate wetlands**;
- response-free coordinates and hydroperiod for all 274;
- repeated detection histories for only **47 surveyed wetlands**;
- three known 2003 reintroduction founders at 1-based indices `15, 33, 274`;
- explicit missing detection states and three subsequently destroyed sites.

Because annual occupancy is not observed over all 274 wetlands, the valid EOG design is **not** an annual changing-current-source forecast across the full network. Latent occupancy at the 227 unsurveyed wetlands may not be imported as observed EOG source state.

The prospectively narrowed target is:

> **multi-horizon first survey-recorded detection from the three known 2003 founders, evaluated on the 47 archived surveyed sites.**

Early positive detections may constrain/eliminate frozen rules, but they are not automatically promoted to observed annual source states.

This is a survey-recorded detection target, not latent colonization probability or actual route reconstruction.

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

The response firewall read only bounded physical headers of text-like data files. `y.wide.dryad.csv` rows were not opened and binary response objects were not deserialized.

A convenience artifact copy of `MetadataS1.docx` was not used for adjudication because the one-time workflow treated its binary bytes as documentation text. The exact original file was nevertheless checksummed. Scientific adjudication relies on the frozen R code, bounded CSV headers, source manifest and public study methods.

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

The first Gate-1 run stopped on a benchmark-only `zip(strict=True)` error while checking three adjacent pairs among four worlds. Removing `strict=True` was the only correction. Node universe, source bytes, thresholds, gate criteria and response firewall did not change.

Canonical files:

- `gate1_scale_adequacy_declaration.json`
- `gate1_result.json`

The thresholds are analyst-choice structural scales, not estimated frog dispersal limits.

## Gate 2 frozen before response

`gate2_prediction_comparator_contract.json` now fixes:

- calibration years `2007–2012`;
- heldout years `2013–2017`;
- fixed founders and five rule worlds;
- Layer A exact rule identities for contraction/falsification;
- unchanged Layer B `symmetric_world_support_summary_v1`;
- same-world mean-only comparator;
- founder-connectivity logistic baseline;
- repeated-detection dynamic-occupancy HMM;
- flexible random forest;
- response/estimability/metric/adverse rules.

No response value has been inspected. Gate 2 still requires a response-free implementation/smoke audit before `y.wide.dryad.csv` may be opened once.

## Independence boundary

Published aggregate ecological findings were viewed when screening the candidate. Therefore this is not a completely outcome-naive ecological system.

No EOG world-set forecast score, Layer-B heldout metric or EOG favourable/adverse result has been viewed. Published findings may justify process relevance and comparator class but may not tune EOG thresholds, Layer-B features, holdout years or decision rules.

## No-rescue boundary

Do not:

- promote latent unsurveyed occupancy to observed source state;
- restrict the 274-node universe to detected sites;
- change founders or structural scales after response access;
- replace fixed-founder prediction with annual current-source prediction;
- expose exact world IDs as supervised features;
- retune `symmetric_world_support_summary_v1`;
- reinterpret recorded non-detection as certain latent absence;
- infer one actual colonization route.
