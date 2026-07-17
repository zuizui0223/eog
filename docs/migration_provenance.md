# Extraction provenance

Environmental Occupancy Geometry (EOG) was developed inside `zuizui0223/acsp` and extracted into this standalone repository after the numerical API was frozen.

## Source checkpoints

- ACSP PR #35: original implementation and validation workflows.
- ACSP main commit `cfa24ba30fa0607e530d5cf716ce8729d54d773e`: implementation copied into the first standalone EOG package.
- ACSP main commit `3d2017e9a342eca13f0a17f1d3c473a993c4335a`: frozen API contract and edge-case tests.

## Compatibility rule

EOG 0.1.x preserves the following public objects and numerical definitions:

- `OccupancyGeometry`
- `robust_scale`
- `pairwise_distances`
- `minimum_spanning_tree`
- `infer_occupancy_geometry`
- `project_states`

Breaking changes require an explicit major or pre-1.0 compatibility decision and updated frozen fixtures.

## Repository responsibility

This repository owns:

- EOG numerical implementation;
- EOG API and tests;
- synthetic and real-taxon method benchmarks;
- novelty audit and manuscript materials;
- EOG releases and software citation.

ACSP owns survey prioritization, candidate generation, SDM/SSDM support, field logistics, and prospective field validation. ACSP does not vendor or maintain a duplicate EOG implementation after extraction.
