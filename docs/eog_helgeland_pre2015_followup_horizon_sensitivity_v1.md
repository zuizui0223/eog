# Helgeland pre-2015: first encounter vs any later observed island-code change

## Current empirical baseline

In [merged PR #642](https://github.com/zuizui0223/eog/pull/642), the SHA256-verified Dryad 2026 v6 presence archive (10.5061/dryad.rr4xgxdnq, version 421942/file 4576411) was filtered by **physical observation date 1994-01-01 through 2014-12-31**, without inspecting 2015–2022 individual/island/stage values. Among **10,737** IDs with a single physical nest island code, **4,164** had a later direct `capt/obs` record. At the first later date **223** IDs were on a different code and **3,941** on the same code.

The 223 are observed *first-followup code changes*, not natal adult dispersal or a recruitment rate. **They are structurally biased downward as a proxy for ever detecting a different code:** an ID may first be captured again on its recorded nest site, then later be directly observed on another site. A synthetic A→A→B example already demonstrates that logical failure. This audit quantifies whether and how much that happens **in the already exposed 1994–2014 source period**, without using later endpoints.

## Exact follow-up definition, frozen before this new outcome scan

The protocol is `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_followup_horizon_protocol_v1.json`, marked **post-first-followup-exposure / before-all-later site scan**.

- One source nest code per ID across all pre-2015 `stage=nest` records (multiple different nest codes = ambiguous, excluded).
- Strictly later `date` physical direct `capt/obs` only. Same-day-as-nest records are not later events. No `Year` label, `Least_age`, `Least_hatchyear`, `scriptsex`, full-life `born_location`, `downup` or genetic inference as information available at time `t`.
- **Primary sensitivity:** among pre-2015 IDs with unique nest-site codes, count *any* directly observed different code on a later date by 2014-12-31, and specifically the IDs **first seen again on the same code, then only later directly observed elsewhere**. Report the earlier first-code-change count for reference with the same original definition.
- **Secondary:** IDs first seen elsewhere and later observed back on nest code; 30-day and 365-day direct detection and different-code detection, only among IDs with enough **calendar space** until 2014-12-31 for the full window. A complete potential 365-day interval is not complete field-survey effort.
- All source lines receive a date-only filter BEFORE the code accesses ID/island/locality/stage. 2015–2022 outcomes are never queried in this audit. All source ID/island values remain in memory only; outputs contain **numeric aggregates**, without per-island counts or time series.
- Reconcile exact already published source row counts and first-followup 223/3,941/4,164 baselines, or STOP. The source's full-file SHA256 and first physical header are independently reverified before any observation values are inspected.

## Scientific boundaries and why this is useful

Any-site-change-after-nest is an **observed positive-detection property conditional on follow-up**. It is neither guaranteed natal dispersal nor permanent settlement, a demographic source/sink mechanism, an ecological effect, or a model performance result. Recapture probability, heterogeneous study entry and unequal follow-up still confound apparent proportions. An administrative 365-day eligible cohort only mitigates one temporal-censoring problem; it does **not** create surveyed-zero or an effort-corrected dispersal probability.

This follow-up also cannot be called blind external validation: the 2026 data source was published long after the 2014 cutoff and PR #642's aggregate event categories were already seen. Ranke et al. 2021 had previously studied true natal recruitment/destination events. A model beating distance-only dispersal on genuinely source-available post-2020 outcomes remains a **separate unqualified target**.

If the two observed direct-site-code metrics diverge materially, the defensible discovery is a **measurement/observation-window sensitivity** of a dispersal proxy, not an adaptive evolutionary mechanism. The observation-process interpretation must be compared against alternate event definitions and ring/census effort before ecological extrapolation. No baseline EOG-WF 3/31/3 count is changed.

Evidence thread: [Issue #626](https://github.com/zuizui0223/eog/issues/626).
