# EOG v2.1 Fiji Pheidole Stage 2B predictor/reference freeze contract

## Status

**Prospective response-free predictor freeze. Genetic member contents remain prohibited.**

This contract follows the Stage-1 admitted Fiji archive and the response-free focal-group freeze for EGPA0079 (`ululevu`). It is written before any EGPA0079 VCF/genotype/FST/WC member is opened.

Authoritative response-free provenance already established:

- Zenodo record `4965569` / Dryad DOI `10.5061/dryad.xd2547dcp`;
- archive SHA-256 `9a23543ad59d5f4de7e6f26cc91b75dc60f93c259744e640b8f6576fde89abc7`;
- `sequenceMetaData.csv` SHA-256 `5a41f967d81e005be3b3e91f31bb1a7eae26a9e7fe3f2a495aef7162932cdfbd`;
- Stage-1 fingerprint `8291537a50ad0ee7b33f81bf7a71653a6fe317853323f1bc5c98beff132fd184`;
- Stage-2A focal freeze workflow `31660004338`, artifact `9165845346`;
- Stage-2A focal freeze fingerprint `ba3617cae074a49270b3a140dce3671cc8e8eae2f6f8d608747a5734f7a9b077`;
- selected EGPA `EGPA0079`, species label `ululevu`, 175 individuals, 15 response-free population codes.

No genetic-response member was opened to obtain those facts.

## Population node admission

Population-level genetic validation requires minimal within-population replication. Before genetic response access, freeze the following rule:

> Admit an EGPA0079 population as a validation node iff the released response-free `sequenceMetaData.csv` contains **at least 5 individuals** assigned to that population and the population has a finite coordinate centroid.

This rule is based only on sample replication and geography. It is not adjusted after opening a VCF.

Under the already frozen metadata this leaves exactly 11 population nodes:

- `BQ` — 8 individuals;
- `EVN` — 14;
- `GA` — 22;
- `KR` — 10;
- `KV` — 18;
- `LA` — 5;
- `LK` — 11;
- `ML` — 7;
- `TA` — 12;
- `VL3` — 16;
- `VL4` — 44.

Response-free exclusions:

- `CKI` — 1;
- `VL1` — 1;
- `VL2` — 2;
- `WVN` — 4.

No excluded population may be restored after genetic response access. The threshold may not be lowered on this dataset.

Population coordinates are the arithmetic mean of the finite individual coordinates within each admitted response-free population. The centroid set and its fingerprint are frozen as part of the Stage-2B artifact.

## Geography and graph

### Geographic distance

`D_geo` is great-circle distance in kilometres between frozen population centroids.

### Local projection for graph construction

For graph geometry only, use a dateline-aware local equirectangular projection:

- latitude origin = mean latitude in radians;
- longitude origin = circular mean longitude;
- each longitude offset is wrapped to `[-pi, pi]` before conversion to kilometres.

This prevents Fiji nodes on either side of the ±180° meridian from being spuriously separated by ~360°.

### Gabriel graph

Construct the undirected Gabriel graph on the projected population coordinates. The rule is parameter-free apart from a numerical tolerance and contains the Euclidean MST for distinct points.

Let each Gabriel edge have geographic length `d_ij` in kilometres. Define the frozen support/conductance

`w_ij = exp(-d_ij / median_Gabriel_edge_length)`.

The same response-free graph geometry is used to construct conventional graph references and the EOG operator; genetic outcomes do not modify edges or weights.

## Complete conventional-reference candidate family

Freeze **all three** candidates before genetic response access:

1. `geographic` — pairwise great-circle distance;
2. `gabriel_shortest_path` — shortest-path sum of geographic edge lengths on the frozen Gabriel graph;
3. `gabriel_current_flow` — effective-resistance distance from the frozen Gabriel conductance matrix.

This is the complete conventional candidate family for this dataset. No candidate may be removed because it performs poorly and no new candidate may be added after genetic response access.

The future nested selector in #143 chooses among these candidates separately inside each outer-training fold. EOG predictors are prohibited from conventional-reference selection.

## EOG genetic candidate

Use the existing exact-eventual FST-oriented EOG construction:

- directed `DynamicReachabilityEdge` objects in both directions for every Gabriel edge;
- edge geographic support `w_ij` above;
- fixed `loss_support = 0.5`;
- exact eventual first-passage support;
- arithmetic symmetrisation used by the existing eventual-genetic module;
- connected-pair continuous distance from exact-eventual support;
- separate bidirectional-disconnection indicator;
- no finite propagation horizon;
- no fitted support floor;
- no genetic tuning.

The Stage-2B artifact must freeze EOG operator and eventual-connectivity fingerprints before VCF access.

## Genetic response contract (for later Stage 3)

The exact genetic-response member is still unopened at Stage 2B.

When Stage 3 is authorized:

- use only samples aligning to the 11 frozen population codes and frozen focal EGPA;
- audit VCF/sample/population alignment before computing the response;
- compute one predeclared symmetric population-genetic response from the focal RAD data;
- primary intended response is pairwise Weir-Cockerham FST if the release supports an unambiguous diploid biallelic calculation;
- if the released focal VCF cannot support that response unambiguously, status is `non_estimable` rather than changing the endpoint.

Validation transform is frozen as `linearized_fst = FST/(1-FST)` and requires pairwise FST in `[0,1)`.

Common ridge penalty: `1.0`.

## Nested outer/inner validation

Use `evaluate_nested_genetic_reference_selection` from #143 / PR #144.

Outer unit: one entire population. All pairs involving that population are untouched outer-test pairs.

Within each outer-training set, conventional references are selected by inner leave-one-population-out CV using equal-weight inner-population MSE and the lexicographic tie rule. The same selected reference is then compared with and without frozen EOG predictors on the untouched outer population.

Primary fold effect:

`delta_MSE_h = MSE(selected conventional + EOG)_h - MSE(selected conventional)_h`.

Negative favours added EOG information.

Primary aggregate:

`mean_population_delta_MSE = mean_h(delta_MSE_h)` with equal population weight.

Pooled pairwise MSE/MAE are descriptive secondary summaries.

## Empirical uncertainty and GO rule

Freeze before response access:

- bootstrap unit: outer population fold;
- number of bootstrap resamples: `10,000`;
- seed: `20260813`;
- bootstrap statistic: equal-weight mean of resampled outer-population `delta_MSE` values;
- interval: percentile 2.5% and 97.5% bounds.

A Fiji empirical nested-reference **GO** requires all of:

1. the focal raw genetic release aligns unambiguously to all 11 frozen validation populations;
2. all 11 outer folds are estimable under the frozen response and candidate family;
3. `mean_population_delta_MSE < 0`;
4. the 97.5% population-bootstrap bound for mean delta MSE is `< 0`.

No additional favourable-fold-count threshold is required. Candidate selection frequencies are descriptive and retained exactly.

If genetic alignment/response calculation fails, result is `non_estimable`.
If mean delta is zero/adverse or the upper bootstrap bound is non-negative, result is `no_empirical_added_information`.
No candidate/reference redesign is permitted on the same Fiji response.

## Hard response firewall

Until the Stage-2B predictor artifact and manifest are generated and byte-identified:

- do not open any `*.vcf` member;
- do not open `EGPA0048_WC.csv` or any FST/WC output;
- do not open SNP/genotype matrices;
- do not use published genetic clustering/differentiation to alter the 11 nodes, graph, candidate family, EOG operator, transform, ridge penalty or GO rule.

The Stage-2B workflow may re-download the immutable archive to verify provenance and may open only `sequenceMetaData.csv` to reconstruct the already frozen focal/node metadata.

## Relation to Zhoushan

This contract is prospectively defined for Fiji and must not be back-applied to Zhoushan. Zhoushan remains frozen as `indeterminate_strong_reference_failure`, `promotion_go=false`, fingerprint `585b4b6c3a616d353e3abcfd95b5c341cb4e022da012a8d72ad310ddb9ae48cd`.
