# Structural-reachability manuscript submission checklist

## Current journal decision state

**Submission is result-dependent and currently on HOLD.**

The original frozen A-Islands + Tanzania manuscript is already scientifically submission-worthy, but the project has deliberately selected a higher-novelty island-biogeography falsification test before release.

- If the prospectively frozen A-Islands `C − R3` log-loss contrast is robustly negative: **first target = *Journal of Biogeography*, Research Paper**.
- If the new contrast is null, adverse, or indeterminate: **first target = *Ecological Informatics*, Original Research Paper**, retaining the broader structural-adequacy framing.
- *Methods in Ecology and Evolution* remains NO-GO for this empirical version unless a separate general method/simulation contribution is developed prospectively.
- *Ecological Modelling* remains a conditional broader-route backup.

The journal decision rule is frozen in `manuscript/submission/novelty_submission_strategy_2026-08-12.md` and must not be changed to chase whichever journal looks preferable after the result.

## Submission-blocking gates

The paper is **not ready to submit or release** until every blocking item is complete.

### Scientific content already secured

- [x] Positive original real-data benchmark: A-Islands plants.
- [x] Strong-competitor external benchmark: Tanzania forest birds.
- [x] Negative Tanzania result retained and independently reproduced.
- [x] Tanzania spatial-block sensitivity reported as uncertain.
- [x] Species-level inference and all non-estimable cases retained.
- [x] SDM, spatial CV, source distance, current flow and EOG roles separated.
- [x] Existing-method competitor matrix drafted.
- [x] Original full Introduction and Methods converted from contracts to prose.
- [x] Original Results tables generated directly from frozen artifacts.
- [x] Original Results/Discussion preserve the positive/adverse evidence boundary.
- [x] General closest-prior novelty audit completed on 2026-08-12.
- [x] Island-specific closest-prior audit added: Long 2009; Weigelt & Kreft 2013; Sillero et al. 2018; Carter et al. 2020; Daniel et al. 2023.
- [x] Verified closest-prior additions ledger expanded in `manuscript/submission/closest_prior_reference_additions.md`.

### Island-isolation novelty-maximization gate

- [x] Final island reference hierarchy frozen before extension species outcomes (`eog_aislands_isolation_adequacy_v1_3`).
- [x] Original A-Islands graph universe locked to the same 842 surveyed/model-linked islands.
- [x] A-Islands polygon area recovered outcome-free for 842/842 islands and fingerprinted.
- [x] Natural Earth 1:10m v5.1.1 continental-Australia geometry frozen outcome-free and fingerprinted.
- [x] Continental-mainland distance derived for 842/842 islands and fingerprinted.
- [x] R3 includes climate, recipient area, mainland distance, nearest species source, unweighted and area-weighted multi-source pressure, nearest other island, surrounding-island pressure, surrounding-landmass pressure, generic component exposure, and generic mainland stepping-stone frequency.
- [x] Candidate C adds only geography-only species-conditioned EOG connected frequency.
- [x] Held-out labels prohibited from all response-derived spatial feature construction; training presences use focal self-exclusion.
- [x] Primary endpoint, 5/5 class gate, constant-predictor rule, λ=1 fit engine, bootstrap/sign-flip inference and non-estimability accounting frozen before outcome.
- [ ] **Island-isolation adequacy extension executed exactly once under the frozen v1.3 contract.**
- [ ] Raw island-extension held-out predictions, fold applicability, species summaries, uncertainty and result fingerprint frozen without selective deletion.
- [ ] **Island extension result incorporated without weakening R3, retuning graph scales, changing taxa, or selecting a favourable interpretation.**
- [ ] Journal route selected by the predeclared `C − R3` decision rule.

### Closest-prior manuscript framing after the island result

- [ ] Introduction rewritten so the main question is generic-isolation adequacy rather than invention of connectivity/continuity.
- [ ] Carter et al. 2020 explicitly treated as the closest multidimensional-isolation comparator; mainland distance, stepping stones and insular network position are acknowledged as established axes.
- [ ] Weigelt & Kreft 2013 explicitly used to delimit surrounding-landmass novelty.
- [ ] Long 2009 and Sillero et al. 2018 explicitly delimit stepping-stone and graph-theoretic island-connectivity novelty.
- [ ] Daniel et al. 2023 explicitly delimits empirical graph-validation novelty.
- [ ] General connectivity precedents retained where needed so the paper does not imply that suitability+connectivity integration, source-conditioned proximity, source-area weighting, threshold sensitivity, or connectivity uncertainty are novel.
- [ ] `manuscript/structural_verified_references.md` expanded and reverified for every citation actually retained in the final island-focused manuscript.

### Figures and machine-readable manuscript evidence

The existing five-figure set is reproducible for the original manuscript, but the final figure hierarchy must be rebuilt after the island result because the scientific centre has changed.

- [x] Existing Figure 1–5 assets rebuild from committed frozen inputs.
- [x] Existing plotting sidecars and Table 3/Table S1 are retained in machine-readable form.
- [x] Existing figure contracts prohibit realised-movement/colonisation claims.
- [ ] Final Figure 1 redesigned around the island-isolation reference hierarchy (`R0 → R1 → R2 → R3 → C`) rather than generic connectivity novelty.
- [ ] Final A-Islands figure reports the prospectively frozen `C − R3` result and applicability, whatever its direction.
- [ ] Tanzania retained as a non-island strong-reference boundary/stress test rather than forced into a co-equal biological mechanism story.
- [ ] Final figures/tables generated from frozen extension artifacts with fresh byte/fingerprint tests.
- [ ] Final visual QA at chosen journal display size: typography, legends, panel labels, grayscale/colour-vision legibility and required file format/resolution.

### Reproducibility release

- [ ] Tagged software release created.
- [ ] Release commit matches final island-result manuscript/code state.
- [ ] Zenodo/archive DOI minted from the tagged release.
- [ ] Frozen original benchmarks plus island-extension contracts, geographic fingerprints, predictions, summaries, sidecars and submission manifest archived with the release.
- [x] Reproducibility environment boundary documented in `manuscript/submission/environment.md` for the original package.
- [ ] One clean-checkout command path extended to rebuild and verify the final island-focused manuscript figures/tables and the original Tanzania boundary evidence.
- [ ] Canonical fingerprints reproduced from the final release tag.
- [ ] CI/repository and release DOI resolve from the archived version.

### Manuscript package

- [ ] Final title fixed after the island result and journal-route decision.
- [ ] Abstract rewritten around the final island-isolation claim boundary and checked against the selected journal's live limit.
- [ ] Highlights/keywords regenerated for the selected journal if required.
- [ ] Author list, affiliations, corresponding author and contributions finalized and approved by all authors.
- [ ] Data Availability / Code Availability statements updated to include the island-extension frozen inputs and final release identifiers.
- [ ] Generative-AI disclosure reviewed by all authors and conformed to the selected journal's live policy at submission time.
- [ ] Supplementary materials list updated for the final island hierarchy and Tanzania boundary benchmark.
- [ ] Cover letter rewritten for the selected result-dependent journal route.

### Author confirmations still required

- [ ] Funding statement confirmed by all authors.
- [ ] Competing-interests statement confirmed by all authors.
- [ ] Ethics/permit relevance confirmed for any directly contributed field data.
- [ ] Originality and simultaneous-submission statement confirmed by all authors.

### Final live-policy verification

After the result selects the journal route:

- [ ] Re-open the selected journal's current author guide on the actual submission date.
- [ ] Confirm article type, word/abstract/keyword limits, figure formats, reference style, data/code requirements, anonymisation model and required declarations.
- [ ] Confirm the current generative-AI disclosure policy and place the statement exactly where requested.

### Claim guard

The following shorthand is explicitly prohibited because it exceeds the evidence boundary:

- `EOG outperforms SDM`;
- `EOG accounts for dispersal` without a narrower structural definition;
- `connected frequency estimates colonisation probability`;
- `Tanzania shows current flow is better in general`;
- `EOG is the first framework to integrate suitability and connectivity`;
- `occurrence anchoring is novel`;
- `scenario sensitivity or connectivity uncertainty analysis is novel`;
- `EOG discovers that island isolation is multidimensional`;
- `EOG discovers stepping stones`;
- `EOG is the first graph model of archipelagos`;
- `the EOG graph reconstructs historical colonisation routes`.

## Current stop/go rule

**GO only for the one already-frozen island-isolation adequacy execution. Do not submit, mint the final DOI, weaken R3, or run a novelty-rescue analysis while its result is unknown.**

The original A-Islands and Tanzania directions remain frozen. The new island analysis is not a reopening of those outcomes: it is a separately predeclared stronger falsification test whose full reference hierarchy and geographic inputs were fixed before its species outcomes. Once executed, its result must be retained regardless of direction.