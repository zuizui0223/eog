# Helgeland: date-only as-of-t information firewall (synthetic tests only)

**Stage:** `SYNTHETIC_INFORMATION_FIREWALL_ONLY__ECOLOGICAL_HOLD`.

Helgeland's byte-matched 2026 v6 `presence_data_1994_2022` source contains a physical `date` column and source encounter `stage`. The actual `Year` field was mathematically shown in merged PR #632 to use an April–March label across all 73,593 records, but its author-defined biological interpretation has not yet been independently supplied. Earlier structural QC in PR #630 already exposed aggregate same-ID linkage, **not** observed inter-island migration or heldout outcomes.

## Boundary implemented

The pure function `direct_history_as_of(records, cutoff_date)` (script `scripts/helgeland_date_only_asof_firewall_v1.py`) admits only physical source-record observation types `nest`, `capt` and `obs`, dated on/before the literal ISO calendar cutoff. It projects only five columns `ID`, `Island`, `Location`, `date`, `stage` into immutable in-memory tuples. All post-cutoff observations are excluded from the input history. No `Year`, `Least_age`, `Least_hatchyear`, `scriptsex`, `filled`, `gene_new`, retrospective `born_location`, `downup` interpolation or `N_corr` is consulted to construct that information set. No source file is opened by the module.

The additional helper `directly_observed_single_nest_sources_as_of` permits a candidate nestling source **only** if its **already observed pre-cutoff nest records** all agree on one island. It does not use subsequent sightings to fill an unknown nest island. It **does not infer movement, settlement, recruitment or colonization**.

Synthetic tests prove three hard properties: adding an arbitrary post-cutoff encounter cannot alter the already emitted predictor history; changing `Year` or retrospectively inferred ages/sex cannot alter that history; and ambiguous nest-island attribution cannot be silently resolved by subsequent observations. Invalid date strings fail closed.

## Limits

An observation record dated before cutoff is **not proof that it was entered into the source database or available to analysts then**. Nor is a directly observed bird a survey-effort denominator for unobserved birds. Therefore the source-data observation-availability contract remains `HOLD`, along with unqualified field/season definitions, `NO_SURVEYED_ZERO_PANEL_VERIFIED`, and `NO_INDEPENDENT_HELDOUT_EVENT_BENCHMARK`. The helper never accesses *actual source observation records* in CI and never scores ecological effects. The date-only cutoff is a candidate *information firewall*, not a proof of data-source availability or a biological result.

The next actual source audit must ground **database availability/provenance** and detection effort, rather than promote the already exposed historical events. Evidence history: [EOG Issue #626](https://github.com/zuizui0223/eog/issues/626), [Dryad 2026](https://doi.org/10.5061/dryad.rr4xgxdnq), [original authors' pinned code](https://github.com/torhanssonfrank/DensityRegulationHouseSparrows/blob/a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5/R%20scripts/Main%20model%20of%20metapopulation%20dynamics.R).
