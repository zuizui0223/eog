# Tanzania current-flow source audit and pre-outcome repair

This audit is completed before any Tanzania current-flow matrix, resistance
selection, held-out probability, loss, AUC, or EOG performance is calculated.
It separates literal reconstruction of the released Dryad scripts from the
competitor used in held-out evaluation.

## Source identity defect

The released `0_usambara.R` creates `SpatialPoints` from columns 3–4 of each
node table and calls `rasterize(x = sites, y = cost)` without a `field`.
Under the documented `raster` behavior, a missing field transfers feature
indices `1..n`. Neither node table is ordered by `patch_number`; in fact all
42 row indices differ from `patch_number` in both regions. The subsequent
`1_sites.R` script subsets Circuitscape columns by `patch_number`, so a
literal run aliases focal IDs to the wrong patches.

The held-out benchmark therefore writes focal rasters with
`field = patch_number` explicitly. Literal row-index behavior remains
available only as a source-reproduction diagnostic.

## Source-area weighting defect

The paper defines cumulative isolation as pairwise distance divided by a
log10-transformed source-patch area, and the released script implements
`resistance_distance * (1 / log10(area_ha))`. Four East Usambara nodes have
area below one hectare, producing negative source weights. An exactly
one-hectare source would be singular. Such values cannot be interpreted as a
non-negative isolation cost and are inadmissible in the fair held-out
competitor.

Two outcome-free repair conventions are frozen:

- primary: `1 / log10(1 + area_ha)`;
- sensitivity: `1 / area_ha`.

The primary rule is the minimal domain repair that retains logarithmic
compression and the intended monotone ordering in which smaller source
patches receive larger weights. Both rules are finite, positive, and strictly
decreasing for every positive patch area. The literal formula is retained
only for reproduction diagnostics.

## East raster filename

The released script requests `raster_east3_new.tif`, while the verified
Dryad archive contains `raster_east3.tif`. The archived raster already has
only the four expected classes `1..4`. The benchmark therefore uses the
exact digest-verified archive file and does not apply the released `5 -> 4`
or `6 -> 3` recodes.

## Frozen competitor boundary

The fair held-out current-flow competitor will:

1. use explicit `patch_number` focal IDs;
2. use the primary positive source-area weighting, with the raw inverse-area
   rule reported separately as sensitivity;
3. retain the published 512 resistance combinations;
4. select resistance values using outer-training occurrence labels only;
5. never use held-out labels for resistance choice, transformations, failure
   handling, or graph/EOG settings.

A positive or null EOG increment remains equally acceptable. This correction
prevents a source-code identity alias and negative isolation values from
making that comparison uninterpretable.
