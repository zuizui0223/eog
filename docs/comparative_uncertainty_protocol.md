# Comparative EOG effect sizes and sampling diagnostics

Comparative EOG contrasts are valid only when both groups are transformed by the same frozen robust reference. The reference fingerprint must be archived with every result.

## Primary effect size

For comparative extent, report `log(span_B / span_A)` and the span difference in the shared reference units. A positive log ratio means group B is broader than group A in that declared coordinate system.

For `continuity` and `gap_strength`, report simple B-minus-A differences only for groups assigned to the same predeclared support class. These summaries are not comparable across arbitrary cloud geometries.

## Matched-size subsampling

Unequal occurrence counts can change pairwise-distance quantiles even when the generating geometry is unchanged. Every resampling draw therefore uses the same absolute number of rows from both groups:

`floor(min(n_A, n_B) * resample_fraction)`

with a minimum of four rows. The primary estimate is the median matched-size contrast, not the contrast between unequal full samples.

The percentile interval describes sensitivity to thinning the observed occurrence records. It is not a confidence interval over independent ecological populations, a correction for sampling bias, or a posterior interval.

## Direction diagnostics

Direction stability is the fraction of matched-size draws with the same sign as the median contrast. It must not by itself be interpreted as inferential certainty.

A separate label-permutation diagnostic compares the observed matched-size contrast with contrasts obtained after randomly reallocating pooled rows. This diagnostic is valid only when exchangeability under the declared comparison design is plausible. Spatial, temporal, phylogenetic, or survey-design dependence can invalidate that assumption and must be addressed outside this function.

`direction_supported` requires both:

- direction stability of at least 0.90; and
- permutation p-value below 0.10.

`ambiguous` is the logical negation of `direction_supported`. This flag is a reporting guardrail, not proof of no difference.

Each result must include:

- matched-size median effect estimate;
- percentile sensitivity interval;
- matched resample size, fraction, and number of draws;
- direction stability;
- permutation p-value and number of permutations;
- direction-supported and ambiguity flags;
- reference fingerprint;
- support class when required.

## Prohibited uses

Do not compare outputs produced under different references. Do not treat occurrence rows as ecological replicates. Do not call the permutation diagnostic valid when exchangeability is implausible. Do not select resampling fractions, reference modes, or support classes after inspecting which choice gives the strongest contrast.
