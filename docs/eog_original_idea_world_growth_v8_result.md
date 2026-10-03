# Original EOG random world-growth experiment — v8 result

## Result

All seven preregistered hypotheses were supported.

v8 turns the original phrase "what remains unchanged as the world becomes more complex"
into an exact finite-world survival problem.

For a baseline certificate with N admissible future world additions and K threatening
worlds, the exact expected first-failure draw is:

```text
(N + 1) / (K + 1)
```

and the full-pool certificate survives if and only if K = 0.

## Exact directional protection

The v7 protection rules became lifetime statements.

### Robust impossibility under restrictive same-source growth

- certificates: 4,167;
- threatened certificates: 0;
- mean normalized lifetime: **1.000**;
- survival after full pool growth: **100%**.

### Robust reachability under permissive same-source growth

- certificates: 2,628;
- threatened certificates: 0;
- mean normalized lifetime: **1.000**;
- survival after full pool growth: **100%**.

## Opposite-direction growth creates finite lifetimes

Restrictive worlds threatened **81** robust-reachable certificates.

Permissive worlds threatened **1,445** robust-impossible certificates.

Thus the logical protection is strongly directional rather than attached to one
certificate type.

## Mixed/full world growth

Under the full same-source plus new-source growth pool:

### Robust reachability

- mean normalized expected lifetime: **0.974**;
- full-growth survival: **96.1%**.

### Robust impossibility

- mean normalized expected lifetime: **0.715**;
- full-growth survival: **64.8%**.

Difference, impossible minus reachable mean lifetime:

**−0.259**.

This reproduces the v6 endpoint asymmetry dynamically.

## Survival curves

Under all-source growth:

| growth completed | reachable certificate survival | impossible certificate survival |
|---|---:|---:|
| 10% | 0.979 | 0.735 |
| 25% | 0.972 | 0.683 |
| 50% | 0.965 | 0.658 |
| 75% | 0.962 | 0.649 |
| 100% | 0.961 | 0.648 |

The curves are exact combinatorial expectations, not Monte Carlo estimates.

## Additional sources of fragility

Adding equivalent/incomparable same-source worlds shortened normalized lifetime for
**959 certificates** relative to the purely subset/superset directional pool.

Admitting newly compatible source hypotheses shortened lifetime for another
**376 certificates** relative to the complete same-source pool.

So certificate robustness depends on more than whether one parameter setting is more
restrictive or permissive.  Source uncertainty and incomparable mechanism worlds create
additional failure routes.

## Conceptual result

The sequence v6 -> v7 -> v8 now gives a corrected version of the original
reverse-impossibility idea:

1. a universal certificate is stronger when it survives a larger declared world set;
2. impossibility is not intrinsically the stronger certificate type;
3. restrictive world growth protects impossibility;
4. permissive world growth protects reachability;
5. mixed/incomparable/new-source growth gives each certificate a finite threat count;
6. that threat count determines an exact world-growth survival curve.

The useful EOG output is therefore not merely:

```text
possible / impossible
```

but:

```text
certificate type
+ declared world universe
+ allowed expansion direction
+ threat count
+ expected survival under world growth
```

## Boundary

The world-growth axis is model-universe enlargement, not real time.  The numerical
lifetime values should therefore be interpreted as finite-world robustness indices.
