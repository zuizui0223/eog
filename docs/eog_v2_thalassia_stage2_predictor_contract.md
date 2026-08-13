# EOG v2.1 Thalassia response-free Stage-2 predictor contract

## Status

**Prospective response-free freeze. Microsatellite workbook contents remain prohibited until the complete Stage-2 artifact is archived.**

Parent admission: issue #148 and `docs/eog_v2_thalassia_pre_genetic_contract.md`.
Generic nested selector: `docs/eog_v2_nested_genetic_reference_contract.md`.

## Frozen node universe

Use exactly the 17 Stage-1 population codes and coordinates archived under `benchmarks/frozen/thalassia_response_free/`:

`BIA, TUA, AMB, KEN, BIT, PAL, JEP, PAR, BAN, NAT, KUP, MAT, DRI, PAD, CK, MI, Ex2`.

Stage-1 identities:

- coordinate CSV SHA-256 `7311e561ec2dbeecc57b0b6d8b83b4819697f23480303bcb4478e5750660ce49`;
- coordinate fingerprint `334948e6af43c50d5fb7bfec3396065a1c39d64e0bab7eb5f4a767a42249245d`;
- Stage-1 manifest fingerprint `12a34c597dbf4130ad1dcda8a9822504291a0ac7d4f34fa31c43d8d373d49764`;
- opaque microsatellite SHA-256 `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`.

No node may be deleted, renamed, moved, merged or split from genetic information.

## Response-free geometry

### Direct geographic distance

`geographic` is WGS84 great-circle distance in kilometres using Earth radius `6371.0088 km`.

### Gabriel adjacency

For topology construction only, project the 17 frozen WGS84 points with an azimuthal-equidistant projection centered deterministically on:

- arithmetic mean latitude of the 17 sites;
- circular-mean longitude of the 17 sites.

The projection has no fitted radius/k parameter. Gabriel adjacency is defined in this response-free projected plane. Edge distances used in predictors and support weighting are the original great-circle distances, not projected lengths.

### Edge support

For every undirected Gabriel edge with great-circle length `d`:

`support = exp(-d / median_Gabriel_edge_length)`.

The same support is assigned to both directed edge orientations.

EOG transition loss support is frozen at `0.5`, inherited from the already-confirmed exact-eventual genetic construction. No environmental, island-area, current-direction or habitat multiplier is fitted in this confirmation graph.

## Complete conventional reference family

Before genetic response access, freeze exactly:

1. `geographic` — direct great-circle distance;
2. `gabriel_shortest_path` — all-pairs shortest path using great-circle Gabriel-edge lengths;
3. `gabriel_current_flow` — effective-resistance distance from the same Gabriel conductance matrix.

All three stay in the candidate family after response access, regardless of performance. No candidate is added or removed later.

EOG never participates in conventional reference selection.

## EOG predictor

Use the already frozen exact-eventual symmetric FST-oriented construction on the same sub-stochastic operator:

- exact eventual first-passage directional support;
- reciprocal directional supports averaged in support space;
- connected-pair continuous distance `-log(exchange support)`;
- explicit bidirectional-disconnection indicator;
- no finite horizon;
- no numerical support-floor hyperparameter;
- no fitted symmetrisation parameter.

## IBE boundary

No environmental distance is invented for this confirmation. `environmental_distance = 0` is implicit and IBE is **non-applicable**.

## Nested validation settings

Outer unit: population.

For each outer held population, remove every pair involving it before conventional reference selection or fitting. Within outer training populations, select among the complete three-reference family by inner leave-one-population-out equal-weight population MSE, with lexicographic exact-tie resolution. Then fit:

1. selected conventional reference;
2. the same selected reference + frozen EOG continuous distance + disconnection indicator.

Common ridge penalty: `1.0`.

Frozen response transform: `linearized_fst = FST / (1 - FST)`.

The exact raw FST estimator/parser/clone handling is not inferred from observed genotype values in Stage 2; it must be committed in the Stage-3 schema contract before genotype cells are opened.

## Promotion rule

Bootstrap unit: held-out population.

- seed `20260813`;
- exactly `10,000` resamples;
- 95% percentile interval for the equal-weight mean outer-population `delta_MSE`, where `delta_MSE = MSE(selected conventional + EOG) - MSE(selected conventional)`.

A dataset-level EOG GO requires all of:

1. all 17 frozen populations align mechanically to the response, or any non-alignable population produces a provenance/non-estimable stop rather than a response-informed node change;
2. pooled outer MSE of the nested-selected conventional baseline is `<=` pooled outer MSE of the fixed geographic-only baseline, so the selector itself is operationally competitive;
3. equal-weight mean outer-population `delta_MSE < 0`;
4. bootstrap upper 95% bound `< 0`.

If condition 2 fails, status is `indeterminate_selector_reference_failure`; candidate references are not dropped. If conditions 3–4 fail, retain null/adverse status. No graph/reference/EOG rescue is permitted on this dataset after genotype access.

## Stage-2 artifact requirement

Before Stage 3 begins, archive and fingerprint:

- all 136 unordered pair rows;
- all three conventional distance columns;
- EOG continuous distance + disconnection;
- projection center and Gabriel edge list;
- edge-support scale;
- candidate-family fingerprint;
- graph fingerprint;
- dynamic-operator fingerprint;
- exact-eventual connectivity fingerprint;
- this contract SHA;
- generic nested-selector contract SHA;
- response transform/ridge/bootstrap/promotion settings.

The Stage-2 artifact is immutable after genetic response access.

## Directionality boundary

Symmetric FST does not validate the source paper's asymmetric ocean-current/gene-flow hypothesis. Directional support remains a separate future endpoint requiring a separate contract.
