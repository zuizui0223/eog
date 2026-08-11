# Frozen structural results tables

These tables are generated from frozen Figure 2/3 evidence. They are not manually transcribed and do not refit either benchmark.

## Table 3. Main and predeclared sensitivity results

| system | analysis | metric | n_species | n_matched | effect | ci_low | ci_high | null_value | sign_flip_p | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-Islands | Combined connected frequency | conditional concordance | 845 |  | 0.617747 | 0.608681 | 0.626944 | 0.500000 | 0.00001000 | favourable |
| A-Islands | Geography-only connected frequency | conditional concordance | 845 |  | 0.614746 | 0.605950 | 0.623573 | 0.500000 |  | favourable |
| A-Islands | Environmentally constrained connected frequency | conditional concordance | 845 |  | 0.606373 | 0.597487 | 0.615419 | 0.500000 |  | favourable |
| A-Islands | Normalized geographic bottleneck | conditional concordance | 793 |  | 0.528772 | 0.517726 | 0.539568 | 0.500000 |  | favourable |
| Tanzania | Primary weighting \| LOSO | log loss difference | 60 | 826 | 0.032113 | 0.017458 | 0.048675 | 0.000000 | 0.00003000 | adverse |
| Tanzania | Primary weighting \| LOSO | Brier difference | 60 | 826 | 0.004799 | 0.002281 | 0.007315 | 0.000000 | 0.00010999 | adverse |
| Tanzania | Inverse-area sensitivity \| LOSO | log loss difference | 60 | 826 | 0.031624 | 0.016405 | 0.047697 | 0.000000 | 0.00002000 | adverse |
| Tanzania | Inverse-area sensitivity \| LOSO | Brier difference | 60 | 826 | 0.004813 | 0.002344 | 0.007331 | 0.000000 | 0.00011999 | adverse |
| Tanzania | Primary weighting \| spatial MST blocks | log loss difference | 60 | 718 | 0.007305 | -0.006971 | 0.021412 | 0.000000 | 0.30516474 | uncertain |
| Tanzania | Primary weighting \| spatial MST blocks | Brier difference | 60 | 718 | 0.000370 | -0.001913 | 0.002598 | 0.000000 | 0.75751212 | uncertain |
| Tanzania | Inverse-area sensitivity \| spatial MST blocks | log loss difference | 60 | 718 | 0.007913 | -0.006104 | 0.021987 | 0.000000 | 0.26880656 | uncertain |
| Tanzania | Inverse-area sensitivity \| spatial MST blocks | Brier difference | 60 | 718 | 0.000490 | -0.001733 | 0.002711 | 0.000000 | 0.67591620 | uncertain |

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
