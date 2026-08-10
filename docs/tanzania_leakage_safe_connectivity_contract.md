# Tanzania benchmark: leakage-safe connectivity contract

This contract separates **paper reproduction** from **held-out predictive comparison** before any species-level EOG outcome is inspected.

Dataset: Brodie & Newmark (2019), Dryad DOI `10.5061/dryad.p042h0c`.

## Published method that creates a validation issue

The paper's current-flow isolation is species-specific. The authors constructed 30 x 30 m land-cover rasters with four classes (forest, tea, eucalyptus, small-scale agriculture), fixed forest resistance at 1, and varied each nonforest resistance from 1 to 128 in twofold steps. They ran pairwise Circuitscape for every resistance combination and selected the combination that most parsimoniously predicted each bird species' patch occurrence using AIC.

Therefore a current-flow surface selected once using **all 14 patch occurrence labels** is a legitimate paper-reproduction object, but it is not a leakage-safe held-out predictor on the same occurrence dataset.

## Two circuit-theory roles must remain separate

### A. Published-reproduction current flow

Purpose: verify that the official source files/scripts and our execution reproduce the published analysis.

- Recover the exact resistance grid, patch-size weighting, Circuitscape mode, transformations, and AIC selection from the official Dryad scripts.
- Full-data occurrence labels may be used only because this branch is explicitly a reproduction analysis.
- Check that the qualitative/published reference behavior is recovered, including the reported 43/89 converged occurrence models and dominance of current flow among converged species.
- Results from this branch **must not** be reported as held-out predictive evidence for EOG versus current flow.

### B. Fold-safe current-flow competitor

Purpose: provide the strongest fair structural competitor to EOG in held-out evaluation.

For every held-out fold and species:

1. construct/select any species-specific resistance parameters using **training occurrence labels only**;
2. never use held-out occurrence labels for resistance selection, model selection, transformations, thresholds, or failure handling;
3. score the held-out patch only after resistance selection is frozen for that fold;
4. apply the same fold membership and applicability reporting used for EOG;
5. if the official scripts make fold-safe refitting impossible or ill-posed, report the competitor as non-estimable rather than substituting full-data tuned resistance values.

The allowed resistance candidate set is frozen from the paper as powers of two from 1 through 128 for each nonforest class, subject to exact confirmation from the official script before execution. No candidate may be added or removed because of held-out performance.

## Other structural comparators

Nearest-neighbor distance and cumulative weighted Euclidean isolation are not species-label-tuned structural metrics. Their geometry/source formulas are frozen from the official source and then reused unchanged across folds. Regression coefficients using these metrics are still trained within fold.

## EOG fairness rule

EOG may use only training occurrences as anchors within a fold. Any graph radius, edge threshold, local-support setting, or geometry transform must be fixed from source-defined/geometry-only information before held-out labels are inspected.

Thus both species-adaptive methods receive the same fundamental privilege and restriction:

- current flow may adapt resistance parameters to **training labels only**;
- EOG may adapt occurrence anchors/local support to **training labels only**;
- neither may adapt anything to held-out labels.

## Primary comparison hierarchy

The final held-out benchmark should distinguish at least:

1. patch-area/local baseline;
2. + nearest-neighbor isolation;
3. + cumulative weighted Euclidean isolation;
4. + fold-safe matrix-aware current flow;
5. EOG structural reachability;
6. local + fold-safe current flow + EOG, to test incremental EOG information beyond the strongest conventional connectivity model.

Paper-reproduction current flow is reported separately and is not inserted into this predictive hierarchy.

## Valid outcomes

All of the following are scientifically valid:

- EOG improves held-out prediction beyond fold-safe current flow;
- EOG and current flow are complementary but neither uniformly dominates;
- current flow absorbs the EOG signal and EOG has little/no incremental value;
- one or both species-adaptive methods are non-estimable for many species because 14 patches provide limited training support.

The benchmark is intended to locate EOG's boundary, not to force superiority.

No species-level EOG score or held-out outcome is computed in this contract.
