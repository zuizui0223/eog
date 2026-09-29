# Known-truth BAM v2 — frozen result and design boundary

The v2 BAM protocol was executed at commit `ff33cc9b` and completed successfully in workflow run `36540648033`.

## Frozen result

- candidate BAM worlds: 32
- eligible truth worlds: 32
- truth-retention failures: 0
- A/B/M witness-attribution mismatches: 0
- exact-G equivalence violations: 0
- positive-superset violations: 0
- perfect-negative rescue: 336/336 diagnostic superset worlds
- temporal M rescue: 32/32 equal-G worlds with different arrival times
- unique truth with positive-only evidence: 0/32
- unique truth with complete perfect negatives: 0/32
- unique truth after temporal evidence: 0/32
- result fingerprint: `c8f5a6c99627a786a06f4e298b2b7045a728907fe985119b402d16c8d4196d43`

All six preregistered logical hypotheses were supported inside the generated v2 universe.

## But v2 does not authorize a full BAM claim

A post-run design-adequacy audit found two structural degeneracies:

1. The generated required partner occupied **21/21 nodes**, so `B=obligate_partner` was identical to `B=none`.
2. The positive witness audit produced **A-only = 0**. Abiotic differences existed in the candidate definitions but did not independently determine any truth-positive witness in the realized factorial.

Observed witness counts were:

- B-only: 176
- M-only: 80
- BM: 80
- A-only / AB / AM / ABM: 0

Therefore v2 strongly tests an antagonistic B constraint, M, their overlap, exact-G non-identifiability, negative rescue, and temporal M rescue. It does **not** orthogonally activate the required-partner B mechanism or A as an independently falsifiable axis.

The correct conclusion is not “BAM validated.” The correct conclusion is:

> The BAM decomposition is computationally explicit and its set logic behaves correctly, but the v2 virtual ecology did not provide independent excitation of every A/B/M axis.

## Required successor

A v2.1 successor must freeze and pass structural activation gates **before** hypothesis scoring:

- partner occupancy strictly between 20% and 80% of nodes;
- antagonist occupancy strictly between 20% and 80%;
- at least one A-only positive witness pair;
- at least one B-only partner witness pair;
- at least one B-only antagonist witness pair;
- at least one M-only distance witness pair;
- at least one M-only barrier witness pair;
- at least one same-final-G / different-arrival-time M pair;
- at least one positive-superset false world with a perfect-negative diagnostic witness.

If any activation gate fails, v2.1 must STOP rather than tune parameters after scoring.
