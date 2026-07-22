# Spatial support-topology extension to the EOG manuscript program

## Central question

> How can pointwise species-distribution support be transformed into occurrence-conditioned spatial components and competing reachability hypotheses in fragmented landscapes?

## Layered manuscript architecture

The integrated EOG program should distinguish four questions.

| Layer | Input | Question | Primary output |
|---|---|---|---|
| Environmental-state geometry | Observed occurrence-by-feature matrix | How are observed environmental states dispersed or separated under a declared transformation? | Span, MST compactness, separation diagnostics |
| Spatial support topology | Frozen geographical support field | Which superlevel regions form stable occurrence-anchored or detached components? | Component lineage, persistence, anchors, area, support summaries |
| Bridge inference | Declared nodes/components and edge costs | Under which assumptions can declared components or populations be connected? | Cumulative-cost and minimax paths, redundancy, sensitivity |
| Hypothesis survey | Competing bridge families and candidates | Where would observations discriminate among connection hypotheses? | Audited survey ranking and report |

The word `continuity` should not be used as a blanket term across these layers. In environmental-state geometry, the legacy API quantity should be described as **MST compactness**. In geographical grids, use **spatial support topology**. For declared source-target graphs, use **bridge inference**.

## Proposed contribution statement

EOG converts pointwise environmental support into occurrence-conditioned spatial components and explicit reachability hypotheses. Its contribution is not a replacement SDM and not a new shortest-path algorithm. It is an auditable separation of local support, persistent spatial component structure, bridge assumptions, and hypothesis-discriminating survey decisions.

## Support-topology estimand

For a frozen support field `s(x)` and predeclared thresholds `tau`, define superlevel sets

```text
R_tau = {x : s(x) >= tau}.
```

The support-topology layer tracks geographical connected-component lineages across thresholds under an explicit four- or eight-neighbour rule and a hard availability mask. Components are classified as occurrence anchored, persistently detached, transiently detached, or low-support/unresolved. A detached component's lower-threshold merger into an anchored component is recorded, but no route or bottleneck path is inferred.

## Validation sequence

1. Unit tests establish masking, anchoring, persistence, deterministic IDs, and edge-case behavior.
2. Synthetic islands show that identical local support can have different structural classes.
3. Baselines compare local support, nearest-anchor distance, support plus distance, single-threshold components, and multi-threshold topology.
4. Empirical evaluation uses training-only support and island- or region-level held-out detections.
5. Bridge and survey analyses are run only after component construction is frozen.

## Claim limitations

The manuscript must not conclude that a detached component proves fragmentation, true absence, genetic isolation, demographic independence, a causal barrier, colonisation probability, or historical dispersal. `Persistent` refers only to identification across the declared threshold sequence. Empirical claims require independent detections or other external evidence.

## Campanula microdonta case

The existing シマホタルブクロ case is exploratory because prior field outcomes influenced development. A later confirmatory analysis must freeze historical occurrence anchors, support producer and training data, raster mask and resolution, threshold sequence, neighbourhood rule, and held-out detections before topology is calculated. Thresholds must not be chosen after reading held-out detections.
