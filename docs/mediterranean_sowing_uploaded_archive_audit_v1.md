# EOG: source-verified seed introduction and protection-response witness audit

**Status:** Independent source bytes verified; strict full-primary **DATA-QUALITY STOP**, with post-exposure descriptive results from unaffected units. This is **not** a new EOG-WF scored endpoint, a demonstration of out-of-sample prediction superiority, or identification of the underlying natural dispersal mechanism.

## Original source

Acevedo-Limón, L., Rumeu, B., Linares, M. & González-Varo, J. P. (2025/2026). *Uncovering biodiversity deficits: Experimental evidence for dispersal limitation of woody species in Mediterranean forest patches*. *Journal of Applied Ecology*, DOI: [10.1111/1365-2664.70207](https://doi.org/10.1111/1365-2664.70207); dataset: [Dryad 10.5061/dryad.t1g1jwtg3](https://doi.org/10.5061/dryad.t1g1jwtg3), original release 2025-10-16. Research findings in the published paper predate this EOG audit.

User-supplied ZIP: `doi_10_5061_dryad_t1g1jwtg3__v20251016.zip`, SHA-256 `e05646c628caed63c7f169a53c52e3977f5c11dff3f5d1b1d7e7e32bcd871e26`. All **12 ZIP members** have the same sizes and SHA-256 digests as the official Dryad API `stash:files` manifest recorded by EOG GitHub Actions workflow #44669314198 (artifact 14598908226). Files are read from the archive without extraction to filesystem, and their CRCs are checked. An authorized bearer token or a download-capable CI environment is **not** required to verify the user-supplied ZIP against the captured official manifest.

## Integrity findings

The source contains 61,000 sown seed rows, 10 species, 10 forest patches, 1,108 arm-specific stations, and 4,959 unknown germination outcomes. The experiment used two sowing stations (one caged, one exposed) within each plot; 554 indexed plot-level treatment pairs can be constructed.

**Hard-stop:** five repeated `(species, site, year, microhabitat, station, treatment, point, seed)` identifiers occur in the unprotected station for *Rhamnus alaternus*, `dehesa_yeguas`, 2021, shrub, station 5. The protected arm contains 20 rows, and the unprotected arm contains 30, inconsistent with the documented 25+25 design for this large-seeded species. At least two duplicated seed identifiers have different germination/survival values. The identity of the five mislabelled seeds cannot be recovered reliably from these columns. Do **not** silently deduplicate, relabel treatments, or select favorable rows. The predeclared full-panel primary response remains **SOURCE_QUALITY_STOP** until resolved against original research records.

For a descriptive *unaffected-subpanel* audit, quarantine both arms of this plot (50 rows) and label the entire containing species×site×year as ineligible, without treating this exclusion as a preregistered success. The remaining 553 intact plot pairs support 51 unaffected species×site×year units. Both germination status and plot-pair integrity are preserved; unknown germination states remain unknown.

## Main directly observed ecological evidence (independent of repairing those five IDs)

Among **20 species×forest-patch combinations** that were naturally absent according to the authors' sampling:

| Confirmed result in the **unprotected** sowing stations | Species×patch combinations |
|---|---:|
| At least one seed germinated | **20/20** |
| At least one monitored seedling survived its first summer | **17/20** |
| At least one monitored seedling survived its second summer | **11/20** |

All witnesses exclude the questionable 50 rows. The first-summer survival observation count is 241 unprotected seed records, 7 of which have an unknown `germ` value but directly recorded `seedling_surv=1`; the second-summer survival count is 83 monitored seed records. These are **observed witnesses**, not 241 independent ecological replicates. The unprotected first-summer witness is present in **7 forest patches**, and the second-summer witness in **6 patches**.

The result establishes that **absolute stage-specific viability failure at every tested, unsheltered microsite is false in at least 17 of these 20 species×patch combinations**. It is compatible with natural dispersal/arrival limitation, but does **not** establish that this was the unique cause of natural absence: natural recruitment dynamics, unmeasured habitat/process differences, survival to sexual reproduction, and true natural propagule arrival were not observed in this dataset. It does not independently establish a generalized BAM mechanism-identification theorem.

## Frozen sign rule applied only to unaffected units (post-exposure diagnostic)

The EOG PR #706 pre-outcome protocol fixed: (i) **the experimental plot** as paired-arm unit, not each seed; (ii) an equal-plot mean of the protected-minus-unprotected germination fraction for each species × patch × sowing-year; (iii) missing seed outcomes treated as an interval, success=0 or success=1; (iv) a strict operational sign tolerance of `±0.025`. Every pair's lower and upper bounds are averaged within its species×site×year group. The +/-1/40 comparison is verified by exact rational arithmetic; equality at ±0.025 is not classified as nonzero.

| Natural patch status | Positive direction certainly | Negative direction certainly | Within tolerance certainly | Indeterminate due to missing values |
|---|---:|---:|---:|---:|
| Absent: 25 unaffected units | **13** | 2 | 2 | 8 |
| Present: 26 unaffected units | **16** | 0 | 1 | 9 |

These 51 units are nested in only 10 forest patches, with three species sown in two years, and **do not constitute 51 independent biological replicates**. The sign bounds concern observed experimental germination rates given binary missingness—not true effect confidence intervals, counterfactual colonization processes, or a set of all credible ecological A/B/M mechanisms. Hence they are **not** a proof of prospective field predictive performance or mechanism-independent causal identification.

## Reproduction

```bash
python benchmarks/mediterranean_sowing_uploaded_archive_audit_v1.py \
  --source-zip doi_10_5061_dryad_t1g1jwtg3__v20251016.zip \
  --official-manifest validation/mediterranean_sowing_uploaded_archive_v1/official_manifest.json \
  --output-dir /tmp/eog_sowing_audit
pytest -q tests/test_mediterranean_sowing_uploaded_archive_audit_v1.py
```

If the official manifest differs from the archive, stop with `SOURCE_STOP_UNVERIFIED_OFFICIAL_DIGEST`. Check `result.json` for the marked source-quality violation and `unaffected_51_unit_bounds.csv` for the precisely defined unaffected subset. The original source ZIP is **not** committed to GitHub; it can be obtained from Dryad, and the source manifest guards byte identity.

## Relationship to older EOG results

This audit **extends interpretation** of the experiment rather than re-scoring the original EOG artificial A/B/M mask deletion. EOG PR #702's finite-set sign identification survives as a mathematical result; PR #705's NutNet prediction (2 correct, 1 wrong, 5 abstained among eight held-out sites) remains a negative/mixed external exercise. This source verifies stage-specific realized survival without determining the complete historical mechanism, not a new superiority claim. The EOG-WF three-endpoint closure is unchanged.