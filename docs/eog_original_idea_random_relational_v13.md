# Original EOG random-topology relational sufficiency — v13

## Question

v10 showed that static maps can hide topology.
v11 showed that one or two relational measurements could resolve narrow targets in four
hand-built topology archetypes.
v12 showed that the static-map/topology gap persists across random 12-world DAG panels.

v13 asks whether the v11 low measurement burden generalizes.

## Exact problem

Each row contains 12 random topology worlds with the same static A/B/M/G/marginal map.

Available atomic relational measurements are:

- one ordered-pair reachability bit;
- one source-to-node first-passage depth;
- one single-node knockout retained-count.

No raw edge query is allowed.

For each ecological target, v13 finds the exact smallest measurement set whose joint
signature never merges worlds with different target values.

## Why this matters

The desired EOG architecture is not "always reconstruct the whole graph."

It is:

static map
-> declare the ecological question
-> measure only enough relational structure to make that target invariant
-> retain unresolved topology when it cannot change the target.

The random-world panel tests whether that compression survives once the topology
universe is no longer four specially chosen archetypes.
