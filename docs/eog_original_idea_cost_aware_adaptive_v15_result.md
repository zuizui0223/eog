# Original EOG cost-aware adaptive evidence — v15 result

## Result

All eight preregistered hypotheses were supported.

The key result is simple:

> **the best next relational measurement depends not only on the surviving ecological
> worlds and the target, but also on the analyst's cost model.**

Authoritative execution:

- run: 37193176787;
- artifact: 11300468964;
- artifact digest:
  sha256:486a28b4159f2a46ab826c20c7ad436d23c68571167fa8a4052a80108e741333;
- result fingerprint:
  700f0bc17b47c9225a1d3420360df649761900722325e8a03133cb2d156ebc87.

## Adaptive cost never lost to the best fixed panel

Across all 144 random-topology rows, six targets and four cost worlds:

- adaptive-worst-case > fixed-minimum violations: **0**;
- unresolved row-target-cost-world combinations: **0**.

So the cost-aware decision tree never bought its flexibility by relaxing correctness.

## Cost assumptions changed the first measurement

Relative to the equal-cost world, the canonical first action changed **1,023 times**
across the frozen row-target-cost comparisons.

The clearest sensitivity test was predeclared C4.

When one family was made three times as expensive, its pooled canonical-first frequency
fell to zero:

- REL: 8 -> 0;
- FP: 852 -> 0;
- KO: 4 -> 0.

Thus a recommendation such as "measure first passage first" is not universal.  It is
conditional on the assumed acquisition costs.

## Adaptivity remained useful under every cost world

Rows having at least one strict adaptive worst-case saving over the best fixed panel:

- equal cost: **91/144**;
- KO expensive: **80/144**;
- FP expensive: **141/144**;
- REL expensive: **88/144**.

Policies also remained branch-specific:

- equal: 131 rows with branching;
- KO expensive: 130;
- FP expensive: 143;
- REL expensive: 129.

So cost sensitivity did not reduce the planner to one fixed ordering.

## A useful example: expensive first-passage measurements

Making FP cost 3 while REL/KO cost 1 changed the pairwise-relation target from:

- best fixed mean cost: 4.014;
- adaptive worst-case mean: 3.049;
- realized adaptive mean: 2.829.

The planner avoided expensive FP as the first action entirely, switching first choices
to REL or KO measurements while preserving exact target resolution.

## Narrow targets still stop earlier

For every cost world, at least one row allowed intervention response or critical-node
count to be identified at lower adaptive worst-case cost than full topology identity.

This preserves one of the strongest results from the earlier finite-world programme:

> do not recover more mechanism/topology than the declared ecological question needs.

## Current formulation of EOG evidence design

The next-measurement problem now has three explicit conditioning objects:

1. **world set** — what ecological histories remain compatible?;
2. **target** — what ecological question must be resolved?;
3. **cost world** — what measurements are expensive or cheap to acquire?

The optimal action can change when any of the three changes.

## Boundary

The cost numbers are synthetic.  They are not yet estimates of field money, time,
mortality, sequencing cost or observer effort.

The next useful step is therefore not another arbitrary cost ratio.  It is to ask
whether a single evidence policy can remain acceptable when the **cost world itself is
uncertain**, rather than known in advance.
