# Frozen Y3 herbivore-exclusion experimental analogue: an independent-site target-identifiability test

## Current status

Prospective protocol **frozen before viewing any row-level post-treatment composition** at `validation/nutnet_hodapp_y3_target_v1/protocol_v1.json`. The source-bounded retrieval/checksum script is an access gate. No treated site response has been scored.

**Parent:** merged EOG [PR #702](https://github.com/zuizui0223/eog/pull/702) (nonzero-direction stratification of original synthetic BAM results); merged [PR #704](https://github.com/zuizui0223/eog/pull/704) (successful Dryad metadata-only access). This new source must not be counted as another EOG-WF predictive endpoint.

## Frozen empirical basis

- Hodapp et al. (2018), *Ecology Letters*, DOI [10.1111/ele.13102](https://doi.org/10.1111/ele.13102). The published study reports **41 NutNet sites, 131 blocks, pretreatment year Y0 and 3–5 treatment years**.
- Hodapp et al. (2019), Dryad [10.5061/dryad.8vs569h](https://doi.org/10.5061/dryad.8vs569h), `composition-data.csv` and `env-param-Y0.csv`. Size and MD5 from an exact official Dryad metadata response (Actions #44524886138) are locked in the protocol. A possible Zenodo archive [5023851](https://zenodo.org/records/5023851) is not trusted until it matches original Dryad MD5 for **both** files.

The publication already reports overall treatment-associated turnover patterns; **independent-site heldout validation here is retrospective, not outcome-naïve discovery of the overall direction**. The within-site signs and detailed raw responses were not inspected when the protocol was frozen.

## Explicit target (not original environmental-niche span)

At each site, within matched blocks, compare the 90th percentile of **strictly positive pairwise Hellinger distances among plot-level species composition vectors** at year 3 versus pretreatment year 0. All species coordinates are shared at each site; plots and blocks are identical across years. The signed site outcome is the difference between the temporal span changes in Fence and Control:

```
Y_site = [Span(Fence,Y3) - Span(Fence,Y0)]
       - [Span(Control,Y3) - Span(Control,Y0)]
```

Primary sign tolerance is a frozen absolute ±0.02 Hellinger-distance units. Negative means the spatial community-state span changed less under fencing than under controls; positive means it changed more. This does **not** mean that the physiological niche of a species expanded or contracted. The predeclared secondary response is median matched-block Jaccard turnover difference, **not** a substitute.

Minimum three matched Control/Fence blocks per eligible site, complete Y0/Y3 census with stable identifiers, and minimum twenty independent eligible sites and five holdout sites. Absence is encoded only when the vegetation census is sufficiently complete; missing observations must not be converted to absence. Data-quality STOP precedes target scoring.

## Frozen model-disagreement and heldout test

The site-level heldout split uses SHA256 of site_code with fixed literal salt `EOG_NUTNET_Y3_20261119_V1|`; 25% of eligible sites are held out. Candidate models are fixed: training-site mean, ridge using Y0 abiotic environment, ridge using Y0 composition heterogeneity/richness, and ridge using both. Ridge penalty is alpha=10, features normalized with **training-site statistics only**. No holdout outcomes enter fitting, scaling, imputation or model selection.

Sign prediction for heldout site is issued only if **all four** models predict >+0.02, or **all four** predict <-0.02. Otherwise **abstain**. Report coverage, wrong-sign number, conditional correct-sign fraction, number of abstentions, and single-model baseline with **site as the independent unit**. Nonzero target-sign unanimity among candidate *prediction models* is **not proof of full causal BAM mechanism ambiguity or resolution**.

## Source gate and outcome access

`benchmarks/nutnet_hodapp_source_byte_gate_v1.py` reads only fixed official Dryad API and an explicitly declared potential Zenodo mirror; it accepts file bytes **only** if both source size and MD5 match the original authoritative manifest. It writes raw CSVs solely after integrity checks, but itself inspects only headers. It records access-denied, missing, corrupted and unverifiable-mirror scenarios as explicit `SOURCE_BYTE_STOP`.

If source bytes are unavailable or the schema does not support complete matched Y0/Y3 plot data, STOP. Do not replace the data source, response target, threshold, years, aggregation, eligibility, or holdout after reading outcomes just to obtain a positive result. The model universe is a limited family of predictor structures; it is not the original known-truth A/B/M family.

## Reproduce gate

```bash
python -m pytest -q tests/test_nutnet_hodapp_source_byte_gate_v1.py
python benchmarks/nutnet_hodapp_source_byte_gate_v1.py --output-dir /tmp/nutnet_hodapp_y3
```

Run and archived outputs are a **source-access verdict**, not predictive superiority, species-level causal effects, or any new EOG-WF scored endpoint.
