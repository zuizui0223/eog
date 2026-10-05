# Original EOG history-to-state process family — v26 result

## Result

Six of eight preregistered hypotheses were supported.

The two refutations are scientifically important:

- P5 was refuted: the three age-sensitive process families did **not** produce different
  design-row sets with versus without history memory;
- P6 was refuted: rows whose exact age differences were hidden by the persistent lag-2
  threshold were not rescued by the transient or saturating process in the full design-row
  panel.

The main result is therefore more specific than the preregistered headline:

> **whether hidden colonization history survives into a present ecological state depends
> on how the downstream state map partitions colonization age, but process choice need
> not change the coarse yes/no presence of history memory at the whole-design level.**

Authoritative execution:

- workflow run: `37263945496`;
- artifact: `11325488072`;
- artifact digest:
  `sha256:6f1aa148b5ed40ca50836f7288f94b7b42eb56495ac6eedcf0b3759cffcc1ec4`;
- result fingerprint:
  `90096f149d2a3c71b4a00283cef2b1470a7501bbffc6ce39c79fac33540ce27e`.

## Frozen process family

Before scoring, v26 fixed exactly four qualitative mappings from colonization age to
present state:

1. history-blind occupancy;
2. persistent threshold, age >= 2;
3. transient age-1-to-2 window;
4. saturating 0/1/2/3+ age class.

No fifth process was added after scoring.

## A history-blind present state erases age history completely

The control behaved exactly as required:

- rows with history memory: **0/768**;
- history-dependent nodes: **0**;
- v24 hidden-age residuals detected: **0/45**.

So final occupancy alone remains completely blind to colonization age in this frozen
experiment.

## Any age-sensitive target detected memory in the same 726 rows

For all three age-sensitive process families:

- rows with any present-state history memory: **726/768 (94.5%)**.

Their row-level memory sets were identical:

- persistent threshold vs transient window: Jaccard = **1.0**;
- persistent threshold vs saturating age class: Jaccard = **1.0**;
- transient window vs saturating age class: Jaccard = **1.0**.

This refutes P5 as preregistered.  In this generator, process class did not determine
whether a design row had *any* age-sensitive present-state memory.

## But process choice changed how much history survived

Although the same 726 rows contained some memory under every age-sensitive process, the
amount of state affected differed strongly.

History-dependent node fractions were:

- persistent threshold: **0.274**;
- transient window: **0.458**;
- saturating age class: **0.492**.

History-dependent node counts were:

- persistent threshold: **2,461**;
- transient window: **4,112**;
- saturating age class: **4,412**.

Thus a binary statement that “history matters” discards substantial process-specific
information about where and how much of the present landscape retains history.

## The hard v24 aliases expose strong target dependence

The strongest result appears inside the **45** v24 rows where occupancy + provenance
already failed to distinguish colonization-age histories.

Number of those 45 aliases split by each present-state target:

- history-blind occupancy: **0/45**;
- persistent lag-2 threshold: **12/45**;
- transient age-1-to-2 window: **45/45**;
- saturating age class: **45/45**.

Therefore the same hidden age differences can be invisible to one biologically plausible
state target yet fully visible to another.

This supports P8 and sharpens the v25 conclusion: target specificity is not merely a
rare exception around a generally fixed history effect.  It can determine whether a
residual historical difference is visible at all.

## More state categories are not the whole explanation

The four-state saturating target detected all 45 v24 hidden-age aliases, but so did the
two-state transient target.

Therefore the useful distinction is not simply:

> more present-state categories = more history information.

A coarse target can retain the relevant historical contrast when its state boundary is
aligned with the ages on which the histories differ.

Conversely, the persistent lag-2 binary threshold retained only 12 of the 45 hidden-age
aliases.

This alignment interpretation is a post-result structural inference, not a separately
preregistered test.

## Exact age can still be finer than every declared present-state target

There were **6/768** rows where exact age history differed but the persistent threshold
did not.

There were also **6/768** rows where exact age history differed but the saturating 0/1/2/3+
target did not.

None of the threshold-hidden rows was rescued by the transient or saturating target in
the full design-row panel.

So even a richer finite age-state map can erase distinctions that remain present in exact
colonization age.

## Biological interpretation

The result changes the ecological question.

The useful question is no longer simply:

> does history matter?

It is:

> **which present ecological variables retain which components of time-since-colonization
> history?**

Two landscapes can share the same final occupancy and provenance while differing in
colonization age.  Whether that difference remains ecologically visible depends on the
response of the downstream process to age.

Real systems could express such maps through maturation, transient susceptibility,
successional state, local adaptation, mutualist accumulation, pathogen build-up or soil
legacy.  v26 does **not** demonstrate any of those mechanisms empirically; it establishes
the structural distinction in the frozen known-truth system.

## Corrected mainline conclusion

The strongest statement supported by v25-v26 is:

> **distributional history is not a binary property that is either remembered or
> forgotten by the present.  Present landscapes retain a target-specific projection of
> history: different ecological state mappings can preserve very different amounts of
> the same hidden colonization-age information.**

## Next question

The next valid question is not to add more arbitrary process shapes.

The v26 result points to a sharper structural hypothesis:

> **history retention is governed by how a downstream process partitions the spectrum of
> hidden colonization-age differences, not simply by whether the process is monotone or
> by how many state categories it has.**

That can be tested prospectively by freezing matched-complexity age-to-state partitions
with shifted boundaries and asking whether retention follows boundary alignment with the
hidden age contrasts.
