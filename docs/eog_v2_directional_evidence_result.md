# EOG v2 independent directional-evidence confirmation result

## Status

The frozen synthetic confirmation defined by `benchmarks/directional_evidence_confirmation_contract.json` was executed on the predeclared seed set without changing candidate operators, directional thresholds, source policy or gates after outcome inspection.

Authoritative workflow run: `31694565199`.

- head: `a2dd88aae0294336a102071321e13702e0475f88`;
- artifact: `9178765198`;
- artifact digest: `sha256:3dcecc9796098ef7954c0453d6a1625bf32a5a5e2c13de225bb883762336efe7`;
- contract fingerprint: `dc7e43c33fd724c813c09b8dbbc6228cb6d377271f40330323b0f8920d98db3c`;
- result fingerprint: `c06d71d5c9b872fe20bf0004b9369b61c90806dae4edb00795cafa566afe365d`.

Frozen decision: **PASS**.

## Occurrence-only starting point

All three candidate rules were deliberately constructed to remain compatible with the same fixed-source occurrence pattern:

- true one-way chain: occurrence coverage `1.0`;
- symmetric over-permissive rule: occurrence coverage `1.0`;
- reverse-dominant but weakly forward-connected rule: occurrence coverage `1.0`.

This reproduces the previously established identifiability boundary: occurrence compatibility alone cannot distinguish these candidate processes.

## Independent directional evidence

Three independent directional constraints were declared: `A -> B`, `B -> C`, and `C -> D`. The directional resolution ratio was frozen at `2.0` before outcome inspection.

Across all `8/8` confirmation seeds:

- the true one-way chain supported all `3/3` directional constraints;
- the symmetric over-permissive rule left all `3/3` constraints `bidirectional_or_ambiguous`;
- the reverse-dominant rule contradicted all `3/3` constraints.

The combined qualitative statuses were identical in every confirmation seed:

- `true_chain` -> `compatible_with_occurrence_and_direction`;
- `permissive` -> `indistinguishable_directional_evidence`;
- `reverse_dominant` -> `contradicted_by_directional_evidence`.

## Scientific consequence

The result establishes the next narrow EOG v2 inference step:

> independent directional evidence can discriminate among some candidate transition rules that are indistinguishable from occurrence compatibility alone.

This does not make the true-chain label a posterior probability or prove a unique historical route. The permissive rule remains explicitly indistinguishable rather than being forced into rejection, and evidence-specific statuses remain visible.

## Next boundary

Future evidence types should be added separately rather than averaged into an omnibus score. Candidate extensions include:

- independently established historical colonisation order;
- directional movement/dispersal observations;
- repeated survey/non-detection evidence only when an observation/detection model is defensible;
- extinct or historical stepping-stone evidence;
- genetics retained as independent external validation.

Any empirical use requires an evidence-specific provenance and admission contract frozen before outcomes are used to tune candidate transition rules.
