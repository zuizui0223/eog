# Tanzania current-flow execution contract

This document freezes the executable matrix-aware competitor **before any Tanzania species performance is inspected**. It follows the source audit in PR #112 and does not reinterpret the released script as a valid held-out analysis.

## Role

The output is a complete library of pairwise effective-resistance matrices for the 512 source-declared nonforest resistance profiles in East and West Usambara. Later folds may select among those candidates with outer-training occurrence labels only. This stage performs no resistance selection and fits no occurrence model.

## Explicit graph semantics

The released R script did not record all Circuitscape executable defaults. The held-out competitor therefore makes every relevant graph choice explicit:

- the verified land-cover raster is treated as a resistance raster;
- East and West remain separate graphs;
- eight-neighbour cell adjacency is used;
- cardinal edge conductance is the arithmetic mean of endpoint cell conductances;
- diagonal conductance is divided by `sqrt(2)`;
- focal cells are identified by the repaired `patch_number`, never by table row order;
- forest resistance is one and the three nonforest resistance axes retain the frozen powers-of-two grid.

These choices define the held-out competitor. They are not claimed to reconstruct an unrecorded historical executable byte-for-byte.

## Computational resolution

The verified rasters contain about 3.34 million East and 9.03 million West cells at approximately 30 m. Literal full-resolution execution of all 512 profiles is not feasible on a standard hosted runner. The following outcome-free resolution contract is therefore fixed:

- **primary:** categorical block-mode aggregation by factor 4, approximately 120 m;
- **resolution sensitivity:** factor 8, approximately 240 m;
- ties in a block select the lowest source class;
- partial edge blocks retain observed cells only;
- both resolutions must preserve all 42 focal patches as distinct graph nodes.

Factor 4 was retained as the finest standard-runner resolution demonstrated to fit the available memory/time envelope. Factor 8 provides a complete resolution-sensitivity replicate. Species labels, AIC, log loss, AUC, and EOG performance played no role in this choice.

## Effective-resistance computation

For each region and resistance profile, the implementation builds the sparse graph Laplacian, grounds one focal node, factorizes the reduced Laplacian once, and solves unit-current right-hand sides for all remaining focal nodes. Pairwise effective resistance is recovered from the focal submatrix of the grounded inverse. Synthetic tests require agreement with exact series rules and a dense Moore–Penrose pseudoinverse on small graphs.

The resulting 42-by-42 resistance matrix is transformed into two source-area-weighted isolation vectors:

- primary: `1 / log10(1 + area_ha)`;
- sensitivity: `1 / area_ha`.

## Sharded reproducibility

The 512 profiles are split into 16 deterministic shards of 32 profiles for each region. Every shard is run at both resolutions with BLAS threads fixed to one. Aggregation requires exactly:

- 2,048 region × profile × resolution candidate rows;
- 1,024 matched factor-4 versus factor-8 comparisons;
- no duplicate or missing keys;
- all pre-outcome flags to remain false.

The aggregate artifact records complete matrix and row fingerprints plus outcome-free resolution concordance. The final held-out benchmark remains locked until this candidate grid is complete and frozen.

## Claim boundary

This stage may support the statement that a reproducible source-derived matrix-aware current-flow competitor was generated. It does **not** establish that current flow predicts occurrences, that EOG improves on current flow, or that the released 30 m analysis was exactly reproduced.

## Completed outcome-free candidate grid

The first full sharded execution completed all 2,048 region × profile × resolution rows and all 1,024 matched factor-4 versus factor-8 comparisons without missing or duplicate keys. The frozen aggregate fingerprints are:

- candidate index SHA-256: `f99c9fc71107f91fd593636f49216b1040d620ad83411068c00400a14cafed45`;
- resolution-comparison SHA-256: `e009f499112eb3eca7aa66a98a51163ef89e041e7c1c250e12bdd48d1d13babd`.

Resolution concordance was high for the derived isolation quantities. Across the 1,024 matched region-profile comparisons, factor 4 versus factor 8 Spearman correlation had median 0.987 and minimum 0.937 for the primary weighted isolation, and median 0.987 and minimum 0.942 for the inverse-area sensitivity. Pairwise effective-resistance matrices were more resolution-sensitive (median Spearman 0.969, minimum 0.754), which is why the factor-8 sensitivity is retained rather than treated as redundant. These are computational-resolution diagnostics only; they use no occurrence labels or predictive scores.
