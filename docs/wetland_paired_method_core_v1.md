# A fully recorded acoustic–visual core exposes taxon-selective observation filtering

## Result and intended use

**Completed post-exposure source-data audit, not a new ecological causal effect or occupancy-model refit.** The original Hungarian wetland amphibian CSV retains an `acoustic` row **and** a `visual` row for **every** recorded site×calendar-date group. This supplies a deterministic, constant *recorded-method-name* subset without the published R preprocessing step that independently reselects source rows into 20 pseudo-occasions. However, these two methods alone miss many source-confirmed positive records of certain amphibians.

**Article:** Wenner, B., Lestyán, B. B., Móré, A., Vadász, C., Kelemen, A. & Mizsei, E. (2025). *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837). The article is under CC BY 4.0. Original data and R: [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115). Data locally mirrored in `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

**Question:** For a data-recording-complete `acoustic + visual` core, how many *originally recorded positive* site×species and site×date×species observations are retained? All evidence is calculated as Boolean `count > 0` from the source, with no invented absence, probabilistic detectability, or reclassification of missing methods.

## Coverage: what the original CSV actually represents

| CSV method-row representation | Full archive (29 sites) | Published Q1 (27 sites) | Published Q2 (13 intervention sites) |
| --- | ---: | ---: | ---: |
| Distinct source site×dates | **129** | **117** | **64** |
| Site×dates with exactly one `acoustic` row | 129/129 | 117/117 | 64/64 |
| Site×dates with exactly one `visual` row | 129/129 | 117/117 | 64/64 |
| Site×dates with ≥1 `dipnet` row | **59** | **57** | **27** |
| Site×dates with ≥1 `bottletrap` row | **62** | **58** | **31** |
| Native acoustic+visual CSV source rows in core | 258 | 234 | 128 |

This is a **complete recorded method-row pair**, *not a standardized effort certificate*. The paper's Methods (§2.2) explicitly state that visual, acoustic and dipnet sampling were used in ordinary surveys, with two observers and variable observation duration of approximately 15 minutes to 3 hours. The archive's missing `dipnet` rows on **70/129** site×dates therefore **cannot be interpreted as proof dipnet was not deployed**. These may reflect the source table's recording/aggregation conventions, and method-specific effort cannot be independently reconstructed from these rows alone.

Bottle traps were additionally deployed (15–50 traps per wetland according to the paper), and the original CSV contains two `site:method:doy` group keys shared by multiple bottletrap rows. This profile does not delete, sum, or assume independent physical trap observations from these rows.

## Full original method evidence versus paired acoustic+visual evidence

| Source-positive evidence | Full archive | Original Q1 | Original Q2 |
| --- | ---: | ---: | ---: |
| All-method **site×species** positive groups | 153 | **144** | **77** |
| Site×species positives seen by acoustic or visual | 110 | **104** | **61** |
| Native positive site×species not seen in paired core | **43** | **40** | **16** |
| Fraction of source positives retained by paired core | 71.9% | **72.2%** | **79.2%** |
| All-method source-positive **site×date×species** groups | 365 | 346 | 207 |
| Source-positive site×date×species seen in paired core | 249 | **234** | **148** |
| All-method date-positive groups not seen in paired core | 116 | **112** | **59** |

The paired core includes every **recorded** date and exactly two source method rows per date. Every paired-core positive is also a full original source positive: method restriction removes authentic positive witnesses but cannot invent positive witnesses. **Unseen by the selected two methods is not an observed biological absence**.

### Strong taxon dependence

| Amphibian species | Q1 full-method positive sites | Q1 paired-core positive sites | Source-positive sites unseen in paired core | Q2 full→paired-core positive sites |
| --- | ---: | ---: | ---: | ---: |
| *Lissotriton vulgaris* | 21 | **6** | **15/21** | **9→3** |
| *Triturus dobrogicus* | 7 | **1** | **6/7** | **4→1** |
| *Bombina bombina* | 18 | 11 | 7/18 | 12→8 |
| *Hyla arborea* | 24 | **22** | 2/24 | **12→12** |
| *Pelophylax ridibundus* | 18 | **18** | 0/18 | **10→10** |

Of Q1's **40** full-source positive groups not seen in the paired core, **21** involve the two recorded newt species above; in Q2, the corresponding number is **9/16**. The source records also verify that aquatic-method rows carry the missed positives, but the difference between newts and frogs is **an observation-route difference** (the published survey says traps were added to detect newts and larvae), not an experimentally isolated species-level ecological effect.

The article itself recognizes species-varying method detectability: trapping is more effective for newts, and visual/acoustic surveys more effective for certain frogs. This matches the **direction** of the observed source recording patterns, without making a causal claim about ecological habitat suitability, population persistence, or species interactions.

## EOG interpretation

Let `O_full` be the full original recorded positive set and `O_AV` the source-observed acoustic+visual positive set. **`O_AV ⊆ O_full`** is source-verified. Under EOG's fixed finite universe, fixed sources, and fixed support masks/rules, positive-only compatible world sets satisfy **`W(O_full) ⊆ W(O_AV)`**.

This inclusion concerns the *logical direction of constraint loss*, not the number of actual ecological worlds excluded. The incomplete core can leave more fixed candidate worlds uneliminated because it omits true recorded positive witnesses. If the method-specific nondetections were incorrectly treated as species true absences, it could instead yield an opposite error, excluding otherwise compatible worlds.

**Crucial biological interpretation:** A method-standardized source-record panel changes the observed taxonomic distribution, and that taxonomic distortion could falsely resemble an environmental filter or biotic structure. There is **no evidence in this source analysis that acoustic/visual recording differences are natural A, B or movement M processes**.

## Remaining limitations

- The original article reports dipnet effort as part of ordinary visits, but dipnet rows are sparse in the released CSV: the representation may encode only some method results rather than all deployment. A missing row does **not** prove the method was absent or no detection.
- Recorded acoustic+visual presence on every date does **not** imply constant 2-observer time, acoustic detectability, visual visibility, or comparable detection probabilities.
- Source record grouping `surv=site:method:DOY` cannot identify individual bottle traps; no trap-level resampling or independent observational likelihood is fit.
- The within-site survey season spans up to **91 days**; closure, phenology and repeated-visit independence are unverified.
- No source-only deterministic method selection can prove original author occupancy coefficients incorrect without model refitting under defensible field effort and closure assumptions.
- **No occupancy fit, causal treatment effect, real-world EOG A/B/M estimation, independent fresh predictive advantage, fourth EOG-WF endpoint or merge of Draft PR #697**.

## Source-backed executable deliverables

- `validation/wetland_paired_method_core_v1/protocol.json`: post-exposure source-anchored protocol committed before its CI computation.
- `benchmarks/wetland_paired_method_core_v1.py`: SHA256-verified source method-pair audit and source-positive union tests.
- `tests/test_wetland_paired_method_core_v1.py`: fail-closed synthetic duplicate/missing acoustic or visual method and source-data checks.
- `validation/wetland_paired_method_core_v1/result_receipt.json`: canonical verified result fingerprint and CI artifact identifiers.
- Full auditable `*_paired_core_site_date_species.csv` and `*_paired_core_site_species_positive_registry.csv` for all three cohorts, deposited in source-gated GitHub Actions artifacts.

This is a **methodological evidence-preservation result**, not independent validation of any new ecology mechanism. The next scientifically necessary information is the field effort/response semantics of missing dipnet rows, actual observation duration/method dependencies and a justified temporal target for occupancy.
