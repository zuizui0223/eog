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
- has universal behavior across taxa and environmental variable sets.
