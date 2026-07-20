# Population-pair bridge inference

EOG bridge inference evaluates a declared graph connecting one source population to one target population through occurrence, patch or candidate nodes.

It does **not** estimate suitability, occupancy probability, colonisation probability or a historical dispersal route. It reports relative path diagnostics under declared nodes, edges, cost components and weights.

## Edge components

Each undirected edge retains three non-negative components:

- geographic cost: distance or a declared dispersal-kernel transformation;
- environmental cost: shared-reference environmental distance;
- barrier cost: a structural penalty such as a sea crossing or ridge.

The weighted total is used for path optimisation, while the unweighted component totals remain available for interpretation.

## Outputs

- **minimum cumulative path**: path minimizing the sum of weighted edge costs;
- **minimum bottleneck path**: path minimizing the largest weighted edge cost that must be crossed;
- **direct edge cost**: source-to-target jump cost when declared;
- **bridge gain**: direct cost minus minimum cumulative path cost;
- **edge-disjoint path count**: number of alternative routes using only edges below a declared threshold.

A positive bridge gain means that declared intermediate states provide a lower cumulative-cost connection than the direct source-target edge. It does not show that those states are occupied or that the inferred route was historically used.

## Shared environmental reference

Environmental edge costs must be calculated under one predeclared `RobustReference`. Re-scaling each node group separately would erase between-state environmental differences and invalidate transition comparisons.

## Required next layers

The core intentionally defers candidate-node construction, survey effort, detection, temporal propagation, dispersal-kernel estimation and empirical validation. Those layers should be added as separately auditable modules rather than hidden inside edge weights.
