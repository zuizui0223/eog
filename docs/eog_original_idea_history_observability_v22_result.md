# Original EOG history observability — v22 result

## Result

Seven of eight preregistered hypotheses were supported.

The failed hypothesis is informative:

> **dispersed sources did not require fewer snapshots than clustered sources once a
> history was identifiable.**

Instead, dispersed source geometry made history **identifiable more often**.

Authoritative execution:

- run: 37261490070;
- artifact: 11324282807;
- artifact digest:
  sha256:fe74470d84018941a9fe180218c281effa67cea1e0b577ccb8a86e874e776129;
- result fingerprint:
  3436235e0cc96b14088c27377a79b057b1018c74e71edbd48bac0a83e8a9e9dd.

## Equilibrium occupancy contains zero history information

All three activation histories converge to the same equilibrium occupied set.

Equilibrium-snapshot violations:

**0**.

So a final distribution can be perfectly measured and still contain no information
about the ordering of source activation.

## Transient snapshots can recover hidden history

The frozen observation library used complete non-source occupancy snapshots at t4, t5,
t6 and t8.

Full activation history was exactly identifiable in:

- clustered source design: **231/384**;
- dispersed source design: **348/384**.

When identifiable, the minimum burden was always exactly **one snapshot**.

The canonical minimum time was t4 in all such cases.

## Q3 was refuted

Q3 predicted that dispersed source systems would require fewer snapshots than clustered
systems among identifiable cases.

Mean minimum burden among identifiable rows:

- clustered: **1.0**;
- dispersed: **1.0**.

Difference: **0**.

Q3 remains REFUTED.

The post-result diagnostic shows the correct geometry effect:

- clustered identification rate: **60.2%**;
- dispersed identification rate: **90.6%**.

Thus source geometry affects **whether history leaves an observable transient
signature**, not how many snapshots are needed once that signature exists.

## Provenance needs less information than full history

The coarser equilibrium provenance target was never harder to identify than exact
activation-history identity.

Exact burden violations:

**0**.

Strict target-specific savings occurred in **261/768** design rows.

Moreover, provenance required zero transient snapshots in:

- clustered: 20 rows;
- dispersed: 241 rows.

Those are cases where all three activation schedules already induce the same equilibrium
provenance class even though full history identity remains distinct.

## One snapshot is often enough, but not always

Full history was identified by one post-activation snapshot in **579/768** design rows.

Yet even the complete four-snapshot library left full history unresolved in
**189/768**.

So temporal observation is powerful but does not guarantee historical identifiability.

## Later is not always better

In **428/768** design rows:

- an earlier single snapshot among t4/t5/t6 identified full history;
- t8 alone did not.

As trajectories converge, later occupancy maps can erase the very transient differences
that carried historical information.

## EOG interpretation

v21 separated equilibrium occupancy from provenance memory.
v22 adds an observability distinction:

1. some histories leave a transient occupancy signature that one early snapshot can
   recover;
2. some histories differ only in provenance and do not remain distinguishable from the
   frozen occupancy-snapshot library;
3. once the system approaches equilibrium, waiting longer can destroy history
   information.

The important object is therefore not simply temporal data quantity, but the match
between:

- ecological history target;
- observation type;
- observation timing.

This is the source-history analogue of the earlier target-specific evidence results.
