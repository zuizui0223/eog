# Hungarian wetland amphibians: native dated survey groups without 20-row normalization

## Outcome and claim status

**Completed post-exposure original-source observation-grain audit.** The source contains materially useful **recorded site×calendar-date visit groups** that can be represented without resampling 20 pseudo-occasions per site. This is a source-backed *candidate repeated-detection history*, **not a fitted single-season occupancy model or verification of visit independence/closure**.

Original source: Mizsei & Wenner (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0; archived native CSVs pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc` with survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd` and site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`. The original author code has 27 Q1 sites after excluding `kis-banyato` and `vadasz-turjan`, and 13 intervention Q2 sites; both source cohorts are preserved.

## Three distinct source grains

**Native source row:** a CSV record with date, method and nine species counts; not a documented independent physical trap/visit. The original `surv` string is exactly `site:method:doy` for all 381 archived rows. Its two double-row bottletrap groups are kept, not "deduplicated".

**Site×calendar date:** grouping of all source rows sharing a site/date. Every distinct recorded date is kept once, and an observed positive at **any recorded method** on that date gives a positive for that site's date×species. This Boolean OR preserves the complete native positive site×species evidence exactly. A date with only recorded non-detections remains a **recorded non-detection**, not ecological absence.

**Site×date×method:** one of four recorded method families (`acoustic`, `visual`, `dipnet`, `bottletrap`). Each method/date/species is recorded as `RECORDED_POSITIVE` (source-positive), `RECORDED_NONDETECTION` (method source rows exist but no recorded positives), or `METHOD_NOT_RECORDED` (there is **no source row for that method**; missing, **not zero**). Same-key bottletrap rows contribute to the recorded-positive OR but their counts are **not summed** across unidentified physical traps.

## Actual original-CSV source structure

| Metric | Full archive | Original Q1 | Original Q2 |
| --- | ---: | ---: | ---: |
| Sites | 29 | **27** | **13** |
| Original CSV rows | 381 | **351** | **188** |
| Recorded distinct site×date groups | **129** | **117** | **64** |
| Recorded distinct site×date×method groups | 379 | 349 | 186 |
| Recorded positive site×species pairs | 153 | **144** | **77** |
| Positive site×date×species groups | 365 | 346 | 207 |
| Distinct dates within each site | 2–7 | **2–7** | **3–7** |
| Within-site first-to-last survey-day span | 2–91 days | **2–91 days** | **21–91 days** |
| Median within-site span | 34 days | **34 days** | **37 days** |
| Sites with first-to-last dates ≥30 days apart | 15/29 | **14/27** | **10/13** |
| Source-positive site×species detected on only one recorded date | 64/153 | **59/144** | **25/77** |
| Source-positive site×species detected by only one method family | 64/153 | **57/144** | **22/77** |

Source observation dates range from **2024-03-24 to 2024-06-28** (across the archive and Q1/Q2). A date group may include 2, 3 or 4 recorded methods, in different combinations. For Q1, **24** date groups have 2 methods, **71** have 3 and **22** have 4; Q2: **14**, **42**, and **8**, respectively. The source does **not** supply constant method effort across all dates.

### Missing method data are not negative observations

The machine-readable method status ledger includes every site×recorded-date×4 declared methods×9 species cell, with missing statuses explicitly distinguished.

| Status counts | Q1 | Q2 |
| --- | ---: | ---: |
| `RECORDED_POSITIVE` | 493 | 301 |
| `RECORDED_NONDETECTION` | 2,648 | 1,373 |
| `METHOD_NOT_RECORDED` | **1,071** | **630** |
| Total method-status cells | 4,212 | 2,304 |

The source-only declaration `METHOD_NOT_RECORDED` means a method lacks a native CSV entry on that date, **not proof that it was not deployed**, and it must not be silently recoded to `RECORDED_NONDETECTION`.

### 7-column dated-visit history with genuine missing values

For downstream method development, we additionally construct an *ordinal within-site* date-index history with the **maximum actual recorded visit count = 7**, padding only sites with fewer real dates using NA (blank CSV detection cells). The ordinal index **does not align absolute calendar dates across sites** and is not a verified independent occupancy replicate.

| History cells: sites×7 visit ordinals×9 species | Q1 | Q2 |
| --- | ---: | ---: |
| Total | **1,701** | **819** |
| Cells attached to actual recorded dates | 1,053 | 576 |
| No recorded visit: **NA**, not zero | **648** | **243** |
| Native source-positive site×species lost | **0** | **0** |

Compare this with the previous original 20-occasion R reprocessing: Q1 `351 → 540` selected pseudo rows but only 287 distinct native rows; Q2 `188 → 260` and 153 distinct native rows. Source-positive site×species lost in the original seed=123 replay were 3 and 6, respectively, and mean 256-seed losses were 9.96 and 4.92. The new dated-visit ledger does not perform such source-row selection, so its observed-positive evidence is preserved by construction.

## Scientific implications and STOP conditions

The dataset supplies authentic dates, repeated recorded site visits, multiple detection methods and basic weather fields. It provides a basis for building a **method-aware repeated-observation model** provided the field sampling assumptions can be independently established.

However, repeated recorded calendar dates do **not** automatically imply independent or identically distributed sampling occasions. Notably, many sites span **30–91 days**, potentially substantial amphibian breeding-phenology and local seasonal changes. Whether the biological state is closed across this interval is not validated. Each observed method-date record is also an aggregation with unknown physical trap effort for some methods; the two duplicate composite bottletrap keys remain unresolved as physical trap units.

**Supported:** exact original survey/visit group counts, method/date recorded evidence and missingness, source-positive site×species reconstruction, and explicit full information retention without stochastic pseudo-row selection.

**Not established:** physical trap IDs, independent effective effort, detection probabilities, season closure, occupancy coefficients, restoration-treatment effects, historical dispersal, independently observed A/B/M or a fourth EOG-WF empirical prediction endpoint. The former source-key `BLOCKED_CONFLICTING_SURVEY_IDENTIFIERS` gate remains specifically a stop on a *rowwise likelihood falsely assuming a unique physical survey ID*, not a conclusion of native data corruption. Aggregating Boolean *positive evidence* does not settle count likelihoods or effect estimation.

## Reproducibility and data lineage

- Post-exposure frozen contract: `validation/wetland_native_visit_ledger_v1/protocol.json`
- Source-verified deterministic reconstruction: `benchmarks/wetland_native_visit_ledger_v1.py`
- Synthetic negative-control tests: `tests/test_wetland_native_visit_ledger_v1.py`
- Canonical machine result/sha-index: `validation/wetland_native_visit_ledger_v1/result_receipt.json`
- Source files are retrieved by the PR's original wetland identity workflow and verified by exact SHA256 before use.
- Output CSV tables: `published_q1_daily_detected.csv`, `published_q1_method_status.csv`, `published_q1_padded_history.csv`, and corresponding Q2/full-archive files. These are archived in the GitHub Actions artifact; they are not mutable copies of the original author data.

[Completed source-authenticated CI run #43682196252](https://github.com/zuizui0223/eog/actions/runs/43682196252), **SUCCESS**. Result fingerprint `4c487bb1b00579cbff22be30ae056615708abb275f82eb5091f5df61c4c1b533`; artifact ID **14148716904**, ZIP SHA256 `0dc459e32d8b6773844567cd095029d4e5b0485153f5f002febaac8747a9a404`. Artifact includes full native source-method, date-detection and 7-column NA-padded visit status CSVs.

**Next inferential decision:** Check visit effort and species activity-period closure against the actual published field protocol and, where necessary, author/field logs. A source-faithful detection/occupancy likelihood can only be defined after deciding if visits are genuine repeated occasions, whether dependence between methods/traps is handled, and which season or dynamic population state the estimand concerns. No occupancy fit has been executed here.
