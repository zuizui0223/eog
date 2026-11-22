# EOG wetland observation-method lattice: evidence completeness is not contrast-sign stability

## Result and status

**Source-authenticated retrospective processing experiment:** The same 27 original Q1 wetland sites and the same recorded amphibian survey rows were re-expressed through **all 15 nonempty subsets of the four method families** (acoustic, visual, dipnet, bottletrap). Exactly 9 species×3 category contrasts = 27 recorded source-positive site-rate differences are recalculated for each subset, producing 405 deterministic comparisons. There is **no field treatment assignment, occupancy model, p-value, independent population replication, or new EOG-WF scored endpoint**.

Original study: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837); original data/code [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. Immutable source mirror `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`: survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

The previously independently certified 27-site Q1 cohort is **13 intervention, 6 control, 8 artificial** sites, 351 native CSV rows, 117 site×recorded-date groups, **144 native-positive site×species pairs**. Full original source evidence is the Boolean OR of `count>0` in any of the four recorded method families. For every method subset the same source site IDs, category labels and nine species are retained, and only which recorded method rows can contribute positive evidence changes.

A fixed protocol for enumerating **all 15 subsets** was committed at `validation/wetland_method_channel_lattice_v1/protocol.json`, SHA `bb776bf12d0386a11205ba65d3f7cf7a42b8ee8c`, before these new subset results were scored. This is nevertheless **post-exposure analysis of a repeatedly inspected source**.

## Which method makes the source contrasts unstable?

### Leave exactly one recorded method out

| Excluded method | Three-method retained panel | Positive native site×species retained | Exclusive source-positive witnesses lost | Strict reversals of 27 original category signs |
| --- | --- | ---: | ---: | ---: |
| Acoustic | visual + dipnet + bottletrap | **132/144** | **12** | **1/27** |
| Visual | acoustic + dipnet + bottletrap | **128/144** | **16** | **4/27** |
| **Dipnet** | acoustic + visual + bottletrap | **120/144** | **24** | **5/27** |
| Bottletrap | acoustic + visual + dipnet | **139/144** | **5** | **0/27** |

The method exclusion associated with the largest number of **strict sign reversals** is **removing dipnet**, and it also drops the most site×species positives found exclusively by one method (24). This is a *source-evidence accounting association*, not evidence that dipnet biologically causes a restoration effect.

The original two-method panel `acoustic+visual` preserves **104/144** native-positive pairs and reverses **5/27** category contrast signs. Crucially, even the leave-dipnet-out three-method panel has **5/27** strict reversals; the larger family of input methods alone does not guarantee correct sign preservation.

### Other informative method combinations

| Recorded method subset | Native-positive site×species retained | Strict sign reversals (of 27) | Site×dates with a CSV row for **every included method** (of 117) |
| --- | ---: | ---: | ---: |
| acoustic + visual | **104** | **5** | **117** |
| visual + dipnet | **127** | **0** | **57** |
| acoustic + visual + dipnet | **139** | **0** | **57** |
| acoustic + visual + bottletrap | **120** | **5** | **58** |
| All four methods | **144** | **0** | **22** |

For this fixed original site universe, **visual+dipnet is the smallest method-family subset that reproduces all 27 full-source contrast *directions***, including original zero/tie directions. Yet its source-positive support is only **127/144**. And only **57/117 recorded site×dates** have *both* method rows represented in the public CSV. Therefore this panel is **not** a verified uniformly sampled two-method experiment, a full-evidence-preserving substitute, or an inferential recommendation.

### Full 15-panel audit

All combinations were evaluated, not just those displaying interesting signs. The complete `method_subsets.csv` and `method_subset_contrasts.csv` are in the GitHub Actions artifact. In source method order:

| Methods included | Native positives | Strict sign reversals |
| --- | ---: | ---: |
| acoustic | 38 | 3 |
| visual | 90 | 5 |
| dipnet | 104 | 5 |
| bottletrap | 54 | 7 |
| acoustic + visual | 104 | 5 |
| acoustic + dipnet | 122 | 4 |
| acoustic + bottletrap | 82 | 8 |
| visual + dipnet | 127 | 0 |
| visual + bottletrap | 106 | 5 |
| dipnet + bottletrap | 110 | 5 |
| acoustic + visual + dipnet | 139 | 0 |
| acoustic + visual + bottletrap | 120 | 5 |
| acoustic + dipnet + bottletrap | 128 | 4 |
| visual + dipnet + bottletrap | 132 | 1 |
| acoustic + visual + dipnet + bottletrap | **144** | **0** |

Sign reversals are determined using **integer site-positive counts and denominators**, and defined only for strictly nonzero positive-to-negative or negative-to-positive changes relative to full-source values. Transitions to/from exact ties are separately retained in the CSV. No p-values, significance claims or confidence intervals were computed.

## Positive witness exclusivity and complete method necessity

Each original source-positive site×species has a nonempty set of method families that recorded it. A positive is *method-exclusive* when **only one method family** ever recorded it across original observations. Since each of the four families has at least one exclusive positive, **no proper method subset** can preserve all **144** original source-positive site×species pairs.

| Method uniquely recording a native-positive site×species | Exclusive positives |
| --- | ---: |
| acoustic | **12** |
| visual | **16** |
| dipnet | **24** |
| bottletrap | **5** |
| **Total method-exclusive positive pairs** | **57/144** |

The other **87** positive pairs have records in two or more method families. A separate Boolean-OR Shapley-style **descriptive allocation** assigns 1/k to each method that recorded a positive detected by k methods, summing to exactly 144 across the source-positive masks. This is an accounting identity, not estimated relative sampling effort, detection probability or causal method importance.

The complete source-positive site×species method witness table has **144 rows**, preserving which method(s) recorded each positive and the category of the original site.

## EOG implication: observational gates can change apparent constraint directions

If `O_full` is the original four-method source-positive set and `O_P` is the subset positively recorded by method family panel `P`, then for every nested method panel `P⊆Q`:

`O_P⊆O_Q⊆O_full`.

The CI checked this **for all nested pairs of the 15 method panels**. With a fixed declared EOG world universe, fixed sources and unchanged positive-support masks, the positive-only compatibility set therefore reverses inclusion:

`W(O_full)⊆W(O_Q)⊆W(O_P)`.

However, **signs of group-level descriptive prevalence contrasts need not be monotonic** in the method subset. A single missing method can change both groups' observed site-positive fractions differently. Exactly that happens in the archived source: removing dipnet causes five sign reversals, while removing bottletrap does not reverse any. **No actual candidate ecological world counts were computed**, and this lemma does not apply to EOG operators that redefine sources/support masks from the observed set.

A naive reading of paired-core nondetections as true local absence would be scientifically unsupported and can falsely suggest an abiotic/biotic/movement filter. This audit does not identify real A, B or M mechanisms, nor evaluate natural community turnover or a restoration treatment effect.

## Field protocol and source-quality limits

The article's Methods §2.2 report visual, acoustic and dipnet activities during regular field visits, but the archived CSV has dipnet method rows in just **57/117** original Q1 site×dates and bottletrap rows in **58/117**. Their row absence does **not** establish that the methods were not deployed in the field. In the full four-method panel, source rows for **all four** methods are jointly represented at only **22/117** site×dates; site-level positives across different recorded dates are still unioned for descriptive evidence, *not* an equal four-method effort survey.

The record spans up to **91 days** within a site; closure, method effort, observer-time comparability, physical bottletrap identity and independent visit assumptions remain unverified. Original `surv` is a site×method×DOY grouping key, not a unique physical trap ID, and two same-key bottletrap groups are preserved without deduplication.

No original `unmarked` model was fitted, no coefficients or causal restoration effects computed, no physical sampling-effort correction was attempted, and no EOG-WF fourth scored endpoint was introduced.

## Inspectable evidence and verification

- Fixed protocol: `validation/wetland_method_channel_lattice_v1/protocol.json`.
- Source-bound code: `benchmarks/wetland_method_channel_lattice_v1.py`.
- Fail-closed synthetic controls: `tests/test_wetland_method_channel_lattice_v1.py`.
- Machine-readable result/sha receipt: `validation/wetland_method_channel_lattice_v1/result_receipt.json`.
- Artifact CSVs: `method_subsets.csv` (15), `method_subset_contrasts.csv` (405), `native_positive_site_species_witnesses.csv` (144).

[Authenticated CI #43710742795](https://github.com/zuizui0223/eog/actions/runs/43710742795), **SUCCESS**, result fingerprint `d9ce91154c34abc1e0619feb803b0a39b7721ef18dcd01c85279d3b6c581f254`, artifact **14159873171**, ZIP SHA256 `c50ca0a51ac10edfdb7866b0796921b0a07337f4afecfcf665eac4689fdd3f7f`. This is one observed source record and deterministic method-subset lattice, not 15 independent biological experiments.
