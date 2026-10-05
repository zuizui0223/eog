# EOG v29 candidate pre-screen — wood-decomposer target-specific history retention

## Status

**CANDIDATE PASSED SCIENTIFIC + RIGHTS SCREEN; RAW MATERIALIZATION PENDING.**

No EOG v29 target score has been calculated and no scoring protocol has yet been frozen.

## Candidate

Leopold DR, Wilkie JP, Dickie IA, Allen RB, Buchanan PK & Fukami T (2017).

*Priority effects are interactively regulated by top-down and bottom-up forces:
evidence from wood decomposer communities.*

Ecology Letters 20:1054–1063.

Article DOI: `10.1111/ele.12803`

Public dataset: Dryad `10.5061/dryad.7p2cv`

Dryad data files:

- `sample.data.csv` — sample metadata and wood-decomposition measurements;
- `species.prevalence.csv` — prevalence of the 10 fungal species in each microcosm;
- `collembola.csv` — repeated categorical observations of fungivore abundance.

## Why this candidate matters after v28

v28 showed, in one manipulated plant–microbiome experiment, that arrival-order history was
strongly above its null baseline in fungal community composition but nearly at the null
baseline in an aggregate downstream disease-state target.

The 2017 wood-decomposer experiment is an especially useful second system because the same
assembly-history manipulation was applied to a factorial ecological context while both
community composition and an ecosystem-function target were measured on the same
microcosms.

The published experiment crossed:

- 2 initial nitrogen levels;
- 2 fungivore treatments;
- 5 assembly-history conditions, consisting of four initial fungal species plus a
  no-fungus control;
- 5 replicates;
- 2 destructive harvests (6 and 12 months).

The four manipulated initial colonists were:

- *Ascocoryne sarcoides*;
- *Bisporella citrina*;
- *Daldinia novae-zelandiae*;
- *Trametes versicolor*.

For a target-specific history-retention benchmark, the no-fungus control should not be
treated as a fifth history level unless a later frozen protocol explicitly justifies that
choice.

## Rights screen

Dryad publishes datasets under the Creative Commons Zero (CC0) Public Domain Dedication.

Therefore this candidate does **not** have the independent-reuse restriction that stopped
v27.

Dataset citation and provenance must still be preserved as scholarly attribution.

## Scientific screen

The source publication already reports that assembly history, nitrogen and fungivore
presence interactively affect both:

1. fungal community composition;
2. wood decomposition / wood mass loss.

Therefore v29 must not claim discovery of those effects.

The EOG-specific question, if raw materialization succeeds, should instead be:

> **Does the fraction of present-state variation retaining manipulated assembly history
> differ between fungal community composition and wood decomposition, and does that
> difference itself depend on ecological context (nitrogen × fungivore)?**

This provides a direct test of whether the v28 community-to-function attenuation pattern
is reproducible, absent, or reversed in a second manipulated system.

## Pre-score design boundary

Before raw values are inspected for EOG scoring, the following must be fixed from schema
and experimental design only:

1. exact microcosm identifier joining `sample.data` and `species.prevalence`;
2. exact labels for nitrogen, fungivore, history and harvest;
3. which harvest is primary;
4. whether primary history levels are the four initial fungal species only;
5. exact decomposition variable;
6. exact community representation from the 10 prevalence counts;
7. reduced/full nested models;
8. context-stratified permutation rule;
9. missing-value and control handling;
10. primary sensitivity set.

No target or filter may be added after scoring because it improves agreement with v28.

## Likely inferential architecture — not yet frozen

The natural starting point is:

- experimental unit: one mixed-community microcosm;
- context: nitrogen × fungivore;
- history: initial fungal species;
- target A: fungal community composition;
- target B: wood mass loss / decomposition;
- reduced model: context only;
- full model: context × history;
- history retention: all incremental terms involving history;
- randomization: history labels permuted within the declared ecological context;
- evaluate 12-month harvest as a likely primary endpoint because both community
  composition and decomposition were reported there.

These are **candidate design choices**, not an authoritative v29 protocol.

## Exposure boundary

Already visible before any v29 scoring:

- article abstract and published headline directions;
- four initial-colonist identities;
- 2 × 2 × 5 × 5 × 2 factorial design;
- Dryad file names and usage notes;
- published result that community composition and wood decomposition both depend on
  assembly history and context;
- Dryad CC0 reuse policy.

Not yet accessed for v29 scoring:

- raw CSV values;
- exact column names;
- EOG common-panel membership;
- any EOG partial R²;
- any EOG null distribution;
- any cross-target retention contrast.

## Current blocker

The current execution environment can retrieve the Dryad landing-page metadata but has
not materialized the individual CSV file streams or file IDs.

This is a **transport/materialization blocker**, not a scientific or licensing STOP.

Do not substitute:

- values digitized from article figures;
- published treatment means;
- inferred row ordering;
- reconstructed pseudo-data.

The next valid step is to materialize the three exact Dryad CSVs, fingerprint them, inspect
schema only, and then freeze the v29 scoring protocol before computing any EOG result.
