# Wetland observation gates are jointly restrictive: source positives split across method and calendar date

## Completed original-source result

**A new source-verified, post-exposure observation-grain analysis:** We crossed the original recording method panel (**all four original method families** versus **acoustic+visual**) with **actual within-site calendar-day windows** (first-anchored or last-anchored, inclusive 7/14/21/30/45/60/91 days). The unit of evidence is **at least one positive original recorded row for one site×species**, never an inference of biological absence, detection independence or population change.

The key new result is a **split-method/time source witness**: at some site×species, the species has a positive **acoustic/visual record somewhere in the original source** and a positive **additional-method record inside a particular calendar window**, but **no acoustic/visual positive within that same window**. Both marginal source-positive indicators are true, yet their jointly filtered indicator is false. This happens for **16/144 original Q1 source-positive site×species pairs in the last-14-day window** and for **9/77** Q2 intervention site×species pairs. First-14-day windows have just **1** such pair in each cohort.

Original data: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837 ([DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837)), original data/code at [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. Fixed source mirror `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`; survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

The Q1 cohort is the exact original **27 sites**, 351 native rows, 117 distinct site×calendar dates, nine species and **144** full-four-method source-positive site×species pairs; AV across all dates has **104**. The Q2 intervention-only subset has 13 sites, 188 rows, 64 site×dates, **77** full source-positive pairs and **61** full-period AV-positive pairs. Q2 site×species records were checked against the exact matching Q1 source witness histories.

## One source positive, five disjoint outcomes

For any original full source-positive site×species pair, define:

- `F_all`: source-positive in **any** original method over **all** archived dates;
- `M_all`: source-positive via original **acoustic or visual** method on **any** archived date;
- `F_window`: source-positive in **any** method inside the chosen real calendar window;
- `M_window`: source-positive via **acoustic or visual inside the same window**.

All use original `count>0` and the **same site/taxon**. Original method-row and physical-trap identities are not invented. We require `M_window ⊆ M_all ∩ F_window ⊆ F_all`, but `M_window` can be smaller than `M_all ∩ F_window` because the two marginal positive witnesses occur on different rows.

| Mutually exclusive original source-positive class | Source-based rule | Q1 first 14d | Q1 last 14d | Q2 last 14d |
| --- | --- | ---: | ---: | ---: |
| Joint positive survives both restrictions | `M_window` | **73** | **48** | **25** |
| Positive inside window, only by additional methods throughout source | `F_window \ M_all` | 22 | 30 | 10 |
| Acoustic/visual positive only outside window; nothing positive inside | `M_all \ F_window` | 30 | 40 | 27 |
| **Split witness:** additional method positive inside, AV positive outside, but no AV positive inside | `(F_window ∩ M_all) \ M_window` | **1** | **16** | **9** |
| Excluded by either marginal gate already | `F_all \ (F_window ∪ M_all)` | 18 | 10 | 6 |
| **Total all-original positive site×species** | Exactly partitioned | **144** | **144** | **77** |

These five categories describe source-positive *observation records*, not natural biological states. In the last 14-day Q1 source, the 16 split witnesses belong to **9 intervention, 6 artificial and 1 control** source-positive site×taxon pairs.

### Exact additional loss beyond marginal support-set intersection

At Q1 **last 14 days**, the full source has 144 positives. Dropping dates outside that window leaves **94** positives (loss **50**). Keeping acoustic+visual across all dates leaves **104** positives (loss **40**). The two *marginal loss sets* overlap on **10** original positive pairs. If the joint positive mask were simply the intersection of the two separately aggregated masks, one would predict:

`144 - (50 + 40 - 10) = 64` retained pairs.

But the **real row-level joint filter** retains just **48**. The **16 additional missing** source-positive pairs are the split-method/time witnesses. This is a direct and exact example of source record aggregation being insufficient for evaluating two observation gates independently.

At **first 14 days**, the comparable count is **73 actual AV-positive pairs** versus **74** in the intersection of the two marginal positive sets (one split witness). For Q2 at **last 14 days**, there are **25** actual joint positives versus **34** marginal-intersection positives (nine split witnesses).

**The row filters themselves commute.** The nonseparability arises because the Boolean `any-positive` site×species **aggregation was applied before** intersecting two marginal positive support sets, forgetting the original method/date co-occurrence. Do not call this a physical noncommutativity of the date or method operations.

### Concrete authentic row witnesses

Two examples from the source's original CSV line numbers, not simulated data:

- `orditoi-zsilip`, *Hyla arborea*, original artificial wetland: **visual positive 2024-03-24** (original CSV line 6), outside that site's last-14-day window; **dipnet positive 2024-05-30** (line 368), inside its final window. An acoustic/visual positive exists in the full history and a full-method positive exists in the final window, but no AV-positive row exists in the final window.
- `szena-dulo`, *Lissotriton vulgaris*, original control wetland: **visual positive 2024-03-24** (line 11), outside the final window; **bottletrap positive 2024-04-13 and 2024-04-14** (lines 112 and 146), inside. Again the two source witnesses do not coincide in method and date.

Every split-witness record is independently auditable through `*_positive_pair_window_detail.csv`: source site, original taxon, window horizon/anchor, positive method, date, native source CSV line, AV-positive outside source lines and additional-method-positive inside source lines. Repeated `surv` bottletrap keys are not silently deduplicated or assumed independent traps.

## Calendar × method restricts the recorded category signs as well

The analysis also evaluated the original Q1 site-level *source-positive* fraction difference for **9 taxa × 3 wetland group comparisons × 14 calendar windows × 2 method panels = 756** contrast rows. The original full-source category groups remain fixed at **13 intervention, 6 control, 8 artificial** sites, even if a given window includes only one recorded date for some sites. This is **not** an occupancy-adjusted or equal-effort comparison.

| Q1 subset | Recorded source positives retained of 144 | Strict contrast-sign reversals against full-calendar/full-method baseline (of 27) | Strict AV vs full-method differences **within same window** (of 27) |
| --- | ---: | ---: | ---: |
| First 14d, all four methods | **96** | 11 | — |
| First 14d, AV only | **73** | 10 | 5 |
| Last 14d, all four methods | **94** | 7 | — |
| Last 14d, AV only | **48** | 9 | 5 |
| First 30d, all methods | 115 | 8 | — |
| First 30d, AV only | 85 | 6 | 8 |
| Last 30d, all methods | 127 | 5 | — |
| Last 30d, AV only | 85 | 7 | 5 |
| All original dates, all methods | **144** | **0** | — |
| All original dates, AV | **104** | **5** | 5 |

Strict reversal means opposite, **nonzero** integer-cross-product signs of the recorded positive-site fractions. Exact ties are recorded separately. Different time/method subsets can change source-recorded group signs; these are **deterministic repeated descriptions of the same 27 sites**, not 756 independent tests, statistical evidence of true occupancy change, or restoration treatment effects.

The observed number of source positives monotonically increases when a chosen anchored window grows, but the **sign** of a difference between two original category fractions is not guaranteed monotone. It depends on where each species' source-recorded positives occur across methods, dates and original groups.

## Significance for EOG inference and required safeguards

The source-positive mask from a narrowly selected method×calendar subset is always contained in the full original source-positive set. With all else fixed, positive-only constraints weaken as original positive witnesses are removed. Yet **the same-site/taxon positive witness list must retain method and calendar provenance**: evaluating one observational gate using a marginalized positive mask and a second gate independently may **overstate** the evidence surviving their intersection.

This is an EOG measurement/observation-gate result, not empirical proof that ecological `A` (abiotic suitability), `B` (biotic persistence) or `M` (movement) drives habitat differences. No real EOG ecological transition-world counts have been enumerated here. The authors' field method effort, underlying detection probabilities and within-season closure are unverified. The paper reports ordinary dipnet use even though dipnet CSV rows are absent from many site×dates; a missing method row is not confirmed nondeployment.

Original source survey dates span up to 91 days per site; source-positive records over this time can reflect seasonality, different survey methods/efforts or genuine temporal biological change. The source's `surv` field is site×method×DOY grouping, not a physical trap ID. An observed source zero is never coded as true ecological absence. No occupancy model, causal restoration effect, independent EOG-WF scored fourth endpoint, or new A/B/M biological claim is made.

## Reproducible artifacts and verification

- Pre-committed **post-exposure** contract: `validation/wetland_joint_method_calendar_gate_v1/protocol.json`, committed as `231c770c14e67368c37eb250431adacc18db191d` before new joint results were computed.
- Executable: `benchmarks/wetland_joint_method_calendar_gate_v1.py`, reusing original SHA-pinned source and Q1 144/104 witness guards; fail-closed unit tests: `tests/test_wetland_joint_method_calendar_gate_v1.py`.
- Fixed 14-window summaries: `published_q1_window_summary.csv` and `published_q2_window_summary.csv` (14 rows each).
- Source-positive site×species×window histories: `published_q1_positive_pair_window_detail.csv` (**2,016** rows) and `published_q2_positive_pair_window_detail.csv` (**1,078**).
- Full original Q1 date×method wetland group comparison ledger: `published_q1_category_method_calendar_contrasts.csv` (**756** rows).
- Signed result/provenance: `validation/wetland_joint_method_calendar_gate_v1/result_receipt.json`.

[Source-authenticated original CSV GitHub Actions #43892391431](https://github.com/zuizui0223/eog/actions/runs/43892391431) **SUCCESS**. Result fingerprint `e9214692926cd1d865d7bccdd5438c5af977d4332a3faad4321de2a3b8e783ba`; archived artifact ID **14238126291**, ZIP SHA256 `e5d50f85902e51de75f410b2b51e0db2dfd62e9cb4076645c2757353cdef7078`. CI checked native original source SHA, source-positive cohort totals, all 14×2 fixed dates/panels, partition reconciliation and Q1's 756 contrast rows.

**Status:** Verified original-source observation method/time analysis. The PR remains Draft and unmerged; frozen EOG-WF 3 scored, 31 scientific STOPs and 3 administrative exclusions are unchanged.
