# Tanzania non-island benchmark: pre-outcome comparison contract

This document freezes the scientific comparison roles for the Tanzania forest-fragment validation **before any species-level EOG outcome is inspected**.

Dataset: Brodie & Newmark, *Heterogeneous Matrix Habitat Drives Species Occurrences in Complex, Fragmented Landscapes* (American Naturalist 2019), Dryad DOI `10.5061/dryad.p042h0c`.

## Why this is a strict external benchmark

The published study already showed that patch occurrence is strongly related to patch area and isolation, and that isolation estimates accounting for heterogeneous landscape matrix structure substantially outperform isolation estimates that ignore matrix heterogeneity. Therefore EOG must not be compared only against a naive pointwise or Euclidean-distance baseline.

## Frozen comparison tiers

1. **Local patch baseline**
   - Patch-local attributes only.
   - Patch area is mandatory because it is part of the published island-biogeographic occurrence framework.
   - Additional local covariates may be used only if their semantics are explicitly verified from the official Dryad bytes/source scripts in a later pre-outcome schema PR.
   - Connectivity, occurrence-anchor distance, circuit/current-flow values, node-network quantities, or matrix-raster summaries are prohibited from this tier.

2. **Simple isolation baseline**
   - A structural comparator that ignores matrix heterogeneity, matching the conceptual comparator in the published study.
   - Its exact field/formula must be recovered from the verified Dryad source scripts or tables before outcomes; it must not be reconstructed by tuning against species performance.

3. **Published matrix-aware connectivity competitor**
   - The strongest published structural comparator available from this dataset.
   - Must use the study's matrix-aware/circuit-theory isolation definition as recovered from verified official source files/scripts.
   - This competitor is not rebranded as EOG and is retained even if it outperforms EOG.

4. **EOG structural reachability**
   - Occurrence-anchored structural reachability computed from the same verified node geometry and landscape matrix inputs.
   - Held-out occurrence labels may never define graph parameters, anchors, local-support fit, or thresholds.
   - The EOG comparison asks whether explicit occurrence-anchored landscape configuration contributes information beyond local patch attributes and conventional isolation/connectivity measures.

## Evaluation contract

- Use spatial holdout; random site-level leakage is not acceptable.
- Within each fold, only training occurrences may serve as EOG anchors.
- Species are eligible only with at least 10 presences and 10 absences in the verified occurrence table; the eligible count is not inspected until the verified-byte/schema gate passes.
- Report applicability/failure reasons rather than silently dropping non-estimable species or folds.
- Primary inferential direction and effect metric will be frozen in a later PR after the verified schema reveals the actual site and landscape structure, but before any species-level EOG score is calculated.
- Exact graph scales/radii are **not** fixed here because coordinate units, node spacing, and raster scale have not yet been verified from official bytes. They must be derived from published/source-defined spatial scales or a prespecified geometry-only rule, never selected by occurrence performance.

## Required comparisons

At minimum, final non-island reporting must preserve all four tiers where executable:

`local patch baseline` → `+ simple isolation` → `+ published matrix-aware connectivity` → `EOG structural reachability`

EOG may be complementary rather than superior. A valid outcome includes no incremental EOG benefit once matrix-aware connectivity is controlled.

## Claim boundary

This benchmark is designed to test generalization beyond islands. Success would support the claim that EOG captures occurrence-anchored structural information in fragmented landscapes; it would not by itself establish a mechanistic dispersal probability or prove universal superiority over connectivity models.

No species filtering result, fitted occurrence model, graph score, AUC, concordance, or other EOG performance is computed in this contract.