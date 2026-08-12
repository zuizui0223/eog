# EOG v2 frozen source-expansion confirmation result

## Outcome

**FAILED promotion gate; retain without rescue.**

One-time workflow run: `31601076569`.

Frozen contract fingerprint:

`387118b1de858514f073bd8ea49a0a721d21b52a0`

Correction: the authoritative contract fingerprint used by the run is:

`387118b1de858514f0734c989b97d1559d020abcc9965098892dd8bb85fc2ac4`

Artifact ID: `9143557433`.
Artifact digest:

`sha256:05d9c503cdcc8426fc44a11f3620df1ca6ff98ee86672efcc7265ec361c32338`

The implementation-blob verification passed before the fresh confirmation seeds were evaluated. The benchmark itself completed successfully; the workflow failed only because the frozen scientific decision was `passed = false`.

## Frozen gate results

- outer-test label invariance: **PASS**, maximum absolute feature difference `0.0`;
- inner positive self-exclusion: **PASS** for every confirmation seed;
- favourable-seed count over the seedwise best non-leaky reference: **PASS**, `6/8` against threshold `6/8`;
- mean held-out log-loss gain over the seedwise best non-leaky reference: **FAIL**, observed `0.034717170807057995` against the frozen threshold `0.05`.

Therefore the confirmation fails exactly one predeclared promotion gate.

## Mean held-out performance

Mean log loss:

- environment: `0.7430561726933274`;
- fixed dynamic: `0.3735647459862299`;
- expanded nearest source: `0.4787490420485980`;
- expanded source pressure: `0.5123297558916784`;
- nested expanded dynamic: `0.3174006531076432`;
- deliberately leaky expanded dynamic audit control: `0.3732456406269119`.

The seedwise-best non-leaky reference has mean log loss `0.3521178239147012` when the best reference is selected separately within each frozen seed. Nested expanded dynamic is better on average, but the predeclared improvement magnitude is not large enough for promotion.

## Seedwise boundary

Expanded dynamic is adverse relative to the seedwise best reference for seeds `1709` and `2203` and favourable for the other six frozen seeds. The two adverse seeds are retained.

## Interpretation

This result supports the **leakage-control implementation** but not the stronger scientific promotion claim that admitting additional positive training targets as contemporary EOG-R sources yields a sufficiently large and consistent predictive increment beyond practical source-based references.

Accordingly:

- the nested source-expansion machinery may remain available as an experimental sensitivity analysis;
- it must not be promoted as the default EOG-R source policy from this confirmation;
- no seed, gate, graph, fold, horizon or source-construction rule may be changed to rescue this failed confirmation;
- any later source-policy proposal is a new prospective method-development line requiring new rationale and new independent confirmation data.

This failure narrows EOG v2 rather than weakening the frozen fixed-source result: the fixed-source comparator confirmation remains the primary synthetic evidence for the current EOG-R estimand.
