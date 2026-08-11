# Proposed supplementary materials

This file defines the submission supplement from analyses and audit outputs that already exist. It does not authorize a new post-outcome analysis.

## Supplementary Table S1 — Applicability and non-estimability accounting

Authoritative machine-readable source:

- `manuscript/result_tables/table_s1_applicability_accounting.csv`

The table retains A-Islands primary/bottleneck non-estimability and Tanzania LOSO/spatial-block matched and invalid counts. Failure categories must not be collapsed or silently removed during journal formatting.

## Reproducibility appendix — source-to-result audit

Primary source files:

- `figures/figure_5_audit_contract.json`
- `figures/output/figure_5_metadata.json`
- `manuscript/figure_5_caption.md`
- `manuscript/figure_5_accessibility.md`
- `manuscript/result_tables/structural_results_tables_metadata.json`

If Figure 5 is moved from the main paper to the supplement during editorial formatting, its claim boundary must remain unchanged: fingerprints document provenance and rebuildability, not ecological causality or preregistration.

## Machine-readable figure data

Archive the exact plotted sidecars with the paper/release:

- Figure 2:
  - `manuscript/figure_data/aislands_species_concordance.csv`
  - `manuscript/figure_data/aislands_mode_estimates.csv`
  - `manuscript/figure_data/aislands_applicability.csv`
  - `manuscript/figure_data/aislands_fold_coverage.csv`
- Figure 3:
  - `manuscript/figure_data/tanzania_species_loso_effects.csv`
  - `manuscript/figure_data/tanzania_aggregate_contrasts.csv`
  - `manuscript/figure_data/tanzania_applicability.csv`
- Figure 4:
  - `manuscript/figure_data/structural_cross_system_evidence.csv`

These data are derived projections for the manuscript figures. They do not replace citation of the original A-Islands, CHELSA, or Tanzania source data.

## Machine-readable main results

- `manuscript/result_tables/table_3_main_sensitivity_results.csv`
- `manuscript/result_tables/table_s1_applicability_accounting.csv`
- `manuscript/result_tables/result_table_manifest.json`
- `manuscript/result_tables/structural_results_tables_metadata.json`

## Extended computational contracts

The archival release should retain, rather than reformat away, the existing contracts and audit documents needed to reconstruct design timing and claim boundaries, including:

- A-Islands authoritative contracts and frozen benchmark projections;
- Tanzania source, geometry/formula, current-flow selection, held-out scoring, and clustered-inference contracts;
- structural competitor matrix;
- figure manifests and result fingerprints;
- CI tests that enforce negative and non-estimable outcomes.

These files are code/reproducibility supplements, not additional ecological results.

## Items not to introduce as retrospective supplement analyses

Do not add trait-specific radii, directional edges, alternative weighting selected from the Tanzania outcome, new graph scales, or post-outcome subgroup screens as confirmatory supplementary evidence. Such variants require a separately frozen prospective analysis and must leave the current Tanzania result visible.
