# Mode-separation comparator benchmark

This document records the frozen outcome of issue #15 and PR #16.

## Question

The benchmark asked whether the developmental `core_local_bridge_score` should replace conventional two-cluster diagnostics as a named manuscript measure of mode separation.

The comparison used:

- raw `gap_strength`;
- frozen `core_local_bridge_score`;
- two-cluster K-means silhouette;
- centroid separation normalized by within-cluster dispersion.

Connected controls were correlated Gaussian, t3, skewed, S-curve, ring, and 5% remote-point contamination. Mode cases were overlapping, medium, and wide equal modes plus 20:80 and 35:65 unequal modes at n = 60, 120, and 240.

## Verified decision values

- minimum core-local-bridge AUC: 0.5208;
- minimum K-means silhouette AUC: 0.1163;
- minimum unequal-mode core-bridge advantage over silhouette against contamination: 0.0000;
- predeclared publication gate: failed.

## Structure-specific pattern

The failure does not imply identical behavior.

For equal modes, the core-local-bridge score substantially exceeded forced two-cluster silhouette when connected curved and ring-like controls were included. Examples:

- equal-medium, n=120: core bridge AUC 0.9096 versus silhouette 0.1633;
- equal-wide, n=240: core bridge AUC 0.9988 versus silhouette 0.2121;
- equal-overlap, n=240: core bridge AUC 0.5208 versus silhouette 0.1421.

For unequal modes, conventional clustering was already extremely strong:

- 20:80 modes: silhouette AUC 0.9742 to 0.9917;
- 35:65 modes: silhouette AUC 0.9238 to 0.9913;
- core bridge did not obtain the predeclared >=0.05 advantage over silhouette against the contaminated connected control.

## Interpretation

No single winner should be declared.

- K-means silhouette answers whether a forced two-cluster partition is compact and separated, and is especially effective for strongly imbalanced modes in this benchmark.
- The core-local-bridge score answers whether a balanced dense-core split is supported by a locally long MST bridge, and is less easily impressed by arbitrary two-way partitions of S-shaped and ring-like connected clouds.

The core-local-bridge score therefore must not be promoted as a universal replacement for clustering or as a general fragmentation statistic. The defensible next use is as a complementary, topology-sensitive diagnostic reported beside conventional clustering, with disagreement treated as information rather than averaged into a tuned ensemble.

## Publication decision

The issue #15 publication gate failed. The score remains outside the public API. Any real-taxon application must be exploratory and must report both the score and conventional clustering diagnostics without selecting taxa or interpretations from one metric alone.
