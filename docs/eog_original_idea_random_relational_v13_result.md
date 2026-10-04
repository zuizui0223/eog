# Original EOG random relational sufficiency — v13 result

## Result

All eight preregistered hypotheses were supported across **144 random topology
panels**, each containing **12 static-equivalent topology worlds**.

The v11 one-measurement shortcuts did not generalize.

Instead, most topology-sensitive targets required **three relational measurements**,
occasionally four.

## Exact burden

Across 144 rows:

- pairwise relation: mean **3.264**, median **3**;
- first passage: mean **3.264**, median **3**;
- intervention: mean **3.104**, median **3**;
- critical-node count: mean **2.903**, median **3**;
- full topology identity: mean **3.264**, median **3**;
- joint relational suite: mean **3.264**, median **3**.

No target had an unresolved row.

For pairwise relation, first passage, full topology and the joint relational suite:

- 106/144 rows required 3 measurements;
- 38/144 required 4.

## Random worlds break the hand-built shortcut

In v11, one first-passage measurement could resolve first-passage, intervention and
critical-node-count targets in the four controlled archetypes.

That shortcut disappeared in random topologies.

At eight active nodes, relation/first-passage/topology identity required **3.69**
measurements on average.

At 12 nodes the mean fell to **3.08**, and at 16 nodes to **3.02**.

Because each row still contains only 12 candidate worlds, this is a statement about the
informativeness of available relational measurements, not a claim that larger networks
are intrinsically easier.

## Static map versus relational information

All 12 candidate worlds in a row have the same static nodewise representation.

Yet three or four targeted relational measurements are enough to distinguish their
topology-sensitive targets — and even the exact finite topology identity.

So the relevant information gap is now quantitative:

> a complete static map may carry zero discrimination among the 12 worlds, while a tiny
> target-chosen relational subset carries enough information to resolve the target.

## Different targets need different information

Intervention remained slightly coarser than complete pairwise relation structure:

- intervention mean burden: 3.104;
- pairwise relation: 3.264.

Critical-node count was coarser again: 2.903.

Target class count was positively associated with burden, but only weakly:

- pooled Spearman rho = **0.0801**.

Thus class count alone does not explain which relational measurements are informative.

## Cross-family evidence remains useful

Exact minimum designs using a measurement family different from the semantic target
family occurred in:

- pairwise relation: 144/144 rows;
- intervention: 144/144;
- first passage: 141/144;
- critical-node count: 143/144.

The shortest path to a target is therefore not necessarily to measure that target's
own most obvious relation type.

## No universal first measurement

Canonical exact minima used **11 different first measurement IDs**.

Most were first-passage measurements, but one knockout measurement also appeared.

This is important operationally:

> once the candidate world set changes, the most informative next relation changes.

## Next question

v13 optimized one fixed measurement set that must resolve the target for all possible
outcomes.

The next valid experiment is adaptive.

After observing the result of the first relational measurement, EOG can contract the
world set and choose a different second measurement for each branch.

The test is whether an exact adaptive decision tree:

- reduces expected measurement burden;
- reduces worst-case burden in at least some rows;
- chooses different next measurements after different outcomes;
- preserves exact target resolution.

That is the natural bridge from relational sufficiency to sequential evidence design.
