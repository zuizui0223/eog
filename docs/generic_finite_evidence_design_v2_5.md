# Generic finite evidence design v2.5

## Result

The BAM-specific v2.4 planner was generalized to a domain-agnostic finite-world API.

The generic planner knows nothing about A, B, M, barriers or movement. It receives only:

1. a finite set of world IDs;
2. the current evidence signature for each world;
3. a preregistered evidence/intervention library with one predicted outcome per world;
4. optionally, the currently surviving world subset.

It returns unresolved world pairs, per-evidence discrimination, residual equivalence classes, and an exact minimum separating evidence set when one exists.

## Frozen validation

All four preregistered hypotheses were supported.

### G1 — reproduce v2.4

The generic API exactly reproduced the frozen BAM planner:

- worlds: 64
- unresolved pairs: 16
- H challenge splits: 8
- P challenge splits: 8
- repeat-passive control splits: 0
- exact minimum design: H + P
- minimum size: 2

### G2 — fail closed when the library is insufficient

The library was restricted to:

- P barrier challenge
- repeat passive state

The H-only aliases were therefore deliberately left without a discriminating evidence channel.

The generic planner returned:

- minimum separating set: **null**
- insufficient library: **true**
- final classes: 48 singletons + 8 doubletons

It did not invent a new intervention or weaken the target.

### G3 — replan after world contraction

One member of each P-only passive alias pair was removed to mimic prior evidence contracting the finite compatible-world set.

The active universe became 56 worlds with 8 unresolved H-only pairs.

The exact next design changed from two interventions to:

[
{	ext{H long-corridor challenge}}
]

with minimum size 1.

Thus the evidence plan is conditional on the current surviving world set rather than fixed globally.

### G4 — evidence addition is monotone

Across every subset of the frozen evidence library, adding another evidence channel never merged worlds that were already separated.

Monotonicity violations: **0**.

## Frozen receipt

- workflow run: 36550447749
- artifact digest: sha256:2dbd9034f46ddea9202f7e6b157d1c388106589e730dd8e68636df2a30169554
- result fingerprint: a2365bcd014ebbe2722f8c04a3df0f149a4eb6af2fcf97b27cf11435721d8abd
- generic plan fingerprint: 1719954fe6f27554f2b74ac7ddbc428f39dc8fa44603167d8fb89ab4939a5303

## Product consequence

The post-closure EOG line now has a generic finite evidence-design primitive:

[
	ext{current compatible worlds}
ightarrow
	ext{unresolved pairs}
ightarrow
	ext{candidate evidence partitions}
ightarrow
	ext{exact minimum separating design}.
]

The planner remains fail-closed. If the declared evidence library cannot separate the surviving world set, the answer is unresolved / insufficient library.

This does not assert that the finite world universe contains biological truth.
