# EOG v2.1 Thalassia Stage-3 microsatellite response contract

## Status

**Frozen before the microsatellite workbook container, worksheet names, cells, alleles, multilocus genotypes, pairwise FST or other genetic response are opened by EOG v2.1.**

Parent response-free artifacts:

- Stage-1 geography: `benchmarks/frozen/thalassia_response_free/`;
- Stage-2 predictors: `benchmarks/frozen/thalassia_stage2_predictors/`;
- Stage-2 manifest fingerprint `ef119675a596fe2044aca97b43efc618cfb7b00aee1dc3a1663ff5736c0a94ea`;
- frozen candidate family `gabriel_current_flow`, `gabriel_shortest_path`, `geographic`;
- frozen exact-eventual connectivity fingerprint `e0ab1d046906d362b6766ec7b887e300d25efb119282406a0daf319abd156f89`.

Response source identity:

- Dryad DOI `10.5061/dryad.404rm`;
- UWA-declared archival mirror Zenodo `4937634`;
- file `Genalex_Th3all_IAA.xlsx`;
- released size `118400` bytes;
- MD5 `ec25c053161d4d62b86c860193475784`;
- SHA-256 `aaaab9e302c9be8cf4e108d2aee5867c0b64ed70b6d3b81bad4d60168ee7f2f3`.

No other genetic file may substitute for this workbook in the primary response.

## Source-method boundary

The source article reports a panel of 16 microsatellite markers but the full original methods text is not lawfully available to this automated workflow. EOG therefore does **not** claim to reproduce the publication's exact pairwise FST software/settings unless a later independent cross-check establishes that equivalence.

The response estimator below is frozen as an auditable EOG validation response before genotype access. It is supported by the marker/data type, standard codominant microsatellite practice, and related `T. hemprichii` work, but it is labelled a raw-genotype recomputation rather than an exact reproduction of an unseen published matrix.

GenAlEx 6.5 format documentation defines codominant genotypes as two adjacent columns per locus, sample labels in column 1, population labels in column 2, and codominant missing alleles as `0`.

## Stage 3A — first authorized schema audit

Only after this contract is committed may the exact workbook be opened.

The first opening is a **schema audit only**. It may report:

- workbook sheet names and dimensions;
- the standard GenAlEx parameter cells / row locations;
- declared number of loci, samples and populations;
- population-size parameters and population-label tokens;
- locus header names and the fact that each locus uses two adjacent allele columns;
- sample-label uniqueness;
- counts of empty/zero allele cells and partially missing diploid locus pairs;
- mechanical population-token alignment to the frozen 17 nodes.

Stage 3A must not compute or report:

- allele frequencies;
- heterozygosity or allelic richness;
- multilocus genotype identities/counts;
- pairwise or overall FST;
- clusters, assignments, migration or genetic distances.

### Population alignment

Frozen primary IDs are:

`BIA, TUA, AMB, KEN, BIT, PAL, JEP, PAR, BAN, NAT, KUP, MAT, DRI, PAD, CK, MI, Ex2`.

A workbook population token may map only by a response-free alias table constructed from Stage-1 `Code` and `Site name` fields. Matching is case-insensitive after trimming whitespace and removing non-alphanumeric characters. Every token must resolve uniquely to exactly one frozen population and every frozen population must be represented. No allele/genetic similarity may assist mapping.

### Schema admission

Stage 3A passes only if all are mechanically true:

1. the exact released SHA/size identity matches;
2. exactly one standard codominant GenAlEx data block can be identified without using allele distributions;
3. it declares exactly 16 loci and 17 populations;
4. the declared sample count equals the number of data rows used by the block;
5. each locus has exactly two adjacent allele columns;
6. sample IDs are non-empty and unique;
7. all population tokens map uniquely to all 17 frozen population IDs;
8. allele cells are numeric or missing (`0`/empty); nonzero allele codes are positive;
9. no population/node addition, deletion, merge, rename or relocation is required.

If this fails, status is `non_estimable_microsatellite_schema_or_population_alignment` and no FST is computed.

## Stage 3B — frozen primary genetic response

Stage 3B is authorized only after a successful Stage-3A schema artifact is archived.

### Individual eligibility

Primary analysis uses only samples with complete non-missing diploid genotypes at **all 16 frozen loci**. A locus is missing for a sample if either allele is `0` or empty. Partially missing allele pairs are treated as missing; no imputation occurs.

No locus is removed for HWE, null alleles, linkage, polymorphism, observed FST, influence, or apparent fit. All 16 released loci remain in the primary estimator.

### Exact multilocus clone correction

`T. hemprichii` is clonal. Primary analysis therefore uses one representative of each **exact complete 16-locus multilocus genotype (MLG) within each frozen population**.

Canonical MLG identity is the ordered 16-locus vector after sorting the two allele codes within each locus. Only exact complete matches qualify as duplicates; near matches are never merged.

For an exact duplicate MLG within a population, retain the deterministic representative with the lexicographically smallest normalized sample ID; source row number is the secondary tie breaker. No cross-population MLG collapse is performed.

If any frozen population has fewer than two unique complete 16-locus MLGs after this rule, primary status is `non_estimable_insufficient_clone_corrected_genets`; that population is not dropped to rescue the analysis.

### Pairwise FST estimator

Compute all `17 choose 2 = 136` unordered pairwise multilocus **Weir & Cockerham (1984) theta** estimates using the already unit-tested implementation in `benchmarks/zhoushan_weir_cockerham.py`:

- all 16 loci in frozen order;
- each locus contributes the sample-size-corrected multiallelic `a`, `b`, `c` variance components;
- multilocus theta is `sum(a) / sum(a+b+c)` across all usable allele/locus components;
- no FST value is clipped.

Because Stage 2 froze `linearized_fst`, every primary pair must be finite and satisfy `0 <= theta < 1`. If any primary pair is negative, non-finite, or `>=1`, status is `non_estimable_linearized_fst_domain`. Negative theta is **not** rounded to zero after it is seen.

Primary response matrix is:

`linearized_fst = theta / (1 - theta)`.

The raw theta matrix is retained alongside the transformed response.

## Predeclared sensitivity — not promotional

A descriptive sensitivity uses all **complete 16-locus ramets** without exact-MLG collapse, with the same 16 loci and Weir-Cockerham estimator. This sensitivity never substitutes for the primary clone-corrected response and never determines `promotion_go`.

No incomplete-sample imputation, locus filtering, alternative FST estimator or post-response clone threshold is permitted on this dataset's primary line.

## Nested prediction and decision

Use only the byte-frozen Stage-2 predictors.

For every outer held-out population:

1. remove all pairs involving the outer population from training and conventional-reference selection;
2. select among the frozen conventional candidates `gabriel_current_flow`, `gabriel_shortest_path`, `geographic` using inner leave-one-population-out equal-weight population MSE;
3. exact ties resolve lexicographically;
4. fit the selected conventional baseline on outer training;
5. fit the **same** selected conventional reference + frozen exact-eventual EOG continuous distance + disconnection indicator;
6. score both on all 16 untouched pairs involving the outer population.

EOG never participates in candidate selection.

Common ridge penalty: `1.0`.

Also score the fixed `geographic`-only model on the same outer folds, independent of the nested selector, to test whether the selected conventional baseline is operationally competitive.

## Frozen bootstrap and GO rule

Inference unit: held-out population.

For each of 17 outer populations retain:

`delta_MSE = MSE(selected conventional + EOG) - MSE(selected conventional)`.

Bootstrap:

- exactly `10,000` population resamples with replacement;
- seed `20260813`;
- 95% percentile interval of the equal-weight mean `delta_MSE`.

A dataset-level GO requires all:

1. all 17 populations / 136 primary pair responses are represented under the frozen clone-corrected response;
2. pooled outer MSE of the nested-selected conventional baseline is `<=` pooled outer MSE of fixed geographic-only;
3. equal-weight mean outer-population `delta_MSE < 0`;
4. bootstrap upper 95% bound `< 0`.

If condition 2 fails, status is `indeterminate_selector_reference_failure`; no candidate is dropped. If conditions 3–4 fail, the result is retained as null/adverse. Any non-estimable primary response condition above stops before a promotion decision.

## Irreversible boundaries

After Stage 3A begins, none of the following may change on this dataset:

- the 17 nodes or coordinates;
- projection/Gabriel graph;
- candidate reference family;
- EOG operator/connectivity;
- response transform;
- ridge penalty;
- exact-MLG clone rule;
- 16-locus inclusion rule;
- FST estimator;
- nested selector;
- bootstrap seed/count;
- GO/NO-GO thresholds.

Symmetric pairwise FST cannot validate directional migration/current effects. Directionality remains out of scope.
