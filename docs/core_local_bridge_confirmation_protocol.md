# Independent confirmation of the core local bridge score

This protocol addresses issue #13. The statistic was frozen before this confirmation:

1. robust-scale the declared feature matrix;
2. estimate each point's local scale from the median distance to its five nearest neighbours;
3. discard the 10% of points with the largest local scales;
4. rebuild the MST on the retained core;
5. divide the longest core edge by the larger local scale at its two endpoints;
6. multiply by the smaller-component fraction divided by 0.5.

No neighbour count, trimming proportion, scaling rule, or formula may be changed in response to this confirmation.

## Independent generators

Connected cases include correlated Gaussian clouds, Student-t clouds with df 3 and 8, two skew strengths, S-shaped and ring manifolds, and Gaussian cores contaminated by 2%, 5%, or 10% remote points.

Fragmented cases include three unseen two-mode separations, unequal 20:80 and 35:65 modes, and three unseen missing-bridge widths.

Sample sizes are 60, 120, and 240. Analyses use 2, 4, and 8 dimensions. Only the two-informative-feature analysis is primary; higher-dimensional analyses are untuned negative controls.

## Frozen confirmation gate

The confirmation passes only if all conditions hold in the primary two-dimensional analysis:

- minimum fragmented-versus-connected AUC >= 0.80;
- minimum AUC improvement over raw gap strength >= 0.30;
- AUC >= 0.75 for unequal 20:80 modes;
- no connected-generator median exceeds the matched fragmented median.

A failed gate is retained. The score must not enter the public API or manuscript-scale real-data analysis after failure.
