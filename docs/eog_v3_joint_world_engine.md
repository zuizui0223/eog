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

Plan the next evidence action:

```bash
eog-v3-plan-evidence \
  --input examples/eog_v3/evidence_planning_input.json \
  --output evidence_plan.json \
  --objective ecological
```

The allowed planning objectives are:

- `joint`: minimize worst-case surviving ecological × observation worlds;
- `ecological`: minimize worst-case ecological-world projection size.

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

The v3 engine reproduces the frozen v2.7/v2.8 known-truth results:

- strict perfect-detection universe: 48 joint survivors / 48 ecological worlds;
- broad perfect + imperfect universe: 112 joint survivors / 64 ecological worlds;
- ideal p=1 calibration restores the 48-world ecological projection;
- joint-world objective selects detection-process calibration;
- ecological-world objective selects gold-standard target-state observation;
- no-op evidence is not recommended;
- adding evidence contracts or preserves the current joint-world set;
- expanding the observation-world universe preserves or enlarges the ecological
  projection.

Scientific result fingerprint:

`fbabf1af57a684331eb7094481402bd63cc9fdf753c4b9accb7bfa83673bfccf`

Latest CLI-inclusive validation is recorded on PR #515.

## Boundary

EOG v3 does not assert that:

- the declared ecological universe contains the biological truth;
- a surviving world is historical truth;
- nonzero probability is equivalent to plausibility;
- one planning objective is universally preferable;
- more evidence necessarily identifies a unique mechanism.

It provides exact bookkeeping and falsification **inside declared finite worlds**.
