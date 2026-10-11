# Helgeland: how first observed recapture misses later site-code changes

**Current stage: exploratory post-exposure diagnostic, not EOG predictive performance.** Previous real-data PR #642 (merged as `ab959f6786eb732a40fa338a716c8ed9f311885e`) verified that **4,164** uniquely nest-coded IDs had a first later direct `capt/obs` record before the end of 2014: **3,941** first observed on the nest `Island` code and **223** on a different code. This selected detected-record denominator is **not** natal dispersal (Ranke et al. 2021's already published 376/2192 natal recruit estimand differs in numerator and denominator).

## Nontrivial, answerable ecological observation-process question

**How much observed later code change is missed by looking at only the first subsequent physical encounter?** A nest on code A, first recapture A, then a later sighting B will be counted as *same* by the 223/4164 proxy, even though a later B encounter is directly recorded. A second process question is whether first-different observations are subsequently reobserved back on nest code; such a later return would undermine a simplistic first-encounter-as-permanent-settlement reading.

These questions can be evaluated **within the already exposed 1994–2014 positive encounter series only**, using source-authenticated original `date`, `ID`, `Island`, `Location`, and literal `stage=nest/capt/obs`. Derived `Year`, age, `scriptsex`, genetics, full-series fitted island, abundance, and **all 2015–2022 site/ID/stage values** remain out of the analysis.

## Protocol fixed before evaluating the later records

`validation/eog_virtual_world_ecology_synthesis_v1/helgeland_pre2015_later_site_switch_protocol_v1.json` was committed before this follow-up outcome check. The code first revalidates **both original upstream file-byte SHA-256 and physical first header**, reruns PR #642 and requires the exact previously exposed source counts, then scans the same file again with the **date mask preceding reading individual/site/stage fields**. It never writes individual trajectories or named island/code output.

Among IDs with first followup on the nest code (3,941), classify: at least one **strictly later calendar date** with a *single different Island code*, only ambiguous multi-code later dates (without a definitive switch), or no later different code. Track how many had another distinct direct observation date at all, so the hidden-switch result is not mistaken for a population-wide dispersal rate. For the 223 first-different IDs, similarly classify later directly observed returns to the nest code or unresolved date-code conflicts. For first-same-to-later-different records, report broad lag bins (1–30, 31–365, over 365 days) between **recorded encounter dates** only, explicitly not the actual movement date.

The categories must partition the frozen 3,941 / 223 records exactly. Any different original row count, source hash, header or first-stage count is a fatal STOP. Mock negative controls show that a first same-site encounter can hide later different-site observation, contradictory later same-date island codes remain ambiguous, and poisoned 2015+ rows cannot influence history.

## Critical scientific limitations

These are **conditional positive re-detection counts**, not independent observations of whether animals were absent from other sites or what dates dispersal occurred. Detection effort, individual survival, breeding status, capture probability and uneven observation length bias every count. A later different-code sighting might reflect temporary visitation, genuine dispersal, recording or numeric-code semantics (the latter still need crosswalk). A later return to nest code does not prove a successful return migration. No suitable 2020 source-input model, true surveyed-zero denominator, EOG forecasting discrimination, colonization, founding or fitness effect is established.

**If a result is significant for study design**, it will be that first-followup proxies are demonstrably temporally incomplete, not that EOG predicts island colonization. Source, frozen counts and all HOLDs tracked at [Issue #626](https://github.com/zuizui0223/eog/issues/626).
