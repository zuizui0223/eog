# Original EOG source-confluence provenance — v19 result

## Result

All eight preregistered hypotheses were supported.

v18 showed that source placement controls coverage and insurance. v19 shows that the
same geometry also controls how quickly source provenance disappears after source
basins merge.

Authoritative execution:

- run: 37252018824;
- artifact: 11321161763;
- artifact digest:
  sha256:bc4910968de071bab204ee9793a25aa4df69ce591ea8787ef8c8e6c62c7c6686;
- result fingerprint:
  a1a4bcf4a8e6f91888f41e9f14826c662da66b869348c14ed8592b411636fd2d.

## Static final distributions lose provenance

With two clustered sources, the mean fraction of union-reachable nodes compatible with
at least two sources was **0.640**.

With two dispersed sources it was only **0.078**.

At three sources:

- clustered: **0.711**;
- dispersed: **0.146**.

Clustered-minus-dispersed ambiguity was therefore about **+0.56** at both source
counts.

## First-passage order recovers most of the lost information

Among statically ambiguous nodes, timing resolved a unique earliest source for a large
fraction:

- clustered, 2 sources: **85.2%**;
- clustered, 3 sources: **81.9%**;
- dispersed, 2 sources: **93.0%**;
- dispersed, 3 sources: **93.3%**.

Residual ambiguity as a fraction of the whole reachable union fell to:

- clustered 2: **0.108**;
- clustered 3: **0.145**;
- dispersed 2: **0.0048**;
- dispersed 3: **0.0116**.

Timing therefore restores a great deal of source information, but not all of it.

Irreducible equal-earliest ambiguity remained in:

- 100 clustered two-source landscapes;
- 166 clustered three-source landscapes;
- 20 dispersed two-source landscapes;
- 50 dispersed three-source landscapes.

## Confluence is downstream biased

Across source sets containing both unique-origin and ambiguous nodes:

- mean normalized potential of ambiguous nodes: **0.323**;
- unique-origin nodes: **0.531**;
- ambiguous minus unique: **−0.208**.

Lower normalized potential is farther downstream in the frozen outlet geometry.

So source basins tend to remain distinguishable upstream and lose provenance after
confluence downstream.

## Clustered sources converge earlier

Among the 104 landscapes where both two-source treatments produced confluence, the
clustered confluence front occurred **0.508 normalized-potential units farther
upstream** than the dispersed front on average.

This links v18 and v19 directly:

> clustered source placement buys redundancy and source-loss insurance, but it also
> causes source basins to merge earlier and erases source provenance over more of the
> reachable distribution.

## More sources increase ambiguity monotonically

Adding the third source never reduced the absolute number of statically ambiguous
nodes.

Exact violations: **0**.

The earliest-origin set was always a nonempty subset of the static-origin set.

Exact violations: **0**.

## Current ecological statement

A final distribution does not simply record where a species can be reached from.

It also has a **provenance geometry**:

- upstream source-specific basins;
- confluence fronts;
- downstream zones compatible with several source histories.

Static occurrence support loses that provenance after basin confluence.

First-passage order can recover much of it, but equal-time confluence remains
structurally ambiguous.

This is the clearest direct implementation so far of the original EOG
distributional-watershed idea.
