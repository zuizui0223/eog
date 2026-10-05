# Original EOG age-dependent present state — v25 result

## Result

All eight preregistered hypotheses were supported.

The main result is:

> **two distribution histories can end with the same occupancy and the same source
> provenance, yet differ in present ecological state because their colonization ages
> differ.**

This is the first step in the source-history sequence where hidden history is mapped
through a prospectively frozen present-state process rather than treated only as an
identifiability target.

Authoritative execution:

- workflow run: `37263354553`;
- artifact: `11325074752`;
- artifact digest:
  `sha256:16e773999f51cf765798d3373fd069cdca4679451a6d5a92ad246cfa01410fee`;
- result fingerprint:
  `998c24e22e355f703c2a787780ced11abd01280c0ca5deb3b17e8848af3f7ad0`.

## Frozen consequence process

Before scoring, v25 fixed one simple state rule:

- present horizon = the v24 common T*;
- maturation lag = two structural propagation steps;
- a reached non-source node is mature when its colonization age is at least two steps;
- occupancy persists;
- no abundance, extinction, density dependence or fitness was added.

So the result cannot be produced by choosing a lag after observing the age maps.

## Hidden age sometimes changed the present state

v24 had identified **45** v23 residual rows in which occupancy + provenance still hid
different first-arrival maps.

Under the frozen lag-2 process:

- **12/45 (26.7%)** produced different mature-state maps;
- 33/45 did not.

Therefore colonization-age memory can be present-state relevant, but it is not
automatically so.

## Same occupancy and provenance can hide a present-state difference

The full v23 residual set contained 81 rows.

Exactly **12** of those rows had:

- identical final occupancy;
- observational aliasing under the complete v23 occupancy + provenance evidence;
- but different present mature/not-yet-mature maps.

This closes the logical chain:

```text
different source activation history
        ↓
different first-arrival / colonization-age map
        ↓
same final occupancy + same provenance can still occur
        ↓
different present state under a fixed age-dependent process
```

## History relevance is target-specific

The converse also occurred.

There were **6/768** design rows where:

- first-arrival maps differed;
- mature-state maps were identical.

So “the histories are different” is not itself enough to claim ecological relevance.

One must declare the downstream ecological target.

This is the same target-specific principle that appeared earlier in the BAM
identifiability programme, now expressed for distributional history.

## Exact history can be unnecessary

There were **42** design rows in which exact activation history remained unresolved
while the mature-state target was already identical across the remaining histories.

Thus the inferential target hierarchy is now:

```text
final occupancy
< source provenance
< mature present state / colonization-age consequences
< complete first-arrival map
< exact activation history
```

The ordering is informational and need not be strictly separated in every row.

## Present-state memory is widespread in the frozen generator

Across all 768 source-geometry design rows:

- rows with any mature-state memory: **726/768 (94.5%)**;
- rows with unique-origin mature-state memory: **461**;
- rows with confluence mature-state memory: **377**.

Mean fraction of non-source nodes whose mature state differed among histories:

- clustered sources: **0.330**;
- dispersed sources: **0.400**.

The spatial location of the memory differed strongly by source geometry:

- clustered systems concentrated much of it in confluence zones;
- dispersed systems concentrated much more in unique-origin zones.

## Biological interpretation

v24 showed that a final occurrence map can forget colonization timing.

v25 shows why that hidden timing can matter in principle.

Two places may both be occupied by the same apparent source lineage at the present, but
one may have been colonized earlier.  Any ecological property that depends on time since
arrival can therefore differ even when final occupancy and source provenance agree.

Examples in real systems could include stage structure, soil or mutualist accumulation,
local adaptation, pathogen build-up or community succession — but **none of those are
claimed by v25**.  The benchmark uses only the abstract frozen maturation state.

## Correction against overclaiming history

The six age-different / mature-equivalent rows are as important as the favorable cases.

They show that:

> **hidden history is not automatically ecologically consequential.**

History matters only through a declared process that maps history into a target state.

## Next question

The next valid question should not add another arbitrary consequence just because the
lag-2 process worked.

Instead ask a more general structural question:

> **Which properties of an age-dependent process determine whether hidden
> colonization-history differences survive into the present state?**

That can be answered by a small prospectively frozen process family
(monotone threshold, transient window, saturating memory) and by testing which
history aliases each family preserves or erases.
