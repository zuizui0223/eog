# EOG wetland: what additional observation could convert a weak prevalence bound into a strict sign?

## Status and answer

**Completed source-authenticated counterfactual observation-design calculation, NOT actual negative evidence or a field survey plan with validated methods.** Earlier work with the original Q1 wetland amphibian records showed that, if each original positive is assumed correct and all source nondetections are treated as unknown, **23 of 27** source species×category contrasts allow both strict signs; the other **four** are only *weakly* one-sided (two nonnegative, two nonpositive). **None has an identified strictly positive or strictly negative biological prevalence difference from source positives alone.**

This v1 exercise enumerates **every original Q1 site whose unknown species×site status could, if independently and conclusively proven absent**, make one of those four weak one-sided contrasts strict. It then searches for the **smallest number of distinct sites** which, in the mathematically most favorable case, could accommodate all required species-specific negative evidence. This is an ideal information-witness problem, not a claim that true absence is observable from existing nondetections.

Original source: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837), archived native data and scripts [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115), CC BY 4.0. Source pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, surveys SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site categories SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

## Exact condition for distinguishing a strict prevalence sign

For category `g`, the original Q1 study has `n_g` sites, of which `k_g` had at least one positive archived species count. Let `z_g` be the **number of sites with independently verified true absence** (not simply archive nondetection or no dipnet CSV row). Conditional on all positive counts being correct and the hypothetical site/species binary status being static:

`k_g / n_g <= pi_g <= (n_g - z_g)/n_g`.

The identified group difference `Delta(A-B)` then lies between:

`k_A/n_A - (n_B-z_B)/n_B`

and

`(n_A-z_A)/n_A - k_B/n_B`.

**One actual authenticated negative in the incomplete group suffices** when the comparison's other category is already **fully source-positive at every site**. That is why the four weakly one-sided contrasts are interesting observation-design targets. Yet this requires *true-negative certification* and biologically meaningful temporal closure; repeated non-detection with imperfect detection is not logically equivalent.

## Four original source comparisons that could become strict

Both `Lissotriton vulgaris` and `Hyla arborea` have **positive archived source records at all 8/8 artificial sites**. This fact alone bounds artificial−control to be **nonnegative** for each taxon and intervention−artificial to be **nonpositive**. Exact original archived positive site counts and hypothetical outcomes are:

| Original source contrast | Source positives | Current conditional contrast interval (pp) | Which group needs one independently certified true-negative site? | Interval after **hypothetical one** valid negative (pp) |
| --- | --- | --- | --- | --- |
| `Lissotriton vulgaris`, intervention−artificial | 9/13 vs 8/8 | **[−30.77, 0]** | Intervention (one of four source-unconfirmed sites) | **[−30.77, −7.69]** |
| `Lissotriton vulgaris`, artificial−control | 8/8 vs 4/6 | **[0, +33.33]** | Control (one of two source-unconfirmed sites) | **[+16.67, +33.33]** |
| `Hyla arborea`, intervention−artificial | 12/13 vs 8/8 | **[−7.69, 0]** | Intervention (its single source-unconfirmed site) | **[−7.69, −7.69]** |
| `Hyla arborea`, artificial−control | 8/8 vs 4/6 | **[0, +33.33]** | Control (one of two source-unconfirmed sites) | **[+16.67, +33.33]** |

All 4 intervals after a valid negative **exclude zero**, but the table describes *conditional possibilities*, **not measured true absence or an observed shift in biology**. A new positive detection instead tightens the unknown interval in the opposite direction and can support a zero-difference completion; positive evidence alone still cannot prove a strictly nonzero difference when the competing group already has 8/8 recorded positives.

## Counterfactual joint visit optimization

There are **9 source-unconfirmed species×site candidate statuses across 7 distinct source sites** relevant to the four weakly one-sided contrasts. Treating a visit to one site as potentially supporting *separate, independently valid* negative certificates for both species, an exhaustive set-cover search found exactly one **two-site** solution:

| Exact source site ID | Original category | Original recorded site×dates | Species with no source positive that a valid independent test would have to address | Weak contrasts potentially resolved |
| --- | --- | ---: | --- | --- |
| `rachaz_2` | Intervention | **5** | `Lissotriton vulgaris` and `Hyla arborea` | Both intervention−artificial comparisons |
| `nyarfas-turjan-laperdo` | Control | **2** | `Lissotriton vulgaris` and `Hyla arborea` | Both artificial−control comparisons |

Thus **minimum distinct candidate sites = 2**, but **minimum separately certified site×species absence statuses = 4**. Other collections of four certificates spread over more than two source sites are mathematically possible. The **two-site solution is unique for reducing the distinct site count** within the seven observed source-site candidates.

The seven eligible site identifiers and all nine species×site unknowns are preserved in the CSV output. Selecting `rachaz_2` and `nyarfas-turjan-laperdo` is an information-geometry result, not an endorsement that either site is accessible, a modern sampling location, biologically appropriate at a particular time, or geographically located by this study's coordinates.

### Important asymmetry of information

At these two sites, **one valid negative of each taxon would establish a strict sign** only under the perfect-positive and static-state assumptions, because the comparison groups already have all eight artificial sites source-positive. If either target taxon is instead *truly present* at the proposed site, that result is also informative, but the corresponding negative witness does **not** exist there and the strict sign is not established by that result alone.

For example, `Hyla arborea` was source-positive in 12/13 intervention sites and all 8/8 artificial sites. The sole intervention site lacking a source-positive record is `rachaz_2`. If its true status were independently proved absent, the hypothetical intervention−artificial difference would be **exactly −1/13**; if independently shown present, both categories would be 100% positive and the difference would be **exactly 0**. These are mutually exclusive counterfactual outcomes and not current ecological findings.

## What would actually be required in the field?

**Not sufficient:** A new visit with no detection, even using acoustic, visual, dipnet and bottletrap together. A recorded zero is not a certified true absence. Several original methods may have unequal exposure or different seasonal detectability, and the source's within-site visit spans reach **91 days**.

**Required for this exact logical test:** Independent evidence sufficient to adjudicate a site/species true status at a well-defined biologically closed period, validated positive specificity, appropriate effort/observer detection model and known unit of analysis. If only probabilistic detection evidence can be achieved, use an **explicit detection model with uncertainty**, rather than calling an estimated low occurrence probability a logically proven negative. The original paper's method-row coverage itself cannot prove field method nondeployment.

These site labels are source data identifiers; no physical travel route, permission verification, field accessibility or geolocation has been established. The source categories are observational, not randomized; even a strictly identified site prevalence difference **would not by itself establish a causal effect of restoration**. No empirical A/B/M mechanism or EOG finite-process world set has been estimated.

## Executable source and verification

The v1 source-pinned analysis is a deterministic minimum-witness and set-cover calculation:
- Pre-scoring protocol: `validation/wetland_negative_witness_plan_v1/protocol.json` committed as `d117c3d20fbff524a45984f001eedb301f744dec`.
- Code: `benchmarks/wetland_negative_witness_plan_v1.py`, reusing the source authentication from `benchmarks/wetland_positive_only_partial_id_v1.py`.
- Tests: `tests/test_wetland_negative_witness_plan_v1.py`, including rejection of negative certificates contradicting native positives, fractional counts and conflation of positive-only bounds with strict inference.
- Result/sha record: `validation/wetland_negative_witness_plan_v1/result_receipt.json`.
- Complete CSV evidence in GitHub artifact: `weak_one_sided_target_list.csv` (**4 rows**), `source_unconfirmed_candidate_site_species.csv` (**9 rows**), and `site_visit_joint_target_coverage.csv` (**7 rows**).

[Source-authenticated GitHub Actions #43714787444](https://github.com/zuizui0223/eog/actions/runs/43714787444), **SUCCESS**, result fingerprint `6f941a575e664115aeb636371cde23d4fb8171d03b514fe4de8219bdfad21829`, artifact ID **14161749487**, ZIP SHA256 `faa00e58ace633c9f66b9eaf03c866a6646931124666f56a5d45dedcc82e8616`. A first synthetic test mistakenly assumed the four *certificate* sets were unique; certificate sets can span multiple sites. After correcting the **test expectation only**, the original-source analysis and independent native source checks passed. All results are **post-exposure counterfactual information design**, not new biological data.

**Scientific STOP:** No true negatives observed, no actual field expedition commissioned, no occupancy/refitted author coefficients, independent A/B/M proof, ecological process-world count, additional EOG-WF predictive endpoint or merge of Draft PR #697. The earlier EOG-WF 3 scored/31 scientific STOP/3 administrative exclusion record stays frozen.
