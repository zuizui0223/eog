# Contextual representation fresh validation v1

## Closed result

The first fresh response-blind real-data validation of the post-closure EOG contextual representation is terminally **adverse**.

Portal Project / *Dipodomys merriami*:

- baseline macro heldout log loss: `0.40928333029868325`;
- source-symmetric sequential contextual augmentation: `0.444094795095135`;
- augmented minus baseline: `+0.03481146479645175` (`+8.505%` relative);
- augmented heldout-period wins: `45 / 135`;
- baseline macro Brier: `0.11591549273427827`;
- augmented macro Brier: `0.12581689751153713`.

The endpoint had strong estimability (4,190/5,320 calibration positive/negative plot-periods and 1,485/1,568 heldout positive/negative plot-periods; all 135 heldout periods contained both classes).

## What was fixed relative to Tampa

This endpoint did **not** reproduce the exact Tampa representation defect:

- Layer B was refreshed sequentially by context rather than reused as one static node-level vector;
- prediction-facing source aggregation was source-symmetric and label-invariant;
- repeated-entity Layer-B vectors were not all static;
- entity-level vectors were not injective identities;
- train/serve semantics were frozen under one procedure.

Therefore the known-truth diagnosis established genuine failure modes, but removing those failure modes was **not sufficient** to produce real predictive added value.

## New clue: world-set saturation

Layer A never contracted in Portal. All four local worlds plus `external_open` survived the entire sequence. Consequently the contextual representation changed because the source geometry/support field evolved, not because evidence eliminated declared worlds.

Tampa was also fully world-set saturated. Louisiana, by contrast, exhibited explicit Layer-A falsification of all six frozen local worlds and retained only `external_open`, while its paired predictive gain was small but favorable.

This motivates a new **post-outcome prospective hypothesis**:

> Prediction-facing contextual world-support summaries may be scientifically eligible only when calibration evidence causes non-trivial Layer-A world-set contraction; support-geometry variation under a fully saturated world universe may be insufficient or harmful as supervised augmentation.

This is not established by Portal and must not be used to rescue or reclassify the consumed adverse endpoint. Before making it a default product gate, it requires a newly frozen known-truth intervention and an independent response-blind real-data validation. Azores contraction status is not yet recovered well enough to claim a complete favorable-versus-adverse pattern.

## Boundaries

- Portal is consumed and is not rerun or repaired.
- The result does not count as a fourth endpoint in the closed EOG-WF manuscript series.
- The original favorable / favorable / adverse closed synthesis is unchanged.
- No universal claim about source-symmetric or sequential v2 prediction is supported.
- The strongest supported upgrade is now narrower: static reuse and arbitrary single-source anchoring are avoidable failure modes, but contextual Layer B still requires an independent eligibility criterion tied to whether its epistemic world state actually changes.
