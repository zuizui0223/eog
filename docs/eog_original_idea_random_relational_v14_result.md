# Original EOG adaptive relational evidence — v14 result

## Result

All eight preregistered hypotheses were supported across the **144 random topology
panels** from v12/v13.

The central result is:

> **Once the outcome of each relational measurement is used to replan the next
> measurement, EOG can often identify the declared topology-sensitive target with fewer
> measurements than the best fixed nonadaptive panel.**

## Worst-case adaptive burden

The exact adaptive decision tree never required more measurements than the exact best
fixed v13 panel.

Violations: **0**.

Strict worst-case savings occurred in **262 row-target combinations**.

Examples:

| target | fixed mean | adaptive worst-case mean |
|---|---:|---:|
| pairwise relation | 3.264 | 2.986 |
| first passage | 3.264 | 2.986 |
| intervention | 3.104 | 2.833 |
| critical-node count | 2.903 | 2.465 |
| full topology identity | 3.264 | 2.986 |

Critical-node count gained the largest mean worst-case saving.

## Realized branches save more

The canonical worst-case-optimal policy was then followed under each of the 12 possible
realized worlds.

Mean realized depths were:

- pairwise relation: **2.541**;
- first passage: **2.536**;
- intervention: **2.433**;
- critical-node count: **2.165**;
- full topology identity: **2.541**.

Rows with a strict realized-path saving relative to the fixed panel:

- pairwise relation: **143/144**;
- first passage: **143/144**;
- intervention: **141/144**.

So adaptation is useful even where its worst-case bound remains unchanged.

## Replanning is genuinely outcome-dependent

At least one target had a branching policy in **131/144** rows.

For pairwise relation, first passage, intervention, topology identity and the joint
relational suite, branching occurred in 106 rows.  Critical-node count branched in 123.

Different first outcomes therefore lead to different second measurements.

This is not just a fixed measurement order written as a tree.

## There is no universal first measurement

Across canonical adaptive policies, **24 different first action IDs** appeared.

All three measurement families occurred:

- first-passage;
- knockout;
- pairwise relation.

Thus the best first question depends on the current candidate-world set and declared
target.

## Narrow targets can stop before topology identity

In **75 rows**, intervention or critical-node-count identification had a strictly smaller
adaptive worst-case depth than full topology identity.

That preserves the target-specific principle:

> **do not identify the whole distribution process if the ecological question has
> already become invariant.**

## Full topology remains exactly solvable

Full topology identity was unresolved in **0/144** rows.

Its adaptive worst-case depth was:

- 2 measurements in 2 rows;
- 3 measurements in 142 rows.

So adaptive savings are not obtained by weakening the target.

## Main implication

v10–v13 established that a static raster can hide topology and that a small set of
relational measurements can recover topology-sensitive targets.

v14 adds the sequential version:

> **relational evidence should be chosen after each observed outcome, because the
> remaining distribution worlds determine which relation is informative next.**

The EOG object is therefore not just a set of candidate histories.  It also supports an
exact interrogation policy over those histories.

## Boundary

Measurement counts are finite-world information counts. They do not yet include field
cost, detectability, destructive sampling, timing or ethical constraints.

The next useful question is whether adaptive measurement remains advantageous when
different relational measurements have different costs and feasibility constraints.
