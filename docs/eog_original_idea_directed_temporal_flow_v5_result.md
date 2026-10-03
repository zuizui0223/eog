# Original EOG directed and temporal flow — v5 result

## Result

Six of seven preregistered hypotheses were supported.

The result cleanly separates **source/history information** from **spatial-envelope
information**.

## Directionality broke the v4 plateau

The v4 undirected worlds had shown no increase in robust-impossibility recovery when
positive coverage increased.

The matched v5 undirected control again showed a flat recovery:

- 10%: **0.1911**
- 25%: **0.1911**
- 50%: **0.1911**
- 100%: **0.1911**

After orienting the same filtered edges toward a frozen outlet, recovery became:

- 10%: **0.6047**
- 25%: **0.6504**
- 50%: **0.6545**
- 100%: **0.6552**

So directionality converted extra occurrence anchors into new robust-impossibility
information.

## Directionality also broke source symmetry

Mean surviving source hypotheses at full positive coverage:

- undirected static: **27.14**
- directed static: **2.15**
- directed temporal: **2.06**

Exact source recovery:

- undirected: **0/272**
- directed static: **53/272**
- directed temporal: **71/272**

This is a direct known-truth demonstration of why the original EOG "flow" intuition
matters: a connected undirected component hides source identity, while directional
reachability makes different source positions observationally distinguishable.

## Ordered relations became strongly asymmetric

Every eligible directed truth world contained at least one asymmetric source-target
relation.

Mean fraction of unordered truth-reachable pairs for which exactly one direction was
reachable: **0.806**.

Thus a distribution represented as an unordered cloud discards a large amount of
structural information in this generator.

## Temporal order added history information

At full positive coverage, adding reached-by-depth constraints:

- strictly contracted the directed-static survivor set in **70/272** rows;
- reduced mean surviving source count from **2.154** to **2.055**;
- increased exact source recovery from **53** to **71** rows;
- increased exact world recovery from **8** to **10** rows.

So temporal positives were genuinely informative about which source/history remained
possible.

## But temporal order did not add robust impossibility at full coverage

The predeclared D5 hypothesis was **REFUTED**.

Full-coverage robust-impossibility recovery:

- directed static: **0.655179**
- directed temporal: **0.655179**

Difference: **0**.

Temporal evidence removed some source/history worlds, but those eliminated worlds did
not enlarge the union of reachable nodes across the remaining worlds.

This gives a sharper decomposition of EOG information:

1. **identity information** — which source/history/world remains compatible;
2. **envelope information** — which nodes remain possible or robustly impossible.

The two are not interchangeable.

## Current conclusion

The original flow idea survives a stronger known-truth test:

- local viability and reachability are distinct;
- spatial arrangement of occurrences matters;
- directionality is crucial for source/history information;
- directionality can increase robust impossibility information;
- temporal order can identify history without necessarily changing the final
  reachability envelope.

The next experiment should therefore stop asking whether "more evidence" is useful in
general. It should ask:

> **Which evidence channels cross a target-equivalence boundary and change the
> reachability envelope, and which merely distinguish worlds inside the same envelope
> class?**
