# SW Finland response-free schema normalization

## Status

**Frozen before any `outcome` value is accessed by EOG v2.**

The byte-identical Dryad file reached the predeclared response-free admission and exposed one released representation mismatch: the existing admission code expected every declared graph-habitat field to parse numerically, while the released table represents `Limestone` with categorical `Yes`/`No` tokens.

Dryad's public data dictionary defines `Limestone` as presence of limestone on the island with the semantic coding `0 = absent, 1 = present`. It separately defines `Buildings`, `Meadow_or_pasture`, forest, sand, open-rock, marsh, and shore-meadow variables as proportional land-cover fields. The publication also treats limestone as a categorical yes/presence effect.

Therefore the response-free CSV adapter now applies exactly one declared representation normalization before the unchanged admission/prepare code:

- `Limestone = Yes` -> `1`;
- `Limestone = No` -> `0`;
- existing numeric `0`/`1` remain unchanged;
- no other column receives categorical coercion.

A nonnumeric token in any other numeric response-free field still fails the frozen parser. The `outcome` column is not read, counted, summarized, stratified, or modeled during this normalization.

This is a file-schema normalization, not a change to the habitat variable set, graph definition, environmental distance, source reconstruction, R0/R1/R2/C models, folds, loss support, bootstrap, or GO/NO-GO rule. The raw file bytes and SHA-256 remain unchanged and are still required to match the Dryad cryptographic digest through the institutional-mirror transport contract.
