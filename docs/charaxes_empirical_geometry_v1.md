# First real-data EOG resource-geometry readout: Charaxes

## What was actually executed
The old v1 schema run40862766046 returned HTTP406 before any file payload. Separately committed transport v2 changed only Accept to */* at the same Zenodo20525795 URLs. Run42220224476 succeeded: both files are text/plain; exact original sizes and MD5s match. This supports content-negotiation failure, not unavailable ecological data. Prior STOP is preserved. Verified source bytes are cached in artifact13503530806; later analyses do not redownload from Zenodo.

## Actual source grain
The original reduced CSV contains **1544 unique trap_ID records in 2018–2021**, **167 detection-positive records**, **1377 nondetections**, **417 individuals**, and **26 districts**. No missing cells or inconsistency between positive counts and the supplied occupancy flag. Public source description reports1666 traps over seven years; the released reduced file is a narrower subset. Exclusions and later-year differences are not reconstructed. Unique trap IDs do not prove spatial independence.

## Original EOG integration
Primary feature space: log1p host cover within5km (%) and log1p nearest-host distance(km). Two fixed sensitivity panels add the published host-connectivity index or local0.5km host cover. These are resource/landscape proxies, not independent A/B/M measurements. There is no climate or coordinate field; no geographic topology or true dispersal inference is attempted.

All groups share one reference per panel. Host cover is zero in873/1544 records at5km and1389/1544 at0.5km. MAD is therefore zero despite genuine variation. The contract specifies full-survey SD scaling after log1p, retaining the fixed-reference principle without erasing a zero-inflated feature. Core EOG code is unchanged; parity tests compare span, MST compactness and gap with the original comparative API under this same external reference. Centroid dispersion is a simple comparator, not an EOG novelty claim.

167 detected records are compared against999 equal-size draws: (1) unrestricted all-survey draw, (2) district×year×oak-species matched draws. Conditional counts are retained in68 detection-containing strata among160 total strata. The same draws are used across panels. These are sampling reference distributions, not confidence intervals on population effects. Conditional randomization assumes within-stratum exchangeability; residual spatial correlation and unequal trap effort remain possible.

## Results (exploratory, not independent confirmation)
Under district/year/oak matching in the primary panel:

| Quantity | Observed / matched-null median | Exploratory two-sided MC p |
|---|---:|---:|
| EOG90% pairwise span |0.9648758311|0.146|
| Mean distance to centroid |0.8898732025|0.002|
| MST compactness |0.9715703152|0.332|
| MST largest/median-edge gap |1.0186168666|0.950|

Primary breadth contraction is **not supported at a conventional5% threshold**; this is not an equivalence claim. The clearer secondary association is lower average centroid dispersion (about11%). Its unadjusted Monte Carlo p is0.002; a conservative post-hoc Bonferroni over all24 reported metric×panel×null comparisons is0.048, conditional on the unverified exchangeability assumptions. Do not select this secondary endpoint and relabel it primary.

Adding connectivity or local cover creates apparent unconditional span enlargement (1.1907× or1.2044×). After district/year/oak matching these ratios are0.9675 and0.9926, with MC p0.200 and0.738. This is a concrete sampling-composition warning, not proof of resource-driven niche broadening.

Deleting each district, while holding the original full-survey reference fixed, gives smaller primary span ratios in25/26 checks; ratios range0.94387–1.00932. These are dependent sensitivity checks, not26 independent replications or25 significant tests.

## Defensible conclusion
The observed capture cloud can differ in average concentration without a clearly supported shift in its upper pairwise extent. Breadth, dispersion and separation are different readouts. This supplies a real-data demonstration of the original EOG multi-summary logic, **not evidence that EOG beats a centroid statistic**, reconstructs causal BAM axes, or measures true occupancy.

This source does not provide direct abiotic tolerance, independently measured movement, coordinates, or effort/detection replicates. There is no new causal full-BAM validation, no new EOG-WF endpoint4, and no replacement of the closed3/31/3 evidence.

## Reproduce offline
Use the original verified reduced CSV (SHA2569338e8f064079c7f9694a55d9b948afedd93b9ac74c771befcbff48218376cd8):

```bash
python benchmarks/charaxes_empirical_geometry_v1.py --source C_jasius_reduced_dataset.csv --output-dir results
```

The analysis contract was committed at3ff68b0a6418917922926b63e118d53d9981d9e0 after schema/QC but before these geometry scores. It is explicitly retrospective/exploratory because published biological associations were already known. All24 contrasts,999 draws per null/panel, and26 leave-one-district checks are retained. Local full result JSON SHA256:ba72635150c62e792ec61a3477b25c37154ef6cb6ccf298138461f34e8334cb8. CI verifies numeric parity, not an unproven cross-platform byte identity.
