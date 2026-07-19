# Environmental occupancy geometry as an auditable description of observed environmental states

## Alternative titles

1. Environmental occupancy geometry as an auditable description of observed environmental states
2. From environmental point clouds to reproducible geometric comparisons
3. Auditable comparison of observed environmental-state geometry

## Provisional title

**Environmental occupancy geometry as an auditable description of observed environmental states**

## Abstract

Ecological occurrence records are often summarized in environmental space, yet geometric comparisons can be distorted by preprocessing choices, unequal sample sizes, unsupported topology assumptions, and post hoc selection of favorable reference systems. We developed Environmental Occupancy Geometry (EOG), a deliberately restricted framework for describing observed environmental-state point clouds and comparing their extent under a frozen shared transformation. EOG reports standardized within-cloud dispersion, minimum-spanning-tree compactness, descriptive separation evidence, and sampling diagnostics. Comparative extent is defined only after all groups are transformed by the same predeclared median–MAD reference, and its primary effect size is the log ratio of 0.90 pairwise-distance spans. Validation was organized as a sequence of attempted falsifications. Independent robust scaling failed to recover global dilation, showing that standardized span cannot support claims about absolute niche breadth. Minimum-spanning-tree compactness also reversed direction across unmatched intrinsic support classes, ruling out its interpretation as a universal path-directness statistic. In contrast, shared-reference scaling recovered a two-fold synthetic dilation with area-under-the-curve values of 1.0 across tested sample sizes, and matched-support path comparisons separated straight and curved paths with area-under-the-curve values of 1.0. A reference-policy audit rejected outcome-informed and leakage-prone constructions, while matched-size subsampling and label-permutation diagnostics recovered known extent differences with a median absolute log-ratio error of 0.057 and limited false directional support under equal-shape null comparisons to 0.083. A deterministic analysis manifest, strict CSV schema, audited runner, and frozen end-to-end example make analytical choices and outputs traceable. EOG is therefore not a fragmentation detector, suitability model, or universal niche-breadth estimator. Its contribution is an auditable workflow for restrained geometric description and predeclared comparison of observed environmental states.

## 1. Introduction

Occurrence records are commonly projected into environmental feature spaces to describe where organisms, populations, regions, or time periods have been observed. Such projections appear simple: rows represent observations, columns represent environmental variables, and distances among rows provide an intuitive picture of environmental dispersion or separation. The inferential difficulty lies not in calculating those distances but in deciding what they mean. The same point cloud can appear broad or narrow depending on scaling, a minimum-spanning tree can change with sample density and intrinsic support dimension, and apparent gaps can arise from sparse or uneven sampling. These problems are amplified when analytical choices are made after inspecting the geometry.

Existing ecological workflows address related questions through species-distribution models, occupancy models, environmental hypervolumes, clustering, ordination, and topological summaries. EOG does not replace those methods. It targets a narrower problem: how to describe the geometry of observed environmental states and compare selected quantities without silently changing the coordinate system, support assumptions, or sampling design. The unit of analysis is the observed occurrence-by-feature matrix, not an inferred suitability surface or latent occupancy process.

The framework began with broader ambitions. Early formulations treated pairwise-distance span as environmental breadth, minimum-spanning-tree compactness as continuity or path directness, and large tree edges as possible evidence of fragmentation. Frozen synthetic benchmarks contradicted those interpretations. Independent robust scaling removed global dilation, and tree compactness changed direction when cloud support classes were mismatched. Rather than hiding these failures, we used them to narrow the estimands and redesign the comparative workflow.

The resulting contribution is not a new family of geometric statistics. Pairwise distances, minimum-spanning trees, and largest-edge summaries are established ideas. The contribution is an auditable contract around their use: predeclared features, explicit scaling modes, frozen reference provenance, support-class restrictions, matched-size sampling diagnostics, claim-limited reporting, and deterministic input and result fingerprints. We ask three questions. First, which geometric summaries remain interpretable within a single robustly standardized cloud? Second, when can environmental extent be compared across groups? Third, can the complete analysis be frozen and reproduced without outcome-dependent tuning?

## 2. Methods

The authoritative implementation-level specification is `docs/manuscript_methods_specification.md`, and the permitted wording for every output is defined in `docs/claim_matrix.md`. The manuscript should not duplicate those definitions with alternative terminology.

### 2.1 Scientific estimand and unit of analysis

EOG operates on a finite matrix of observed environmental states. Each row is an occurrence or sampling record and each column is a predeclared environmental feature. EOG describes the geometry of those rows in the declared feature space. It does not estimate occurrence probability, detection probability, suitability, causal effects, missing support, or latent occupancy.

### 2.2 Default single-cloud geometry

For single-cloud description, each feature is centered by its sample median and divided by its median absolute deviation multiplied by 1.4826. Constant features are mapped to zero. Standardized span is the 0.90 quantile of positive pairwise Euclidean distances. Tree compactness is environmental diameter divided by total minimum-spanning-tree length. Gap strength is the largest positive tree edge divided by the median positive tree edge. Component labels are descriptive diagnostics created by thresholding tree edges; they do not establish ecological fragmentation.

### 2.3 Comparative geometry under a frozen reference

Comparative extent requires one robust reference fitted once and applied unchanged to all groups. The reference stores the feature medians, scales, constant-feature indicators, and provenance. Under this common transformation, the primary comparative effect is

\[
\log\left(\frac{\operatorname{span}_B}{\operatorname{span}_A}\right).
\]

The corresponding span difference in reference units is retained as a supplementary effect. Absolute values produced under different references are not compared.

### 2.4 Reference modes

Three modes are permitted. An external reference is fitted independently of the evaluated groups. A training-only reference is fitted to a declared baseline or training set before held-out evaluation. A pooled-descriptive reference includes the compared groups and supports only retrospective symmetric description. Outcome-informed reference construction, evaluation leakage into external or training-only references, and prospective use of pooled-descriptive references are rejected.

### 2.5 Sampling diagnostics

Unequal sample sizes are handled by drawing the same number of rows from both groups in every resample. The matched draw size is the floor of the smaller group size multiplied by the predeclared resampling fraction, with a minimum of four rows. The reported effect is the median across matched-size draws, and the interval is a percentile sensitivity interval conditional on the observed records. It is not a population confidence interval.

A separate label-permutation diagnostic is reported when exchangeability is defensible. Directional support requires both at least 0.90 resampling direction stability and a two-sided permutation value below 0.10. Spatial clustering, repeated observations, temporal dependence, phylogenetic structure, or unequal effort can invalidate exchangeability and require a design-specific permutation scheme.

### 2.6 Support-class restriction

Tree compactness and gap strength may be compared only for groups assigned to the same predeclared intrinsic support class. A comparison between a compact two-dimensional cloud and a one-dimensional curved path is not treated as a valid test of path directness.

### 2.7 Analysis manifest and audited runner

Every confirmatory comparison is frozen in an `AnalysisManifest` containing the scientific comparison, feature order, group direction, reference declaration and fingerprint, primary metric, support class, resampling and permutation settings, random seed, claim scope, prohibited claims, software version, and group-specific input fingerprints. The audited runner accepts only file paths as command-line options. It rejects column-order drift, duplicate row identifiers, non-finite values, unexpected groups, reference mismatches, and input-fingerprint mismatches. Identical inputs and manifests produce deterministic machine-readable outputs.

## 3. Results

### 3.1 Default geometry is descriptive within a standardized cloud

The public API robustly handles duplicate states, constant features, all-identical rows, one-dimensional matrices, and empty candidate projections with matching feature dimension. Non-finite entries and undersized occurrence matrices are rejected. These tests establish numerical behavior, not ecological validity.

### 3.2 Independent scaling falsified the universal breadth interpretation

When compact and globally dilated clouds were scaled independently, standardized span did not distinguish the two conditions. Across sample sizes of 60, 120, and 240, area-under-the-curve values were approximately 0.50, 0.38, and 0.53. This result demonstrates that independent median–MAD scaling removes global dilation. Standardized span therefore measures within-cloud dispersion after normalization and cannot be interpreted as absolute environmental breadth across independently scaled groups.

### 3.3 Unmatched support classes falsified universal path directness

A benchmark comparing a compact cloud with a curved manifold produced the opposite direction from the intended continuity interpretation. Minimum-spanning-tree compactness depends on intrinsic support geometry, sample filling, and sample size. We therefore abandoned generic path-directness claims and restricted comparisons to predeclared matched support classes.

### 3.4 Shared-reference scaling recovered comparative extent

Under one shared robust reference, compact and two-fold dilated synthetic clouds were perfectly separated at all tested sample sizes, with area-under-the-curve values of 1.0. Median recovered width ratios were approximately 1.98–2.06 across valid reference modes. These results support comparative extent in the declared reference units, not universal niche breadth.

### 3.5 Matched-support path comparisons recovered geometric differences

Straight and curved noisy paths compared within the same one-dimensional support family were separated by tree compactness with area-under-the-curve values of 1.0 across tested sample sizes. This result supports matched-support comparison while reinforcing that cross-support comparisons are invalid.

### 3.6 Reference-policy audit prevented leakage and claim inflation

External, training-only, and pooled-descriptive references each recovered the synthetic dilation with area-under-the-curve values of 1.0 under their permitted use cases. Absolute span values differed among reference modes, confirming that outputs from different references are not directly interchangeable. The policy layer rejected outcome-informed references, evaluation leakage, and prospective pooled-descriptive use.

### 3.7 Matched-size diagnostics controlled sample-size artifacts

The first uncertainty benchmark failed because equal resampling fractions produced unequal absolute draw sizes and because subsampling intervals were incorrectly evaluated as population-coverage intervals. After changing to equal absolute draw sizes and separating resampling stability from permutation support, the known two-fold dilation was recovered with a median absolute log-ratio error of 0.057. Directional support for the known effect was 1.0, while false directional support under equal-shape null comparisons was 0.083.

### 3.8 The complete workflow was reproducible

The manifest contract, strict CSV runner, and frozen synthetic example all passed deterministic reproduction checks. The canonical example reproduced a log span ratio of 0.726, a sensitivity interval of 0.605–0.932, direction stability of 1.0, and a permutation diagnostic of 0.0099. Altering an input value, row identity, feature order, group label, or reference identity changed a fingerprint or caused validation failure.

## 4. Discussion

EOG provides a disciplined way to describe and compare observed environmental-state geometry. Its strongest contribution is not any single geometric statistic. It is the separation of estimands and the enforcement of the assumptions required for each one. Single-cloud standardized span describes dispersion after within-cloud normalization. Comparative span describes relative extent only under one frozen reference. Tree compactness and gap strength remain conditional on support class and sampling design. Sampling intervals describe sensitivity to the observed records, while permutation diagnostics require exchangeability.

The negative benchmarks are central results. Independent scaling erased the very dilation that a universal breadth measure should detect. Unmatched support classes reversed the intended interpretation of tree compactness. Null-family calibration either over-rejected connected non-Gaussian clouds or absorbed fragmented clouds. These failures narrowed the method and prevented attractive but unsupported claims. In that sense, EOG is a case study in validation by attempted falsification rather than metric accumulation.

The framework remains deliberately separate from species-distribution and occupancy modelling. It cannot infer unobserved suitability, correct for imperfect detection, identify missing environmental bridges, or estimate fragmentation probability. Candidate projection reports distances to observed states and is diagnostic only. Component counts and large tree edges summarize the observed cloud; they do not establish absent habitat or ecological disconnection.

Several limitations remain. Environmental variables can be highly correlated, poorly measured, or selected with insufficient ecological rationale. Occurrence data can be spatially clustered and effort-biased. Median–MAD references can still be affected by structured contamination, and the current contamination benchmark is limited. Tree summaries remain sensitive to sample filling. The framework currently supports two-group comparisons and does not solve hierarchical replication, repeated-measures dependence, or design-based spatial inference. These are not cosmetic caveats; they define the boundary of defensible use.

The practical benefit of the framework is auditability. A reader can inspect which features were used, how the reference was constructed, which metric was primary, whether support classes were matched, how many records entered each draw, what claim language was permitted, and whether the inputs match the frozen manifest. Negative and ambiguous results are retained rather than converted into a headline score. This makes EOG suitable as a transparent descriptive component within broader ecological studies, provided its outputs are not promoted beyond their declared scope.

## 5. Minimum reporting checklist

A study using comparative EOG should report:

1. the ecological comparison and unit of analysis;
2. all feature names, units, transformations, and ecological rationale;
3. group definitions and observation counts;
4. reference mode, provenance, intent, and fingerprint;
5. primary metric and any supplementary diagnostics;
6. support class for tree-sensitive comparisons;
7. resampling fraction, matched draw size, draw count, permutation count, and seed;
8. effect estimate, sensitivity interval, direction stability, permutation diagnostic, and ambiguity status;
9. manifest and input fingerprints;
10. allowed and prohibited claims;
11. relevant sampling-bias, dependence, and exchangeability limitations;
12. software version and reproducible command.

## 6. Figure plan

**Figure 1 — Conceptual workflow.** Observed occurrence-by-feature matrix; predeclared feature set; frozen reference; within-cloud versus comparative geometry; matched-size diagnostics; manifest-bound output.

**Figure 2 — Falsification of universal interpretations.** Independent-scaling compact versus dilated benchmark; unmatched compact-cloud versus curved-path tree compactness. The figure should emphasize failure, not conceal it.

**Figure 3 — Valid comparative recovery.** Shared-reference compact versus two-fold dilation across sample sizes and valid reference modes; recovered log ratios and width ratios.

**Figure 4 — Support-matched and uncertainty diagnostics.** Straight versus curved matched paths; known-effect and equal-shape-null distributions under matched-size resampling and permutation.

**Figure 5 — Reproducibility contract.** Manifest, fingerprints, strict CSV, deterministic runner, and canonical result bundle.

## 7. Table plan

**Table 1 — Quantity and claim matrix.** Condensed from `docs/claim_matrix.md`.

**Table 2 — Validation sequence.** Benchmark question, expected behavior, result, methodological consequence, and evidence file.

**Table 3 — Reference modes.** External, training-only, and pooled-descriptive construction, permitted intent, allowed claim, and prohibited use.

**Table 4 — Minimum reporting checklist.** Required fields for manuscript and archived result bundle.

## 8. Evidence map

- Single-cloud API and edge cases: `tests/test_geometry.py`
- Robustness and irrelevant dimensions: `benchmarks/robustness_audit.py`
- Negative archetype results: `docs/multiaxial_archetype_results.md`
- Shared-reference recovery: `docs/shared_scaling_contract_results.md`
- Reference policy: `docs/reference_choice_results.md`
- Comparative uncertainty: `docs/comparative_uncertainty_results.md`
- Methods definitions: `docs/manuscript_methods_specification.md`
- Claim restrictions: `docs/claim_matrix.md`
- Frozen example: `docs/frozen_comparison_tutorial.md`

## 9. Statements that must not appear as conclusions

- EOG estimates absolute niche breadth from independently scaled clouds.
- EOG continuity is a universal measure of path directness or tortuosity.
- Gap strength or component count proves ecological fragmentation.
- EOG estimates missing support, suitability, occupancy, or detection probability.
- A subsampling interval is a population confidence interval.
- A permutation value is valid without a defensible exchangeability design.
- Candidate projection is a habitat-suitability score.
- EOG has a universal threshold or composite headline score.
