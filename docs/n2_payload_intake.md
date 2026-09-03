# N2 payload intake boundary

EOG accepts Chapter-2 handoff envelopes using schema ID `n2-to-n3-payload-v1` from `zuizui0223/odsp`.

The intake implementation is `eog.n2_handoff`. It is intentionally independent of the ODSP Python package: EOG validates the serialized envelope and re-derives whether the object is eligible for N3 rather than trusting an upstream permission flag.

## Empirical admission

An axis-resolved state is admitted to empirical N3 only when the payload is internally consistent with all of the following:

- evidence scope is `empirical`;
- support semantics are `species_support`;
- added-axis semantics are declared;
- the source boundary was prospectively frozen;
- thickness was estimable;
- transferability is `generalizing`;
- all supplied independent held-out gains are positive;
- the handoff category is `empirical_axis_resolved_supported`;
- the state artifact semantics are `empirical_species_support`;
- payload fingerprint and state-artifact SHA-256 pass.

The state artifact is therefore an integrity-pinned input, not an inferred permission.

## Non-admitted N2 objects

`descriptive_projection_only` can retain projection/thickness summaries for interpretation, but it cannot provide an empirical axis-resolved species-state artifact to reachability analysis. This is the category of the completed European free-tailed bat N2 lane.

`known_truth_method_state_only` can be admitted for method testing, never as empirical species evidence. `structural_capacity_only` remains structural capacity and cannot be relabelled as species support. `unavailable` carries neither a state artifact nor a projection output.

## Integrity check

```python
from eog.n2_handoff import inspect_n2_handoff_payload, verify_n2_state_artifact_bytes

intake = inspect_n2_handoff_payload(payload)
if intake.accepted_for_empirical_n3:
    verify_n2_state_artifact_bytes(payload, state_bytes)
```

This intake boundary does not alter any frozen EOG endpoint or allow N3 results to retune N2.
