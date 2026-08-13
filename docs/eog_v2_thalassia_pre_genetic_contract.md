# EOG v2.1 Thalassia hemprichii pre-genetic admission contract

## Status

**Response-free Stage 1 only. Exact microsatellite contents are not authorized until Stage 2 predictors are byte-frozen.**

Study: Hernawan et al. (2017), *Historical processes and contemporary ocean currents drive genetic structure in the seagrass Thalassia hemprichii in the Indo-Australian Archipelago*, DOI `10.1111/mec.13966`.

Data: Dryad `10.5061/dryad.404rm`.

Dryad separates:

- `GPS site IAA.xlsx` (file-stream `28987`) — response-free sampling-site GPS metadata;
- `Genalex_Th3all_IAA.xlsx` (file-stream `28986`) — response-bearing microsatellite genotype workbook;
- `Th_SNP_data_UdhiHernawan_Chapter3.phy` — SNP sequence source, outside the primary microsatellite validation.

Dryad states that genotype site IDs correspond to the site IDs in the GPS workbook and that the microsatellite panel contains 16 markers.

## Hard response firewall

Before Stage 2 is fully frozen:

Permitted:

- download/read the full GPS workbook;
- record GPS workbook file identity, worksheet names, cells, site IDs and coordinates;
- download the microsatellite workbook as an opaque byte object only for file existence, size and SHA-256;
- delete the opaque genetic file before artifact upload.

Prohibited:

- opening the microsatellite workbook container;
- inspecting its ZIP member names, worksheet names, cell values, site/sample labels or allele values;
- computing FST, genetic distances, clusters or migration;
- reading the SNP file to reconstruct microsatellite sample identities;
- using exact published genetic values to choose nodes, graph topology, candidate references or EOG settings.

The Stage-1 audit code must not accept a genetic-file path; it receives only the already-computed opaque size/SHA-256 strings.

## Stage 1 admission

GPS metadata must mechanically provide:

- a stable site ID for each sampling site;
- finite latitude and longitude for each admitted site;
- no duplicate site ID with conflicting coordinates;
- at least 8 unique finite-coordinate sites;
- a deterministic response-free site/coordinate fingerprint.

If the workbook schema is not mechanically interpretable on the first schema audit, Stage 1 remains unresolved and the genetic workbook stays unopened internally. Any later schema adapter must be defined using the GPS workbook only.

## Stage 2 boundary

Only after Stage 1 PASS:

- freeze the complete site set and coordinates;
- freeze longitude/projection handling;
- freeze conventional candidate family at minimum `geographic`, `gabriel_shortest_path`, `gabriel_current_flow` unless one is mathematically non-applicable before response access;
- freeze exact-eventual EOG predictors on the same response-free graph;
- freeze the #143 nested outer/inner population-held-out selector;
- freeze response transform, common ridge penalty and a 10,000-population bootstrap rule;
- byte-archive the complete response-free predictor bundle.

EOG never participates in conventional-reference selection.

## Stage 3 boundary

Only after the Stage-2 bundle is archived may `Genalex_Th3all_IAA.xlsx` be opened once for a separately declared schema audit and exact symmetric microsatellite response calculation.

No post-response site deletion, graph/reference candidate removal or EOG retuning is allowed. Any GO, null, adverse, non-estimable or indeterminate result remains visible.

## Claim boundary

Primary genetics are symmetric isolation/connectivity. Pairwise FST cannot validate the study's asymmetric gene-flow/current-direction narrative; a directional endpoint would require a separate frozen contract.
