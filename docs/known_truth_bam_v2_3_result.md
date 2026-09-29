# Known-truth BAM v2.3 — intervention identifiability

## Starting point

BAM v2.2 showed that complete passive A/B/M state evidence did not identify all parameter worlds.

The 64 frozen parameter worlds collapsed into 48 complete-state equivalence classes:

- 32 singleton classes;
- 8 duplicate classes differing only in barrier permeability `P`;
- 8 duplicate classes differing only in movement horizon `H`.

These aliases were not caused by missing occurrence data. The paired parameter values generated exactly the same passive A/B/M state under the frozen landscape.

## Frozen interventions

Two axis-specific challenges were preregistered before execution.

### P challenge

A standardized source was placed at `r1c3`, immediately left of the hard barrier, and one-step access to `r1c4` was observed.

Both frozen dispersal radii can span the one-cell distance and both frozen horizon values exceed one step. Therefore the challenge isolates barrier permeability.

### H challenge

A standardized source was placed at `r1c0` in a barrier-free 9 × 3 corridor and access to `r1c8` was observed.

- with `D=1.01`, the target needs 8 steps;
- with `D=2.01`, the target needs 4 steps.

Thus `H=3` cannot reach the target while `H=8` can, independent of barrier permeability.

## Results

All preregistered hypotheses were supported.

- P-only alias classes split: **8/8**
- H-only alias classes split: **8/8**
- axis-specificity violations: **0**
- passive equivalence classes: **48**
- intervention-augmented equivalence classes: **64**
- final class-size distribution: **64 classes of size 1**
- finite-world parameter identification after both challenges: **64/64 = 100%**

Result fingerprint:

`654ec11ce21455989b399c7668f06595cd499b5acb347b78bdc17582f92960f2`

## What changed scientifically

The v2.2 50% parameter-identification ceiling was not a permanent property of the parameter universe.

It was conditional on a passive observational regime in which two movement parameters were dormant.

The interventions changed the observation geometry:

[
	heta_1 
eq 	heta_2,qquad
S(	heta_1)=S(	heta_2)
]

under the passive landscape, but

[
I(	heta_1)
eq I(	heta_2)
]

under an intervention designed to activate the differing parameter.

Therefore the important distinction is between:

1. **passive non-identifiability** — alternative parameters induce the same observed state;
2. **structural non-identifiability under an evidence class** — no observation available in that class separates them;
3. **intervention-resolvable ambiguity** — a finite challenge exists that makes the alternatives predict different outcomes.

## EOG consequence

EOG can now be framed as more than a finite-world filter.

For a surviving world set, it can ask:

> Which observation or intervention would divide the remaining worlds most strongly?

This changes the downstream task from forced model selection to **falsification-driven evidence design**.

The next implementation should therefore rank a finite library of admissible observations/interventions by the world pairs they distinguish, and identify the smallest challenge set needed to separate the current compatible worlds.

## Boundary

The 100% result is conditional on:

- the frozen 64-world candidate universe;
- the two idealized intervention designs;
- exact intervention outcomes;
- no observation error.

It is not a claim that all ecological mechanisms are experimentally identifiable.
