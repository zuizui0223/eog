# Original EOG target-relational sufficiency — v11

## Question

v10 showed that a static nodewise distribution map can be exactly identical while
pairwise relations, first-passage history and intervention response differ.

v11 asks the constructive follow-up:

> **How much relational information is actually needed for the ecological target at
> hand?**

The goal is not to force full edge-topology recovery.

## Atomic relational measurements

The fixed library contains:

- REL: one ordered-pair reachability bit;
- FP: one source-to-node first-passage depth;
- KO: one single-node knockout retained-reachability count.

For each v10 four-world static equivalence class, every atomic measurement partitions
the four topology worlds.

An exact search finds the smallest set of those partitions that is sufficient for a
declared target.

## Targets

- complete pairwise relation signature;
- source first-passage signature;
- single-node intervention signature;
- critical-node count;
- joint relation + first-passage + intervention suite.

## Target-specific sufficiency

A selected relational summary is sufficient for target T when any worlds that remain
indistinguishable under the selected measurements also have the same T value.

Thus unresolved edge topology is allowed when it cannot change the declared ecological
answer.

## Why this matters

The original EOG idea does not require replacing one over-compressed raster with an
over-complete network representation.

The desired endpoint is a target-sufficient relational quotient:

static map
-> add only the relational evidence needed for the target
-> stop even if multiple edge topologies remain.

This is the topology analogue of the earlier target-quotient principle, now applied to
the information lost by nodewise maps.
