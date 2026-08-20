# Tvärminne Daphnia two-layer EOG-WF validation

## Final status

This fresh prospective attempt completed its once-only heldout endpoint without post-response retuning.

- Layer-B vs mean-only: **`favorable_layer_b_predictive_value`**
- Layer-B vs strong external baseline: **`adverse_external_predictive_added_value`**
- authoritative result fingerprint: `8fcf0e74452e29e14fd63efa51184bfbb00b7fb075ad485616798d8fd3a5a4ae`

The correct interpretation is mixed, not a promotion to a generally superior predictor.

## Prospective path

The candidate was selected from Luo et al. (2022), *Multispecies coexistence in fragmented landscapes*, PNAS, using Figshare article `20329245`, version 1. All scientific/modeling choices were frozen before `data_M.csv` was opened.

Response-blind gates established:

1. stable anonymous Figshare source and archive identity;
2. 546 response-independent pools with separately released patch size and pairwise distance;
3. four distinct nested response-blind structural scales;
4. released D. magna annual endpoint semantics and missingness boundary;
5. fixed 1982–2006 calibration / 2006–2017 heldout temporal design;
6. five fixed Layer-A worlds;
7. unchanged `symmetric_world_support_summary_v1` Layer-B representation;
8. strong conventional logistic/RF comparators using the same patch-size, temperature and connectivity information;
9. exact response-count gate and no-fit-on-failure rule;
10. exact runtime/runner lock and full response-free synthetic smoke;
11. generic 16-key machine-checkable outcome-access authorization.

The authorization decision was `authorized_once_only_exact_count_gate_required` with zero missing freeze keys and decision fingerprint `ededbd2a70fff93842462d988ee86d789caa6a31da8168ce5d85941a30d12c73`.

## Once-only execution

The sole response-capable execution was:

- workflow run `32368225530`;
- head `e7e92fd72c67853280ddf4a5a116dab07a5f2774`;
- `run_number = 1`;
- `run_attempt = 1`;
- conclusion `success`.

A later audit recovered the artifact without reexecuting the response. Audit run `32368453417` confirmed the same once-only run and result.

## Exact count gate

The response was sufficiently estimable under the prospectively frozen minima:

| quantity | observed | minimum |
|---|---:|---:|
| calibration 0→1 events | 730 | 10 |
| calibration 0→0 non-events | 10,102 | 40 |
| heldout 0→1 events | 258 | 10 |
| heldout 0→0 non-events | 4,502 | 40 |
| heldout transitions with both classes | 11 | 8 |

All 35 annual transitions had at least one current occupied source pool.

The released response matrix resolved to 546 × 36 annual values. It contained zero explicit missing tokens at release time; the endpoint remains the paper/release annual 0/1 code and zeros are **not** interpreted as latent biological absence.

## Layer A: exact rule contraction worked strongly

The five prospectively declared worlds began as:

- `geo_lcc250`;
- `geo_lcc500`;
- `geo_lcc750`;
- `geo_lcc900`;
- `geo_exponential_full`.

At the very first calibration update, `1982→1983`, all four finite hard-threshold worlds were eliminated by positive targets. Only `geo_exponential_full` survived, and it remained through the final heldout transition.

This supports the Layer-A role of exact identities as auditable compatibility/falsification state. It does **not** identify the full exponential rule as the true biological dispersal process, route or history.

## Layer B: small independent value beyond mean support

Layer B was estimable beyond the prospectively frozen mean-only representation. All eight extra symmetric columns were retained and the largest residual SD after projection on the shared baseline + mean-only columns was `0.4532423929`.

Primary macro-heldout-transition log loss:

| representation/model | macro log loss |
|---|---:|
| geometry/process RF | **0.204084** |
| geometry/process logistic | 0.258052 |
| Layer B | 0.285714 |
| mean-only EOG | 0.287275 |

Layer B minus mean-only = `-0.001561`, and Layer B had lower log loss in **8/11** heldout annual transitions. Therefore the frozen rule returns:

> **`favorable_layer_b_predictive_value`**

This is evidence that the shape/dispersion of the surviving world-set support contains some heldout information beyond surviving fraction plus mean support. The effect is small.

## External predictive added value was adverse

The strong external RF was much better than Layer B:

- RF macro log loss: `0.204084`;
- Layer B macro log loss: `0.285714`;
- Layer B minus RF: `+0.081631`;
- Layer B beat RF in **0/11** heldout transitions.

Frozen status:

> **`adverse_external_predictive_added_value`**

Therefore this fresh validation does not support EOG Layer B as a superior standalone general prediction product.

## Product boundary after Daphnia

The evidence now supports a narrower architecture:

1. **Layer A** — exact world identities remain the scientific update/falsification state.
2. **Layer B** — label-invariant world-set summaries can carry non-redundant predictive information, but should be treated as diagnostic/contextual or candidate complementary features.
3. **Strong external predictor** — remains necessary when predictive accuracy itself is the product objective.

The next valid question is not “can another dataset make standalone EOG beat RF?”. A scientifically cleaner next estimand is whether frozen EOG Layer-B features add heldout value **on top of** an already strong external predictor, prospectively tested on a fresh system.

## No-rescue boundary

Do not:

- retune Daphnia worlds, thresholds, split, Layer B, comparators, count minima or metrics and call the rerun independent;
- replace the RF comparator because it won;
- promote the surviving full-support world to biological truth;
- search sequentially for a favourable standalone-prediction dataset.

Canonical compact result: `outcome_result_summary.json`.
