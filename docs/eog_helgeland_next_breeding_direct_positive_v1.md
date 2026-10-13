# Helgeland: first direct detection versus next-calendar-year breeding-season detection

**Analysis status:** exploratory post-exposure, positive encounter codes only. The earlier 223 first-different / 451 any-different / 228 first-same-then-later-different ID counts have already been exposed in merged PRs #642–#644. The present design was frozen separately, in commit `4a137bd7be47ef41ca14d73613d4a233c10c78fb`, **before** examining the new next-calendar-year May–August classification.

## One biological observation problem

The first direct `capt/obs` event after a `nest` event may happen in the birth year. It does not establish where a marked bird was during the following breeding season. Ranke et al. (2021, DOI 10.1111/1365-2656.13580) considered birds recorded as recruits in their **second calendar year** and describes the study's breeding-season fieldwork mainly from early May to mid-August, with additional autumn capture. Its original recruit denominator (376 dispersers among 2,192 recruits) is not the same as EOG's direct-positive denominator.

The pinned 2026 source script classifies `lifestage=recruit` using processed `Least_age==1`; the physical `stage` records in the raw direct observation file are `nest/capt/obs`. We deliberately **do not import `Least_age` or the original `Year`** because neither its retrospective derivation nor availability by forecast cutoff has been certified. The published 2026 source is not historical predictor data for 2014.

## Frozen, paired observational estimand

A cohort comprises ring IDs with exactly one raw `nest` **Island CODE** throughout pre-2015 directly recorded history. Its origin is the unique code and its birth reference the earliest physically dated `nest`. To avoid right-censoring the next-year seasonal observation window, exclude earliest-nest years 2014 and later. Exclude earliest-nest months outside May–August, and report those exclusions. The inclusive May–August range is a **broad, explicit calendar convention**, not a claim that all island-years were equally visited through 31 August.

For each eligible ID, search only direct `capt/obs` events strictly later than its earliest nest, with physical date no later than **2014-12-31**. The paired comparison is:

- **First raw positive:** island code(s) on the first directly observed post-nest `capt/obs` date, irrespective of calendar season.
- **Next breeding-season positive:** island code(s) on the earliest directly observed `capt/obs` date in **May–August of calendar year birth+1**.
- **Same/different/ambiguous:** same or different from unique nest code only if that first date contains a single code; conflicting same-day codes are unassigned/ambiguous.
- **No next-year positive:** record as undetected under this window, *never* as field-surveyed zero or biological absence.

The analysis outputs a three-by-three first-raw / next-breeding positive cross-tab **on the same directly reobserved individuals**, plus birth cohort exclusions, qualified observed count and number whose raw first event preceded their next-breeding event. It does **not** compare denominators from unlike observation cohorts or estimate survival-adjusted movement.

## Source safety and reproducibility

Input: independently Dryad-v6 SHA-256-attested source `Data/presence_data_1994_2022.txt` from author commit `a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5`, physical header reverified in #628–#629. The CLI first reruns the original #642 first-source QC and matches its exact frozen aggregate counts, plus #643's 223/451/228, before any new seasonal aggregation.

Inside the new row reader, `date` is inspected **before ID/Island/stage**, and every record before 1994 or after 2014 is suppressed without touching its identity or site. It reads no `Location`, `Year`, `Least_age`, inferred `lifestage`, sex, genotypes, `filled`, `N_corr` or 2015–2022 destination. Only aggregate counts and false scientific-claim flags may be exported. Raw bird IDs, island codes and individual observation dates are not emitted.

The dedicated workflow tests fabricated first-same→next-different, first-different→next-same, same-day ambiguity, autumn-only re-detection, 2014 temporal censoring, winter nest exclusion, future-field poisons and retrospective-column irrelevance. It runs the pinned original source check, generates a one-shot aggregate artifact, and fails if its partition or safety gates are violated. An independently inspected empirical receipt must be frozen before merge.

## Independently inspected original-source result (2026-10-14)

The first successful pinned-source [CI run 38421455942](https://github.com/zuizui0223/eog/actions/runs/38421455942), artifact `11825833740` (ZIP SHA-256 `95b64aa88cac16685f441083e73fde59e71aed7090c328afec4a7d1f6578dd55`), was independently downloaded and its complete aggregate-only receipt examined. The fully exact [frozen JSON](../validation/eog_virtual_world_ecology_synthesis_v1/helgeland_next_breeding_direct_positive_observed_frozen_v1.json) is now compared **field-for-field** against each real-source CI rerun.

- 10,737 original uniquely nest-code-anchored IDs, 5 ambiguous nest-code IDs.
- 664 earliest nests from 2014 were excluded due to the 2015 observation cutoff. **Zero** earliest nests were outside May–August among the remaining source IDs.
- **10,073** eligible earliest-nest IDs have a full next-calendar-year May–August window under this explicit calendar rule. Of these, **1,313** were directly reobserved in the target season and **8,760 had no qualifying positive record** (not verified surveyed absence).
- Among 1,313 directly reobserved, first qualifying target-season code was **same** in **1,075**, **different** in **238**, **ambiguous** in **0**.
- 987 of the 1,313 had a still earlier post-nest physical `capt/obs` event before their qualifying next-season record.

### Same-ID cross-tabulation

| First post-nest direct code (any calendar) | Next-year breeding season: same | Next-year breeding season: different |
| --- | ---: | ---: |
| Same as unique nest code | 1,074 | **124** |
| Different from unique nest code | **1** | 114 |

There are **125/1,313 (9.52%) discordant classifications**. The main direction of discordance is **124 first-same → next-year-different** versus **1 first-different → next-year-same**. This is direct evidence that the observed site-code classification depends materially on **when** a positive encounter is selected, even within the same detected ID cohort.

Neither the **238/1,313** code difference nor the 125/1,313 discordance is an unbiased natal dispersal, breeding recruitment or migration rate. The 1,313 denominator selects individuals reobserved in the specified window; missing observations are not proven zeros, while the study's independent recruit and CMR/detection filters have not been recreated. The apparent numerical closeness to Ranke et al. 2021's published 376/2,192 recruit dispersers is **not an independent replication**, because dates, eligible IDs, observation processes, study periods and recruitment definitions differ.

## Strict interpretation boundary

A **next-calendar-year breeding-season re-detection is not a verified breeding event or recruitment**. Ranke et al. applied a separate recruit definition; raw detection stage is not that variable. Nor does an apparent code difference establish permanent dispersal, source-sink founding, true geographic crosswalk, equal surveillance effort or out-of-time EOG prediction. Even a large paired discrepancy would demonstrate sensitivity to the chosen *observational time window* and motivate access to an independent actual recruitment/survey-effort register, not prove a new ecological dispersal mechanism.

**Original-model code-universe caution:** The pinned author's `R scripts/Main model of metapopulation dynamics.R` filters out literal `Island` codes `33` and `0` before its demographic model, whereas this frozen observation-process diagnostic preserves the previously defined unfiltered raw-code cohort for exact comparability with #642–#644. We have **not** yet quantified how many of these IDs encounter those codes or whether excluding them changes the paired matrix. No interpretation as a mapped route among the eleven named study islands is authorized until an independently validated code dictionary and a separate, explicitly post-exposure sensitivity are available.

Keep Issue #626's HOLDs and the original EOG-WF 3 favorable/favorable/adverse endpoint decisions unchanged.

### Inspectable commands

```bash
python -m pytest -q tests/test_helgeland_next_breeding_direct_positive_v1.py
python scripts/audit_helgeland_next_breeding_direct_positive_v1.py \
  --upstream-checkout upstream_public \
  --output build/helgeland-next-breeding-direct-positive-v1.json
```

Output is refused if a path already exists. The script does not fetch from the internet on its own.
