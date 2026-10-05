# EOG v30 result — grassland above/belowground target-specific history retention

## Result

The frozen external benchmark completed successfully after one non-statistical packaging
bug was repaired. The repair removed an absent output-metadata lookup and did not alter
the frozen estimand, panel, permutation rule, target definitions or source data.

Authoritative execution:

- workflow run: `37288341858`;
- artifact: `11335900414`;
- artifact digest:
  `sha256:33eb4cc20e89a7cdf7405f72fa37582511f95477852205f42e96d7a69e8b4fb8`;
- result fingerprint:
  `272dc58ef05977ce990811809b44c94889a0c68339b4a7ba93c615a239cd6a59`.

All pinned source blobs reproduced their frozen Git identities.

The primary panel contained **19 rhizoboxes**:

- F-first: 6;
- G-first: 7;
- L-first: 6.

Replicate blocks 1–7 all retained at least two history labels.

## Primary target-specific retention profile

The frozen model compared:

[
M_0 = 1 + mathrm{Replicate}
]

against:

[
M_1 = 1 + mathrm{Replicate} + mathrm{History}.
]

History labels were randomized within replicate for **9,999** paired permutations.

### Aboveground functional-group composition

Forbs/Grasses/Legumes shoot-biomass composition, Bray–Curtis:

- observed partial R²: **0.9529**;
- permutation-null mean: **0.1666**;
- null median: **0.1495**;
- null 95% interval: **0.0271–0.4214**;
- null-calibrated excess (E): **+0.8034**;
- permutation p: **0.0001**.

Arrival order is therefore extremely strongly retained in the final identity structure of
the aboveground community.

### Belowground vertical root distribution

Six-layer root-biomass distribution, Bray–Curtis:

- observed partial R²: **0.1853**;
- permutation-null mean: **0.1669**;
- null median: **0.1509**;
- null 95% interval: **0.0287–0.3747**;
- null-calibrated excess (E): **+0.0344**;
- permutation p: **0.3765**.

The full vertical root-biomass distribution therefore contains little history signal
beyond that expected under within-block randomized arrival identities.

### Frozen cross-target contrast

[
Delta E =
E_{mathrm{shoot composition}}
-
E_{mathrm{root distribution}}
=
mathbf{+0.7690}.
]

This is a very large target-specific difference in retained assembly history on the same
experimental units.

## Independent exact-permutation audit

In addition to the preregistered 9,999-permutation scorer, all **31,104** unique
within-replicate history-label configurations were independently enumerated after the
protocol freeze.

That audit gave:

- shoot composition R² = 0.9529, exact null median = 0.1487,
  (E=+0.8042), exact p ≈ 0.000064;
- root distribution R² = 0.1853, exact null median = 0.1516,
  (E=+0.0337), exact p ≈ 0.3755;
- (Delta E approx +0.7705).

The exact audit therefore agrees with the frozen Monte Carlo result in both magnitude and
interpretation.

## Scalar sensitivities

### Total shoot biomass

- partial R²: **0.2350**;
- null median: **0.1402**;
- excess: **+0.0948**;
- p = **0.2562**.

Thus the exceptionally strong aboveground history signal is not simply a difference in
total plant production.

The history is retained mainly in **which functional group contributes the biomass**, not
in how much total shoot biomass is produced.

### Root mean depth

Biomass-weighted mean root depth:

- partial R²: **0.4050**;
- null median: **0.1287**;
- excess: **+0.2762**;
- p = **0.0767**.

This lower-dimensional root summary retains more historical information than the full
six-layer Bray–Curtis target, but the preregistered randomization diagnostic is not below
0.05 in the primary raw-data panel.

This does not contradict the published source paper, which reported treatment effects on
rooting depth using its own models and source-specific data treatment. v30 asks a
different, null-calibrated history-retention question.

## Frozen source-outlier sensitivity

The source analysis removed Rz 137 from root-biomass analyses because one layer was
considered potentially affected by data encoding.

v30 primary deliberately retained Rz 137. The predeclared sensitivity removing it gives
n = **18**:

### Shoot composition

- R² = **0.9450**;
- null median = **0.1650**;
- (E=+0.7800);
- p = **0.0003**.

### Full root distribution

- R² = **0.1785**;
- null median = **0.1632**;
- (E=+0.0153);
- p = **0.4461**.

### Root mean depth

- R² = **0.6690**;
- null median = **0.1316**;
- (E=+0.5373);
- p = **0.0071**.

### Total shoot biomass

- R² = **0.1731**;
- null median = **0.1599**;
- (E=+0.0131);
- p = **0.4637**.

The primary cross-target result is therefore not driven by Rz 137:

- (Delta E = +0.7647) without Rz 137.

However, the scalar root-mean-depth conclusion is sensitive to that source-data decision
and must remain a sensitivity result.

## Ecological interpretation

The strongest result is not simply that priority effects exist.

The source study already established that assembly history can alter grassland structure
and rooting depth.

v30 adds a target-specific information result:

> **The identity of the first-arriving plant functional group remains almost perfectly
> recoverable from final aboveground functional-group composition, while the same history
> is barely distinguishable from randomized history in the complete vertical
> root-biomass distribution.**

The total-shoot sensitivity sharpens this further.

Arrival history is strongly visible in **community identity structure**, but not in the
aggregate amount of aboveground biomass.

Thus ecological history is not uniformly written into all properties of a community.
The same experiment can simultaneously contain:

- a very strong compositional memory;
- weak aggregate productivity memory;
- weak full-distribution belowground memory;
- and a potentially stronger signal in one selected spatial summary, mean root depth.

## Relation to v28

v28 and v30 are independent in important ways:

- different research groups;
- microbial versus grassland plant communities;
- fungal-species versus plant-functional-group arrival histories;
- host disease versus belowground spatial organization as the second target.

Yet both show the same broad structure:

> **A manipulated assembly history can remain strongly encoded in community composition
> while being much less visible in another present ecological target measured on the
> same experimental units.**

This does **not** establish a universal monotonic law of information loss.

It does establish that the v26 target-specific history-retention result is not confined to
a synthetic world or to one microbial experiment.

## Claim boundary

Do not claim:

- that assembly history has no belowground effect;
- that the source paper's root-depth result failed replication;
- that history always attenuates from composition to function or spatial structure;
- causal mediation from shoot composition to root distribution;
- that p=0.05 is the definition of ecological memory;
- that the root-mean-depth outlier sensitivity is a primary result.

Do claim:

> **Across a second independent manipulated system, the amount of assembly history
> retained by the present depends strongly on which ecological state is measured:
> functional-group composition preserves the arrival identity, whereas aggregate
> productivity and the full belowground spatial distribution preserve far less of it
> under the same blocked null calibration.**

## Next question

With v28 and v30, the empirical question changes.

It is no longer merely:

> does history affect present ecology?

The sharper question is:

> **What determines whether a present ecological variable preserves or erases information
> about assembly history?**

The next analysis should therefore compare target mappings across the completed systems
rather than accumulating arbitrary third examples.
