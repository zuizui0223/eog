# Czech dry-grassland public patch-level covariate source

This document freezes a secondary public source for the same 272-patch Czech dry-grassland system before any non-island EOG outcome is inspected.

## Source identity

Belinchón, Hemrová & Münzbergová (2019), *Abiotic, present-day and historical effects on species, functional and phylogenetic diversity in dry grasslands of different age*, PLOS ONE 14(10): e0223826, DOI `10.1371/journal.pone.0223826`.

The paper states that its Supporting Information contains **S4 Table**, a text database of dry-grassland patch characteristics including environmental, present-day and historical variables as well as diversity indices. The Data Availability statement says the relevant data are contained in the manuscript and Supporting Information.

## Frozen system facts from the published Methods

- study system: 272 dry-grassland patches in an approximately 8 × 8 km landscape in northern Bohemia, Czech Republic;
- current dry grasslands occupy small fragments totaling about 4% of the study area;
- patch-level abiotic variables include slope, potential direct solar irradiation, topographic wetness index and relative elevation derived from a 10 m DEM;
- present-day isolation was defined from all surrounding patches within **0.5 km**, using surrounding patch area `A_k` and edge-to-edge distance `d_jk` as `I_j = -log(sum(A_k / d_jk^2))`;
- present-day and historical landscape configuration were analyzed separately from local abiotic variables.

## Role in EOG validation

This source may be used to recover or cross-check patch-level covariates and patch IDs while the Dryad Oikos workbook remains unavailable to hosted CI. It is **not** allowed to replace true graph geometry with a scalar isolation index.

A full EOG graph remains permitted only if one of the following is available and reproducibly linked to patch IDs:

1. patch coordinates;
2. patch boundaries;
3. an explicit pairwise distance or adjacency representation.

The published 500 m isolation radius remains the primary graph scale if geometry is recovered, with 250 / 500 / 1000 m already frozen as sensitivity scales in `docs/czech_grassland_geometry_contract.md`.

## Leakage boundary

The S4 patch table contains diversity outcomes in addition to covariates. Any future ingestion must explicitly select only predeclared patch identifiers and abiotic/landscape covariate columns for geometry/support preparation before species-level occurrence outcomes are joined. Diversity-index columns must not influence graph construction, species eligibility, local-support tuning or threshold selection.

## Scientific boundary

This document does not inspect species-level EOG performance, retain or exclude taxa, fit a support model, construct a graph, or calculate conditional concordance/bottleneck statistics. It only freezes the identity and allowed role of a public patch-level source.