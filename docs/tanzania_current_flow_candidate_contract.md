# Tanzania current-flow candidate-library contract

This stage materializes the matrix-aware structural competitor for the Tanzania forest-fragment benchmark **without selecting a resistance combination for any species and without calculating predictive performance**.

## Scientific role

The candidate library is an input to a later leakage-safe comparison. For every species and outer holdout fold, the later runner may select among the frozen candidates using outer-training occurrence labels only. The held-out labels may not influence resistance selection, source weighting, raster resolution, focal identity, graph semantics, solver settings, or failure handling.

A candidate matrix is therefore not evidence that a resistance setting predicts occurrence. It is only a deterministic landscape quantity indexed by a declared resistance combination.

## Frozen source and repairs

The source remains Dryad version `23134` for DOI `10.5061/dryad.p042h0c`. Every workflow reacquires the official nine-file archive and verifies the frozen file sizes and MD5 digests.

The pre-outcome source audit in PR #112 remains authoritative:

- focal IDs are explicit `patch_number` values rather than implicit node-table row indices;
- the verified archive file `raster_east3.tif` is used directly;
- the primary positive source-area weight is `1 / log10(1 + area_ha)`;
- `1 / area_ha` is the declared source-area sensitivity;
- the literal released `1 / log10(area_ha)` weighting remains a source-reproduction diagnostic only.

## Resistance grid

Forest resistance is fixed at one. Eucalyptus, tea, and other agriculture each use the predeclared set

```text
1, 2, 4, 8, 16, 32, 64, 128
```

This gives `8 × 8 × 8 = 512` ordered candidates per region. East and West retain the different class-to-land-cover mappings recovered from the official scripts.

## Explicit grid semantics

The independent candidate engine fixes the following Circuitscape-compatible raster semantics:

- raster data type;
- pairwise effective resistance;
- cell values interpreted as resistances;
- eight-neighbour connectivity;
- adjacent conductance equal to the mean of the two cell conductances;
- diagonal conductance divided by `sqrt(2)`;
- all 42 focal patches identified by `patch_number`.

The implementation solves the conductance-Laplacian system directly and tests it against exact line and cycle-network effective resistances. It does not depend on a mutable external Circuitscape installation during candidate generation.

## Outcome-free resolution rule

The source rasters are approximately 30 m. Running all 512 candidates at the original resolution is not suitable for a reproducible continuous-integration benchmark. Resolution is therefore selected from geometry alone, before occurrence performance:

1. aggregate by powers of two;
2. require every one of the 42 explicit focal patches in each region to occupy a distinct coarse cell;
3. choose the coarsest shared factor satisfying that rule.

At factor 16, East Usambara has only 40 distinct focal cells. At factor 8, both East and West retain all 42. The primary candidate library is therefore fixed at factor 8, approximately 240 m.

Categorical aggregation uses block mode with a deterministic smallest-class tie break. If the modal class would erase the verified class at a focal cell, that coarse focal cell is replaced by the class at the original fine-resolution focal coordinate. This uses node geometry and source raster values only.

This coarse library is a computational benchmark representation, not an exact 30 m reproduction. A later outcome-free resolution audit should test a predeclared subset of resistance combinations at finer resolution before final biological interpretation.

## Computation and sharding

Each region is divided into 16 contiguous candidate-index shards. For each candidate, the runner saves:

- the full `42 × 42` pairwise effective-resistance matrix;
- primary positive area-weighted isolation for all 42 targets;
- inverse-area sensitivity isolation;
- resistance-axis values and candidate index;
- canonical fingerprints rounded to 12 decimal places.

The aggregate stage requires exactly candidate indices `0..511` once per region, the frozen resistance-grid order, all 16 shards, and matching shard fingerprints. East and West libraries receive separate fingerprints plus one combined library fingerprint.

## Prohibited operations in this stage

The candidate workflow does not:

- read or export species occurrence outcomes;
- choose a resistance combination;
- fit an occurrence or suitability model;
- calculate log loss, Brier score, AUC, concordance, or calibration;
- compare current flow with EOG;
- change the EOG graph or anchor contract.

The next gate is outer-training-only resistance selection followed by matched held-out prediction under the already frozen Tanzania scoring and species-cluster inference contracts.
