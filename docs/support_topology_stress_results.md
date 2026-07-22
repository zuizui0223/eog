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

For each scenario, the benchmark records the complete class count and fingerprint. The primary retention indicator asks whether both `occurrence_anchored_component` and `persistent_detached_component` remain present. Transient component frequency is reported separately.

## Anchor-lineage correction

The original benchmark exposed an anchor-position retention of `0.2`. The cause was a birth-state classification rule: a component born above the support value of its occurrence cell remained detached even after that occurrence entered the same lineage at a lower threshold.

EOG now propagates anchor status across the full component lineage while retaining the history needed for audit:

- `birth_anchor_ids` records anchors present when the component first appeared;
- `anchor_ids` records anchors encountered anywhere in the lineage;
- `anchor_entry_threshold` records the first threshold at which any anchor entered;
- `component_class` uses eventual lineage-level anchor status.

A component may therefore be born detached and later become occurrence anchored without erasing that sequence.

## Frozen results contract

The workflow now requires:

- 100% retention across threshold sequences;
- 100% retention across neighbourhood rules;
- 100% retention across tested grid refinements;
- 100% retention across tested anchor locations;
- at least 90% retention under frozen support noise.

The exact JSON output is uploaded by `.github/workflows/support-topology-stress.yml` as `support-topology-stress-results`.

## Interpretation

Passing this benchmark shows that the two-island structural distinction is stable to the tested threshold lists, neighbourhood rules, raster refinements, within-island anchor locations, and small support perturbations in this frozen design.

It does not show that the method outperforms support-only or distance-only baselines. It does not establish biological isolation, occupancy, demographic connectivity, colonisation probability, or historical dispersal. Those require held-out empirical comparisons.
