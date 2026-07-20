# Bridge sensitivity across graph declarations

A single bridge graph is conditional on radius, k-nearest-neighbour degree, environmental-jump filters, barrier inputs and cost weights. `evaluate_bridge_sensitivity` evaluates one declared population pair across a frozen ensemble of such assumptions.

## Outputs

- `connected_frequency`: fraction of all declared scenarios in which source and target are connected;
- `minimum_cost_node_support`: among connected scenarios, the fraction whose minimum-cumulative-cost path uses each intermediate node;
- `minimum_bottleneck_node_support`: the corresponding frequency for minimax paths;
- `minimum_cost_edge_support`: edge frequencies among connected minimum-cost paths;
- `positive_bridge_gain_frequency`: among connected scenarios containing a direct source-target edge, the fraction in which an intermediate path has lower cumulative cost;
- p10, median and p90 summaries of cumulative, bottleneck, geographic, environmental, barrier and redundancy diagnostics.

Disconnected scenarios remain in the denominator of `connected_frequency`. They are not silently discarded. Node and edge support frequencies use connected scenarios as their denominator because no path exists in disconnected scenarios.

## Interpretation boundary

These frequencies quantify sensitivity to the supplied scenario ensemble. They are not Bayesian posterior probabilities, colonisation probabilities, occupancy probabilities, dispersal probabilities or evidence that a historical route was used.

A scenario ensemble should be justified before inspecting results. It should cover biologically defensible graph-construction and weighting assumptions, not a grid selected to maximise support for a preferred bridge.

## Recommended reporting

Report at least:

1. every scenario declaration and fingerprint;
2. connected frequency;
3. disconnected scenario reasons;
4. node and edge support on both minimum-cost and minimax paths;
5. cost quantiles;
6. direct-edge bridge-gain support where applicable;
7. the distinction between construction sensitivity and biological uncertainty.
