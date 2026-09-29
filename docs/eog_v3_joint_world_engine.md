# EOG v3 joint-world engine

## Status

EOG v3 is a **post-closure experimental API line**. It does not alter the frozen
EOG-WF empirical denominator, manuscript result, Layer-A evidence, or Layer-B
prediction result.

Its purpose is to expose the known-truth development result as a small reusable
finite-world engine.

## Core objects

EOG v3 separates two finite uncertainty axes.

### Ecological worlds

An ecological world maps each declared target to a latent ecological state.

Example:

```json
{
  "world_id": "eco_present",
  "state_by_target": {
    "site": "present"
  }
}
```

The state labels are domain-defined strings. They can represent presence/absence,
BAM state classes, interaction states, movement states, or other finite declared
ecological hypotheses.

### Observation worlds

An observation world declares which outcomes are possible for each
`(channel, ecological_state)` pair.

Example:

```json
{
  "world_id": "imperfect",
  "supports": [
    {
      "channel_id": "survey",
      "ecological_state": "present",
      "possible_outcomes": ["zero", "positive"]
    },
    {
      "channel_id": "survey",
      "ecological_state": "absent",
      "possible_outcomes": ["zero"]
    }
  ]
}
```

No prior probability is attached to the worlds.

### Joint worlds

The engine evaluates the exact finite Cartesian product

[
W_J = W_E 	imes W_O.
]

For an evidence event

```json
{
  "target_id": "site",
  "channel_id": "survey",
  "observed_outcome": "zero"
}
```

a joint world survives only if that outcome occurs in the declared support for
the ecological state and observation channel.

The ecological conclusion is therefore a **projection** of surviving joint worlds,
not a conclusion under one silently fixed observation model.

## CLI

Install:

```bash
python -m pip install .
```

Evaluate one joint universe:

```bash
eog-v3-joint-evaluate \
  --input examples/eog_v3/joint_evaluation_input.json \
  --output joint_result.json
```

Plan the next one-step evidence action:

```bash
eog-v3-plan-evidence \
  --input examples/eog_v3/evidence_planning_input.json \
  --output evidence_plan.json \
  --objective ecological
```

Plan an exact robust set and adaptive decision tree:

```bash
eog-v3-plan-adaptive \
  --input examples/eog_v3/evidence_planning_input.json \
  --output adaptive_plan.json
```

The one-step planner supports:

- `joint`: minimize worst-case surviving ecological × observation worlds;
- `ecological`: minimize worst-case ecological-world projection size.

The adaptive planner works on the surviving **joint worlds** and returns:

- the exact minimum nonadaptive robust separating action set, when it exists;
- whether the supplied action library is insufficient;
- minimum worst-case adaptive depth;
- all optimal first actions;
- a deterministic canonical first action;
- worst-case depth when each action is forced to be first.

Actions are used at most once. After every realized outcome, only joint worlds whose
declared possible-outcome set contains that outcome remain active.

## Fail-closed behavior

The engine deliberately distinguishes several states.

### universe_falsified

`true` means no declared joint world survives the observed evidence.

This is conditional on the declared finite ecological and observation-world universes.

### unresolved

Multiple joint or ecological worlds remain compatible.

This is a valid terminal state.

### fail_closed_no_improvement

The evidence planner sets this to `true` when none of the supplied candidate
actions strictly improves the selected worst-case objective.

The planner does not invent a post hoc action.

## Evidence planning

For every surviving joint world, each candidate action supplies a finite set of
possible outcomes.

The planner reports:

- guaranteed joint-world pair splits;
- worst-case surviving joint worlds;
- worst-case surviving ecological worlds;
- objective-specific best actions.

Two worlds are **guaranteed** to be separated by an action only when their possible
outcome supports are disjoint.

No hidden prior or expected-utility weighting is used.

## Frozen validation

The public v3 surface is regression-tested against the canonical post-closure
known-truth programme rather than against a new empirical endpoint.

### Joint ecological × observation worlds

The v3 engine must reproduce the frozen v2.7 result:

- strict perfect-detection universe: **48 joint / 48 ecological worlds**;
- broad perfect + imperfect-detection universe: **112 joint / 64 ecological worlds**;
- direct perfect-detection calibration restores **48 joint / 48 ecological worlds**;
- appending evidence contracts or preserves the current joint world set.

Parent fingerprint:

`085587287263d5ebb4016455ac74406b14979e7de25e57e12b8a607becd5cd1d`

### Robust set-valued evidence design

On the canonical three-hypothesis v2.8 fixture:

- repeat one survey: **0/3** robust pair splits;
- repeat four surveys: **0/3**;
- direct detection calibration: **2/3**;
- direct target-state assay: **2/3**;
- exact minimum robust separating set: the **two direct channels**, size **2**.

Parent fingerprint:

`a459ebd6bdde502c5d86aad7baf37443d17d1156fb358a373c5429c5c94115f8`

### Adaptive evidence tree

The v3 adaptive wrapper must reproduce v2.9:

- minimum worst-case depth: **2**;
- optimal first actions: calibration or direct state assay;
- repeat-survey-first worst-case depth: **3**;
- remove calibration: worst-case exact resolution impossible;
- remove state assay: worst-case exact resolution impossible.

Parent fingerprint:

`19e441e930c1c3fc116780fa8bfb4b09c178e69c4379a1ef69e47f5b13218822`

### Broader known-truth evidence behind the API

The API is also bounded by independent generality tests:

- **12 deterministic BAM systems / 768 truths**: complete positives uniquely
  identified **0/768** BAM states; complete direct BAM state evidence recovered
  **768/768** state-equivalence classes;
- **independent stochastic generator / 384 runs**: truth retention and finite-set
  contraction held, while universal witness realization and strict benefit of
  unordered accumulated history were refuted;
- **temporal stochastic extension**: 8 static support classes became 20 temporal
  classes and 256/384 runs showed strict temporal contraction;
- **8 preregistered stochastic landscapes**: 2 remained DESIGN_STOP and all U1-U8
  claims held in the 6 eligible landscapes / 1,152 runs.

The strongest supported product interpretation is therefore **finite-world
falsification plus evidence/intervention design**, not generic true-process recovery.

Integrated validation protocol:

`validation/eog_v3_joint_world_engine/integrated_protocol_v1.json`

## Boundary

EOG v3 does not assert that:

- the declared ecological universe contains the biological truth;
- a surviving world is historical truth;
- nonzero probability is equivalent to plausibility;
- one planning objective is universally preferable;
- more evidence necessarily identifies a unique mechanism.

It provides exact bookkeeping and falsification **inside declared finite worlds**.
