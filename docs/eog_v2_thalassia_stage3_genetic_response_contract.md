# EOG v2.1 Thalassia Stage-3 genetic-response schema contract

## Status

**Prospective freeze before genetic cell access.** The released microsatellite workbook
`Genalex_Th3all_IAA.xlsx` remains opaque at this stage. This contract fixes the only parser,
missing-data rule, clone handling, pairwise FST estimator, and response transform that may be
used for the Thalassia independent genetic validation.

Parent contracts:

- Stage 1 response-free geography: `docs/eog_v2_thalassia_pre_genetic_contract.md`;
- Stage 2 response-free predictors: `docs/eog_v2_thalassia_stage2_predictor_contract.md`;
- nested conventional-reference selector: `docs/eog_v2_nested_genetic_reference_contract.md`.

Frozen source identities:

- study DOI: `10.1111/mec.13966`;
- Dryad DOI: `10.5061/dryad.404rm`;
- released genetic workbook SHA-256:
  `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`;
- Stage-2 predictor-bundle fingerprint:
  `ef119675a596fe2044aca97b43efc618cfb7b00aee1dc3a1663ff5736c0a94ea`.

The independent response is a newly computed symmetric microsatellite differentiation
endpoint. It is **not** a claim that EOG reconstructs the authors' published FST table exactly.

## Pre-response external format basis

Dryad describes the microsatellite workbook as GenAlEx-formatted genotype data. The source
paper describes a panel of 16 microsatellite markers. The official GenAlEx 6.5 guide specifies
that codominant genotypes use two columns per locus, population samples occur in contiguous
blocks, parameters and labels occupy rows 1-3, genotype data begin at C4, and codominant
missing data are encoded as `0`.

These public format statements are used only to define a parser before the genetic cells are
opened. They are not genetic outcomes.

## Frozen population universe

Use exactly the 17 Stage-1 population IDs, with Stage-1 site names as the only accepted
response-free aliases:

`BIA, TUA, AMB, KEN, BIT, PAL, JEP, PAR, BAN, NAT, KUP, MAT, DRI, PAD, CK, MI, Ex2`.

No numeric, inferred, fuzzy, or response-derived aliases may be added after access. No
population may be deleted, merged, split, or renamed from genotype content.

## GenAlEx sheet admission

The parser in `benchmarks/thalassia_genalex_stage3.py` is authoritative.

A worksheet is a candidate only if standard GenAlEx parameter cells state:

- `A1 = 16` loci;
- `C1 = 17` populations.

Exactly one candidate worksheet must satisfy the complete contract. Otherwise the dataset is
non-estimable for this validation.

For the admitted sheet:

1. `B1` is a positive integer sample count.
2. `D1...` contains 17 positive population sizes summing exactly to `B1`.
3. `D2...` contains the complete frozen population set, expressed only as frozen code or
   frozen Stage-1 site name.
4. row 3 supplies 16 unique, non-empty locus labels in the first column of each diploid pair
   (`C, E, G, ...`).
5. rows `4...(B1+3)` contain unique non-empty sample IDs in column A and frozen population
   labels in column B.
6. sample rows occur in the contiguous population blocks declared by rows 1-2.
7. the 32 allele columns are numeric finite non-negative integers.
8. undeclared non-empty raw cells below the declared sample block are prohibited.

A schema failure is a non-estimable stop. The parser is not modified to rescue this dataset.

## Missing-data rule

GenAlEx codominant missing value `0` is interpreted only as a diploid `0/0` genotype.

- `0/0` => missing locus for that sample;
- `0/x` or `x/0` with `x > 0` => schema failure;
- empty/non-numeric/non-integer allele cells => schema failure.

Before FST estimation, samples with any missing locus are removed as **complete-case
samples**. This rule is frozen before response access; no locus-specific or population-specific
missingness threshold is chosen after viewing the data.

## Clone handling

Because *T. hemprichii* is clonal, the response is computed on a predeclared genet-level
subset.

Within each population only:

1. use complete 16-locus MLGs after unordered allele-pair canonicalization;
2. identical complete MLGs are treated as exact clonemates for this validation;
3. retain exactly one representative, chosen deterministically by lexicographically smallest
   sample ID;
4. never collapse matching MLGs across different populations.

This is an operational, response-free clone rule. It does not claim to reproduce a
published `Psex`-based clone assignment. If a frozen population retains fewer than two complete
unique MLGs, the dataset is non-estimable and no rule is relaxed.

## Pairwise FST estimator

Use the already pre-response-frozen implementation in
`benchmarks/zhoushan_weir_cockerham.py`:

- multilocus Weir-Cockerham (1984) theta;
- sum variance components across all usable alleles/loci;
- no clipping to `[0, 1]`.

All 136 unordered population pairs must yield finite theta. Negative sampling estimates are
retained. Any non-finite theta or `theta >= 1` is a non-estimable stop; values are not clipped,
replaced, or pairwise-deleted.

## Genetic response transform

For every one of the 136 Stage-2 pair rows:

`linearized_fst = theta / (1 - theta)`.

Negative theta therefore remains negative after transformation. The frozen nested selector
receives this transformed response unchanged.

## Stage-4 execution boundary

Only after this Stage-3 contract, parser, tests, and fingerprints are committed may a one-time
workflow open the real genetic workbook.

That execution may only:

1. verify the frozen workbook SHA-256;
2. run the frozen parser;
3. apply the frozen complete-case / clone rules;
4. compute the frozen 136-pair response;
5. mechanically join it to the already archived Stage-2 predictors;
6. run the already frozen nested conventional-reference selection and promotion rule;
7. archive the response, QC counts, selected references, outer predictions, bootstrap result,
   and all fingerprints.

After workbook access there is no Thalassia-specific parser, clone, FST, transform, candidate
reference, graph, EOG, ridge, bootstrap, or promotion-rule rescue.

## Claim boundary

This dataset can validate only whether frozen EOG exact-eventual symmetric reachability adds
held-out information beyond a prospectively selected conventional symmetric genetic
reference. Symmetric FST does not validate directional dispersal, asymmetric gene flow,
colonization probability, or calendar-time propagation.

## Frozen implementation identity

- parser SHA-256: `6647440e581f62b3a8ed21064946e4366b7773b0ca5f54bd2ff389254ab047c3`;
- parser test SHA-256: `4ae295941668e8750fab55d564472791fe8d7c59ee3a4861fed299041e6d1a7a`;
- genetic workbook content accessed while defining these files: `false`;
- genetic response computed while defining these files: `false`.
