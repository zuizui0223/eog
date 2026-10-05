# Original EOG source-history memory — v21 result

## Result

All eight preregistered hypotheses were supported.

The core result is:

> **the final occupied distribution can completely forget source activation order while
> the source-provenance map still remembers it.**

The three histories had exactly the same final source identities, source count, A/B/M
landscape and equilibrium reachable union.  Only the assignment of activation times
{0,2,4} to the three sources changed.

Authoritative execution:

- run: 37253585524;
- artifact: 11322163376;
- artifact digest:
  sha256:666ae4757128e8d3455bd8caeffee31d15c38da381db55f08215861705a3ff38;
- result fingerprint:
  40d349a8b134c72add0cd4aeb757b569654d45a519c2efcfe9114a1584dfdd25.

## Transient occupancy remembers activation order

Across 768 source-geometry design rows, transient occupied sets differed among the three
histories in **552**.

Mean pairwise transient occupancy Jaccard distance:

- clustered sources: **0.095**;
- dispersed sources: **0.221**.

Thus dispersed source systems were more sensitive in their transient spatial footprint
to which source activated first.

## Equilibrium occupancy forgets history

Equilibrium occupied-set equality violations:

**0**.

Every activation history eventually converged to exactly the same final occupied node
set.

So if only the final occurrence map were observed, activation order would be invisible.

## Provenance retains history after occupancy converges

Despite identical equilibrium occupancy, the equilibrium earliest-source map differed
among histories in **507/768** design rows.

Mean provenance disagreement fraction:

- clustered: **0.711**;
- dispersed: **0.106**.

Clustered-minus-dispersed difference:

**+0.606**.

This is a strong geometry dependence.  Clustered source basins overlap heavily, so
changing activation order changes which source wins first arrival over a large part of
the final distribution.

## Static source ambiguity and temporal recovery

Static source-origin ambiguity was high for clustered sources:

- clustered: **0.711**;
- dispersed: **0.146**.

Once activation time and path depth were used, mean earliest-origin ambiguity dropped
to:

- clustered: **0.0046**;
- dispersed: **0.0129**.

Timing therefore removed most static source ambiguity.

But it did not remove all of it: equal-earliest ties remained in some landscapes.

## Two forms of memory move in opposite directions

The source geometry effect split cleanly:

- dispersed sources → stronger **transient occupancy memory**;
- clustered sources → stronger **equilibrium provenance memory**.

So “history dependence” is not one scalar phenomenon.

The same final system can remember history in:

1. which nodes were occupied during the transient;
2. which source arrived first at nodes that are eventually occupied in every history.

## EOG interpretation

This is a direct known-truth realization of the distributional-watershed idea.

Two river systems can end with the same water extent while retaining different
information about which upstream basin reached downstream nodes first.

For EOG this means:

> **final distributional state and distributional history must be represented
> separately.**

A static final map can be an exact representation of equilibrium occupancy and still be
an incomplete representation of the ecological history that generated it.
