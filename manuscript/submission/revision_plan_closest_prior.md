# Closest-prior manuscript revision plan

This is a **pre-release blocking revision**. It changes literature positioning only; it must not change any frozen benchmark result, graph, fold, effect, interval or inference rule.

## Introduction edits required

1. After the current paragraph on least-cost, circuit theory and habitat-network models, add a dedicated paragraph on **integrated suitability/connectivity precedents**:
   - Berlow et al. 2013;
   - Ortiz-Rodríguez et al. 2019;
   - Van Moorter et al. 2023;
   - Riva et al. 2024;
   - Kim et al. 2024;
   - Felin et al. 2025.
2. State explicitly that EOG does not introduce accessibility, environmental-quality + network integration, occupied-neighbour predictors, or habitat-network occurrence prediction.
3. Add a second short paragraph on **model-choice uncertainty**:
   - Ortiz-Rodríguez et al. 2023;
   - Prima et al. 2024;
   - Cushman et al. 2026.
4. Replace any broad implicit gap with the narrower validation gap:

   > The unresolved question addressed here is not whether connectivity can be added to a distribution or occupancy model, but whether an occurrence-conditioned structural quantity earns an incremental held-out claim after local support and direct source proximity are fixed, and whether any gain survives a strong landscape-specific connectivity reference.

5. Keep the existing four study questions, but ensure question 3 is visibly the falsification/strong-reference test rather than a second validation example.

## Discussion edits required

1. In Section 4.1, compare EOG explicitly with functional habitat and habitat-network occurrence models and state that the difference is the **held-out incremental estimand and evidence contract**, not the existence of a network term.
2. In Section 4.4, cite Riva 2024 and the recent connectivity/SDM integrations when arguing that reference-model content must be part of the claim.
3. In Section 4.5, describe source-to-result fingerprints and failure accounting as an implementation of auditability, not the first reproducibility framework in ecological modelling.
4. In Section 4.7, cite Ortiz-Rodríguez 2023, Prima 2024 and Cushman 2026 when motivating prospective graph/parameter uncertainty work.

## References required

Add the verified DOI records from `closest_prior_reference_additions.md` to the manuscript reference list and `structural_verified_references.md`.

## Claim guards after revision

The revised manuscript must contain, in substance:

- “EOG is not the first integration of suitability and connectivity.”
- “Occurrence-conditioned and nearest-occupied-patch predictors have precedents.”
- “Sensitivity to dispersal thresholds and connectivity-model choices has precedents.”
- “The present contribution is a leakage-safe, reference-conditioned incremental validation framework.”

It must not contain claims of universal superiority or realised movement/colonisation probability.

## Regression requirement

After the prose/reference changes, run the full test suite and the offline structural submission-package rebuild. All frozen A-Islands and Tanzania values and fingerprints must remain byte-identical where they are currently declared immutable.