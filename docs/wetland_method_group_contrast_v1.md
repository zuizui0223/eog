# Wetland method-filter sensitivity: recorded group contrasts can reverse without any change in field observations

## Scope, source and research question

This is a **post-exposure descriptive source-record analysis**, not an experiment, occupancy model or causal restoration estimate. It asks whether restricting the *same source observations at the same original sites* to the two perfectly represented **acoustic+visual method rows** changes apparent species occurrence differences among the original Q1 wetland classes.

Original study: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837); native data and author R in [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0.

The native survey and site CSV files are pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc` and verified by survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd` and site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

We retain the **author Q1 27-site cohort** (13 intervention/restoration, 6 control, 8 artificial waterbody sites), excluding `kis-banyato` and `vadasz-turjan` as in its original published R code. The baseline is the source-site/species Boolean OR over all original recorded methods/dates. The paired core uses the same source and source sites, but only acoustic and visual rows. **Both methods have exactly one source row at all 117 original Q1 site×calendar-date groups**, but this is recording completeness, not independently verified constant effort.

## Site-level and group-level source facts

| Original wetland category (`ci`) | Sites | Full-method source positive site×species | Acoustic+visual positive site×species | Source positives unseen by paired core | Mean source-recorded species per site, full → core |
| --- | ---: | ---: | ---: | ---: | ---: |
| Intervention | **13** | **77** | **61** | **16** | **5.923 → 4.692** |
| Control | **6** | **23** | **15** | **8** | **3.833 → 2.500** |
| Artificial | **8** | **44** | **28** | **16** | **5.500 → 3.500** |
| Total | **27** | **144** | **104** | **40** | — |

A species-site source-positive is counted if any original row has count greater than zero. All row-level count assignments are left untouched; no 20-pseudo-occasion random resampling, source-record deletion, physical trap deduplication or artificial zero is carried out.

### Strict direction reversals in recorded positivity differences

Each taxon×group contrast is the difference between **fractions of sites with at least one recorded source-positive observation** in the two original groups. Positive/negative signs are calculated from integer cross-products, not from rounded displayed percentages. **There are 5 strict nonzero direction reversals in the 27 predeclared species×category contrasts.** A sixth comparison reaches a zero tie but is *not* a strict reversal.

| Taxon, category A minus category B | Full methods (percentage points) | Acoustic+visual (percentage points) | Difference in points |
| --- | ---: | ---: | ---: |
| *Lissotriton vulgaris*, intervention − control | **+2.56** | **−26.92** | −29.49 |
| *Bufo bufo*, intervention − control | **−12.82** | **+20.51** | +33.33 |
| *Lissotriton vulgaris*, intervention − artificial | **−30.77** | **+23.08** | +53.85 |
| *Lissotriton vulgaris*, artificial − control | **+33.33** | **−50.00** | −83.33 |
| *Bufotes viridis*, artificial − control | **−8.33** | **+8.33** | +16.67 |

The most striking same-sites example is *Lissotriton vulgaris*: full records report **9/13 intervention, 4/6 control, 8/8 artificial** source-positive sites, whereas acoustic+visual records report **3/13, 3/6, 0/8**. The observation subset alone changes the *artificial minus control* contrast from +33.33 to −50.00 percentage points.

Some differences involve very few sites and some full-method differences are near zero (e.g. +2.56 points); **reversal counts are descriptive, not a hypothesis-test tally, p-value or an empirical causal treatment effect**. The archive is not a randomized treatment trial, and statistical independence/detection-adjusted occupancy have not been established.

## Why the source method metadata matter

The source method-day representation itself varies among original Q1 categories:

| Q1 category | Recorded site×dates | Site×dates with a dipnet CSV row | Site×dates with a bottletrap CSV row |
| --- | ---: | ---: | ---: |
| Intervention | 64 | 27 | 31 |
| Control | 18 | 10 | 12 |
| Artificial | 35 | 20 | 15 |

These are frequencies of **data rows represented in the public CSV**, not field-method deployment or standardized effort. Indeed, the published Methods §2.2 state that acoustic, visual and dipnet techniques were used during ordinary visits, while only 57/117 Q1 dates have a dipnet CSV row. It would be incorrect to infer that a method was not deployed just because its row is absent in the released source.

Adding aquatic-method recorded positives changes the apparent representation of newts more strongly than that of many frogs. No conclusion about habitat selection, natural extinction, restoration success, local persistence, colonization history, biotic B, or movement M can be inferred from this method-only operation. It establishes **method-filter sensitivity of the observed species/site evidence**, not the biological process generating those occurrences.

## EOG inference and proper uncertainty semantics

Let `O_full` be the full native source-positive site×species set and `O_AV` the paired acoustic+visual source-positive set. By construction and source reconciliation:

`O_AV ⊆ O_full`.

Under a *fixed* finite world universe with unchanged sources, rules and positive-support masks, positive-only compatibility has the expected direction:

`W(O_full) ⊆ W(O_AV)`.

Method restriction can cause authentic positive witnesses to be **missing from the selected source representation**, making fixed-world exclusion weaker. Any claim that a source-positive species is biologically absent because it was not detected by acoustic/visual would instead introduce a contradictory negative observation. **No actual ecological worlds have been enumerated, no world-count difference calculated and evidence-dependent/source-changing EOG operators are not covered by this inclusion lemma.**

## Reproducible outputs and scope limits

- Post-exposure protocol: `validation/wetland_method_group_contrast_v1/protocol.json`.
- Python source-verified evaluator: `benchmarks/wetland_method_group_contrast_v1.py`.
- Negative-control/unit tests: `tests/test_wetland_method_group_contrast_v1.py`.
- Machine-readable result: `validation/wetland_method_group_contrast_v1/result_receipt.json`.
- Original Q1 site-level source richness, 9 taxa×3 category prevalence table, and all 27 exact contrast rows are delivered in the GitHub Actions artifact, with their individual SHA256 checksums and a result fingerprint.

**Inference STOP:** No occupancy likelihood, prevalence-corrected species richness, fitted treatment effect, statistical significance of direction changes, equal method effort, seasonal closure, physical trap identity, new causal A/B/M or fourth EOG-WF scored endpoint is established. Draft PR #697 remains **unmerged**. Any eventual biological inference requires validated field effort/visit units, phenological closure assumptions and independently appropriate observation likelihoods.
