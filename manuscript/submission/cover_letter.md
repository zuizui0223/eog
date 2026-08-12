Dear Editor,

We submit the Original Research Paper, **“When does landscape configuration add held-out information? An auditable reference-conditioned framework across islands and forest fragments,”** for consideration in *Ecological Informatics*.

The manuscript addresses a validation problem in ecological modelling: local environmental support, source proximity, generic graph configuration, and landscape-specific connectivity are often combined, yet the incremental value assigned to a new structural predictor depends on what the declared reference model already contains. We present Environmental Occupancy Geometry (EOG) as an auditable structural-adequacy framework for asking whether occurrence-conditioned landscape configuration earns an additional held-out claim after an explicitly frozen reference. EOG is not presented as a replacement species-distribution model or as an estimator of dispersal or colonisation probability.

The evidence is deliberately falsifiable. In an original A-Islands benchmark of 886 vascular-plant taxa across 842 islands, held-out occupied and unoccupied islands were compared only within strata matched for pointwise climatic support and nearest-training-occurrence distance. Among 845 estimable taxa, connected frequency retained conditional ordering information (mean concordance 0.618; species-bootstrap 95% interval 0.609–0.627). We then prospectively froze a substantially stronger A-Islands reference before inspecting the extension outcome. That reference included climate, recipient island area, continental-mainland distance, nearest species source, unweighted and area-weighted multi-source pressure, surrounding island number and landmass, generic island-network exposure, and generic mainland stepping-stone accessibility. Adding only the species-conditioned EOG connected-frequency term to this R3 reference **increased** held-out log loss by 0.00349 (95% interval 0.00247–0.00451); 341 species favoured the addition and 545 were adverse. The one-time execution used 886 estimable taxa, 4,231 evaluable species-folds and 712,515 held-out predictions and is frozen under result fingerprint `5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a`.

A separate external benchmark reaches a compatible strong-reference boundary. Across 60 bird species in 14 Tanzanian forest fragments, the reference already contained patch area, training-selected matrix-aware current flow, its interaction with patch area, and nearest-training-occurrence distance. Adding the generic EOG term increased primary leave-one-fragment-out log loss by 0.032 (95% interval 0.017–0.049), while the spatial-block sensitivity was smaller and uncertain.

We consider the combination of these results central to the contribution. The original A-Islands result shows that a structural ordering can remain after limited conditioning on local support and nearest-source distance. The prospective strong-reference A-Islands test shows that this observation does not justify a universal predictive increment once substantially richer island information is represented. Tanzania independently shows the same need to evaluate structural additions against the strongest scientifically defensible reference. Because the endpoints differ, we do not treat these estimates as effect sizes on one common scale. Instead, the paper formalises the reference content itself as part of the estimand.

The computational workflow is fully auditable. Source identities, graph scenarios, folds, training-only transformations, non-estimable cases, one-time execution provenance, raw-output checksums, manuscript sidecars, and cryptographic result fingerprints are retained. The A-Islands strong-reference test was frozen before its species outcomes, executed once after a zero-outcome smoke gate, retained despite its adverse direction, and then permanently disabled from rerunning in the active workflow. The adverse Tanzania result is likewise independently reproduced and frozen.

We believe this combination of ecological modelling, held-out falsification, explicit reference-conditioned estimands, uncertainty and failure accounting, and reproducible data-science infrastructure is well aligned with the scope of *Ecological Informatics*.

**AUTHOR CONFIRMATION REQUIRED before submission:** confirm that the manuscript is original, is not under consideration elsewhere, and has been approved by all authors.

Sincerely,

`<CORRESPONDING_AUTHOR_NAME>`  
`<AFFILIATION>`  
`<EMAIL>`
