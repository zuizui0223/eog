# Axis-resolved realized support: time and vertical partition hidden by 2D maps

Status: **future extension / not part of the current EOG-WF endpoint**. Tracks issue #323.

## Scientific motivation

Most raster species-distribution products collapse use into a horizontal map. Let

```text
S_s(x, y, z, t)
```

be the non-negative support or use assigned to taxon `s` at horizontal location `x,y`, vertical stratum `z`, and time bin `t`. A conventional planar product is a marginal projection,

```text
P_s(x, y) = sum_{z,t} S_s(x, y, z, t).
```

Two taxa can therefore have identical `P(x,y)` even when their full supports do not overlap. For example, a hypothetical small grassland mammal and a snake-like predator could use the same horizontal cells but occupy different heights, activity periods, or height-by-time combinations. A 2D map would show co-occurrence; the axis-resolved state may show little simultaneous co-use.

The first EOG slice is deliberately narrower than a new dynamic niche model. It asks:

> **How much apparent overlap is created by collapsing measured vertical and temporal axes?**

## Projection-audit estimand

The internal module `eog.v2.axis_resolved_support` independently normalizes two support tensors and reports Schoener overlap in four representations:

- `D_xyzt`: full horizontal × vertical × temporal state space;
- `D_xy`: planar projection after marginalizing z and time;
- `D_xyz`: time-marginalized support retaining the vertical axis;
- `D_xyt`: z-marginalized support retaining the temporal axis.

It then reports threshold-free differences:

```text
vertical hidden partition = D_xy - D_xyz
temporal hidden partition = D_xy - D_xyt
total projection collapse = D_xy - D_xyzt
joint-only hidden partition = min(D_xyz, D_xyt) - D_xyzt
```

Because marginalization cannot increase total-variation distance, these differences should be non-negative apart from numerical tolerance. Positive values mean a lower-dimensional map makes two support distributions appear more similar than they are in the retained state space.

The joint-only term detects cases in which neither z nor time alone separates the taxa, but the z × time combination does. A simple example is one taxon using low strata by day and high strata by night while another uses the opposite combinations: their z marginals and time marginals are identical, but their joint states are disjoint.

## Relationship to SDMR Product A

Product A does not infer a literal true niche from real occurrence data. Its empirical target is the environmental distribution implied by a fitted relative-suitability surface compared with unused occurrence environments under a frozen information barrier. The candidate selector evaluates niche overlap, centroid, breadth, and quantile-profile recovery in a common audit space, while ordinary prediction is a guardrail.

This extension exposes one reason a planar/environment-only audit can be incomplete. Where time or vertical use is measured, the ecological audit state may need to be expanded from

```text
E(x,y)
```

to

```text
(E(x,y,z,t), z, t)
```

or evaluated conditionally within predeclared z/time strata. The predictor-selection question then becomes whether a selected variable set reconstructs held-out **axis-resolved realized support**, not merely a horizontally projected occurrence environment.

Literal truth remains available only in a known-truth simulation where the generating support tensor is fixed and hidden from selection. In real data, the strongest claim is conditional axis-resolved use or realized support; physiological fundamental niche and causal interaction require independent demographic, physiological, or experimental evidence.

## Observation-process requirements

Apparent temporal or vertical separation can be manufactured by sampling. A confirmatory analysis must freeze before response inspection:

- sensor operating times and downtime;
- sensor height, depth, detection cone, and vertical coverage;
- taxon-specific detectability by time and z;
- time-bin and vertical-bin definitions;
- cyclic time treatment for hour-of-day or season;
- missing-cell masks and minimum support per stratum;
- whether support is occupancy, activity, passage, acoustic detection, telemetry residence, or another state.

A camera at ground level and a microphone in the canopy do not provide interchangeable evidence. Effort must be represented at the same `x × y × z × t` resolution or the analysis must abstain.

## Relationship to EOG and ODSP

ODSP is a superseded tombstone. Its support-field topology was migrated to EOG, so active code belongs here rather than in a second ODSP implementation.

This projection audit precedes topology and reachability:

```text
axis-resolved support generator
    -> projection-collapse audit
    -> axis-specific support topology
    -> time-respecting / vertical-transition worlds
    -> positive-evidence conditioning and forecasting
```

The current slice implements only the first arrow. It does not add a generic connectivity operator, change the active EOG-WF paper denominator, or establish a validated biological method.

## Next valid development stages

1. **Known-truth tensor simulations** — generate concealed temporal, vertical, and joint partition; verify recovery without exposing truth during selection.
2. **Axis-specific topology** — define horizontal, vertical, and temporal adjacency separately rather than treating all axes as Euclidean neighbours.
3. **Time-respecting reachability** — transitions must move forward through time, with cyclic schedules handled explicitly.
4. **Observation-aware empirical validation** — use independently held-out telemetry, acoustics, cameras, depth loggers, or other data with frozen effort semantics.
5. **Interaction interpretation** — only after independent evidence distinguish coexistence, avoidance, encounter opportunity, predation, or competition. Planar overlap alone is insufficient.

## Claim boundary

A large projection-collapse gap means only that the declared lower-dimensional representation discarded separation present in the measured support tensor. It does not by itself prove niche partitioning as a coexistence mechanism, causal avoidance, predator-prey interaction, occupancy, abundance, demographic viability, or a fundamental niche difference.
