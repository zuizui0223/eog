# Frozen held-out comparison for spatial support topology

## Purpose

This benchmark fixes one synthetic fragmented landscape, one historical occurrence anchor, one candidate set, and binary held-out detections before any score is evaluated. It compares five predeclared rules:

1. local support only;
2. inverse distance to the historical anchor;
3. equal-weight support plus inverse distance;
4. detached membership at a single threshold;
5. persistent detached membership across three thresholds.

The purpose is to establish an executable comparator contract before real-taxon evaluation. It is not evidence of transfer to ecological data.

## Frozen landscape

The grid contains:

- a western support component containing the historical anchor;
- an eastern component with the same local support pattern but no historical anchor;
- hard unavailable cells separating the two components;
- two isolated patches that are detached at a single threshold but fail the declared three-step persistence rule.

Four held-out detections are placed in the high-support birth cells of the eastern persistent component. Negative candidates include matched-support cells in the anchored western component and the two transient detached patches.

## Scores

`support_only` is min-max scaled local support.

`distance_only` is min-max scaled inverse Euclidean distance to the historical anchor.

`support_plus_distance` is the frozen equal-weight mean of the first two scores.

`single_threshold_detached` is one for a detached component at threshold `0.70` and zero otherwise.

`multi_threshold_persistent` is one only for a `persistent_detached_component` under thresholds `0.80, 0.70, 0.60` with `minimum_persistence_steps=3`.

No score is fitted to the held-out labels.

## Evaluation

The workflow reports:

- ROC AUC, using pairwise comparisons with half credit for ties;
- Brier score;
- candidate-level support, distance, component classes, and all five scores.

The frozen contract requires the multi-threshold rule to have higher ROC AUC and lower Brier score than all four comparators in this constructed case.

## Interpretation

The benchmark demonstrates a specific failure mode:

- support alone cannot distinguish matched-support anchored and detached cells;
- distance favours nearby anchored cells;
- a single threshold confuses transient detached patches with the persistent detached component;
- multi-threshold persistence separates those structures in this frozen design.

This does **not** establish empirical predictive superiority, occupancy probability, colonisation, historical dispersal, demographic connectivity, or general transfer to real taxa. The next confirmatory step must use training-only support, predeclared anchors and thresholds, and island- or region-level held-out detections.
