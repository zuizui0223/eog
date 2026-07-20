# Real-taxon demonstration: diagnostic disagreement in observed environmental-state geometry

## Purpose

This case study demonstrates why environmental point-cloud diagnostics must be interpreted as separate estimands. It is not a species-level inference about niche multiplicity, fragmentation, missing support, or ecological mechanism.

## Frozen analysis provenance

The archived values were produced by GitHub Actions workflow `Real-taxon mode audit`, run ID `29691009988`, from commit `13cb6b5f5c45ad06851d0b8c6b19c2fb0c60785e`. The successful artifact had SHA-256 digest `ece12e504c8264306784c2f8f92090af3104d5351d2f9b0f9666f3ef5b5f7ede`.

The declared taxa and geographic windows are stored in `benchmarks/real_taxon_pilot_manifest.csv`. The audit:

- retrieved coordinate-bearing occurrences from GBIF;
- thinned records at 10 km;
- capped each taxon at 240 analysis records;
- sampled CHELSA variables `bio1`, `bio4`, `bio12`, and `bio15`;
- required at least 60 complete records;
- used seed `20261015`;
- used 20 subsampling repeats at an 0.8 fraction.

All six declared taxa were eligible. No taxon failed and no taxon was excluded for insufficient complete CHELSA records. The completion decision and exact summary are archived in `benchmarks/expected/real_taxon_mode_decision.json` and `benchmarks/expected/real_taxon_mode_summary.csv`.

## Verified results

| Taxon | Complete n | Gap strength | Core-bridge score | Core-bridge subsample median [p10, p90] | K-means silhouette | Silhouette subsample median [p10, p90] | Cohort agreement class |
|---|---:|---:|---:|---:|---:|---:|---|
| *Fagus sylvatica* | 240 | 7.866 | 0.0068 | 0.0095 [0.0083, 0.0534] | 0.390 | 0.394 [0.358, 0.421] | intermediate or mixed |
| *Quercus robur* | 240 | 9.245 | 0.0323 | 0.0405 [0.0093, 0.0934] | 0.343 | 0.391 [0.354, 0.558] | bridge high, silhouette low |
| *Pinus sylvestris* | 240 | 9.451 | 0.0083 | 0.0187 [0.0080, 0.0296] | 0.355 | 0.356 [0.346, 0.470] | intermediate or mixed |
| *Bombus terrestris* | 240 | 8.654 | 0.0058 | 0.0094 [0.0050, 0.0645] | 0.721 | 0.718 [0.703, 0.736] | silhouette high, bridge low |
| *Vanessa atalanta* | 240 | 5.226 | 0.0249 | 0.0205 [0.0086, 0.0647] | 0.453 | 0.443 [0.412, 0.463] | intermediate or mixed |
| *Vulpes vulpes* | 240 | 5.600 | 0.0885 | 0.0268 [0.0099, 0.1045] | 0.537 | 0.526 [0.469, 0.596] | both high |

## Informatics interpretation

The principal result is disagreement, not a taxonomic ranking.

- *Quercus robur* ranked high for the density-trimmed core-local-bridge score but low for K-means silhouette.
- *Bombus terrestris* showed the reverse pattern: high silhouette and low core-bridge evidence.
- *Vulpes vulpes* ranked high for both diagnostics.

These patterns demonstrate that silhouette and core-bridge evidence are not interchangeable summaries. Silhouette describes partition compactness and separation under a K-means representation. The core-bridge score describes a local density-trimmed bridge pattern. A taxon can score highly on one without scoring highly on the other because the methods ask different geometric questions.

Subsampling intervals also differ in width. For example, the silhouette estimate for *Bombus terrestris* remained narrowly high across subsamples, whereas the core-bridge intervals for several taxa were broad relative to their full-data values. This supports reporting diagnostic-specific stability rather than replacing multiple quantities with a composite score.

## Permitted claims

The case study supports the following statements:

1. all six declared workflows completed with the predeclared minimum sample size;
2. diagnostic rankings differed among silhouette and core-bridge evidence;
3. diagnostic-specific subsampling stability differed among taxa;
4. claim-limited reporting is necessary because the diagnostics measure different geometric properties.

## Prohibited claims

The case study does not establish that any taxon:

- occupies multiple ecological niches;
- has fragmented or disconnected environmental support;
- contains a missing environmental bridge;
- is more specialized, adaptable, or vulnerable than another taxon;
- has a biologically meaningful cluster structure;
- differs causally because of taxonomy, geography, or life history.

## Manuscript-ready result paragraph

A frozen real-data demonstration was conducted using six European plant and animal taxa. After 10-km thinning and a cap of 240 complete CHELSA records per taxon, all six analyses completed successfully. The diagnostic rankings were not interchangeable. *Quercus robur* was classified as high for core-local-bridge evidence but low for K-means silhouette, whereas *Bombus terrestris* showed high silhouette and low core-bridge evidence; *Vulpes vulpes* ranked high for both. Subsampling intervals likewise differed among diagnostics and taxa. These results are not evidence of multiple niches or environmental fragmentation. They show that established point-cloud diagnostics answer distinct geometric questions on real occurrence–environment data and should therefore be reported separately with metric-specific claim limits.

## Figure 4 specification

Figure 4 should contain:

- panel A: the six taxa ordered by K-means silhouette with subsampling p10–p90 intervals;
- panel B: the same taxa ordered by core-bridge score with subsampling p10–p90 intervals;
- panel C: a rank-rank comparison highlighting *Q. robur*, *B. terrestris*, and *V. vulpes*;
- panel D: a claim-boundary box distinguishing geometric diagnostic disagreement from biological inference.

## Reproducibility limitation and next step

The archived summary is traceable to one successful workflow artifact, but the workflow retrieves live GBIF records and samples external CHELSA rasters. Re-running it later may therefore change the occurrence set even with the same random seed. This demonstration is suitable as a frozen audit result, not yet as a fully input-fingerprinted confirmatory comparison.

The next step is to archive the exact thinned coordinate and CHELSA feature matrices for a smaller declared comparison, assign row-level fingerprints, fit one explicit shared reference, and execute the comparison through `AnalysisManifest` and the audited runner. That future analysis should address comparative extent; the present case study addresses disagreement among descriptive separation diagnostics.
