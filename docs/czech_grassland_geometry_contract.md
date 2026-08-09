# Czech dry-grassland geometry contract

This contract freezes the structural interpretation of the Belinchón–Hemrová–Münzbergová 272-patch dry-grassland benchmark **before any species-level EOG outcome is inspected**.

The benchmark is intended to test whether a structural reachability layer can add information beyond local environmental support in a fragmented **non-island** plant landscape. It is not intended to re-label the published isolation index as EOG connectivity.

## Frozen source and integrity gate

The source dataset is Dryad `10.5061/dryad.jh9w0vt8f`, associated with *Functional traits determine why species belong to the dark diversity in a dry grassland fragmented landscape*.

The workbook identity was frozen independently before this contract:

- file: `Belinchón.et.al.Oikos2020.data.xlsx`;
- size: 75,727 bytes;
- SHA-256: `ddc63118750c4685ec4ab35560299de312c57a8a120a71b27f31d94193e37867`.

No workbook-derived geometry may be used unless the supplied bytes pass that exact integrity gate.

## Published spatial definition

The published 272-patch system defines landscape configuration from mapped dry-grassland patches in GIS. Present-day isolation was calculated from surrounding patches within a **0.5 km radius**, using patch area and **edge-to-edge distance**:

`I_j = -log(sum_k(A_k / d_jk^2)), j != k`

where `A_k` is surrounding patch area and `d_jk` is edge-to-edge distance. Historical analogues were calculated for mapped potential grassland habitat in 1843 and 1980 (and, in the related 2019 analysis, 1954).

This establishes that the original study had genuine pairwise spatial geometry. It does **not** establish that the released workbook contains coordinates, boundaries, or a pairwise distance matrix.

## Geometry admissibility gate

The full EOG structural benchmark is admissible only if one of the following can be recovered from verified source material:

1. patch coordinates sufficient to calculate distances under a declared metric;
2. patch polygons/boundaries sufficient to calculate edge-to-edge distances; or
3. an explicit pairwise distance/adjacency representation tied unambiguously to the 272 patch IDs.

A scalar published isolation value by itself is **not** admissible graph geometry. If only `I_j`-type isolation scores are available, the dataset remains useful for a conceptual landscape-filtering replication but not for a full graph reachability benchmark.

## Frozen primary geographic rule

If admissible geometry is available, the primary graph uses the published landscape scale rather than tuning a radius from species outcomes:

- nodes: surveyed dry-grassland patches;
- geographic edge eligibility: edge-to-edge separation `<= 500 m`;
- geographic edge distance: edge-to-edge distance where patch boundaries are available;
- if only point coordinates are available, point distance is retained as an explicit approximation and is not called the published edge-to-edge metric.

The **500 m** threshold is frozen from the published study design and is not species-specific.

## Frozen sensitivity family

To distinguish conclusions that depend narrowly on 500 m from conclusions stable to scale, the geographic sensitivity family is frozen at:

- 250 m;
- 500 m;
- 1000 m.

The 500 m scenario is primary. The 250 m and 1000 m scenarios are symmetric half/double-scale sensitivity checks. They receive equal status as sensitivity analyses and cannot be selected post hoc by EOG performance.

No species-specific radius, optimized dispersal kernel, or threshold selected on held-out incidence is allowed.

## Area-weighted structural diagnostic

Because the published isolation definition combines source area with inverse-square distance, a secondary structural diagnostic may retain the predeclared edge/source quantity:

`source_mass_jk = A_k / d_jk^2`

This quantity is not a dispersal probability. It may be summarized along candidate paths or around targets as a sensitivity diagnostic, but the primary EOG graph remains a declared geometric reachability graph rather than a re-expression of `I_j`.

## Environmental support remains separate

The original study distinguishes local abiotic filtering from present-day and historical landscape configuration. The EOG replication must preserve that separation:

- local support is fit from local abiotic variables only;
- structural reachability is calculated from admissible patch geometry under the frozen geographic rules;
- present-day/historical area and isolation variables are retained as competitor or explanatory landscape baselines, not silently folded into local support.

This prevents the structural layer from winning simply by reusing the same landscape variables in both the support model and graph.

## Historical landscape layer

Historical maps from 1843 and 1980 are scientifically important, but a historical graph is permitted only if historical patch/PGH geometry can be linked reproducibly to the contemporary patch IDs. Historical scalar isolation and area variables alone do not satisfy this requirement.

Therefore the primary external EOG test is **present-day geometry first**. Historical structural scenarios are a separate extension, not required for the first replication.

## Held-out comparison contract

If the verified data support a full EOG benchmark, evaluation follows the same conceptual separation used in A-Islands:

1. freeze the upstream local-support model independently;
2. construct reachability using training-presence anchors only;
3. retain unlabelled/surveyed patches as potential structural nodes where justified by the data contract;
4. compare held-out presences and absences conditional on similar local support and nearest-anchor distance;
5. treat 0.5 as the null for pairwise conditional concordance;
6. keep taxa/folds with no comparable pairs as explicit applicability failures.

The exact fold design and taxon eligibility thresholds must be frozen in a later contract **after schema audit but before any EOG outcome**.

## Mandatory baselines

Any full benchmark must compare EOG structural reachability against at least:

- local environmental support alone;
- nearest training-presence distance;
- published present-day isolation, where available;
- present-day patch area, where available.

This is essential because the published isolation index already encodes distance and source area. EOG is only interesting here if it contributes something beyond these simpler spatial summaries.

## Interpretation boundary

A positive result would support only the claim that graph-structured reachability carries additional held-out incidence information in a fragmented plant landscape after controlling for pointwise support and simple proximity.

It would not establish:

- a true dispersal route;
- a species-specific dispersal kernel;
- realized movement through intermediate patches;
- demographic or genetic connectivity;
- that the published isolation formula is mechanistically correct;
- that EOG is generally superior to SDMs;
- causal effects of historical fragmentation.

The central purpose is narrower: test whether the structural signal observed in the island benchmark generalizes to a non-island patch network under spatial assumptions fixed independently of species-level EOG outcomes.
