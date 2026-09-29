# EOG v3 runnable examples

These examples exercise the public post-closure EOG v3 API. They do not alter the
frozen EOG-WF manuscript or empirical denominator.

## Evaluate a joint ecological × observation universe

```bash
eog-v3-joint-evaluate \
  --input examples/eog_v3/joint_evaluation_input.json \
  --output joint_result.json
```

The example contains two ecological worlds (target absent/present), two observation
worlds (perfect/imperfect), and one zero-detection event. The ecological-present world
remains possible only through the imperfect observation world.

## Rank the next evidence action

```bash
eog-v3-plan-evidence \
  --input examples/eog_v3/evidence_planning_input.json \
  --output evidence_plan.json \
  --objective ecological
```

Use `--objective joint` when the target is the full ecological × observation state
rather than only the ecological projection.

## Plan robust and adaptive evidence collection

```bash
eog-v3-plan-adaptive \
  --input examples/eog_v3/evidence_planning_input.json \
  --output adaptive_plan.json
```

This returns the exact minimum robust separating set when one exists, plus the
worst-case adaptive depth, optimal first actions, canonical first action, and
forced-first depths.

## Input schema

The documented input surface is:

`schemas/eog_v3_joint_input.schema.json`

The CLI also enforces semantic constraints such as unique world IDs, complete
action-outcome mappings over surviving joint worlds, and non-empty support sets.

## Fail-closed states

- `universe_falsified=true`: no declared joint world survives current evidence.
- multiple survivors: explicit unresolved state.
- insufficient robust action library: no minimum separating set is returned.
- adaptive_resolvable=false: the supplied action library cannot guarantee singleton
  identification in finite worst-case depth.

All statements remain conditional on the declared finite ecological, observation, and
action universes.
