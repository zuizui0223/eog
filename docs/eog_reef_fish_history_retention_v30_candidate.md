# EOG v30 candidate pre-screen — reef-fish target-specific history retention

## Status

**CANDIDATE PASSED SCIENTIFIC + RIGHTS SCREEN; METADATA PROBE PENDING.**

No v30 response value or EOG target score has been accessed.

## Candidate

Geange SW & Stier AC (2010).

*Priority effects and habitat complexity affect the strength of competition.*

Oecologia 163:111–118.

Article DOI: `10.1007/s00442-009-1554-z`

BCO-DMO primary dataset: ID `726890`

Related BCO-DMO datasets:

- habitat area: 726929;
- focal-fish lengths: 727007;
- background reef community: 726945.

BCO-DMO marks the experimental datasets as **CC-BY-4.0**.

## Why this is the next system

v28 established in a plant–fungal experiment that the same manipulated history was
strongly retained above null in fungal community composition but was close to its null
baseline in aggregate rust-lesion state.

The reef-fish experiment is from a different research system and uses a different kind of
history manipulation: whether competitors arrive simultaneously with focal settlers or
five days earlier.

It measures at least two present ecological targets on each experimental reef:

1. focal-fish survival;
2. aggression against focal fish.

This allows an independent test of the EOG proposition that the same manipulated history
need not be equally visible in different present-state targets.

## Published design facts visible before v30 scoring

The source paper and BCO-DMO metadata establish:

- experimental unit: isolated patch reef;
- focal species: *Thalassoma quinquevittatum*;
- three focal settlers introduced to each reef;
- habitat complexity: 2 vs 4 *Pocillopora verrucosa* colonies;
- competitor condition:
  - absent;
  - simultaneous arrival (0 days);
  - competitors introduced 5 days earlier;
- two temporal blocks;
- five replicates per treatment × block;
- reefs surveyed twice daily for five days.

The publication already reports that arrival timing affects both survival and aggression.
That direction is **not** a fresh v30 discovery.

## Primary history definition before response access

For the EOG history-retention benchmark, the primary manipulated history contrast is
prospectively restricted to reefs that contain competitors:

- `simultaneous`: focal fish and competitors introduced together;
- `prior_5d`: competitors introduced five days before focal fish.

The no-competitor treatment is a competition control, not an alternative realization of
the same arrival-order history, and is therefore excluded from the primary retention
estimand.

This choice is fixed before reading the primary dataset's response values.

## Context definition before response access

Primary ecological context:

- habitat complexity;
- temporal block.

The initial intended reduced/full structure is:

- reduced: context only;
- full: context + history + context × history.

The exact encoding is not frozen until the dataset metadata confirms available columns and
factor labels.

## Candidate targets before response access

Exactly two primary target families are declared:

1. **survival** of focal fish at experiment end;
2. **aggression** against focal fish.

If the primary dataset does not contain both at the reef level, v30 stops rather than
silently substitutes a different endpoint.

## Null-calibration principle

v28 showed that raw partial R² can be misleading when a large history-by-context subspace
is added.

Therefore any v30 history-retention score must be calibrated against permutations of the
arrival-timing history label under the experimental randomization structure.

The exact permutation strata are frozen only after metadata confirms block and habitat
coding.

## Exposure boundary

Already viewed:

- source-paper abstract and qualitative headline;
- published experimental design;
- qualitative result that later arrival lowers survival and increases aggression;
- BCO-DMO dataset IDs and CC-BY-4.0 status.

Not yet viewed through v30:

- primary dataset response rows;
- response-value distributions;
- exact BCO-DMO column names for dataset 726890;
- common-panel membership;
- any EOG partial R²;
- any permutation-null distribution;
- any target-retention ordering.

## Next step

Query BCO-DMO ERDDAP **metadata only**:

1. discover the ERDDAP dataset identifier associated with BCO-DMO dataset 726890;
2. retrieve variable names and attributes;
3. fingerprint the metadata response;
4. confirm survival, aggression, timing, habitat, block and reef identifiers exist;
5. freeze the scoring protocol;
6. only then open response values.

