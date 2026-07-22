# Support topology stress benchmark

## Question

Does the headline distinction between an occurrence-anchored support component and a persistent detached support component remain identifiable under predeclared analytical perturbations?

This benchmark addresses numerical and structural sensitivity. It does not test whether the topology classes predict occupancy, colonisation, dispersal, or future detections.

## Frozen synthetic design

The support field contains two land components separated by hard masked sea cells.

- The western island contains one historical occurrence anchor.
- The eastern island has a similar range of local support values but no anchor.
- A near-threshold one-cell land patch is included so that low-persistence noise may vary without changing the two headline components.

The baseline threshold sequence is `0.80, 0.70, 0.60`, with four-neighbour connectivity and two required threshold appearances for persistent classification.

## Predeclared stress dimensions

The benchmark varies:

1. threshold density and placement;
2. four- versus eight-neighbour connectivity;
3. nearest-neighbour grid refinement at factors 1, 2, and 3 while preserving equal-area cell totals;
4. occurrence-anchor position within the same western land component;
5. 50 deterministic Gaussian support perturbations with standard deviation 0.02 on available cells.

For each scenario, the benchmark records the complete class count and fingerprint. The primary retention indicator asks whether both of the following remain present:

- `occurrence_anchored_component`;
- `persistent_detached_component`.

Transient component frequency is reported separately rather than treated as failure of the headline structure.

## Frozen results contract

The workflow freezes both positive and negative results.

Expected stable dimensions:

- 100% retention across threshold sequences;
- 100% retention across neighbourhood rules;
- 100% retention across tested grid refinements;
- at least 90% retention under frozen support noise.

Expected negative result:

- anchor-position retention is `0.2` (one of five tested positions).

Under the current birth-state rule, a component is labelled occurrence anchored only when an anchor is already present in its first recorded superlevel-set snapshot. Four anchors located on lower-support cells enter the same western component only at lower thresholds, so the western component remains classified from its unanchored birth state. This exposes a genuine anchor-threshold dependence rather than a runtime error.

The exact JSON output is uploaded by `.github/workflows/support-topology-stress.yml` as `support-topology-stress-results`.

## Interpretation

The positive results show that the two-island structural distinction is stable to the tested threshold lists, neighbourhood rules, raster refinements, and small support perturbations in this frozen design.

The negative anchor result means the occurrence-anchored label is not yet robust to within-component anchor support. Before empirical use, EOG must either:

1. require anchors to be active at the highest analysed threshold and audit that requirement; or
2. revise the classification rule so later anchor entry changes the component's anchor status while preserving lineage history.

No empirical claim should rely on anchor classification until that design choice is resolved and revalidated.

This benchmark does not show that the method outperforms support-only or distance-only baselines. It does not establish biological isolation, occupancy, demographic connectivity, or historical dispersal. Those require held-out empirical comparisons.
