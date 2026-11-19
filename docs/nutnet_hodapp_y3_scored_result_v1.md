# NutNet Y3 heldout geometric-response direction — source-exact scored result (v1)

## Evidence category and chronological integrity

**Result: mixed/negative, not predictive superiority.** The specific site-level target, source MD5/size, admissible prediction-model roster, site-heldout split, sign tolerance, and abstention rule were recorded in `validation/nutnet_hodapp_y3_target_v1/protocol_v1.json` at commit `b5ae8afd45de101504539b87482114a731ff247d`, **before individual original CSV treatment responses were opened**. This result note is **post-score**. The overall published treatment-turnover conclusions were known from the paper and cannot be relabeled discovery.

Source: Hodapp et al. (2019), Dryad [10.5061/dryad.8vs569h](https://doi.org/10.5061/dryad.8vs569h) and corresponding Hodapp et al. (2018), *Ecology Letters* DOI [10.1111/ele.13102](https://doi.org/10.1111/ele.13102). Two original CSVs were downloaded via Zenodo record 5023851, but each **exactly matched the original official Dryad metadata MD5 and file size**. The ecological observations were not modified.

## Source and eligibility

| Property | Observed result |
|---|---:|
| Species-cover long-table rows | 29,829 |
| Named taxa in the released source table | 1,303 |
| Site codes in composition table | 42 |
| Independent site codes in pre-treatment environment table | 41 |
| Site × block pairs in composition data | 132 |
| Year-0 and year-3 plot identities both recorded | 497 |
| Year-0 and year-3 blocks with **exactly one** matched Control and Fence plot each | 104 |
| Sites with at least 3 eligible matched blocks | **30** |
| Primary site-level modeling train / heldout | **22 / 8** |

The original article used 41 sites and 131 experimental blocks. The released composition table contains an extra site code, `saline.us`, with year-3 but no year-0 record and no site entry in `env-param-Y0.csv`. It is unsuitable for the predeclared baseline-to-year-3 target and is not a newly independent replicate. Some sites have multiple Control plots within a block; the preregistered exact-one-per-arm requirement removes those blocks rather than selecting the best plot after outcomes are inspected.

Taxon×plot×year keys, treatment consistency, positive cover, and original file checksums passed the audit. The target uses site-level same-taxon Hellinger composition vectors, full-census positive pairwise-distance 90th percentile, and treatment differencing across Y0 and Y3. **This is community-state geometry, not physiological-niche breadth or direct A/B/M mask deletion.**

## Observed response and site-heldout prediction

Frozen site response:

```
D_site = [span(Fence,Y3) - span(Fence,Y0)]
       - [span(Control,Y3) - span(Control,Y0)]
```

Classify as increase if `D_site > 0.02`, decrease if `D_site < -0.02`, or no detectable directional difference under the declared operational tolerance otherwise. Across all 30 eligible sites, observed classes were **14 increase, 12 decrease, 4 near-zero**.

Four models were fit **only on 22 training sites**: intercept-only, abiotic Y0 baseline, biotic Y0 baseline and joint Y0 covariates; ridge alpha=10 for non-intercept models. Predictions were issued only when all four models unanimously exceeded +0.02 or all fell below −0.02. Five of eight untouched heldout sites were marked **abstain**.

| Heldout evaluation | Outcome |
|---|---:|
| Independent heldout sites | 8 |
| Models unanimous with a nonzero sign | **3 / 8** |
| Correct signed predictions | **2 / 3** |
| Wrong signed predictions | **1 / 3** |
| Abstention | **5 / 8** |
| Train-mean always-signed baseline correct | **4 / 8** |
| Train-majority-nonzero-sign baseline correct | **4 / 8** |

Every one of the three unanimously issued signs was **positive**; each was the **same positive prediction as the intercept-only training-mean comparator**. No heldout negative prediction was certified. The unanimously wrong case is `sereng.tz`: actual `D_site=-0.1263` (decrease), while all four models predicted an increase. Correct positive examples were `rook.uk` and `smith.us`. Consequently the consensus rule neither demonstrates universally correct response-direction identification nor independent incremental directional information over its simplest positive baseline.

The 2/3 conditional accuracy is **not** a calibrated estimate of external predictive reliability: only eight independent sites were evaluated, and selective abstention changes the denominator. A cross-method superiority claim is **not supported**. The originally interesting synthetic result remains a correct finite-world identification claim, but no empirical generalization to real experimental shifts follows.

## Reproduction and numerical cross-checks

- Frozen protocol: `validation/nutnet_hodapp_y3_target_v1/protocol_v1.json` (commit `b5ae8afd`).
- Main source gate: `benchmarks/nutnet_hodapp_source_byte_gate_v1.py`; both downloaded CSVs must match authoritative Dryad MD5 and size.
- Scorer: `benchmarks/nutnet_hodapp_y3_score_v1.py`, with independent site-level SHA256 holdout partition, predeclared zero tolerance, model-unanimity and all-abstention reporting.
- Source+score GitHub Actions: [run #44542335891](https://github.com/zuizui0223/eog/actions/runs/44542335891), conclusion success. Artifact ID `14538643500`, ZIP SHA-256 `88a430587245f02c93020279d6e3daa29f88d313d45c2741d7a523ac25b4bfc7`.
- Local vs Linux CI cross-check: all site outcome signs, holdout IDs, signed/abstained decisions and summary counts identical. Maximum model-prediction numerical discrepancy ≈`8.7e-16`; maximum site-response discrepancy ≈`1.2e-16`. **Full JSONs are not byte-identical** because of negligible floating-point differences.
- A second independently written distance check using SciPy `pdist` reproduced all 30 site effects to `1e-12`, and a direct regularized linear-system solve reproduced all four predictor-family outputs to `1e-11`. This was an after-result numerical audit, not independent ecological validation.

## Scientific consequence / STOPs

1. Mechanism ambiguity and target-sign ambiguity are distinct mathematical quantities, but within the declared Y3 experimental analogue unanimous fitted-model signs were **not perfectly reliable**.
2. Published NutNet evidence is useful for external response validation, but the experimental manipulations are specific to nutrient addition and vertebrate grazing reduction; they are **not ideal binary deletion of all abiotic/biotic constraints**, and spatial dispersal M is not independently observed.
3. The candidate models are exploratory prediction structures, **not a true posterior over competing ecological mechanisms**. Agreement among these models therefore does not certify mechanism-independent physical response.
4. **STOP** any post-result changes that drop the intercept family, change the sign tolerance, switch the target year, select favorable sites, or change the heldout split to rescue prediction accuracy. New experiments/independent archives and a newly frozen protocol would be required.
5. The original EOG-WF 3 scored endpoints, synthetic BAM receipts and manuscript outcomes are unchanged; this is a **separate, retrospective external-data stress test** with a preserved negative finding.
