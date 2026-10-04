# Original EOG cost-uncertain adaptive evidence — v16 result

## Result

Seven of eight preregistered hypotheses were supported.

The refuted hypothesis was U4:

> **No row-target combination had one adaptive policy that was simultaneously
> oracle-optimal in all four cost worlds.**

Thus cost uncertainty imposed an irreducible price everywhere in the frozen panel.

Authoritative execution:

- workflow run: 37205953953;
- artifact: 11305864610;
- artifact digest:
  sha256:f2b20fa067b1cb8e335012b1f2bccc6f5c75cf406e69c233ab939f83d7bdc73a;
- result fingerprint:
  41ba3c29e1adb71ed2c832ec1e7f10955ac88c6567c29ce6f9c4b1d9ed6eafd4.

## Exact resolution remained possible

Across 144 random-topology rows × six targets = **864 row-targets**:

- unresolved under the cost-blind adaptive solver: **0**;
- negative regret relative to a cost-specific oracle: **0**.

So the common policy constraint did not destroy exact target resolution.

## But zero-regret robustness did not exist

Positive irreducible regret occurred in:

**864/864 row-targets.**

Zero-regret common policy:

**0/864.**

The preregistered coexistence claim U4 was therefore refuted.

The common policy always had to sacrifice oracle optimality in at least one cost world.

## Minimax regret mattered

Compared with freezing the v15 equal-cost-optimal tree and carrying it unchanged into
the other cost worlds, the cost-blind minimax-regret policy had strictly smaller maximum
regret in:

**821/864 row-targets.**

So robust planning was not merely a relabeling of the equal-cost solution.

## Cost uncertainty changed the evidence path

The canonical first action changed relative to the equal-cost oracle in:

**322/864 row-targets.**

Across the selected minimax policies the canonical first-action families were:

- FP: **802**;
- REL: **49**;
- KO: **13**.

There was no universal first action.

## Regret scale

Mean minimum achievable maximum regret was close to two synthetic cost units for every
target:

- pairwise relation: 2.014;
- first passage: 2.014;
- intervention: 2.000;
- critical-node count: 2.049;
- full topology identity: 2.014;
- joint relational suite: 2.014.

Every target had zero zero-regret rows.

## Target specificity survived cost uncertainty

In **52/144** random-topology rows, the robust cost-blind policy for intervention or
critical-node count had a strictly lower maximum total cost than the policy needed for
full topology identity.

So even after adding cost-world uncertainty, the principle remains:

> collect enough information for the ecological target, not automatically enough to
> identify the complete topology.

## Current interpretation

The next-measurement problem now has four distinct uncertainty objects:

1. surviving ecological worlds;
2. declared ecological target;
3. measurement outcome uncertainty;
4. measurement-cost world.

A policy can be exact for the ecological target while still being non-optimal in every
possible cost world.

This is another version of the original EOG idea: uncertainty should remain explicit
rather than being hidden behind one chosen analytical world.

## Boundary

The four cost worlds are synthetic. They do not represent calibrated field budgets.

The result therefore supports a structural statement about evidence-policy robustness,
not a practical claim that one particular REL, FP or KO measurement should be purchased
in a real field programme.
