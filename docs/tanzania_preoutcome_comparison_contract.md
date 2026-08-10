# Tanzania non-island benchmark: pre-outcome comparison contract

This document freezes the scientific comparison roles for the Tanzania forest-fragment validation **before any species-level EOG outcome is inspected**.

Dataset: Brodie & Newmark, *Heterogeneous Matrix Habitat Drives Species Occurrences in Complex, Fragmented Landscapes* (American Naturalist 2019), Dryad DOI `10.5061/dryad.p042h0c`.

## Published structural facts recovered before outcome inspection

The paper reports 14 closed-canopy forest fragments in the East and West Usambara Mountains, with patch area spanning 0.2--908 ha. It analyzes occurrence (presence/absence over a 31-year survey period) for 89 bird species; the published occurrence models converged for 43 species because the remainder had insufficient variation across patches.

Three isolation definitions are explicitly distinguished:

1. nearest-neighbor Euclidean distance;
2. cumulative weighted Euclidean distance to all other patches, with source-patch area weighting;
3. cumulative current-flow/resistance distance through a heterogeneous four-class matrix (forest, tea, eucalyptus, small-scale agriculture), again with patch-size weighting.

The matrix rasters were constructed at 30 x 30 m resolution. The paper states that occurrence was modeled with logistic regression as a function of log10 patch area, log10 isolation, and their interaction. These published facts may be used to verify source semantics, but actual column names and executable formulas still require the official Dryad bytes/scripts.

## Why this is a strict external benchmark

The published study already showed that patch occurrence is strongly related to patch area and isolation, and that isolation estimates accounting for heterogeneous landscape matrix structure substantially outperform isolation estimates that ignore matrix heterogeneity. Therefore EOG must not be compared only against a naive pointwise or Euclidean-distance baseline.

## Frozen comparison tiers

1. **Local patch baseline**
   - Patch-local attributes only.
   - Patch area is mandatory because it is part of the published island-biogeographic occurrence framework.
   - Additional local covariates may be used only if their semantics are explicitly verified from the official Dryad bytes/source scripts in a later pre-outcome schema PR.
   - Connectivity, occurrence-anchor distance, circuit/current-flow values, node-network quantities, or matrix-raster summaries are prohibited from this tier.

2. **Simple isolation baseline**
   - Preserve both published matrix-homogeneous comparators when executable: nearest-neighbor distance and cumulative weighted Euclidean distance.
   - Their exact source fields/formulas must be recovered from the verified Dryad source scripts/tables before outcomes; they must not be reconstructed by tuning against species performance.

3. **Published matrix-aware connectivity competitor**
   - The strongest published structural comparator available from this dataset.
   - Must use the study's matrix-aware/circuit-theory isolation definition as recovered from verified official source files/scripts.
   - This competitor is not rebranded as EOG and is retained even if it outperforms EOG.

4. **EOG structural reachability**
   - Occurrence-anchored structural reachability computed from the same verified node geometry and landscape matrix inputs.
   - Held-out occurrence labels may never define graph parameters, anchors, local-support fit, or thresholds.
   - The EOG comparison asks whether explicit occurrence-anchored landscape configuration contributes information beyond local patch attributes and conventional isolation/connectivity measures.

## Evaluation contract

- Use geometry-aware holdout; random site-level leakage is not acceptable. The exact blocking rule remains deferred until official site coordinates and East/West membership are verified.
- Within each fold, only training occurrences may serve as EOG anchors.
- **Correction to the previous contract:** a 10-presence/10-absence threshold is impossible with only 14 patches and is therefore revoked before any species-level outcome inspection.
- Minimal global eligibility is instead **at least 2 presences and 2 absences**. This is the minimum class-support condition required so that a leave-one-site-out training set can still contain both classes. Any stricter fold-specific estimability rule will be frozen from geometry/model structure before EOG outcomes and must be applied identically to every comparison tier.
- The published 43/89 convergence result is a source-reproduction sanity check, not an eligibility target and not a criterion that may be tuned to reproduce the paper.
- Report applicability/failure reasons rather than silently dropping non-estimable species or folds.
- Primary inferential direction and effect metric will be frozen after the verified schema reveals the actual site/landscape structure, but before any species-level EOG score is calculated.
- Exact graph scales/radii are **not** fixed here because coordinate units, node spacing, and raster scale have not yet been verified from official bytes. They must be derived from published/source-defined spatial scales or a prespecified geometry-only rule, never selected by occurrence performance.

## Required comparisons

At minimum, final non-island reporting must preserve all tiers where executable:

`local patch baseline` → `+ nearest-neighbor isolation` → `+ cumulative weighted Euclidean isolation` → `+ published matrix-aware connectivity` → `EOG structural reachability`

EOG may be complementary rather than superior. A valid outcome includes no incremental EOG benefit once matrix-aware connectivity is controlled.

## Claim boundary

This benchmark is designed to test generalization beyond islands. Success would support the claim that EOG captures occurrence-anchored structural information in fragmented landscapes; it would not by itself establish a mechanistic dispersal probability or prove universal superiority over connectivity models.

No species filtering result, fitted occurrence model, graph score, AUC, concordance, or other EOG performance is computed in this contract.
