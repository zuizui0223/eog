# EOG known-truth BAM simulation programme — current scientific spine

## Central question

Can a species' observed geographic distribution identify the Abiotic, Biotic and Movement processes that generated it?

The simulation treats BAM explicitly:

[
G_0 = A cap B cap M
]

where:

- **A** = abiotic suitability;
- **B** = biotic permissibility generated from an independently distributed required partner/resource and antagonist;
- **M** = source-conditioned accessibility under dispersal distance, barriers and a finite movement horizon.

The true BAM world is known to the simulator but hidden from the EOG inference layer.

## Stage 1 — positive-occurrence falsification

Known-truth virtual biogeography first established the exact witness rule:

A candidate world can be eliminated by positive occurrence evidence only if at least one observed occurrence lies outside the candidate's reachable/occupied set.

In the preregistered 64-case factorial, complete positive sampling uniquely identified the true process in **0/64** cases because every truth had at least one observationally equivalent or more permissive alternative.

Therefore:

> more positive occurrences do not guarantee true-process recovery.

## Stage 2 — full BAM and evidence ladder

The source-compatible BAM v2.2 universe contained:

- 2 A modes;
- 4 B modes;
- 5 M modes;
- **40 candidate BAM worlds**.

All 40 were eligible truth states.

The activation audit independently exercised:

- A-only witness: 3;
- partner-B-only witness: 12;
- antagonist-B-only witness: 12;
- M-distance-only witness: 5;
- M-barrier-only witness: 1.

The evidence ladder yielded:

| Evidence | unique BAM truth |
|---|---:|
| positive occurrences only | 0/40 = 0% |
| + complete perfect surveyed negatives | 3/40 = 7.5% |
| + temporal movement-arrival evidence | 8/40 = 20% |

Perfect negatives removed every diagnostic over-permissive superset world, and temporal evidence removed every equal-final-G world whose M arrival times differed. Yet 80% of complete BAM mechanisms remained non-unique.

### Biotic-interaction asymmetry

For 7 diagnostic obligate-partner truth cases, the corresponding no-B world survived positive evidence in 7/7 cases. Perfect negatives eliminated it in 7/7.

For 10 diagnostic antagonist-exclusion truth cases, the no-B world survived positive evidence in 10/10 and was eliminated by perfect negatives in 10/10.

Thus positive coexistence alone does not identify causal interaction dependence against a more permissive no-interaction explanation.

## Stage 3 — truth-blind active interventions

The residual ambiguity was treated as an experimental-design problem rather than a reason to force model selection.

The frozen intervention library contained:

1. A transplant challenge;
2. partner/resource removal;
3. antagonist addition;
4. movement-only arrival probes.

At each step EOG selected the intervention whose **predicted outcomes most evenly partitioned the currently surviving worlds**. The true world was not used for selection.

Starting from the passive state after complete negatives and temporal evidence:

- unique truth before intervention: **8/40 = 20%**;
- unique truth after active intervention: **40/40 = 100%**;
- median interventions required: **2.5**;
- maximum: **4**;
- true-world eliminations: **0**;
- monotonicity failures: **0**;
- complete intervention signatures: **40 distinct / 40 worlds**.

The greedy truth-blind selector reached the same equivalence limit as the complete intervention panel in every truth case.

## Main scientific result

The strongest result is not that EOG can select the correct model from occurrence data.

It is the opposite:

> **A realised distribution is a many-to-one projection of A, B and M. Even complete spatial occupancy and movement timing can leave most causal BAM mechanisms non-identifiable.**

However, this ambiguity is structured rather than hopeless.

Different evidence types attack different equivalence classes:

- positive occurrences reject under-permissive worlds;
- trustworthy negatives reject over-permissive worlds;
- temporal observations expose hidden M differences;
- targeted manipulations isolate A and B mechanisms.

This yields an EOG workflow of:

[
	ext{declare worlds}
ightarrow
	ext{falsify with observations}
ightarrow
	ext{retain unresolved set}
ightarrow
	ext{choose the next discriminating observation/intervention}
]

rather than:

[
	ext{fit models}
ightarrow
	ext{pick one winner}.
]

## Claim boundary

The intervention result is an **identifiability upper bound** under idealized interventions.

It does not establish that:

- perfect negatives are available in real occurrence data;
- field removal/addition experiments are always feasible;
- the candidate world universe contains every real process;
- one surviving world should be called historical truth without an explicit evidence contract.

## Language decision

The current BAM simulations run in roughly one second after environment setup using Python set/bitmask operations.

Therefore C++ is **not required for the current BAM programme**.

Recommended architecture remains:

- Python: scientific contracts, simulation definitions, fingerprints, hypothesis verdicts, active design;
- optional C++ backend only for future large graph/world enumeration if profiling shows a real bottleneck.

The earlier 75.9 s positive-occurrence factorial was slow because it repeatedly recomputed first-passage relations, not because the scientific framework intrinsically requires C++.
