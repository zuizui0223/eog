# Frozen structural results tables

These tables are generated from frozen original A-Islands, prospective A-Islands strong-reference, and Tanzania evidence. They are not manually transcribed and do not refit any benchmark.

## Table 3. Main and predeclared sensitivity results

| system | analysis | metric | n_species | n_matched | effect | ci_low | ci_high | null_value | sign_flip_p | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-Islands | Combined connected frequency | conditional concordance | 845 |  | 0.617747 | 0.608681 | 0.626944 | 0.500000 | 0.00001000 | favourable |
| A-Islands | Geography-only connected frequency | conditional concordance | 845 |  | 0.614746 | 0.605950 | 0.623573 | 0.500000 |  | favourable |
| A-Islands | Environment-constrained connected frequency | conditional concordance | 845 |  | 0.606373 | 0.597487 | 0.615419 | 0.500000 |  | favourable |
| A-Islands | Normalized geographic bottleneck secondary | conditional concordance | 793 |  | 0.528772 | 0.517726 | 0.539568 | 0.500000 |  | favourable |
| A-Islands | Prospective strong island reference \| C vs R3 | log loss difference | 886 | 712515 | 0.003485 | 0.002466 | 0.004508 | 0.000000 | 0.00001000 | adverse |
| A-Islands | Prospective strong island reference \| C vs R3 | Brier difference | 886 | 712515 | 0.000268 | 0.000079 | 0.000457 | 0.000000 | 0.00561994 | adverse |
| Tanzania | Primary weighting \| LOSO | log loss difference | 60 | 826 | 0.032113 | 0.017458 | 0.048675 | 0.000000 | 0.00003000 | adverse |
| Tanzania | Primary weighting \| LOSO | Brier difference | 60 | 826 | 0.004799 | 0.002281 | 0.007315 | 0.000000 | 0.00047999 | adverse |
| Tanzania | Inverse-area weighting \| LOSO | log loss difference | 60 | 826 | 0.030630 | 0.016214 | 0.046937 | 0.000000 | 0.00003000 | adverse |
| Tanzania | Inverse-area weighting \| LOSO | Brier difference | 60 | 826 | 0.004668 | 0.002309 | 0.007025 | 0.000000 | 0.00040000 | adverse |
| Tanzania | Primary weighting \| spatial MST blocks | log loss difference | 60 | 718 | 0.010954 | -0.012171 | 0.033431 | 0.000000 | 0.35657643 | uncertain |
| Tanzania | Primary weighting \| spatial MST blocks | Brier difference | 60 | 718 | 0.000965 | -0.006417 | 0.008239 | 0.000000 | 0.79920201 | uncertain |
| Tanzania | Inverse-area weighting \| spatial MST blocks | log loss difference | 60 | 718 | 0.005702 | -0.015533 | 0.025824 | 0.000000 | 0.59587404 | uncertain |
| Tanzania | Inverse-area weighting \| spatial MST blocks | Brier difference | 60 | 718 | 0.001179 | -0.006963 | 0.008866 | 0.000000 | 0.77570224 | uncertain |

The original A-Islands rows use conditional concordance with null 0.5. The prospective A-Islands strong-reference and Tanzania rows use candidate-minus-reference predictive-loss differences with null 0; negative values favour adding EOG. These endpoints are not a common effect-size scale.

## Table S1. Predeclared non-estimability accounting

| system | analysis | partition | status | count |
| --- | --- | --- | --- | --- |
| A-Islands | bottleneck_secondary | ALL | evaluable | 2591 |
| A-Islands | bottleneck_secondary | ALL | no_finite_comparable_pairs_within_frozen_strata | 1640 |
| A-Islands | bottleneck_secondary | ALL | insufficient_training_classes | 199 |
| A-Islands | primary_combined | ALL | evaluable | 3041 |
| A-Islands | primary_combined | ALL | no_comparable_pairs_within_frozen_strata | 1190 |
| A-Islands | primary_combined | ALL | insufficient_training_classes | 199 |
| A-Islands | isolation_adequacy_C_vs_R3 | ALL | evaluable_folds | 4231 |
| A-Islands | isolation_adequacy_C_vs_R3 | ALL | insufficient_training_class_count_5_5 | 199 |
| Tanzania | primary::primary_loso | ALL | matched | 826 |
| Tanzania | primary::primary_loso | ALL | invalid | 14 |
| Tanzania | inverse_area_sensitivity::primary_loso | ALL | matched | 826 |
| Tanzania | inverse_area_sensitivity::primary_loso | ALL | invalid | 14 |
| Tanzania | primary::spatial_mst_block | ALL | matched | 718 |
| Tanzania | primary::spatial_mst_block | ALL | invalid | 122 |
| Tanzania | inverse_area_sensitivity::spatial_mst_block | ALL | matched | 718 |
| Tanzania | inverse_area_sensitivity::spatial_mst_block | ALL | invalid | 122 |

### Claim boundaries

- The original A-Islands conditional-concordance estimate tests ordering information conditional on frozen pointwise support and nearest-training-occurrence distance.
- The prospective A-Islands C-minus-R3 estimates are paired held-out predictive-loss differences under a separately frozen stronger island reference; negative values favour EOG and positive values are adverse.
- The original A-Islands concordance and the strong-reference predictive-loss difference are different estimands and must not be compared as one effect size.
- Tanzania differences are candidate minus strong current-flow reference; negative values favour adding EOG and positive values are adverse.
- Neither table reports a dispersal, movement, colonisation, or realised-path probability.
- Non-estimable rows remain visible and are not silently dropped from applicability accounting.
