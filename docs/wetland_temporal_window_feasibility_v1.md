# Native wetland amphibian survey windows: temporal proximity versus preserved positive evidence

## Completed result and scientific meaning

**Post-exposure original-source observation-window sensitivity; not an occupancy or closure study.** The 2024 Hungary wetland amphibian CSV has genuine, date-distinct observations, but its same-site sampling periods can span 91 days. We therefore predeclared **7, 14, 21, 30, 45, 60 and 91 calendar days** as observation-window horizons, anchored either at each site's **first** or **last** recorded date. A site is *window-repeated* when at least two different source-recorded calendar dates fall in the window. This is a **descriptive eligibility definition only**, not a certificate of independent field replicates or closed occupancy.

Original source: Mizsei & Wenner (2025), archived survey/site data and author R at [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0; source-pinned `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, original survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`. Q1 follows the author-defined 27-site cohort, 351 native rows, 144 source-positive site×species; Q2 follows the 13 intervention sites, 188 native rows, 77 positives. The *original full-period positivity* is kept in a separate source-positive registry. No seed-dependent 20-row sampling or source-row deletion is used.

Protocol `validation/wetland_temporal_window_feasibility_v1/protocol.json` was committed before this extension was computed. These are nevertheless **post-exposure descriptive tests** of a previously studied public source, not prospectively heldout biological validation.

## Fixed first-anchored windows

Each site contributes exactly those genuine recorded dates within the specified number of days (inclusive) after its **first** recorded survey date.

| Window length | Q1 sites with ≥2 recorded dates (of 27) | Q1 source-positive site×species seen (of 144) | Q2 sites with ≥2 dates (of 13) | Q2 source-positive pairs seen (of 77) |
| --- | ---: | ---: | ---: | ---: |
| 7 days | 17 | 84 (58.3%) | 8 | 38 (49.4%) |
| **14 days** | **20** | **96 (66.7%)** | **10** | **41 (53.2%)** |
| 21 days | 21 | 101 (70.1%) | 10 | 42 (54.5%) |
| **30 days** | **24** | **115 (79.9%)** | **12** | **54 (70.1%)** |
| 45 days | 26 | 138 (95.8%) | 13 | 74 (96.1%) |
| 60 days | 26 | 140 (97.2%) | 13 | 76 (98.7%) |
| 91 days | 27 | 144 (100%) | 13 | 77 (100%) |

**Denominator clarification:** Each positive fraction above uses *all full-period source-positive site×species pairs*, even at sites with fewer than two dates within the window. For **eligible** sites only, the 14-day initial window captures Q1 **83/104** and Q2 **38/54** original positive pairs at eligible sites; the 30-day initial window captures Q1 **111/127** and Q2 **54/68**. Do not treat the fraction in the full-cohort column as a rate over repeated-only sites.

**Trade-off:** A two-week window reduces temporal separation but misses **48/144 Q1** and **36/77 Q2** recorded site×species positive witnesses. Extending to 30 days still misses **29/144 Q1** and **23/77 Q2**. A 45-day first-anchored window recovers ~96% of original positives, but that does **not** show 45-day ecological closure.

## Anchoring on the last survey date is not equivalent

For each site, the same windows are instead anchored backwards from its **last** source-recorded survey date.

| Window | Q1 sites with ≥2 dates | Q1 positive pairs seen | Q2 sites with ≥2 dates | Q2 positive pairs seen |
| --- | ---: | ---: | ---: | ---: |
| 7 days | 4/27 | 92/144 | **0/13** | 44/77 |
| **14 days** | **6/27** | **94/144** | **0/13** | **44/77** |
| 21 days | 17/27 | 118/144 | 7/13 | 57/77 |
| **30 days** | **22/27** | **127/144** | **10/13** | **62/77** |
| 45 days | 25/27 | 136/144 | 12/13 | 69/77 |
| 60 days | 26/27 | 143/144 | 13/13 | 76/77 |
| 91 days | 27/27 | 144/144 | 13/13 | 77/77 |

The asymmetry is important: **none of the Q2 intervention sites has two distinct recorded dates in the final 14-day window**. The 44/77 source-positive pairs seen there come from one last recorded date at each site, not repeated evidence eligible for a conventional repeated-observation analysis.

Under the 30-day windows, Q1 early versus late anchors disagree about **42 source-positive site×species records** (15 seen only in the initial window; 27 only in the terminal window). Q2 disagrees about **34** (13 initial-only, 21 terminal-only). Native-source records did not change; these are *different actual visit subsets*, not ecological extinction/colonization estimates. The two 91-day anchored windows recover every original source-positive record.

## Distinct methods and effort constraints

Method coverage varies by date. We also tested a **strict descriptive** condition: among sites with ≥2 recorded dates in a window, is the **set of method names recorded** exactly identical at each selected date?

| First-anchored repeated sites | Q1 | Q2 |
| --- | ---: | ---: |
| 14 days: same method set every selected date | **2/20** | **2/10** |
| 30 days: same method set every selected date | **1/24** | **1/12** |
| 45 days: same method set every selected date | 0/26 | 0/13 |

These proportions reflect the **recorded method list**, not actual field method deployment, comparable equipment, trap exposure or equal observation effort. An unrecorded method remains **unknown**, not a sampled zero. Nor does an unchanged list establish identical effort.

## What this resolves — and does not

**Resolved at the source/observation layer:** Temporal subset rules can be completely reproduced; the source-positive records outside each window remain available and are never reclassified as biological absences. The count of eligible date-repeated sites, retained native positives, first/last-window sensitivity and recorded method composition is explicit for all 7 predeclared time windows.

**Not resolved scientifically:** Within-season closure, independence of dates, detection process, time-varying breeding phenology, actual trap effort, joint method dependence and physical trap IDs. A shorter interval alone does not prove these assumptions. In particular, the archived record is not a sufficient independent measurement of biotic **B** or movement **M** for an empirical EOG×BAM field test. No `unmarked` likelihood was fit, no restoration treatment effect inferred, and no fourth EOG-WF fresh scored endpoint added.

The appropriate next biological step requires field-method logs, real effort/time exposure, and a defensible organism-level occupancy estimand (e.g., which breeding-state window should be closed). A conditional method-aware occurrence model could then be specified without claiming pseudo-row independence. Until then the observed source-grain and window sensitivity are an inspectable empirical data-method result, not causal inference.

## Code, files and verification

- Protocol: `validation/wetland_temporal_window_feasibility_v1/protocol.json`
- Executable: `benchmarks/wetland_temporal_window_feasibility_v1.py`
- Negative-control tests: `tests/test_wetland_temporal_window_feasibility_v1.py`
- Machine receipt: `validation/wetland_temporal_window_feasibility_v1/result_receipt.json`
- Detail outputs: `published_q1_window_source_positive_detail.csv` and `published_q2_window_source_positive_detail.csv`, one row for each declared horizon×source-positive site×species, retaining first- and last-window capture and two-date eligibility separately.

[Original-source CI run #43694255070](https://github.com/zuizui0223/eog/actions/runs/43694255070) **SUCCESS**; result fingerprint `c53506d95ade7922f81db1aa17387cdbd317257e518392fa037d91676d6aa72e`; artifact **14153786370** ZIP SHA256 `7ebb276b91e2be76f1e315e00c42a152affe445ff5182e7f36502fa36dd99503`. The complete previously verified native site×date/method ledger remains the immutable analysis input representation.
