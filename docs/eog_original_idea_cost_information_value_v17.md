# Original EOG cost-information value — v17

## Question

v16 showed that one policy shared across four uncertain measurement-cost worlds always
pays positive regret.

v17 asks whether it is worth learning the cost world before ecological evidence
collection.

No new cost world or cost ratio is added.

## Perfect information

If the cost world were known exactly, the analyst could use the v15 cost-specific oracle
policy.

The gross value of perfect cost information is therefore the reduction from the v16
cost-blind minimum maximum regret to zero.

This value is also the exact break-even calibration cost in the same synthetic cost
units.

## One-bit cost diagnostics

Three binary diagnostics are considered:

- is FP expensive?;
- is REL expensive?;
- is KO expensive?

A yes outcome identifies one singleton cost world. A no outcome leaves the other three
cost worlds.

After the diagnostic, the ecological evidence policy is re-optimized exactly for the
remaining subset of cost worlds.

The gross information value is the reduction in worst residual regret before any
calibration price is charged.

## Why this closes the cost-world subseries

The v15-v17 sequence asks:

1. what if cost is known?;
2. what if cost is unknown?;
3. what is the value of learning it?

v17 reports the exact break-even value rather than inventing another calibration price.

After this test, synthetic cost-world variants stop.
