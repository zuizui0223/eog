# Spotted lanternfly fresh two-layer EOG-WF validation attempt

## Final status

> **`pre_model_response_registry_mismatch`**

This fresh candidate passed all pre-response screening gates, then stopped immediately after the once-only response opening because the exact frozen county registry disagreed with a prospectively frozen published-count consistency check.

It is **not** favourable, null, or adverse evidence about `symmetric_world_support_summary_v1` because no EOG or external prediction model was fit and no heldout prediction was scored.

## Why the candidate advanced unusually far

Before row-level response access it passed:

1. stable public source transport;
2. endpoint-matched prospective event-count estimability;
3. response-independent Census county node/geometry freeze;
4. response-header firewall;
5. response-blind structural scale diversity/adequacy;
6. frozen Layer-A / Layer-B / comparator / temporal design;
7. full synthetic pre-response runner smoke;
8. package regression on Python 3.10, 3.11 and 3.12 plus the frozen topology benchmark.

## Gate 0 PASS

Response-independent node universe:

- 2020 Census county/county-equivalent Gazetteer;
- conterminous US + DC, excluding AK/HI/PR;
- **3,108 nodes**;
- node ID: GEOID;
- geometry: Census internal-point latitude/longitude;
- geometry fingerprint `5b05192ae33e398c5381bdab37db048373e61e9cd84523fc4f48b7a2bc8dbb07`.

Frozen response source:

- `danielstrombom/SLFS` commit `f0cf5345346ece720b6d6fde18c91072fdcc9b01`;
- `Maps/data_2_temporal.csv`;
- Git blob SHA-1 `e845dcc72080089d11c3f1078766cc14cdeb2340`;
- SHA-256 `9af3fba4e4a45b6bf8c0b11f869a82188297d34c76745535db00238d2020cb4c`.

Authoritative Gate 0 run `32223117325`:

- artifact `9354619504`;
- artifact digest `sha256:aae1be06a1fbd42668f128e690fafc02f90bb5f50e196416c0afca5c7b6abfaa`;
- response rows opened: false;
- response values parsed: false;
- only the 167-byte first physical record was parsed.

Prospective counts used before response access:

- calibration new-county events: 44;
- heldout new-county events: 85;
- calibration non-event lower bound: 3,063;
- heldout non-event lower bound: 2,978;
- three heldout annual transitions expected to contain both classes.

Gate 0 fingerprint:

`2cc08f58ef090901e5aa930cc2803e36279480cc17209c6bfe35d4fc4499cc5f`.

## Gate 1 PASS

The response-blind Haversine structural ladder on all 3,108 frozen county nodes was:

| structural world | threshold (km) | achieved LCC | isolated fraction |
|---|---:|---:|---:|
| `geo_lcc250` | 35.8287 | 0.2864 | 0.4714 |
| `geo_lcc500` | 40.5402 | 0.5006 | 0.2941 |
| `geo_lcc750` | 49.4484 | 0.7519 | 0.1374 |
| `geo_lcc900` | 86.4548 | 0.9556 | 0.0180 |

All four scales were distinct and nested. `geo_lcc900` passed the frozen >=0.90 LCC and <=0.05 isolation criteria.

Authoritative Gate 1 run `32223548701`:

- artifact `9354753392`;
- artifact digest `sha256:796b489b818aa609b5e77c48c0cf55aee567a41c1672b45c8a94bb04606e4d5f`;
- Gate 1 fingerprint `e2d01cfd9802240fdaa2a474ad453165b7fb413e1620b6710c2e24380bd88ca9`.

The structural thresholds remain analyst-choice county-network scales, not biological SLF dispersal estimates.

## Frozen Gate 2 design

Before response access the branch froze:

- calibration: 2014->2018 (four annual transitions);
- heldout: 2018->2021 (three annual transitions);
- no heldout refitting;
- four hard local structural worlds plus one full-support heavy-tail world allowing nonzero human-mediated long-distance possibility;
- equal current-source weights;
- exact sequential rule contraction/falsification;
- unchanged production `symmetric_world_support_summary_v1`;
- geometry/process logistic baseline;
- geometry/process random forest baseline;
- same-world mean-only logistic;
- Layer-B logistic;
- representation estimability, response count, metric and decision rules;
- frozen NumPy/Pandas/scikit-learn runtime.

Exact world labels were not supervised predictive columns.

## Pre-response smoke PASS

The frozen empirical runner passed a synthetic end-to-end smoke before response access.

Run `32224187166`:

- artifact `9354955867`;
- artifact digest `sha256:80e5e81e402995fa6e1b06a7287f73be7529ecfb7ffe60db2d9eb84c781374ce`;
- response bytes opened: false;
- support matrix 5 x 30;
- Layer-B matrix 30 x 10;
- all four local rules eliminated by a synthetic distant target while the heavy-tail rule survived;
- representation estimability check passed.

Package checks from the same frozen scientific head were all green.

## Once-only response opening and stop

Authoritative response-opening workflow:

`32224405320`

Before opening the response, the workflow proved byte-for-byte equality of the runner, Gate 2 contract and runtime lock against the smoke-frozen commit:

`dcba7ec1a668de38d6748d44d24b6bac08ec2e7e`.

The exact Census archive and exact response Git blob/SHA were then verified, and row-level response access occurred for the first and only intentional SLF outcome attempt.

The frozen runner required the cumulative unique positive FIPS registry to equal the prospectively declared published counts before any model fit:

`1, 3, 7, 17, 45, 57, 84, 130` for 2014-2021.

The first mismatch occurred immediately at 2015:

- frozen expected cumulative count: **3**;
- exact response unique FIPS with `infested > 0.5`: **4**.

The runner stopped with:

`published cumulative count mismatch for 2015: 4 != 3`.

Consequently:

- EOG model fits: **0**;
- external comparator fits: **0**;
- heldout predictions: **0**;
- Layer-B score: not computed;
- no favourable/null/adverse prediction conclusion exists.

No artifact was produced by the runner because the mismatch was intentionally checked before model-result creation. Durable stop evidence is in `outcome_stop_result.json` and the GitHub Actions run log.

## Interpretation

The exact response was not retrospectively reinterpreted to replace the frozen published count of 3 with 4. Doing so would alter the prospectively frozen registry semantics after response access.

The correct status is therefore:

`pre_model_response_registry_mismatch`.

This is a validation-design/source-consistency result, not evidence about Layer-B predictive value.

## No-rescue boundary

Do not:

- change the frozen 2015 count from 3 to 4 and rerun this attempt as fresh independent validation;
- change the response definition or temporal split;
- change the five worlds, thresholds, kernels or source weighting;
- change Layer-B, baseline features, model hyperparameters, metrics or decisions;
- reuse SLF as fresh confirmation after redesign.

The once-only outcome workflow was removed after the stop was preserved.
