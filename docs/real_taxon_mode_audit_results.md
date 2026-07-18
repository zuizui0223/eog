# Frozen real-taxon mode-diagnostic audit

## Status

The issue #17 audit completed successfully on the six predeclared taxon-region pairs. The GitHub Actions artifact had digest `sha256:e9045d7800a0380b6c77f541449f9aa9f7cf7d13b9dc7be76a5d07ee5ef4df8e`.

- declared pairs: 6
- auditable status rows: 6
- eligible pairs: 6
- failed pairs: 0
- eligible pairs with subsampling output: 6
- completion gate: passed

All six pairs retained 240 complete CHELSA observations after the frozen occurrence filtering, deterministic 10 km thinning, and analysis cap.

## Full-sample diagnostics

| Taxon | Raw gap | Core-local bridge | K-means silhouette | Centroid separation | Within-cohort classification |
|---|---:|---:|---:|---:|---|
| *Fagus sylvatica* | 7.866 | 0.0068 | 0.390 | 1.647 | intermediate or mixed |
| *Quercus robur* | 9.245 | 0.0323 | 0.343 | 1.709 | bridge high, silhouette low |
| *Pinus sylvestris* | 9.451 | 0.0083 | 0.355 | 1.655 | intermediate or mixed |
| *Bombus terrestris* | 8.654 | 0.0058 | 0.721 | 3.736 | silhouette high, bridge low |
| *Vanessa atalanta* | 5.226 | 0.0249 | 0.453 | 2.047 | intermediate or mixed |
| *Vulpes vulpes* | 5.600 | 0.0885 | 0.537 | 2.530 | both high |

The classifications are relative within this frozen six-pair cohort. They are not universal biological thresholds.

## Subsampling behavior

K-means silhouette was comparatively stable under repeated 80% subsampling. Its full-sample values were generally close to the subsampling medians, with narrow 10–90% intervals.

The core-local bridge score was less stable. In particular, its upper subsampling tails were much wider than its full-sample values for several taxa. This is consistent with the statistic depending on a single retained core bridge and means it should not be interpreted from one fitted value without a stability interval.

Examples:

- *Bombus terrestris*: silhouette median 0.718, 10–90% interval 0.703–0.736; core-bridge median 0.0094, interval 0.0050–0.0645.
- *Quercus robur*: silhouette median 0.391, interval 0.354–0.558; core-bridge median 0.0405, interval 0.0093–0.0935.
- *Vulpes vulpes*: silhouette median 0.526, interval 0.469–0.596; core-bridge median 0.0268, interval 0.0099–0.1045.

## Interpretation

The two diagnostics do not provide interchangeable rankings in real ecological state clouds.

- A high forced two-cluster silhouette can occur without a strong density-core bridge, as in *Bombus terrestris*.
- A relatively strong density-core bridge can occur with a weak forced two-cluster silhouette, as in *Quercus robur*.
- Agreement can occur, as in *Vulpes vulpes*, but this small exploratory cohort cannot establish biological meaning.

Therefore:

1. no combined winner or tuned ensemble is supported;
2. silhouette should be described as evidence for a compact two-group partition;
3. the core-local bridge score should be described as evidence for a balanced bridge separating dense core regions;
4. both require subsampling intervals;
5. neither establishes multiple niches, fragmented geographic populations, or causal ecological mechanisms.

The next validation step must be outcome-based: determine whether either diagnostic improves prospective survey-patch selection against observed detections, rather than expanding the taxon cohort solely to obtain more descriptive metric values.
