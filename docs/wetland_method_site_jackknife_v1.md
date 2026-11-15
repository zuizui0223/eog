# Wetland observation-channel contrasts: which sign reversals survive removal of any one source site?

## Result and evidence status

**Completed source-authenticated post-exposure robustness diagnostic — NOT a jackknife standard error, confidence interval, ecological occupancy estimate, or a fresh field study.** The previously audited 2024 Hungary wetland amphibian survey contains **27 source sites** in the original Q1 analysis (intervention 13, control 6, artificial 8). We already established that comparing full four-method source-positive site records with the acoustic+visual subset reverses **5 of 27** descriptive species-by-wetland-category differences.

The new check asks whether these five cases depend on one exceptional source site. It **removes each of the 27 native sites exactly once**, recomputes both full-method and restricted-method positivity on exactly the **same remaining 26 sites**, and updates the relevant group denominator before comparing signs. This is repeated deterministic *site-deletion robustness*, not 27 independent replicate surveys or valid statistical uncertainty quantification.

Original data: Wenner et al. (2025), *Effectiveness of wetland restoration on amphibians in a drying grassland habitat losing its breeding sites*, *Global Ecology and Conservation* 62 e03837, [DOI 10.1016/j.gecco.2025.e03837](https://doi.org/10.1016/j.gecco.2025.e03837), CC BY 4.0; raw survey and author R at [Zenodo 10.5281/zenodo.15044115](https://doi.org/10.5281/zenodo.15044115). Archive is pinned to `zuizui0223/frogcs@5e2f0a87c639df373fa2700b29403d2ab417a1cc`, survey SHA256 `45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd`, site SHA256 `93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319`.

## Three of five original recorded-sign reversals survive every single-site deletion

Under each site deletion, a contrast is called a **strict method reversal** only when the full-method and acoustic+visual source positivity differences across the same 26 sites have **opposite, nonzero integer-cross-product signs**. Exact zero/ties are categorized separately. Original sample category sizes are 13/6/8; site deletions lead to one category having exactly one fewer site (12/13, 5/6, or 7/8), not a fixed denominator.

| Taxon, comparison of original wetland category fractions | Original 27-site strict reversal | 26-site deletion cases retaining reversal | Deletion cases with an exact zero/tie | Deletion cases with same nonzero direction |
| --- | --- | ---: | ---: | ---: |
| *Lissotriton vulgaris*, intervention − control | Yes | **16/27** | **9** | **2** |
| *Bufo bufo*, intervention − control | Yes | **27/27** | **0** | **0** |
| *Lissotriton vulgaris*, intervention − artificial | Yes | **27/27** | **0** | **0** |
| *Lissotriton vulgaris*, artificial − control | Yes | **27/27** | **0** | **0** |
| *Bufotes viridis*, artificial − control | Yes | **23/27** | **0** | **4** |

The first `L. vulgaris` comparison has a **very small original full-source intervention–control difference of +2.56 percentage points**. Its observed full-method direction itself changes or reaches a tie after **11/27** site deletions, so the source data cannot support claims of a stable category preference from this contrast alone.

The `Bufotes viridis` artificial–control method reversal also disappears with removal of four specific sites (`dog-hegyi-csatorna`, `ordito-kulso-turjan`, `teknos-hati-csatorna-1`, `tucskosi-mocsar`). It remains in 23/27 deletion views. These are sensitivity outcomes, not influence p-values or diagnostic evidence of erroneous field records.

**Three of five** original method sign reversals survive any one of the 27 source-site deletions, **within this fixed source-recording and method-panel definition**. This is stronger than merely finding a sign reversal on the full Q1 dataset, but it does not establish biological absence, a valid occupancy contrast, a treatment effect or across-study generality.

## Method-panel robustness across all 27 deleted-site cases

The evaluation was not restricted to acoustic+visual: it covered **all 15 fixed nonempty subsets** of acoustic, visual, dipnet and bottletrap, the same **9 species × 3 wetland-category comparisons** after every site deletion:

`15 method subsets × 27 excluded sites × 27 contrasts = 10,935 original-source descriptive contrast rows`.

| Subset of recorded method families | Strict reversals in the original intact 27 sites | Minimum / median / maximum strict reversals across 27 single-site deletions | Deleted-site cases with **zero** method reversals |
| --- | ---: | ---: | ---: |
| Acoustic + visual | **5** | **4 / 5 / 6** | **0/27** |
| Acoustic + visual + bottletrap (without dipnet) | **5** | **3 / 5 / 7** | **0/27** |
| Visual + dipnet | **0** | **0 / 0 / 1** | **23/27** |
| Acoustic + visual + dipnet | **0** | **0 / 0 / 1** | **26/27** |
| All four recorded methods | **0** | **0 / 0 / 0** | **27/27** |

The full four-method panel is the reference and must agree with itself. **Even with one source site removed, acoustic+visual always reverses at least four descriptive category signs** relative to the full source records. Conversely, `visual+dipnet` reproduces all 27 original intact-dataset category directions, but that statement fails after **4 of 27** site deletions (one strict reversal), illustrating that intact-dataset sign fidelity is not necessarily site-deletion robust.

## What this says about the data-generating chain

The original positive evidence for each site×species is the Boolean OR of native recorded counts greater than zero. Restricting the input to selected methods yields a subset of those recorded positive witnesses. The wetland-group descriptive signed differences, however, compare *fractions of positive-recorded sites within groups*: removing original positive witnesses may reduce numerator counts in different groups by different amounts, yielding a sign reversal. Because the baseline group sizes are small, deleting one source site can itself change a weak contrast's direction.

This is a concrete illustration of **observation-channel-induced contrast instability and site leverage**, not a proof of an abiotic habitat filter, biotic interaction, dispersal mechanism, historical source world or natural restoration response.

The source-based model:
- has **no field treatment randomization** and uses **no p-values** for these method-contingent category differences;
- does **not** certify equal observation duration/effort, method deployment or independent detection;
- cannot establish source-recorded nondetections as true ecological absences;
- does **not** prove single-season closure when site observations span up to 91 days;
- does **not** identify original physical bottletrap IDs; the two repeated `site:method:doy` bottletrap groups remain preserved and unresolved;
- does **not** refit the original `unmarked` occupancy likelihood, imply original author treatment coefficients are biased, or create a fourth EOG-WF scored endpoint.

The published paper reports dipnet use during ordinary surveys, but the archived Q1 source has a dipnet method row on only **57 of 117** recorded site×dates. Missing dipnet CSV rows cannot be equated to verified nondeployment; an acoustic+visual complete row pair similarly does not guarantee equal field effort.

## Code, full outputs and validation

- Pre-run fixed post-exposure protocol: `validation/wetland_method_site_jackknife_v1/protocol.json`, commit `fa19742d2c8eb861642a55e85b488ebe7a6d4c99`.
- Source-authenticated executable: `benchmarks/wetland_method_site_jackknife_v1.py` (imports pinned method-lattice source validation, recomputes exact integer signs per 26-site view).
- Fail-closed tests: `tests/test_wetland_method_site_jackknife_v1.py`.
- Machine-readable result receipt: `validation/wetland_method_site_jackknife_v1/result_receipt.json`.
- Complete GitHub Actions outputs: `method_panel_site_drop_contrasts.csv` (**10,935 rows**), `method_panel_site_drop_summary.csv` (**405 rows**), `original_five_acoustic_visual_site_drop_details.csv` (**135 rows**).
- [Original-source GitHub Actions #43711780299](https://github.com/zuizui0223/eog/actions/runs/43711780299), **SUCCESS**, fingerprint `37d68253a938f89cf8719a905883594ee90044a676a8c786c6329dac397358d3`; artifact **14160896616**, ZIP SHA256 `153a51e0ff5f5e862c39bcb7d0fd502e6c492bd1c3cd8b225b7a3ba7601c8148`.

The prior initial test attempt used a small synthetic example with **two** sign reversals while its test asserted **one**, and one error-match expected a different label. Both **test expectations were corrected**; the source algorithm was not patched, and the subsequent complete original-source CI passed.

**Decision:** Retain explicit method-channel uncertainty alongside source site identity and category denominators. Original method signs cannot be promoted into claims about habitat suitability, restoration effects or EOG A/B/M mechanisms. The PR remains Draft/unmerged; EOG-WF's closed 3-scored/31-scientific-STOP/3-administrative-exclusion denominator remains unchanged.
