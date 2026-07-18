# Environmental occupancy geometry evidence ledger

This file separates verified results from interpretation. The original development and validation history is preserved in `zuizui0223/acsp` PR #35 and its GitHub Actions artifacts; the standalone implementation was frozen from ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e` and API-contract commit `3d2017e9a342eca13f0a17f1d3c473a993c4335a`.

## Frozen primary quantities

- `continuity`: maximum pairwise distance divided by total MST length.
- `gap_strength`: largest positive MST edge divided by the median positive MST edge.
- `span`: supporting 0.90 quantile of positive pairwise distances by default.
- `component_count`: diagnostic only.

## Synthetic topology discrimination

The final ACSP benchmark matched fragmentation scenarios to the same mean and covariance. Verified summary values were:

- PCA breadth range: 0.
- Gaussian log-volume range: numerical zero.
- two-mode gap strength / connected gap strength: about 2.33.
- missing-bridge gap strength / connected gap strength: about 3.38.
- curved-path continuity / straight-path continuity: about 0.49.

Interpretation: `gap_strength` detects internal fragmentation not represented by covariance breadth, while `continuity` detects path tortuosity. The MST and largest-edge concepts themselves are not claimed as novel.

## Sample-size and dimensionality robustness audit

The standalone predeclared audit used sample sizes 30, 60, 120, and 240, with zero, two, or six added independent noise features and 50 repeats per cell.

Verified clean two-feature results:

- minimum two-mode versus connected `gap_strength` AUC across sample sizes: 0.9488;
- minimum curved versus straight `continuity` AUC across sample sizes: 1.0000;
- connected-null median `gap_strength`: about 2.79 at n=30, 3.23 at n=60, 3.39 at n=120, and 4.57 at n=240;
- clean connected-null median range across sample sizes: about 1.78.

Verified results with six irrelevant features:

- minimum gap-strength AUC: 0.2396;
- minimum continuity AUC: 0.5360.

Interpretation: the intended clean two-dimensional signals are robust over the tested sample sizes, but the absolute null distribution of `gap_strength` is sample-size dependent. A universal raw `gap_strength` cutoff is therefore unsupported. Independent irrelevant dimensions can erase or reverse discrimination, so environmental variables must be selected or reduced using a predeclared procedure. EOG must not be described as robust to arbitrary high-dimensional feature matrices.

## Matched-null calibration and feature-selection audit

The issue #3 audit compared raw gap strength with an empirical percentile obtained from connected Gaussian reference clouds matched to the observed sample size, feature dimension, mean, and covariance. It used 20 repeats and 40 null draws per observed matrix.

The original predeclared gate failed:

- minimum per-cell ecological-preselection calibrated AUC: 0.8025;
- maximum per-cell connected-null median deviation from 0.50: 0.225;
- pooled ecological-preselection AUC at n=30: 0.8563.

This failure is retained as evidence that n=30 is underpowered for confirmatory fragmentation claims.

After pooling scenarios that differ only in variables discarded by ecological preselection, verified results were:

- pooled calibrated AUC at n=60: 0.9701;
- pooled calibrated AUC at n=120: 0.9535;
- pooled calibrated AUC at n=240: 0.9260;
- minimum pooled calibrated AUC for n >= 60: 0.9260;
- maximum pooled connected-null median deviation from 0.50 for n >= 60: 0.0500.

Raw connected-cloud medians still increased strongly with sample size, from about 3.18 at n=30 to about 7.40 at n=240. The calibrated connected-null medians remained between 0.475 and 0.575.

Feature-strategy interpretation:

- ecological preselection is the primary analysis rule;
- correlation filtering at |r| >= 0.80 is a secondary sensitivity analysis only;
- PCA90 and all-variable analyses are supplementary negative controls;
- arbitrary all-variable input is not supported;
- confirmatory gap comparisons require at least 60 occurrence states;
- raw and calibrated gap values must be reported together.

The calibrated percentile is a sample-size-comparative diagnostic, not a posterior probability that a cloud is fragmented.

## Direct CHELSA random-taxon confirmation

The frozen confirmation cohort excluded Campanula and used occurrence coordinates sampled directly against CHELSA bio1, bio4, bio12, and bio15.

- predeclared taxon-region pairs: 12.
- technically eligible and informative pairs: 11.
- median span relative error: about 0.079.
- median continuity absolute error: about 0.030.
- median gap-strength relative error: about 0.119.
- positive nearest-state projection lift: all evaluable pairs.
- complete success: 10 of 11 evaluable pairs.

## Comparator benchmark

Median thinning errors in the verified cohort:

- K-means silhouette: about 0.023.
- continuity: about 0.030.
- span: about 0.079.
- gap strength: about 0.119.
- PCA breadth: about 0.121.
- Gaussian log-volume: about 0.395.

These results do not support a universal-superiority claim. K-means silhouette was highly reproducible but measures a fixed two-cluster separation, whereas EOG directly summarizes MST path directness and strongest internal discontinuity.

## Incremental-information analysis

The real-taxon incremental analysis was exploratory because only eight pairs were evaluable.

- continuity LOO Q2: about -1.69.
- gap-strength LOO Q2: about -5.95.
- largest absolute Spearman correlation between continuity and conventional summaries: about 0.79.
- largest absolute Spearman correlation between gap strength and conventional summaries: about 0.48.

Interpretation: conventional summaries did not reconstruct the topology metrics in this small cohort. Continuity overlaps substantially with clustering and must be described as complementary rather than independent. Gap strength is the stronger novelty candidate.

## Unsupported claims

The current evidence does not establish that EOG:

- replaces species distribution models;
- outperforms every hypervolume, clustering, or topological method;
- introduces the MST, single-linkage, or largest-edge statistic;
- proves causal ecological mechanisms;
- has universal behavior across taxa and environmental variable sets;
- supports one universal raw `gap_strength` threshold across sample sizes;
- is robust to arbitrary inclusion of irrelevant environmental variables;
- supports confirmatory fragmentation inference with fewer than 60 occurrence states.
