# Branching temporal-path Pareto frontier v2

Frozen protocol commit: 4d440ccfaf8669540b0e4e720d1c10efa35ba227. Stacked on draft PR #759 (head f3e59d1c7d5289e0395f62d067a7b4f4e4e43f94). The local Python 3.13.5 runner and receipt were verified against the Git blob SHAs 6ca89c68ef8ffd1950ef9257ff3e52278dd1a39f and 5eb8d9ef37fce342bf6fd86f91df6c53cdbd27a1.

## Method and exactness

For a finite time-directed graph with declared edge costs (duration, distance/duration, environmental transition, barrier permission), a path's required bounds are the componentwise maxima over its edges. Hard-blocked edges are never permitted. At each (node, checkpoint progress) retain the Pareto-minimal vectors of feasible prefixes. Componentwise max is monotone under coordinatewise dominance, so pruning dominated labels cannot remove a minimal completed path. Strict time increase permits a topological pass. The benchmark uses node IDs as distinct integer times, one node per time, no implicit waiting, and ordered checkpoint IDs. This is not yet a general multi-location-per-time adapter. The checkpoint constraint is appropriate to one declared trajectory, not to independent occurrences of multiple individuals/populations.

The possible frontier is Pareto-minimal union of world frontiers. The all-world feasible frontier is Pareto-minimal componentwise maxima of one path vector from each world, i.e. intersection of their upward-closed feasible sets. It means every world has some path, not one common path; an empty world makes the robust frontier empty. Speed ratios use exact rational arithmetic. This is exact for continuous nonnegative bound values on the finite declared graph/time states, not for continuous space/time or unknown routes. The label algebra and multiobjective shortest-path principles are not claimed as new mathematics.

## Results

- All four constructed boundary witnesses passed (tradeoff, checkpoint alias, world quantifier including an empty world, hard block).
- 480 world-level DP versus independent exhaustive DFS comparisons and 480 possible/robust aggregate comparisons: 0 disagreements.
- 321/480 worlds have no checkpoint-constrained path; 96/480 have independently reachable checkpoint and target but no single path visiting both in order. 31/480 have multiple nondominated path vectors.
- Of 240 paired systems, 109 are possible but not robust feasible; in 24 both worlds have a path but the robust frontier differs from possible. Total frontier differences 133/240.

Canonical tradeoff vectors (G,V,E,B): (2,3,1,1) and (3,2,2,0). If the two paths belong to different worlds, the possible frontier stays unchanged, but the robust frontier is (3,3,2,1). This is a shared bound across worlds, not an assertion that those conditions occurred in nature.

These results are generator-specific finite synthetic checks, not biological error rates or independent ecological replications. The random graph generator contains independently drawn worlds and one node per time; no natural uncertainty distribution is calibrated. No McKee source or dense 2h holdout accessed, clock/CRS STOP maintained, frozen EOG-WF 3 scored / 31 scientific STOP / 3 administrative exclusions unchanged. No production API change. Next methodological gate is multi-location per time with explicit wait/transition and checkpoint observation sets, followed by scalability and independent source qualification; no source STOP override.

Replay: `python validation/temporal_path_pareto_v2/run.py` (Python 3.13.5 archived). Compare with result.json.
