# Comparative EOG effect sizes and uncertainty

Comparative EOG contrasts are valid only when both groups are transformed by the same frozen robust reference. The reference fingerprint must be archived with every result.

## Primary effect size

For comparative extent, report `log(span_B / span_A)` and the span difference in the shared reference units. A positive log ratio means group B is broader than group A in that declared coordinate system.

For `continuity` and `gap_strength`, report simple B-minus-A differences only for groups assigned to the same predeclared support class. These summaries are not comparable across arbitrary cloud geometries.

## Uncertainty

Intervals are produced by repeated, matched-fraction, within-group subsampling. They describe sensitivity to the observed occurrence sample. They are not confidence intervals over independent populations, corrections for sampling bias, or posterior probabilities.

Each result must include:

- the full-sample effect estimate;
- percentile interval;
- resampling fraction and number of draws;
- direction stability;
- an ambiguity flag;
- reference fingerprint;
- support class when required.

A result is ambiguous when its interval crosses zero or fewer than 90% of resamples preserve the full-sample direction.

## Prohibited uses

Do not compare outputs produced under different references. Do not treat occurrence rows as ecological replicates. Do not select resampling fractions or reference modes after inspecting which one gives the strongest contrast.