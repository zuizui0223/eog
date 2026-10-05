# Original EOG colonization-age memory — v24 result

## Result

All eight preregistered hypotheses were supported.

The main result is:

> **final occupancy and source provenance can both be identical while colonization-age
> state still remembers the activation history.**

Authoritative execution:

- run: `37262658932`;
- artifact: `11324923934`;
- artifact digest:
  `sha256:195a1e8c8c37ddb5cb7c53d34364b6f94c7b9ee230fd1ee530f26cd05200a017`;
- result fingerprint:
  `300757d753225c7dc3f816f6478436ad5f68fd892d033465dec473bcad69a971`.

## The v23 residual was reproduced exactly

v23 had left **81/768** design rows unresolved for exact activation history after the
complete occupancy + provenance libraries.

v24 reproduced all **81**.

The first failed implementation had recovered only 45 because source-only equilibrium
unions with zero non-source nodes were incorrectly dropped.  That was an implementation
gate failure before a v24 result was produced; no protocol or hypothesis changed.

## Forty-five residual histories hid age information

Among the 81 v23 residual aliases:

- **45** had different complete non-source first-arrival maps;
- **36** had no additional first-arrival information inside the v23 alias.

The complete first-arrival map resolved exact activation history in all 45 hidden-age
cases.

Thus occupancy + source provenance did not fully characterize distributional history.

## Complete first-arrival state is still not exact history

Across all 768 design rows:

- exact history identified by complete first-arrival map: **702**;
- exact history still unresolved: **66**.

So even knowing when every non-source node was first reached does not always recover the
exact activation schedule.

This is another target hierarchy:

```text
final occupancy
    < equilibrium source provenance
    < first-arrival / colonization-age state
    < exact activation history
```

The containments are informational, not claims that each arrow is strict in every row.

## Provenance equivalence does not imply age equivalence

There were **931** activation-history pairs with:

- identical complete equilibrium provenance map;
- different complete first-arrival map.

Source identity and source timing are separate history coordinates.

## Age memory occurs both before and after confluence

History-dependent first-arrival time occurred in:

- unique-origin zones in **499/768** design rows;
- confluence zones in **496/768**.

This is important because provenance tags are history-informative only at confluence,
where source basins overlap.

Colonization-age information is different: even if a node can only come from one final
source, its arrival time changes when that source activates earlier or later.

So a unique source label does not imply a history-invariant local age state.

## Source geometry changes where age memory lives

### Clustered

- exact history identified from first-arrival map: **327/384**;
- mean fraction of non-source nodes with arrival-time disagreement: **0.905**;
- rows with unique-origin age memory: 124;
- rows with confluence age memory: 319.

### Dispersed

- exact history identified: **375/384**;
- mean disagreement fraction: **0.976**;
- unique-origin age memory: 375;
- confluence age memory: 177.

Clustered systems encode much of their history through overlapping/confluent provenance.
Dispersed systems encode more of it as timing differences inside source-specific basins.

## Current EOG history state hierarchy

The source-history programme now separates at least four objects that a final map can
collapse:

1. **final occupancy** — where the distribution ends;
2. **source provenance** — which source arrived first;
3. **first-arrival / colonization-age state** — when each node was first reached;
4. **exact source-activation history** — the full generating schedule.

The final occurrence map can be identical while all three richer history objects differ.

## Next question

v24 deliberately stopped before assigning ecological consequences to age.

The next valid question is therefore not another identifiability assay.

It is:

> **Can two histories with identical final occupancy but different colonization-age
> maps produce different present ecological states under one prospectively frozen
> age-dependent process?**

That would test whether hidden distributional history is merely descriptive or can
become causally relevant to the present.
