# EOG v2 dynamic-occupancy reference boundary

## Status

Development reference-depth boundary for EOG v2. This benchmark is synthetic and does not modify any frozen v0.1 result.

## Purpose

Repeated incidence changes the estimand. When previous occupancy state is observed and the data support a first-order colonisation/persistence model, EOG-R should not be presented as a substitute for that process model.

The benchmark therefore constructs a known truth in which one-step colonisation depends on:

- local viability;
- the observed previous occupancy state;
- incoming support from neighbours that were occupied at the previous step;

while persistence of an already occupied node depends on local viability.

The correctly specified process reference is compared with static finite-horizon EOG-R support.

## Leakage and validation boundary

Forty-eight independent four-node island motifs are simulated for ten repeated time steps. Cross-validation holds out entire spatial motifs, not individual time rows. Thus repeated observations from a held-out motif never enter model fitting.

The process predictor at time `t` uses only occupancy at `t-1`; the current response is never used to construct its own predictor.

This benchmark does not model imperfect detection. An empirical dynamic-occupancy comparison with detection requires repeat-detection data and a model appropriate to those observations.

## Models

1. `state_environment`: local viability + previous occupancy;
2. `state_environment_eog`: local viability + previous occupancy + static EOG-R reachability;
3. `dynamic_occupancy`: local viability + previous occupancy + one-step incoming neighbour pressure;
4. `dynamic_occupancy_eog`: the process reference + static EOG-R reachability.

All four use the same deterministic ridge-logistic calibration and the same held-out rows.

## Development gates

The boundary passes only if:

- the correctly specified process model improves `state_environment` by at least `0.03` mean held-out log loss;
- it improves `state_environment_eog` by at least `0.02`;
- adding static EOG-R to the process model does not improve mean log loss by more than `0.005`;
- the process model beats `state_environment_eog` in at least `6/8` fixed development seeds.

## Interpretation

A pass is a **negative-control result for EOG-R**: when repeated incidence directly identifies the transition process used to generate the truth, the process model should retain primacy.

This does not imply that dynamic occupancy is always available or that it answers the same question as source-conditioned reachability from sparse occurrence snapshots. The role of EOG-R remains most relevant when intermediate configuration, directional/bottleneck structure, or source-conditioned hypotheses are scientifically important but a calibrated repeated-incidence process model is not available.

The result must be retained if adverse to EOG-R; no gate is to be weakened to rescue the method.
