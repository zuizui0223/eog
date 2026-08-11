# Frozen structural results tables

These tables are generated from frozen Figure 2/3 evidence. They are not manually transcribed and do not refit either benchmark.

## Table 3. Main and predeclared sensitivity results

| system | analysis | metric | n_species | n_matched | effect | ci_low | ci_high | null_value | sign_flip_p | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-Islands | Combined connected frequency | conditional concordance | 845 |  | 0.617747 | 0.608681 | 0.626944 | 0.500000 | 0.00001000 | favourable |
| A-Islands | Geography-only connected frequency | conditional concordance | 845 |  | 0.614746 | 0.605950 | 0.623573 | 0.500000 |  | favourable |
| A-Islands | Environment-constrained connected frequency | conditional concordance | 845 |  | 0.606373 | 0.597487 | 0.615419 | 0.500000 |  | favourable |
| A-Islands | Normalized geographic bottleneck secondary | conditional concordance | 793 |  | 0.528772 | 0.517726 | 0.539568 | 0.500000 |  | favourable |
| Tanzania | Primary weighting \| LOSO | log loss difference | 60 | 826 | 0.032113 | 0.017458 | 0.048675 | 0.000000 | 0.00003000 | adverse |
| Tanzania | Primary weighting \| LOSO | Brier difference | 60 | 826 | 0.004799 | 0.002281 | 0.007315 | 0.000000 | 0.00047999 | adverse |
| Tanzania | Inverse-area weighting \| LOSO | log loss difference | 60 | 826 | 0.030630 | 0.016214 | 0.046937 | 0.000000 | 0.00003000 | adverse |
| Tanzania | Inverse-area weighting \| LOSO | Brier difference | 60 | 826 | 0.004668 | 0.002309 | 0.007025 | 0.000000 | 0.00040000 | adverse |
| Tanzania | Primary weighting \| spatial MST blocks | log loss difference | 60 | 718 | 0.010954 | -0.012171 | 0.033431 | 0.000000 | 0.35657643 | uncertain |
| Tanzania | Primary weighting \| spatial MST blocks | Brier difference | 60 | 718 | 0.000965 | -0.006417 | 0.008239 | 0.000000 | 0.79920201 | uncertain |
| Tanzania | Inverse-area weighting \| spatial MST blocks | log loss difference | 60 | 718 | 0.005702 | -0.015533 | 0.025824 | 0.000000 | 0.59587404 | uncertain |
| Tanzania | Inverse-area weighting \| spatial MST blocks | Brier difference | 60 | 718 | 0.001179 | -0.006963 | 0.008866 | 0.000000 | 0.77570224 | uncertain |

A-Islands uses conditional concordance with null 0.5. Tanzania uses candidate-minus-reference differences with null 0; negative values favour adding EOG to the strong current-flow reference.

## Table S1. Predeclared non-estimability accounting

| system | analysis | partition | status | count |
| --- | --- | --- | --- | --- |
| A-Islands | primary_combined | ALL | evaluable | 3041 |
| A-Islands | primary_combined | ALL | no_comparable_pairs_within_frozen_strata | 1190 |
| A-Islands | primary_combined | ALL | insufficient_training_classes | 199 |
| A-Islands | bottleneck_secondary | ALL | evaluable | 2591 |
| A-Islands | bottleneck_secondary | ALL | no_comparable_pairs_within_frozen_strata | 1640 |
| A-Islands | bottleneck_secondary | ALL | insufficient_training_classes | 199 |
| Tanzania | primary::primary_loso | ALL | matched | 826 |
| Tanzania | primary::primary_loso | ALL | invalid | 14 |
| Tanzania | inverse_area_sensitivity::primary_loso | ALL | matched | 826 |
| Tanzania | inverse_area_sensitivity::primary_loso | ALL | invalid | 14 |
| Tanzania | primary::spatial_mst_block | ALL | matched | 718 |
| Tanzania | primary::spatial_mst_block | ALL | invalid | 122 |
| Tanzania | inverse_area_sensitivity::spatial_mst_block | ALL | matched | 718 |
| Tanzania | inverse_area_sensitivity::spatial_mst_block | ALL | invalid | 122 |

### Claim boundaries

- A-Islands estimates test added held-out structural information conditional on frozen pointwise support and nearest-training-occurrence distance.
- Tanzania differences are candidate minus strong current-flow reference; negative values favour adding EOG and positive values are adverse.
- Neither table reports a dispersal, movement, colonisation, or realised-path probability.
- Non-estimable rows remain visible and are not silently dropped from applicability accounting.
