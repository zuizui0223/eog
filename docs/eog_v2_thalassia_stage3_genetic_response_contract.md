# EOG v2.1 Thalassia Stage-3 genetic-response implementation contract

## Status and precedence

**Harmonized after the successful schema-only audit, but before any MLG identity, allele-frequency summary, pairwise FST, genetic distance, clustering or migration response was computed.**

The earlier `docs/eog_v2_thalassia_stage3_microsatellite_contract.md` was committed **before the first workbook-cell access** and is the controlling biological-response contract. This file is an implementation companion only. Where an earlier version of this file conflicted with that first contract, the first contract prevails.

In particular, the controlling rules are:

- a missing allele (`0` or blank) in either member of a diploid locus makes that locus missing for that sample; the sample is then excluded by the frozen complete-16-locus primary rule;
- exact within-population MLG duplicates retain the smallest **normalized** sample ID, with source row as the secondary deterministic tie-break;
- primary Weir-Cockerham theta must satisfy `0 <= theta < 1` for every pair because Stage 2 froze the existing `linearized_fst` response domain;
- a negative, non-finite or `>=1` primary theta produces `non_estimable_linearized_fst_domain`; negative theta is not clipped or retained as a primary transformed response.

No pairwise FST had been computed when these inconsistencies were detected and corrected.

## Frozen parents

- Stage 1 response-free geography: `benchmarks/frozen/thalassia_response_free/`;
- Stage 2 response-free predictors: `benchmarks/frozen/thalassia_stage2_predictors/`;
- Stage 3A schema-only artifact: `benchmarks/frozen/thalassia_stage3_schema/`;
- controlling response contract: `docs/eog_v2_thalassia_stage3_microsatellite_contract.md`;
- nested conventional-reference selector: `docs/eog_v2_nested_genetic_reference_contract.md`.

Frozen source workbook:

- Dryad DOI `10.5061/dryad.404rm`;
- UWA-declared Zenodo mirror `4937634`;
- `Genalex_Th3all_IAA.xlsx`;
- size `118400` bytes;
- MD5 `ec25c053161d4d62b86c860193475784`;
- SHA-256 `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`.

## Schema-only result already frozen

The first authorized workbook opening was schema-only run `31668567528` and did not compute MLGs or FST.

It admitted exactly one GenAlEx block:

- sheet `Genalex`;
- `806` samples;
- `17` populations;
- `16` codominant loci;
- population tokens exactly matching the frozen GPS codes;
- zero missing allele cells in the released workbook;
- zero partially missing locus pairs.

Schema fingerprint: `a0b2c6bb0755f1d09f9aa88fbe4bfa645c5a4c8f011907fe4ceb93f64ff674de`.
Audit fingerprint: `3734a91c72f5f3fc7732e490216b9218b52f79a2506453039a8b2d72a01c03f9`.

These observed schema facts do not alter the already frozen complete-case/missing rules; those rules remain applicable even though this released workbook happens to contain no missing allele cells.

## Frozen response builder

`benchmarks/thalassia_genalex_stage3.py` is the only primary parser/response builder authorized after the pre-FST harmonization manifest is archived.

It must implement the controlling contract exactly:

1. verify exact source SHA-256;
2. mechanically align all 17 populations using only frozen Code/Site-name aliases;
3. parse all 16 diploid microsatellite loci;
4. complete-case filter all 16 loci;
5. exact within-population 16-locus MLG clone correction;
6. deterministic clone representative by normalized sample ID then source row;
7. require at least two unique complete MLGs per population;
8. compute all 136 pairwise multilocus Weir-Cockerham (1984) theta estimates with the already tested Zhoushan implementation;
9. do not clip theta;
10. stop as `non_estimable_linearized_fst_domain` if any theta is negative, non-finite or `>=1`;
11. otherwise transform every pair as `theta / (1-theta)`.

The all-complete-ramet calculation remains a descriptive, non-promotional sensitivity only.

## Nested validation and decision

Use the byte-frozen Stage-2 candidate family exactly:

- `gabriel_current_flow`;
- `gabriel_shortest_path`;
- `geographic`.

EOG never participates in conventional-reference selection.

For each outer held-out population, select the conventional reference by inner population-held-out equal-weight MSE, fit the selected reference and the same reference+EOG on outer training, and score on the untouched 16 pairs involving the outer population.

Also retain fixed geographic-only outer predictions to evaluate selector adequacy.

Common ridge penalty: `1.0`.

Bootstrap:

- held-out population is the replication unit;
- seed `20260813`;
- exactly `10,000` resamples;
- 95% percentile interval for mean `MSE(selected+EOG)-MSE(selected)`.

GO requires all:

1. all 17 populations / 136 primary pairs are admissible;
2. pooled nested-selected conventional MSE `<=` pooled fixed-geographic MSE;
3. equal-weight mean outer-population delta MSE `<0`;
4. bootstrap upper 95% bound `<0`.

If condition 2 fails: `indeterminate_selector_reference_failure`. If conditions 3-4 fail: retain null/adverse status. No candidate/reference/graph/EOG/parser/clone/FST/transform rescue is permitted after the primary response is computed.

## Pre-FST implementation identity

The exact parser, tests, this harmonized contract, the controlling first contract, Stage-2 artifact and Stage-3A schema artifact are fingerprinted together in `benchmarks/frozen/thalassia_stage3_preaccess/manifest.json` immediately before the one-time FST workflow.

That manifest must accurately record that schema-only workbook cells **have** been accessed but that MLG/FST/genetic-response computation is still false.

## Claim boundary

This is an independent symmetric microsatellite-isolation validation. It does not validate asymmetric ocean-current/gene-flow direction, colonization probability, or calendar-time propagation.
