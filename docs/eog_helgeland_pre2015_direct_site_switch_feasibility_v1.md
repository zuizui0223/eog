# Helgeland: observed pre-2015 nest-to-first-direct site-code transition feasibility

**This is an exploratory analysis using already-public 2026 archive observations and is not an out-of-time EOG forecast.** Earlier 2026 aggregate structural QC (merged #630) already revealed 6,299 full-period ringed IDs with one documented nest island and some later physical direct encounter, so the data source and study topic are outcome-exposed. The **site-code change classification** described here is specified before first inspection of pre-2015 migration-like transitions.

## Scientific motivation and strict separation

Dryad 2020 v8 historical source records are identified (merged #634) and shown to have registered file hashes equal to some later copies (merged #639), but their physical originals have not been downloaded: HTTP401/403 via Dryad and a new Zenodo search attempt also failed. It is inappropriate to claim a true publicly available 2020 model on that basis.

The **2026 Dryad v6** `10.5061/dryad.rr4xgxdnq`, numeric version 421942, file ID 4576411, has independently verified whole-file SHA256 parity with the authors' public pinned GitHub commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5` (merged #628) and an attested physical `Year/date/scriptsex/Island/Location/stage/Least_age/Least_hatchyear/ID` header (merged #629).

This diagnostic uses **only actual encounter `date` rather than `Year`** because the latter follows a 4月〜翌3月 label. It limits **all ID, island and stage inspection to 1994-01-01 through 2014-12-31**, an already published historical study window. For post-2014 and pre-1994 source rows, the code inspects `date` only and skips the other variables; this preserves uninspected 2015–2022 movement destinations as possible *future evaluation material*, though historical public availability of the full file remains unverified.

## Frozen event definition and analytical denominators

Source policy is precommitted in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_direct_code_switch_protocol_v1.json`.

A structurally eligible nestling has one or more directly recorded physical `stage=nest` observations on **exactly one `Island` code** in the eligible calendar window. If any pre-cutoff nest stage record puts that ID on multiple island codes, the ID is **ambiguous** and withheld from same/change classifications.

For each otherwise eligible ID, look for the **first strictly later physical `stage=capt/obs` date** no later than 2014-12-31, regardless of `Year`, `Least_age`, `Least_hatchyear`, `scriptsex` or later genotype inference. At that first later date:

- one same island code → `first_followup_same_island_code`;
- one different island code → `first_followup_changed_island_code`;
- more than one island code → `first_followup_ambiguous_island_code`.

Never infer a source from a later ID's first residence, use `filled`/future `downup` states or assign a missing identity. Only **aggregate counts** may be emitted; raw individual IDs, dates and island names/codes are never serialized.

## First real observed result (October 9 2026, exploratory only)

GitHub Actions run **37888118673** passed both SHA256 + physical-firstline source tests, then read **only pre-2015 site-code/ID/stage fields** for first followup aggregation. Metadata-only artifact ID **11596374594**, ZIP SHA256 `2f7767d193397f34d598d9c8d21609da52f5c90e073fea29354271d263f03b6e`, was independently opened.

- **73,593** original rows had their physical observation `date` read to apply the cutoff. **51,162** rows met **1994-01-01 through 2014-12-31** (13,383 `nest`, 37,779 `capt/obs`). **1,070** pre-1994 rows and **21,361** post-2014 rows were suppressed before consulting their ID, site code or stage.
- **17,857** distinct ring IDs occurred in the eligible pre-2015 observations.
- **10,742** IDs had a physical pre-2015 nest record. **5** were inconsistent across multiple nest-island codes; **10,737** had one recorded nest code.
- Within those **10,737** potential source IDs, **4,164** had a first **strictly later** direct `capt/obs` encounter within the same historical window. **6,573** had no such later detected encounter.
- At that *first later encounter date*, **3,941** matched the nest `Island` code, **223** differed, and **0** were simultaneous first-date multi-code ambiguities.

The **223 / 4,164 = 5.4%** is a *selected observed first-followup code-change fraction*, **not** a natal dispersal or successful-recruitment probability. Detection strongly conditions the denominator, and early same-code resighting can occur long before a later genuine dispersal. A synthetic counterexample in the unit tests proves the key logical difference: a nest on A, early recapture on A, then later sighting on B yields **first-followup code changed = false** even though a later island-code switch was observed. Thus directly comparing this fraction with Ranke et al. 2021's existing natal-recruit dispersal proportion **376/2,192** would be misleading because both event and denominator definitions differ.

The independently inspected observed counts are frozen in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_first_direct_site_code_frozen_v1.json`. A fresh dedicated workflow must match these counts exactly before merge.

**Important**: This artifact already exposes *pre-2015* site-code-switch counts and is not a previously untouched ecological outcome; it retains the 2015–2022 individual destination fields uninspected. The full source archive itself was only publicly released much later, so this is **not** a publicly reproducible genuine 2014-issued prediction even with the date firewall.

## Interpretation limits

A recorded `Island` code difference is an **observed site-code change**, *not automatically* natal dispersal (an individual may move temporarily, and `Lurøy-Onøy` grouping/numeric site identity needs independent study-specific confirmation), recruitment, permanent settlement, local recolonization, fitness or an EOG win. The 2021 Ranke paper already observed interisland natal dispersal in 1993–2014; simply finding movements would not be novel.

Because detection is imperfect, counts of those observed again are a **selected detected subset**. They are **not** total nestling-to-adult dispersal rates without effort and detection adjustment. Neither absence from records nor source-year `N_obs/N_corr` can certify zero occupancy. This is a **reproducibility/identifiability** feasibility diagnostic before designing any ecological forecast, not a fitted model.

## Execution

Dedicated GitHub Actions performs pinned public source checkout and independent SHA256/first-header checks first, then analyzes only pre-2015 eligible rows. Synthetic tests verify future 2015+ observation records cannot affect the pre-2015 site-code results even if they contain malicious or retrospectively inferred ID/island values, and ambiguous source/first-destination codes remain unassigned.

Result artifact exports aggregate counts and scientific HOLD flags only. If any source SHA, recorded row count or event-definition reconciliation differs, the job must fail closed.

**Frozen first-phase conclusion:** observation/survey effort, historical source availability, permanent dispersal and independent 2015–2022 held-out forecast remain unqualified. Do not promote them based on these counts. Track in [Issue #626](https://github.com/zuizui0223/eog/issues/626).
