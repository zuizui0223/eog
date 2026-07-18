# Verified real-taxon pilot results

The frozen pilot in `benchmarks/real_taxon_pilot_manifest.csv` was executed by GitHub Actions run `29633686806` from commit `464f1794294e8a52d2c7124e0904160da365f0f6`. The workflow artifact digest was `sha256:1fdbc3f0be2808fce30259846ce3cf99460085c63848bb7043c761f00634f4e4`.

## Pipeline gate

- declared taxon-region pairs: 6;
- status rows produced: 6;
- technically eligible pairs: 6;
- failed pairs: 0;
- ineligible pairs: 0;
- eligible pairs with thinning-stability output: 6;
- pilot gate: passed.

All pairs retained 240 complete CHELSA rows after deterministic 10 km thinning and the fixed analysis cap.

## Pair-level results

| Pair | Raw coordinates | Span | Continuity | Gap strength | Calibrated gap percentile |
|---|---:|---:|---:|---:|---:|
| *Fagus sylvatica*, Europe | 2613 | 4.717 | 0.075 | 7.866 | 1.000 |
| *Quercus robur*, Europe | 2439 | 5.208 | 0.124 | 9.245 | 1.000 |
| *Pinus sylvestris*, Europe | 2355 | 4.658 | 0.101 | 9.451 | 1.000 |
| *Bombus terrestris*, Europe | 2001 | 11.300 | 0.110 | 8.654 | 1.000 |
| *Vanessa atalanta*, Europe | 2613 | 5.805 | 0.092 | 5.226 | 1.000 |
| *Vulpes vulpes*, Europe | 2241 | 5.557 | 0.103 | 5.600 | 1.000 |

The calibrated percentile used 40 connected Gaussian reference clouds matched on sample size, feature dimension, mean, and covariance. A value of 1.0 means that the observed raw gap exceeded every generated reference value; it is not a posterior probability that the ecological distribution is fragmented.

## Repeated 80% thinning stability

Across 120 subsamples, the overall medians were:

- span relative error: 0.0271;
- continuity absolute error: 0.0139;
- gap-strength relative error: 0.1040.

The overall 90th percentiles were:

- span relative error: 0.0786;
- continuity absolute error: 0.0204;
- gap-strength relative error: 0.2585.

Pair-level median gap relative errors ranged from about 0.067 to 0.153. Pair-level 90th-percentile gap errors ranged from about 0.144 to 0.390. Gap strength is therefore less thinning-stable than span and continuity in this pilot and must retain an explicit stability analysis in the manuscript-scale cohort.

## Interpretation boundary

This pilot verifies that the standalone pipeline can retrieve GBIF records, apply the frozen spatial thinning and CHELSA variable rules, compute raw and calibrated EOG quantities, and retain all declared outcomes without taxon replacement.

It does not establish cross-taxon generality. The cohort is small, geographically concentrated in Europe, and deliberately uses common well-recorded taxa. The universal 1.0 calibrated percentiles also indicate that a single moment-matched Gaussian connected-null may be too restrictive for real ecological clouds. The next validation must compare multiple connected-null families before treating the calibrated percentile as the primary manuscript statistic.
