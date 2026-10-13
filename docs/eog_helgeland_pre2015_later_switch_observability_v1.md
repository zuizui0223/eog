# Helgeland: how first observed recapture misses later site-code changes

**Current stage: exploratory post-exposure diagnostic, not EOG predictive performance.** Previous real-data PR #642 (merged as `ab959f6786eb732a40fa338a716c8ed9f311885e`) verified that **4,164** uniquely nest-coded IDs had a first later direct `capt/obs` record before the end of 2014: **3,941** first observed on the nest `Island` code and **223** on a different code. This selected detected-record denominator is **not** natal dispersal (Ranke et al. 2021's already published 376/2192 natal recruit estimand differs in numerator and denominator).

## Nontrivial, answerable ecological observation-process question

**How much observed later code change is missed by looking at only the first subsequent physical encounter?** A nest on code A, first recapture A, then a later sighting B will be counted as *same* by the 223/4164 proxy, even though a later B encounter is directly recorded. A second process question is whether first-different observations are subsequently reobserved back on nest code; such a later return would undermine a simplistic first-encounter-as-permanent-settlement reading.

These questions can be evaluated **within the already exposed 1994–2014 positive encounter series only**, using source-authenticated original `date`, `ID`, `Island`, `Location`, and literal `stage=nest/capt/obs`. Derived `Year`, age, `scriptsex`, genetics, full-series fitted island, abundance, and **all 2015–2022 site/ID/stage values** remain out of the analysis.

## Protocol fixed before evaluating the later records

`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_later_site_switch_protocol_v1.json` was committed before this follow-up outcome check. The code first revalidates **both original upstream file-byte SHA-256 and physical first header**, reruns PR #642 and requires the exact previously exposed source counts, then scans the same file again with the **date mask preceding reading individual/site/stage fields**. It never writes individual trajectories or named island/code output.

Among IDs with first followup on the nest code (3,941), classify: at least one **strictly later calendar date** with a *single different Island code*, only ambiguous multi-code later dates (without a definitive switch), or no later different code. Track how many had another distinct direct observation date at all, so the hidden-switch result is not mistaken for a population-wide dispersal rate. For the 223 first-different IDs, similarly classify later directly observed returns to the nest code or unresolved date-code conflicts. For first-same-to-later-different records, report broad lag bins (1–30, 31–365, over 365 days) between **recorded encounter dates** only, explicitly not the actual movement date.

The categories must partition the frozen 3,941 / 223 records exactly. Any different original row count, source hash, header or first-stage count is a fatal STOP. Mock negative controls show that a first same-site encounter can hide later different-site observation, contradictory later same-date island codes remain ambiguous, and poisoned 2015+ rows cannot influence history.

## Cross-check against the already exposed PR #643 outcome

This PR is **not blind to all later site-code changes**: PR #643 already exposed **228** first-same-then-later-different records and **2** first-different-then-source-code return records. The genuinely new audit is limited to the single-code calendar-day classifications, re-observation opportunities, and encounter-date lag bins. This is a post-exposure refinement, not independent replication or prospective testing.

Importantly, #643 counted `any` different-code positive encounter row, including potentially conflicting distinct site codes on the same date. The present stricter classification treats such later dates as **ambiguous** unless an unambiguous change appears on another date. Therefore, the valid exact reconciliation is:

- `unambiguous first-same later different + ambiguous-only first-same later = 228`;
- `first-same later no different = 3,713`;
- `unambiguous first-different later origin return <= 2`.

The last bound is an inequality because a same-day multi-code conflict need not include the origin code. For the return classification, only contradictory dates containing the original nest code count as ambiguous possible returns; B/C records cannot indicate return to nest code A. These are identity and definition checks, **not new ecological findings**. The source-audit runner now fails closed if the previously frozen, independently verified PR #643 aggregate contradicts the stricter output.

## Critical scientific limitations

These are **conditional positive re-detection counts**, not independent observations of whether animals were absent from other sites or what dates dispersal occurred. Detection effort, individual survival, breeding status, capture probability and uneven observation length bias every count. A later different-code sighting might reflect temporary visitation, genuine dispersal, recording or numeric-code semantics (the latter still need crosswalk). A later return to nest code does not prove a successful return migration. No suitable 2020 source-input model, true surveyed-zero denominator, EOG forecasting discrimination, colonization, founding or fitness effect is established.

**If a result is significant for study design**, it will be that first-followup proxies are demonstrably temporally incomplete, not that EOG predicts island colonization. Source, frozen counts and all HOLDs tracked at [Issue #626](https://github.com/zuizui0223/eog/issues/626).

## Independently inspected original-source receipt (2026-10-13)

The source-authenticated actual-data artifact in [GitHub Actions run 38108969284](https://github.com/zuizui0223/eog/actions/runs/38108969284) (artifact ID `11691227493`) was downloaded and its complete aggregate-only JSON inspected independently. The exact JSON has been frozen in `validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_later_site_switch_observed_frozen_v1.json`; the dedicated CI now fails if an authenticated rerun differs at **any** receipt field.

| Directly observed, 1994–2014 | ID count |
| --- | ---: |
| First followup on nest code | 3,941 |
| Of the above, with any additional observation date | 2,356 |
| Of the above, with no additional observation date | 1,585 |
| First same, then unambiguous different-code observation | **228** |
| First same, later ambiguous-only different-code observation | **0** |
| First same, no observed later different code | 3,713 |
| First followup on different code | 223 |
| Of the above, later unambiguous observation on nest code | **2** |
| Of the above, no observed unambiguous return | 221 |

Observed lag from first same-code followup to first unambiguous different-code observation: **3** at 1–30 days, **178** at 31–365 days, **47** beyond 365 days (sum 228). This is detection lag, **not** biological movement time.

The original first-vs-ever positive-record count reconciles exactly: `223 + 228 = 451` ever directly detected on a different code among the 4,164 linkable IDs. Thus initial-followup-only tabulation captures 223/451 ≈ 49.4% of ever-observed changed-code IDs; the other 228/451 ≈ 50.6% are observed only after the first. These are **selected detectable site-code events**, not unbiased dispersal events or a 50.6% dispersal-rate error. The absence of ambiguous-only records in this source does not establish that multi-code same-day ambiguity is impossible elsewhere.

**Inference remains HOLD:** same source individuals and post-exposure exploratory definitions, no independent temporal test, source-site crosswalk or verified surveyed-negative register, no detection-effort correction, and no EOG forecasting validation. The source is published in 2026 and cannot be treated as a historically available predictor in 2014.
