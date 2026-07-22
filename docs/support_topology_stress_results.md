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

For each scenario, the benchmark records the complete class count and fingerprint. The primary retention indicator asks only whether both of the following remain present:

- `occurrence_anchored_component`;
- `persistent_detached_component`.

Transient component frequency is reported separately rather than treated as failure of the headline structure.

## Frozen acceptance contract

The workflow requires:

- 100% retention across threshold sequences;
- 100% retention across neighbourhood rules;
- 100% retention across tested grid refinements;
- 100% retention across tested anchor locations;
- at least 90% retention under frozen support noise.

The exact JSON output is uploaded by `.github/workflows/support-topology-stress.yml` as `support-topology-stress-results`.

## Interpretation

Passing this benchmark would show that the two-island structural distinction is not an artifact of one threshold list, one neighbourhood rule, one raster refinement, one within-island anchor cell, or small support perturbations in this frozen design.

It would not show that the method outperforms support-only or distance-only baselines. It would not establish biological isolation, occupancy, demographic connectivity, or historical dispersal. Those require held-out empirical comparisons.
