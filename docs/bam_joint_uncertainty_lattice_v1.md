# BAM joint ecological-observation uncertainty lattice v1

## Purpose

Earlier phases expanded two uncertainty axes separately:

- ecological BAM worlds: W0 -> W1;
- assay observation worlds: O0 -> O1.

Phase IX crosses those frozen axes without adding new scenarios.

The four joint universes are:

```text
W0O0 ----> W0O1
 |           |
 v           v
W1O0 ----> W1O1
```

The future ecological decision is the target. Ecological-world and observation-world
identity remain nuisance uncertainty unless target identification requires separating
them.

## Exact burden

For each current-G fiber and structured future transformation, the burden is the exact
minimum number of the same nine frozen actions needed to separate every
target-discordant joint hypothesis.

Insufficiency is treated as infinity.

Because each smaller joint hypothesis set is contained in the corresponding larger
one, exact minimum burden must be monotone along both expansion axes.

## Interaction

The central Phase-IX quantity is not merely whether either uncertainty source increases
burden. It asks whether

[
b(W_1,O_1)
>
\max\{b(W_1,O_0), b(W_0,O_1)\}.
]

Such a case means neither single-axis expansion captures the full evidence requirement
created when ecological alternatives and assay-process alternatives are admitted
together.

This is an exact finite-universe interaction, not a generic statistical interaction
claim.

## Calibration creation

A second diagnostic asks whether ecological expansion changes calibration from optional
to necessary for every exact minimum:

- W0O1 has a finite no-calibration solution;
- W1O1 has a smaller full-library minimum than any no-calibration design.

If so, ecological-world expansion has exposed an observation-process ambiguity that
was irrelevant in the narrower ecological universe.
