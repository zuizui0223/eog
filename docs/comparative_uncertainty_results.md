# Comparative uncertainty audit results

## Outcome

The original audit failed because equal resampling fractions produced unequal absolute draw sizes when group sample sizes differed. For pairwise-distance quantiles, that design confounded sample size with comparative extent. In addition, the original percentile subsampling interval was incorrectly judged by coverage of the generating parameter even though it is a conditional thinning-sensitivity interval rather than a population confidence interval.

The corrected design uses the same absolute draw size for both groups and reports a separate exchangeability-based label-permutation diagnostic for directional support.

## Frozen benchmark

The benchmark used compact Gaussian clouds and two-fold dilated clouds under one external frozen reference, with sample sizes 60, 120, and 240, 20 repeats per sample size, unequal group occurrence counts, 100 matched-size subsampling draws, and 100 label permutations.

Verified decision values:

- median absolute error from the known `log(2)` extent contrast: `0.05713844418962438`;
- proportion of known-effect datasets with supported positive direction: `1.0`;
- proportion of equal-shape null datasets with false directional support: `0.08333333333333333`;
- completion gate: passed.

## Interpretation

Matched-size subsampling removed the direct sample-count confounding in comparative span. The known two-fold extent contrast was recovered accurately and consistently in this synthetic design.

The null false-support rate was below the predeclared 0.10 gate, but it was not zero. `direction_supported` is therefore a calibrated reporting diagnostic under this benchmark, not a guarantee and not a universal hypothesis test.

The permutation component requires exchangeability of pooled rows under the declared comparison. It is not valid by default for spatially clustered occurrences, repeated observations, temporal trajectories, phylogenetically structured units, or unequal survey processes. Such dependence must be handled in the sampling design or with an appropriate restricted permutation scheme before inferential language is used.

## Claim boundary

The audit supports reporting:

- matched-size log span ratios;
- span differences in a common frozen reference;
- conditional thinning-sensitivity intervals;
- direction stability;
- an explicitly assumption-dependent permutation diagnostic.

It does not establish ecological replication, unbiased occurrence sampling, occupancy differences, causal effects, or posterior probabilities.
