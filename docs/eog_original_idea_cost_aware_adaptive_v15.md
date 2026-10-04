# Original EOG cost-aware adaptive relational evidence — v15

## Question

v14 showed that exact outcome-adaptive measurement can reduce the number of relational
measurements needed to identify topology-sensitive targets.

v15 asks whether that result survives when different measurement families have different
predeclared costs.

## Frozen cost worlds

Four analyst cost worlds are used:

| cost world | REL | FP | KO |
|---|---:|---:|---:|
| equal | 1 | 1 | 1 |
| KO expensive | 1 | 1 | 3 |
| FP expensive | 1 | 3 | 1 |
| REL expensive | 3 | 1 | 1 |

These are sensitivity scenarios, not field budgets.

## Exact objectives

For each row, target and cost world:

- fixed reference: minimum total cost of one nonadaptive measurement set sufficient for
  every candidate world;
- adaptive policy: minimum worst-case total cost of a decision tree that can choose the
  next measurement after observing the previous result.

The target-specific stopping rule is unchanged.

## Why this matters

There are two distinct analyst choices:

1. which ecological worlds are considered plausible;
2. which kinds of evidence are considered expensive or feasible.

A robust evidence recommendation should not silently assume that REL, FP and KO
measurements are interchangeable.

v15 therefore treats evidence cost itself as an analyst-world axis.

## Regression requirement

Under equal cost, the weighted fixed solver must exactly reproduce the v13 minimum
measurement counts, and the weighted adaptive solver must reproduce the v14 adaptive
worst-case depths.

Any mismatch is an implementation failure.
