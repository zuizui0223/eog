# Non-island external validation freeze

This document freezes the next external-validation stage before any EOG outcome is calculated on the selected non-island systems.

## Motivation

The original EOG problem is not island-specific. A pointwise SDM or support surface can assign the same local support to two sites while ignoring whether those sites occupy different structural positions relative to the realized distribution. Islands make this mismatch obvious, but the same problem occurs in habitat fragments separated by agricultural, urban, forest, or otherwise unsuitable matrix.

The external-validation goal is therefore to test whether EOG structural information remains useful outside true islands after conditioning on local support and simple geographic distance to known occurrences.

## Validation track A: fully spatial fragmentation benchmark

Primary generality benchmark: Brodie & Newmark, *Heterogeneous matrix habitat drives species occurrences in complex, fragmented landscapes* (American Naturalist; Dryad DOI 10.5061/dryad.p042h0c).

Published data provide:

- 43 bird species occurrence data (`spp_occur.csv`);
- fragment/site information (`Sites.csv`);
- graph/node coordinates for eastern and western landscapes (`Nodes_E.csv`, `Nodes_W.csv`);
- matrix rasters (`raster_east3.tif`, `raster_west3.tif`);
- the authors' analysis scripts.

Role in EOG validation: demonstrate that the same structural machinery works in terrestrial forest fragments rather than true islands. This track is a generality benchmark, not a plant-specific benchmark.

No EOG result from this dataset has been inspected at the time of this freeze.

## Validation track B: plant-specific fragmentation benchmark

Primary plant candidate: Belinchón, Hemrová & Münzbergová, *Functional traits determine why species belong to the dark diversity in a dry grassland fragmented landscape* (Oikos 2020; Dryad DOI 10.5061/dryad.jh9w0vt8f).

The study comprises all 272 dry-grassland patches in a ca. 70 km² Czech agricultural landscape and 95 dry-grassland vascular plant species. Repeated field visits were used to establish patch-level adult presence/absence. Published local abiotic predictors are potential direct solar irradiation in June, topographic wetness index, slope, and relative elevation; patch area and present/historical isolation were treated by the original authors as landscape-configuration variables rather than abiotic predictors.

Role in EOG validation: test the original biological problem directly in plants: species can be absent from apparently suitable habitat because local environmental filtering and dispersal/landscape filtering are distinct.

This track is conditional on recovery of patch geometry or coordinates sufficient to construct a pairwise structural graph. Scalar isolation indices alone are not sufficient for an EOG graph benchmark. If the archived workbook does not contain recoverable patch geometry, the dataset remains a biological replication/interpretation dataset rather than the primary graph-performance benchmark.

No EOG result from this dataset has been inspected at the time of this freeze.

## Frozen evaluation principle

For every external system with sufficient geometry, the primary comparison remains the same conceptual test as in A-Islands:

1. fit or ingest a local support model using only local habitat/environment predictors;
2. hold out spatial units without using held-out labels for fitting, scaling, anchor construction, or graph tuning;
3. derive simple nearest-training-occurrence distance;
4. derive EOG reachability from the predeclared fragment graph;
5. compare occupied and unoccupied held-out units within strata matched on local support and nearest-occurrence distance;
6. use conditional concordance with null 0.5 as the primary structural endpoint.

A positive result means structural position adds information conditional on local support and simple distance. It does not prove a realized dispersal path, colonisation probability, demographic connectivity, or causal barrier.

## Predictor separation rule

Variables used to define local support must not also be silently reused as structural outcomes. Local environmental/habitat predictors and landscape-configuration predictors are declared separately before outcomes.

For the Czech grassland system, the frozen local environmental set is:

- June potential direct solar irradiation;
- topographic wetness index;
- slope;
- relative elevation.

Patch area, present-day isolation, historical area, historical isolation, and patch age are excluded from the primary local-support model. They may be used only as prespecified structural or explanatory secondary variables after the primary EOG result is fixed.

## Species eligibility

Species-level performance is estimated only for taxa with enough occupied and unoccupied units to support spatial holdout. The default pre-outcome rule is at least 10 occupied and 10 unoccupied evaluated units. No species is retained or excluded using an EOG score or held-out performance.

## Decision rule

EOG generality outside islands is supported if a non-island fragmented system shows conditional concordance above 0.5 after matching on local support and nearest-training-occurrence distance, with uncertainty calculated over species where multiple species are available.

Failure to exceed 0.5 is retained as a valid falsification of generality in that system and does not trigger graph-radius, predictor, or species-selection tuning.