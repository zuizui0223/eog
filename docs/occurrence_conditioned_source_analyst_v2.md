# Source and analyst uncertainty in minimum required relaxation — v2

## Boundary

**New predeclared synthetic source×analytical-representation study.**
The protocol was committed first at
[`validation/occurrence_conditioned_source_analyst_v2/protocol_v2.json`](../validation/occurrence_conditioned_source_analyst_v2/protocol_v2.json).
The original EOG-WF 3/31/3 predictive evidence remains closed. This is not a
fourth ecological endpoint, an empirical source-discovery result, or a new
methodological claim for Pareto-minimum mathematics.

## Why the next inference step matters

The preceding v1 benchmark used one declared source A. If the actual origin is
unknown, a conditional `+20 km` statement **does not automatically establish
a species-level minimum movement distance**. A different plausible source may
require a different relaxation. Likewise a relaxable habitat crossing in one
analyst representation may be a declared hard mask in another.

The v2 question is:

> Which minimum additional assumptions allow **at least one** declared
> source×analytical graph hypothesis to explain all positive occurrences, and
> which additional assumptions allow **every** declared hypothesis to explain
> them?

Both are conditional statements. Requiring every hypothetical source to
explain observations is deliberately conservative, NOT evidence that every
source was historically real.

## Two distinct estimands

Define `H = sources × graph variants` over a *common fixed candidate directed
node and edge universe*; each hypothesis `h` has its own physical/nonphysical
edge availability rules but the **same** three threshold units and baseline.

For each `h`, `F_h(theta)` means all positive endpoints are reachable
within 3 steps under its fixed source.

- **Existentially feasible**: `there exists h in H: F_h(theta)`.
- **Universally compatible**: `for every h in H: F_h(theta)`.
- **Source/analyst contingent**: existentially true but not universally true.
- **Excluded by this finite hypothesis set**: none is feasible.

The primary results are two **separate non-dominated relaxation sets**:
`ParetoMin({theta-theta0: exists h F_h(theta)})` and
`ParetoMin({theta-theta0: forall h F_h(theta)})`. These are not
posterior probabilities or demographic mechanism estimates.

Note: The Pareto-minimal points of the *intersection of feasible sets* are
generally **not** the intersection of source-specific Pareto-minimal points.
The full shared threshold lattice must be used.

## Frozen v2 design

- Nodes: A, B, X, Y; observed positives: A and B.
- Candidate fixed singleton sources: A or B.
- Baseline: 10 km geographic single-step maximum; 1 unit feature-transition
  tolerance; relaxable barrier permission 0.
- Original A-to-B options: +1 environmental tolerance via X, +20 km
  direct geographic jump, +1 categorical barrier permission via Y.
- Reverse B-to-A option: 25 km direct jump (requires +15 km geography).
- Analyst graph variants: **soft_crossing** (Y path may be declared passable)
  and **hard_sea_mask** (both directed Y-path edges structurally excluded).
- Fixed maximum of 3 propagation steps.
- Shared exact threshold grid: geography [10,25,30], environment [1,2],
  barrier [0,1], for 12 combinations.
- Four source×graph hypotheses imply 48 exact compatibility decisions.

Each hypothesis runs the original
`infer_required_relaxations` v1 adapter, which itself uses the original
`eog.v2.reachability.reconstruct_compatible_worlds` and
`minimum_relaxation_frontier`. Every shared-grid decision is then
independently checked by bounded directed BFS; the implementation
verifies upward monotonicity under increased relaxation and invariance
to source/graph/edge declaration order.

## Predeclared expected frontiers (research predictions, not field outcomes)

All vectors are **increments (geographic km, environmental scale units,
categorical barrier permission)**, relative to the common baseline.

| Quantifier and declared hypotheses | Expected Pareto vectors |
| --- | --- |
| source A, soft crossing | (20,0,0); (0,1,0); (0,0,1) |
| source A, hard mask | (20,0,0); (0,1,0) |
| source B, either variant | (15,0,0) |
| **some source and some graph** | **(15,0,0); (0,1,0); (0,0,1)** |
| **both sources, soft graph only** | **(20,0,0); (15,1,0); (15,0,1)** |
| **every source AND every graph** | **(20,0,0); (15,1,0)** |

The key falsifiable statement is that a **barrier-only** route, which is
a valid *possible* explanation under source A in the soft representation,
is **not** a guaranteed common explanation when hard-sea masking is admitted.
Conversely every-hypothesis compatibility forces at least +15 km
geographic relaxation, but a +15 km jump **alone** cannot explain A->B
in every source×graph hypothesis.

## Claim discipline

1. This is a constructed, finite 4×12 **logical consistency** test, not an
   independently sampled ecological effect or real movement observation.
2. Candidate source identities are alternative historical hypotheses;
   observed presence A/B alone does not determine founder/colonisation
   direction.
3. Any claimed minimum depends on source declarations, candidate graph
   completeness, environmental scaling, barrier metadata and horizon.
4. A declared hard mask is not justified by an observed zero in a repeated
   detection survey. The two currently open source-policy PRs #697/#698
   likewise distinguish graph-level structural evidence from nondetection.
5. The barrier axis is categorical permission, not barrier height or a
   crossing probability. The three axes cannot be combined in a unit-free
   scalar without independently justified weights.
6. Equal source/analyst cardinalities are **not prior weights**;
   compatibility counts are enumeration counts, not empirical probabilities.

## What this unlocks next

A genuine empirical minimum assumption requires independently sourced
location-specific geography and environmental measurements, fixed candidate
source hypotheses, external traversal constraints or dispersal ranges and a
valid independent evidence clock. First test identifiability and coverage of
the edge universe. Once positive observations are known, comparing
individual observation-to-network graph design revisions **cannot** count as
preregistered external confirmation.

Run locally:

```bash
python -m pytest -q tests/test_occurrence_conditioned_source_analyst_v2.py
python benchmarks/occurrence_conditioned_source_analyst_v2.py --output results/source_analyst_v2.json
```

Any strict `universal` statement here means *within those declared four
hypotheses only*, never all ecologically possible origins, historical routes
or models.
