Dear Editor,

We submit the Original Research Paper, **“When does landscape configuration add to pointwise distribution support? An auditable reachability framework across islands and forest fragments,”** for consideration in *Ecological Informatics*.

The manuscript addresses a practical problem in ecological modelling: local environmental support, spatial evaluation, direct proximity to observed populations, and landscape connectivity are often discussed together even though they answer different questions. We present Environmental Occupancy Geometry (EOG) as an auditable structural layer for testing one narrow incremental question—whether occurrence-anchored landscape configuration retains held-out information after a declared reference model has already represented simpler quantities. EOG is not presented as a replacement species-distribution model or as an estimator of dispersal or colonisation probability.

The paper is built around two frozen empirical benchmarks with deliberately different reference models. In A-Islands, 886 vascular-plant taxa were evaluated across 842 islands. After conditioning held-out comparisons on pointwise climatic support and nearest-training-occurrence distance, 845 taxa had an estimable primary statistic and mean structural conditional concordance was 0.618 (species-bootstrap 95% interval 0.609–0.627). In a stronger external benchmark using 60 bird species across 14 Tanzanian forest fragments, the reference already contained patch area, training-selected matrix-aware current flow, its interaction with patch area, and nearest-training-occurrence distance. Adding the frozen generic EOG connected-frequency feature increased leave-one-fragment-out log loss by 0.032 (95% interval 0.017–0.049). The spatial-block sensitivity was smaller and uncertain.

We consider the paired positive and negative results central to the contribution. They show that a structural estimand can contain information omitted by pointwise support and direct distance, while also demonstrating that the same generic feature need not provide incremental benefit once a strong landscape-specific connectivity representation is already present. The manuscript therefore makes a conditional methods claim rather than a universal-superiority claim.

The computational workflow is fully auditable. Source identities, graph scenarios, folds, training-only transformations, non-estimable cases, figure sidecars, result projections, and cryptographic fingerprints are retained in the repository. Manuscript figures and result tables are generated from frozen machine-readable inputs, and the submission package includes a clean offline rebuild command that verifies the scientific assets against their committed outputs. The adverse Tanzania result was independently reproduced and remains frozen in the manuscript and tests.

We believe this combination of ecological modelling, held-out empirical validation, uncertainty and failure accounting, and reproducible data-science infrastructure is well aligned with the scope of *Ecological Informatics*.

**AUTHOR CONFIRMATION REQUIRED before submission:** confirm that the manuscript is original, is not under consideration elsewhere, and has been approved by all authors.

Sincerely,

`<CORRESPONDING_AUTHOR_NAME>`  
`<AFFILIATION>`  
`<EMAIL>`
