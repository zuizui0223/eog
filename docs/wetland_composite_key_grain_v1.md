# Native wetland `surv` key is a visit-group identifier, not a physical survey-row ID

## Source and primary result

Original observations: Mizsei & Wenner (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, [Global Ecology and Conservation](https://www.sciencedirect.com/science/article/pii/S235198942500438X), DOI [10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837); data/code Zenodo [10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. Source pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc` with the archived survey CSV SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`.

This post-exposure source-grain audit compared the supplied `surv` field with an explicit composite of native fields at the source's **raw 381-row grain**.

**Exact result:** `surv == site + ":" + method + ":" + doy` for **381/381 rows**. Thus the `surv` field is reproducibly a *site × method × day-of-year grouping key*, not a proven unique physical-observation-row identifier.

| Native method | Raw CSV rows | Distinct `surv` grouping keys |
| --- | ---: | ---: |
| Acoustic | 129 | 129 |
| Visual | 129 | 129 |
| Dipnet | 59 | 59 |
| Bottletrap | **64** | **62** |
| **Total** | **381** | **379** |

Exactly two grouping keys each contain two native rows: `feneketlen-turjan:bottletrap:89` and `tengelyut-2:bottletrap:118`. Both groups have the same recorded site/date/method/num/weather but one all-zero species vector and one positive species vector. This is a **within-group count discrepancy**, not proof that the biological rows are mistaken copies.

## Why a repeated grouping key may be legitimate

The original published Methods specify two field observers; visual, acoustic and dipnet observations were pooled by method per visit; **15–50 bottle traps per site** were used depending on wetland size, including multiple restored pools; the traps were used for two consecutive nights and checked daily. This is direct field-protocol evidence for **multiple physical observations per bottletrap method/date group**, but does not prove what each of the two particular repeated lines represents.

The CSV has no independently authenticated trap-level unique identifier for these cases. It is therefore scientifically wrong to assume either:

- `surv` must uniquely identify every biological row, so repeated keys prove erroneous data; **or**
- the repeated keys necessarily correspond to genuinely independent traps and can be modeled as additional independent sampling occasions.

Original physical trap IDs, visit logs, effort/exposure times and author-supported aggregation rules are needed to distinguish distinct trap outcomes, record corrections and data-entry inconsistencies.

## Correction to earlier EOG gate language

The existing `BLOCKED_CONFLICTING_SURVEY_IDENTIFIERS` status **remains justified only for the proposed rowwise detection likelihood that assumes one unique survey ID per independent row**. It is *not* evidence of original source corruption, a reason to delete observations, or a refutation of the published ecological effect. The previous four hypothetical one-row-per-key sensitivity scenarios are explicitly hypothetical and must **not** be silently applied as the 'clean' field data.

The independent source-grain diagnostic now establishes the key's actual construction and emits `COMPOSITE_OCCASION_KEY_NOT_PHYSICAL_ROW_ID` while leaving the original frozen source gate, its signed receipt and all EOG-WF evidence untouched.

## Reproducibility

Executable: `benchmarks/wetland_survey_grain_v1.py`; tests: `tests/test_wetland_survey_grain_v1.py`. The source-pinned GitHub wetland identity workflow checks 381/381 composite-key equivalence and 64 bottletrap rows/62 groups, and uploads `survey_grain.json`.

**Scope:** data grain/field interpretation only. No model-fitting, physical trap identification, occupancy, independent A/B/M, population movement, causal restoration effect or new EOG-WF endpoint is inferred.
