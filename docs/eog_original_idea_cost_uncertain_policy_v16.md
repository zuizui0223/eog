# Original EOG cost-uncertain adaptive evidence — v16

## Question

v15 assumed that the relative acquisition costs of REL, FP and KO measurements were
known before evidence collection.

v16 removes that assumption.

One adaptive tree must be selected before knowing which of the four frozen cost worlds
will apply.  The tree may react to ecological measurement outcomes, but it may not
observe or learn the cost-world identity.

## Robust objective

For any exact adaptive tree, compute four worst-case total costs.

For each cost world, subtract the v15 cost-world-specific oracle optimum.  This gives a
four-component regret vector.

The v16 policy minimizes:

1. maximum regret across cost worlds;
2. then total regret;
3. then maximum total cost;
4. then canonical policy serialization.

The exact solver retains the Pareto frontier of undominated four-cost policy vectors at
each survivor state.

## Why this is an EOG question

The recommended next measurement is already known to depend on:

- the surviving ecological worlds;
- the declared target;
- the measurement cost world.

If the analyst is uncertain about the last item, evidence design becomes another
finite-world robustness problem.

The question is no longer "what is optimal in one cost model?" but:

> what evidence policy remains acceptable across several declared analyst-cost worlds?

## Boundary

The four cost worlds are still synthetic relative-cost scenarios.  Minimax regret is a
robust decision criterion, not a claim about how real field programmes should value
money, time or biological impact.
