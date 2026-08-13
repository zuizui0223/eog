# EOG v2 frozen dynamic-occupancy confirmation contract

## Status

Frozen before confirmation outcomes are inspected.

This confirmation asks whether the dynamic-occupancy/process boundary seen in development reproduces on unused seeds. It is a negative-control test for EOG-R, not a promotion test in which EOG-R is expected to win.

Contract fingerprint:

`ee967ddb36e670eb8946cce9e1c96ac51cd78b392a393cc6036958a010b31848`

## Frozen implementation sources

The confirmation workflow verifies these Git blobs before simulation:

- `benchmarks/dynamic_occupancy_reference_boundary.py`: `9f50a279cebacc58d7368bc47362739f1fe0bd59`
- `src/eog/dynamic_island_reachability.py`: `d3d57a8bef431c34f5d2c13e5e061ade40bcb64f`

Any source change invalidates this exact confirmation.

## Fresh confirmation seeds

`3301, 3407, 3511, 3607, 3701, 3803, 3907, 4001`

These seeds were not used in the development screen.

## Frozen estimand and validation design

The synthetic truth is a first-order repeated-incidence process in which:

- colonisation depends on local viability and incoming support from nodes occupied at the previous step;
- persistence depends on local viability;
- source nodes remain occupied;
- predictors for time `t` use occupancy at `t-1`, never the current response.

Cross-validation holds out complete four-node spatial motifs, so repeated rows from one motif cannot appear in both training and test.

The static EOG-R comparator is constructed from the same frozen lossy graph but does not observe the repeated occupancy transition state.

## Models

- `state_environment`
- `state_environment_eog`
- `dynamic_occupancy`
- `dynamic_occupancy_eog`

## Frozen gates

All gates must pass:

1. `dynamic_occupancy` improves mean held-out log loss over `state_environment` by at least `0.03`;
2. `dynamic_occupancy` improves mean held-out log loss over `state_environment_eog` by at least `0.02`;
3. adding static EOG-R to the correctly specified process model must not improve mean log loss by more than `0.005`, equivalently `dynamic_occupancy_eog - dynamic_occupancy >= -0.005`;
4. `dynamic_occupancy` beats `state_environment_eog` in at least `6/8` confirmation seeds.

## Failure policy

Failure is retained. Confirmation seeds, process truth, thresholds, folds, graph construction and EOG feature construction must not be changed to rescue a failed result.

## Interpretation boundary

A pass supports only this reference-depth conclusion:

> When repeated incidence identifies the correctly specified first-order transition process used to generate the truth, that process model should retain primacy; static EOG-R should not manufacture a material residual gain.

It does not imply that dynamic occupancy is universally available, that imperfect detection has been modelled here, or that EOG-R is unnecessary for source-conditioned questions when repeated-incidence process data are absent.
