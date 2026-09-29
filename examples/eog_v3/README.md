# EOG v3 examples

These examples exercise the public JSON CLI on the experimental post-closure EOG v3
joint-world engine.

## 1. Evaluate a joint ecological × observation universe

`joint_evaluation_input.json` declares:

- two ecological worlds: target absent / target present;
- two observation worlds: perfect / imperfect detection;
- one observed zero-detection event.

Run:

```bash
eog-v3-joint-evaluate \
  --input examples/eog_v3/joint_evaluation_input.json \
  --output joint_result.json
```

Expected qualitative result:

- `eco_absent::perfect` survives;
- `eco_absent::imperfect` survives;
- `eco_present::imperfect` survives;
- `eco_present::perfect` is falsified by the zero-detection event.

Therefore both ecological worlds remain in the ecological projection even though one
joint world is eliminated.

## 2. Plan the next evidence action

`evidence_planning_input.json` adds a finite action library.

Run for the ecological objective:

```bash
eog-v3-plan-evidence \
  --input examples/eog_v3/evidence_planning_input.json \
  --output ecological_plan.json \
  --objective ecological
```

The expected best action is `gold_standard_target_state`.

Run for the joint-world objective:

```bash
eog-v3-plan-evidence \
  --input examples/eog_v3/evidence_planning_input.json \
  --output joint_plan.json \
  --objective joint
```

The expected best action is `calibrate_detection_world`.

The difference is intentional: the preferred next evidence depends on which
uncertainty axis the user wants to reduce.

## Schema

The documented input surface is recorded in:

`schemas/eog_v3_joint_input.schema.json`

The CLI also performs semantic validation that cannot be expressed only by the JSON
schema, including:

- unique ecological and observation world IDs;
- unique target IDs within an ecological world;
- unique channel/state rows within an observation world;
- complete action-outcome mappings over the currently surviving joint worlds.

## Boundary

These examples demonstrate finite-world bookkeeping and evidence design only. They do
not imply that either ecological world is biologically true.
