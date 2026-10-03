# Original EOG expansion-direction experiment — v7 result

## Result

All eight preregistered hypotheses were supported.

v7 resolves the v6 refutation.

The correct statement is not:

> impossibility is intrinsically more robust than possibility.

It is:

> **the certificate protected by world expansion depends on the direction of that
> expansion.**

## Exact protection rules

For each source already compatible with the frozen positive evidence, parameter worlds
were classified by reachable-set inclusion relative to that source's reference world.

### Restrictive additions

A restrictive world has a strict subset of the reference reachable set.

Observed:

- robust-impossible protection violations: **0**;
- robust-reachable certificates erased: **81**, across 46 rows.

A restrictive world cannot make a baseline-impossible node reachable, but it can remove
a node that every baseline world reached.

### Permissive additions

A permissive world has a strict superset of the reference reachable set.

Observed:

- robust-reachable protection violations: **0**;
- robust-impossible certificates erased: **1,445**, across 193 rows.

A permissive world cannot lose a baseline robust-reachable node, but it can make a
baseline-impossible node newly possible.

## Why v6 looked so asymmetric

Among compatible added same-source parameter worlds:

- permissive: **1,583**;
- restrictive: **151**;
- equivalent: **1,315**;
- incomparable: **82**.

The frozen candidate universe therefore expanded much more strongly in the permissive
direction.

That is why v6 found:

- robust reachability retention: 96.1%;
- robust impossibility retention: 64.8%.

The apparent weakness of impossibility was not a property of the logical quantifier
alone.  It reflected what kinds of worlds were being admitted.

## Mixed expansion

Combining restrictive and permissive additions erased both certificate classes:

- robust reachable lost: **81**;
- robust impossible lost: **1,445**.

This was exactly the union of the two directional effects.

## Incomparable worlds add extra fragility

After the directional subset/superset worlds were admitted, adding equivalent and
incomparable same-source parameter worlds caused extra certificate loss in **11 rows**.

The total additional loss was:

- reachability: +18;
- impossibility: +0.

So reachable-set ordering explains most, but not all, same-source parameter-world
fragility.

## New source hypotheses matter too

Allowing worlds from sources whose reference world had not survived the baseline
evidence caused extra loss in **8 rows**:

- reachability: +4;
- impossibility: +22.

Thus the exact directional protection rules require the source hypothesis set to be
held fixed.

## Corrected reverse-impossibility principle

The original intuition can now be stated precisely.

A robust-impossible certificate is protected against future uncertainty when the
admissible expansion is guaranteed to be **restrictive** relative to the certified
source worlds.

It is not protected against a more permissive world, a sufficiently incomparable
world, or a newly admitted source hypothesis.

Likewise, robust reachability is protected against permissive expansion but not
restrictive expansion.

Therefore every EOG robustness statement should declare not only:

- the current world universe;

but also, when possible:

- the **allowed direction of future world expansion**.

This is much stronger than simply saying "impossibility is robust."
