# Original EOG empirical history-retention benchmark — v27 result

## Verdict

**ADMINISTRATIVE / INFERENTIAL STOP before EOG scoring.**

No target-specific EOG retention effect was calculated.

The stop has two independent causes discovered during source audit:

1. the source repository explicitly states that the deposited data are provided to
   reproduce the Catano et al. publication and are not for other purposes without
   written consent from the corresponding author;
2. the published species- and trait-NMDS files do not contain restoration-plot or
   subplot identifiers, so the preregistered plot-blocked multivariate analysis cannot
   be reconstructed from the deposited files.

This is not adverse biological evidence.

## Source identity

Public source repository:

- `chcatano/History_BEF`
- Zenodo DOI: `10.5281/zenodo.7120895`
- GitHub release: v1.0.0

Audited source blobs:

- `BEF_analysis_data_Ecology.csv`:
  `922fc0d8573b0da87c171d44eb3fb17f75522e43`
- `species_NMDS_data_Ecology.csv`:
  `d7a1fa3be0551c5c5110a86b2f85b23dfdb9822b`
- `trait_NMDS_data_Ecology.csv`:
  `943dbf3001218a153fda5170cf4665c93eef93c0`

Raw files are **not** copied into EOG.

## Scalar-data structure is adequate

The main BEF file contains:

- 144 rows;
- 18 restoration plots (`site`);
- 3 establishment-year treatments: 2014, 2015, 2016;
- two observation years: 2019 and 2020;
- exactly 8 subplot rows per restoration plot;
- exactly 4 rows per restoration plot in each observation year.

Therefore the v27 primary experimental unit can be reconstructed for the scalar target
family.

Available declared scalar variables include:

- `abg` — ANPP;
- `decomp` — decomposition;
- `floral.cov` — floral resources;
- `alpha.hill1` — species diversity;
- `FDis` — functional dispersion.

Had reuse permission allowed scoring, the preregistered plot × year aggregation is
structurally materializable without pseudo-replicating the 1-m² subplots.

## Composition targets fail the frozen linkage contract

The deposited composition files contain:

### species_NMDS_data_Ecology.csv

- 234 rows;
- columns: `NMDS1, NMDS2, plant.year, year, age`;
- no `site`;
- no `plot`.

### trait_NMDS_data_Ecology.csv

- 229 rows;
- columns: `NMDS1, NMDS2, plant.year, year, age`;
- no `site`;
- no `plot`.

The v27 protocol froze restoration plot as the randomization unit and forbade guessing
or outcome-informed linkage.

Therefore both multivariate targets trigger the predeclared
`required_target_representation_not_reconstructable` /
`ambiguous_many_to_many_target_linkage` stop boundary.

The rows may be sufficient to reproduce the publication's ordination figures, but they
cannot support the EOG plot-blocked history-retention estimand as frozen.

## Data-use boundary

The repository README states that the deposited data are provided to reproduce analyses
in the Catano et al. publication and are not for other purposes without written consent
from Christopher P. Catano.

EOG v27 is a new methodological reanalysis, not a literal reproduction of the published
analysis.

Therefore the scalar targets are not scored without author permission even though their
experimental-unit structure is adequate.

This access/governance stop was discovered **before** any v27 retention effect was
calculated.

## What v27 accomplished

Although no ecological score is reported, v27 closed several methodological gaps:

1. it froze a real-experiment history-retention estimand before raw-value scoring;
2. it implemented scalar nested-model partial R²;
3. it implemented distance-based nested-model partial R²;
4. it implemented whole-plot history-label permutation rather than subplot shuffling;
5. it exposed an important empirical-data requirement: target data must preserve the
   experimental-unit identity needed by the inferential contract;
6. it demonstrated that “publicly downloadable” is not equivalent to “reusable for a new
   analysis” or “inferentially materializable.”

## Claim boundary

Do **not** claim from v27:

- any new Catano et al. history effect;
- an EOG ranking of ANPP, decomposition, floral resources, diversity or FDis;
- species- or trait-composition retention;
- failure of target-specific history retention in real systems.

Do claim:

> **The proposed empirical history-retention benchmark is executable only when both
> reuse permission and experimental-unit identity survive data publication.  In this
> candidate, scalar experimental units are recoverable, but reuse permission blocks new
> scoring and the deposited ordination products cannot support plot-blocked composition
> inference.**

## Next step

Do not repair this candidate post hoc by:

- treating subplots as independent treatment replicates;
- assigning NMDS rows to plots by row order;
- using establishment-year labels as substitutes for plot identity;
- ignoring the repository's explicit data-use statement.

The next empirical candidate should be pre-screened for **both**:

1. an explicit reuse license permitting independent analysis; and
2. preserved experimental-unit identifiers for all primary targets

before it is frozen as the next EOG real-data benchmark.
