# Falsification-driven experiment design v2.4

## Starting state

The known-truth BAM sequence produced a finite but unresolved parameter universe.

- v2.1: A, B and M were all independently activated, yet positive occurrence data identified 0/64 truth worlds.
- perfect negatives increased unique recovery to 2/64;
- exact occupied-node movement timing increased unique recovery to 6/64.
- v2.2: complete idealized A/B/M state evidence increased recovery to 32/64, but 16 duplicate parameter classes remained.
- v2.3: those duplicates were shown to be inactive M-parameter aliases: 8 barrier-permeability classes and 8 movement-horizon classes. Two targeted challenges separated all 64 worlds.

v2.4 asks whether the next intervention can be chosen directly from the remaining finite-world ambiguity.

## Exact planning formulation

Let the passive evidence induce an equivalence relation over worlds.

Every unresolved unordered pair

[
(w_i,w_j)
]

must be split by at least one intervention whose predicted outcomes differ between the two worlds.

Therefore an intervention set is separating exactly when it covers every unresolved world pair.

This is a finite pair-cover problem, not a prediction-probability problem.

## Frozen library

Three admissible interventions were declared before execution:

1. `P_barrier_challenge`
2. `H_long_corridor_challenge`
3. `repeat_passive_state` — negative control

## Result

Passive complete-state evidence left **16 unresolved pairs**.

Single-intervention discrimination:

| intervention | unresolved pairs split | pairs remaining |
|---|---:|---:|
| H long-corridor challenge | 8 | 8 |
| P barrier challenge | 8 | 8 |
| repeat passive state | 0 | 16 |

After either useful intervention alone, the finite universe contained:

- 48 singleton classes;
- 8 doubleton classes.

The exact minimum separating set was:

[
{	ext{H challenge},	ext{P challenge}}
]

with size **2**.

Adding both produced:

- **64 equivalence classes**
- **64 singleton classes**
- **64/64 uniquely separated worlds**

No pair-cover / augmented-signature mismatch occurred.

Result fingerprint:

`c7107f1511fd7b5542da3f7c501d99f0b8cebe00feec0348ca4d60d510a75b12`

## Frozen hypothesis verdicts

- E1 pair-cover equivalence — **SUPPORTED**
- E2 current intervention-library structure — **SUPPORTED**
- E3 exact minimum design — **SUPPORTED**

## Scientific interpretation

The useful output of an unresolved EOG analysis is not necessarily another fitted model.

It can be a statement of the form:

> These worlds remain observationally equivalent under the current evidence, and this particular finite set of additional measurements would separate them.

This gives the known-truth development sequence a coherent inferential ladder:

[
	ext{occurrence}
ightarrow
	ext{world falsification}
ightarrow
	ext{BAM ambiguity}
ightarrow
	ext{mechanism-specific evidence}
ightarrow
	ext{targeted intervention}
ightarrow
	ext{finite experimental design}.
]

The important distinction is between **adding more of the same data** and **collecting evidence that activates a difference between surviving explanations**.

## Product boundary

The planner is exact only inside:

- a declared finite world universe;
- a preregistered intervention library;
- deterministic or otherwise explicitly declared intervention outcome models.

If the intervention library cannot split every unresolved pair, the correct output is **unresolved / insufficient intervention library**, not an invented post hoc experiment.

The planner therefore supports falsification-driven experimental design without converting surviving worlds into claims of historical truth.
