# Original EOG random world-growth experiment — v8

## Question

The original intuition was about conclusions that remain stable while the considered
world becomes more complex.

v8 turns that into a literal growth process.

Start from the frozen B0 certificate universe. Add compatible worlds one at a time in
uniformly random order from one of five frozen pools.

For a certificate with N possible added worlds and K threatening worlds, the exact
expected first-failure draw is:

(N + 1) / (K + 1).

No Monte Carlo ordering is needed.

## Why this matters

v7 showed which direction of world expansion can threaten each certificate type.

v8 asks how quickly the threat arrives under finite random growth.

This gives each baseline certificate a world-growth survival curve rather than a single
survive/fail label.

The quantity is not calendar time. It is robustness to progressive enlargement of the
declared finite world universe.

## Main comparison

- restrictive same-source growth should leave impossibility certificates immortal
  inside that pool;
- permissive same-source growth should leave reachability certificates immortal;
- the opposite certificate types can have finite lifetimes;
- incomparable worlds and new source hypotheses may shorten lifetime further.

This directly implements the original EOG idea of asking what remains invariant as the
space of plausible worlds becomes progressively richer.
