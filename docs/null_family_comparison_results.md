# Connected-null family comparison results

## Reproducibility

- GitHub Actions workflow: `Connected-null family comparison`
- Run ID: `29635479700`
- Artifact: `connected-null-family-comparison`
- Artifact digest: `sha256:85c52443288a3510f31a4a93a2490cbfe050e72a9456863265f77a344b97878e`
- Repeats per cell: 12
- Null draws per observed cloud: 24
- Sample sizes: 60, 120, 240

## Frozen decision

No candidate null family met the predeclared primary-null criteria. Manuscript-scale expansion remains blocked.

| Null family | Calibration loss | Minimum fragmented AUC | Minimum fragmented detection | Eligible |
|---|---:|---:|---:|---|
| Gaussian | 1.010 | 0.227 | 0.167 | No |
| Student t | 0.323 | 0.155 | 0.000 | No |
| Gaussian copula | 0.536 | 0.201 | 0.000 | No |
| Radial bootstrap | 0.273 | 0.672 | 0.083 | No |

## Interpretation

The Gaussian reference strongly over-rejected heavy-tailed, skewed, and curved connected clouds. Student t references were conservative for Gaussian clouds and erased fragmentation power. Gaussian-copula references preserved empirical margins but also absorbed much of the fragmented structure. Radial bootstrap gave the best trade-off, but still missed the frozen calibration threshold and had weak missing-bridge detection at larger sample sizes.

The failure is structural rather than a tuning accident. A null fitted to the complete observed cloud faces a conflict:

1. a restrictive connected family falsely calls non-Gaussian connected geometry fragmented;
2. a flexible family fitted to observed margins, radii, or dependence can reproduce the very discontinuity being tested and lose power.

Therefore EOG should not replace the Gaussian reference with another single fitted generative null. The next improvement should evaluate fragmentation through resampling stability of the largest-edge partition, component balance, and split persistence rather than interpreting one fitted-null percentile as the primary evidence.

## Manuscript consequence

- Retain raw `gap_strength` as a descriptive quantity.
- Retain the Gaussian percentile only as a documented sensitivity analysis for continuity with the pilot.
- Do not label any current percentile a calibrated fragmentation probability or primary inferential score.
- Do not begin the 30–50 pair confirmatory cohort until a model-free or weakly model-dependent stability criterion is validated.