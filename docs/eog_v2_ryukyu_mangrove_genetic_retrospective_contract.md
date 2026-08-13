# EOG v2 Ryukyu mangrove retrospective genetic-validation contract

## Status

**Independent external dataset, but not prospectively outcome-blind.**

This contract uses the `Rhizophora stylosa` Ryukyu Archipelago study of Thomas, Nakajima & Mitarai (2022), DOI `10.3389/fmars.2022.827590`, and its Dryad dataset DOI `10.5061/dryad.bcc2fqzdh`.

The published article already reports pairwise FST, STRUCTURE clusters and contemporary migration patterns. Therefore this benchmark must never be described as a blinded prospective confirmation. It is a **retrospective external validation/boundary**. The EOG graph below is nevertheless frozen only from published sampling locations and a predeclared geographic rule; published genetic structure, migration arrows, current interpretation and FST values are prohibited from graph construction or tuning.

## Published sampling design used before genetic-response attachment

The primary article reports 354 sampled trees from 16 populations on four islands. Population coordinates are taken verbatim from Table 1:

| Island | Population | Latitude | Longitude |
|---|---|---:|---:|
| Okinawa | OKI | 26.604 | 128.143 |
| Miyako | MYKa | 24.789 | 125.286 |
| Miyako | MYKb | 24.763 | 125.282 |
| Miyako | MYKc | 24.752 | 125.268 |
| Miyako | MYKd | 24.731 | 125.296 |
| Ishigaki | ISGa | 24.542 | 124.296 |
| Ishigaki | ISGb | 24.510 | 124.279 |
| Ishigaki | ISGc | 24.456 | 124.149 |
| Ishigaki | ISGd | 24.467 | 124.125 |
| Iriomote | IRMa | 24.403 | 123.830 |
| Iriomote | IRMb | 24.344 | 123.934 |
| Iriomote | IRMc | 24.344 | 123.928 |
| Iriomote | IRMd | 24.279 | 123.904 |
| Iriomote | IRMe | 24.334 | 123.728 |
| Iriomote | IRMf | 24.331 | 123.714 |
| Iriomote | IRMg | 24.309 | 123.683 |

No genetic value is used to select, delete, connect or weight these nodes.

## Response-free graph

### Geographic distance

Primary `D_geo` is great-circle distance in kilometres between population coordinates.

### Topology

Construct the undirected Gabriel graph after projecting latitude/longitude to a local equirectangular kilometre coordinate system centred on the mean sample latitude/longitude. Gabriel adjacency is deterministic and contains the Euclidean MST, avoiding an outcome-tuned radius or k-nearest-neighbour choice.

### Conductance

For every Gabriel edge `i-j`, with local projected edge length `d_ij`, define

`W_ij = exp(-d_ij / median_Gabriel_edge_length)`

in both directions.

No current direction, published migration direction, inferred ancestry, FST, STRUCTURE cluster, island barrier multiplier, site area or habitat-category multiplier is used in the primary graph.

The EOG-R transition operator uses the already-confirmed genetic-development loss support `0.5`.

## Genetic predictors frozen before attaching the genetic response

### IBD

`D_geo` — great-circle geographic distance.

### IBE

No defensible continuous environmental-distance dataset is available in the released study metadata for this validation. Therefore `D_env` is an all-zero matrix and the nominal `IBD+IBE` model is explicitly interpreted as identical to IBD. This benchmark must not manufacture an IBE claim from mangrove site labels.

### Strong conventional connectivity reference

`D_currentflow` — effective resistance on the same response-free symmetric Gabriel conductance graph.

This is the primary strong reference. EOG does not receive credit merely for improving over straight-line IBD if it cannot add information beyond this graph-aware conventional reference.

### EOG genetic candidate

Use the already frozen exact-eventual FST-oriented construction:

- exact eventual first-passage support under the frozen sub-stochastic operator;
- arithmetic mean of reciprocal directional supports;
- connected-pair distance `-log(exchange support)`;
- a separate bidirectional-disconnection indicator;
- no finite propagation horizon;
- no numerical support-floor hyperparameter;
- no fitted symmetrisation parameter.

## Genetic response

Preferred response is pairwise population FST recomputed from the authoritative released microsatellite genotype file after its file SHA-256 and marker/encoding README have been archived.

The article reports 11 assayed ncSSR loci in Methods while the Dryad landing-page abstract describes 7 microsatellite markers. **Do not assume which loci the released file contains or silently force the published 11-locus analysis onto the released 7-marker dataset.** The released README/data must be inspected first. If the raw release cannot reproduce a well-defined pairwise FST response, the benchmark remains unscored rather than digitizing a preferred subset of Figure 2 without a separate provenance declaration.

If a published pairwise FST matrix is used as fallback because raw genotypes are unavailable, that result is labelled `published-response retrospective sensitivity`, not raw-data replication.

## Validation

Use the existing `eog-v2-genetic-validate` leave-one-population-out runner with:

- response transform: `linearized_fst`;
- ridge penalty `1.0`;
- all genetic pairs involving the held-out population removed from model fitting;
- primary contrast: `strong_reference_eog - strong_reference` MSE;
- secondary contrast: `ibd_ibe_eog - ibd_ibe` MSE.

Negative augmented-minus-reference MSE favours EOG.

## Interpretation

Because published genetic outcomes were already visible before this contract, no p-value or effect threshold is used to declare a new confirmatory success. Report the exact held-out contrasts and their population-specific fold errors.

Interpretation classes are:

- `retrospective_added_information`: strong-reference + EOG has lower held-out MSE than strong reference;
- `retrospective_no_added_information`: difference is zero/adverse;
- `non_estimable`: released genetic response cannot be aligned or reliably reconstructed.

A favourable retrospective result justifies seeking a genuinely outcome-blind second empirical genetic dataset; it does not substitute for that promotion gate.

## Directionality boundary

Symmetric pairwise FST is not used to validate migration direction. The publication's BayesAss migration rates and buoy trajectories may be analysed later as separate directional endpoints only under a separately frozen directional contract.
