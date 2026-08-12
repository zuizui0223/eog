# Structural-reachability manuscript submission checklist

## Current journal decision state

**Scientific route selected: _Ecological Informatics_, Original Research Paper.**  
**Submission remains on HOLD only until the frozen island result is incorporated into the manuscript-facing package and the existing human/release gates are completed.**

The prospectively frozen A-Islands strong-reference test was executed exactly once. Its primary `C − R3` log-loss difference was **+0.0034852** (species bootstrap 95% **+0.0024664 to +0.0045082**; 341 species favourable, 545 adverse). Negative had been predeclared as favourable to EOG, so the observed result is adverse. The predeclared journal rule therefore selects *Ecological Informatics*, not *Journal of Biogeography*.

This result does not erase the original A-Islands conditional-concordance result (`0.6177466`) because the endpoints differ. The original result remains evidence of conditional ordering beyond frozen climatic support and nearest-source distance. The new result shows that the same geography-only species-conditioned EOG feature does **not** earn an incremental predictive claim after the stronger R3 reference. Tanzania remains adverse under its matrix-aware strong reference, with spatial-block sensitivity uncertain.

## Submission-blocking gates

The paper is **not ready to submit or release** until every blocking item below is complete.

### Scientific content already secured

- [x] Original positive real-data benchmark: A-Islands plants.
- [x] Strong-competitor external benchmark: Tanzania forest birds.
- [x] Negative Tanzania result retained and independently reproduced.
- [x] Tanzania spatial-block sensitivity reported as uncertain.
- [x] Species-level inference and all non-estimable cases retained.
- [x] SDM, spatial CV, source distance, current flow and EOG roles separated.
- [x] Existing-method competitor matrix drafted.
- [x] General closest-prior novelty audit completed on 2026-08-12.
- [x] Island-specific closest-prior audit completed before the new outcome: Long 2009; Weigelt & Kreft 2013; Sillero et al. 2018; Carter et al. 2020; Daniel et al. 2023.
- [x] Verified closest-prior additions ledger expanded in `manuscript/submission/closest_prior_reference_additions.md`.

### Island-isolation strong-reference falsification gate

- [x] Final island reference hierarchy frozen before extension species outcomes (`eog_aislands_isolation_adequacy_v1_3`).
- [x] Graph universe locked to the same 842 surveyed/model-linked A-Islands units.
- [x] Polygon area recovered outcome-free for 842/842 islands and fingerprinted.
- [x] Natural Earth 1:10m v5.1.1 continental-Australia geometry frozen outcome-free and fingerprinted.
- [x] Continental-mainland distance derived for 842/842 islands and fingerprinted.
- [x] R3 fixed as climate + recipient area + mainland distance + nearest species source + unweighted and area-weighted multi-source pressure + nearest other island + surrounding-island pressure + surrounding-landmass pressure + generic component exposure + generic mainland stepping-stone frequency.
- [x] Candidate C fixed as R3 plus geography-only species-conditioned EOG connected frequency only.
- [x] Held-out labels prohibited from response-derived spatial feature construction; training presences use focal self-exclusion.
- [x] Primary endpoint, 5/5 class gate, constant-predictor rule, λ=1 fit engine, bootstrap/sign-flip inference and non-estimability accounting frozen before outcome.
- [x] **Island-isolation adequacy extension executed exactly once under the frozen v1.3 contract.** Trigger commit `a9329d929933c919fe6c1c03934f0314c40f5c50`, workflow run `31564146592`, attempt 1.
- [x] Raw held-out predictions, fold applicability, species summaries, aggregate uncertainty and result fingerprint frozen in artifact `9128998976`; aggregate/provenance/independent QA are committed in `validation/aislands_isolation_adequacy_20260812/`.
- [x] Result fingerprint frozen: `5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a`.
- [x] One-time execution workflow removed after success so the authoritative run cannot be repeated from the current repository state.
- [x] Journal route selected by the predeclared rule: **Ecological Informatics** because `C − R3` was adverse rather than robustly negative.
- [ ] **Island extension result incorporated into manuscript prose, figures, tables and cover letter without weakening R3, retuning graph scales, changing taxa, or converting the adverse result into a rescue analysis.**

### Final novelty framing

- [ ] Introduction rewritten around the question **when occurrence-conditioned structural configuration earns an incremental held-out claim relative to the declared reference**, not around invention of connectivity or residual island novelty.
- [ ] Original A-Islands conditional concordance and new A-Islands strong-reference predictive result explicitly separated as different estimands.
- [ ] Discussion states that strong-reference failure is a valid output of the structural-adequacy diagnostic rather than evidence that connectivity is unimportant.
- [ ] R1–R3 explanatory ladder is reported only as post-outcome interpretation of already-predeclared tiers; it must not replace the frozen `C − R3` endpoint.
- [ ] Carter et al. 2020, Weigelt & Kreft 2013, Long 2009, Sillero et al. 2018 and Daniel et al. 2023 retained to delimit island-isolation novelty, without implying that R3 causally explains the original concordance signal.
- [ ] General connectivity precedents retained so the paper does not imply that suitability+connectivity integration, source-conditioned proximity, source-area weighting, threshold sensitivity, graph validation or connectivity uncertainty are novel.
- [ ] `manuscript/structural_verified_references.md` expanded/reverified for every citation retained in the final manuscript.

### Figures and machine-readable manuscript evidence

- [x] Existing Figure 1–5 assets rebuild from committed original frozen inputs.
- [x] Existing plotting sidecars and Table 3/Table S1 remain machine-readable.
- [x] Existing figure contracts prohibit realised-movement/colonisation claims.
- [ ] Figure 1 revised to show `declared reference → held-out structural probe → residual / adverse-or-redundant / indeterminate` rather than presenting EOG as another connectivity index.
- [ ] A-Islands result figure reports **both** the original conditional-ordering result and the prospectively frozen strong-reference `C − R3` result, with distinct axes/labels so incompatible estimands are not visually compared as one effect size.
- [ ] Reference-tier panel reports R0/R1/R2/R3/C as explanatory context and marks `C − R3` as the only primary extension contrast.
- [ ] Tanzania retained as the external strong-reference boundary, with its spatial-block uncertainty visible.
- [ ] Final tables include 886/886 estimable species, 4231/4430 evaluable folds, 199 5/5 class-count failures, 712,515 held-out predictions, and the new result fingerprint.
- [ ] Final figures/tables generated from frozen extension artifacts with fresh sync/fingerprint tests.
- [ ] Final visual QA at Ecological Informatics display size: typography, legends, panel labels, grayscale/colour-vision legibility and required file format/resolution.

### Reproducibility release

- [ ] Tagged software release created.
- [ ] Release commit matches final revised manuscript/code state.
- [ ] Zenodo/archive DOI reserved/minted only after the revised scientific package is frozen.
- [ ] Frozen original benchmarks plus island-extension contracts, geographic fingerprints, raw authoritative outcome artifact, summaries, sidecars and submission manifest archived with the release.
- [x] Reproducibility environment boundary documented for the original package.
- [ ] Clean-checkout command extended to verify final manuscript-facing projections including the new island result while never rerunning the one-time biological outcome.
- [ ] Canonical original A-Islands, new A-Islands strong-reference, and Tanzania fingerprints reproduced from the final release package.
- [ ] CI/repository and release DOI resolve from the archived version.

### Manuscript package

- [ ] Final title fixed; current working title: **“When does landscape configuration add held-out information? An auditable reference-conditioned framework across islands and forest fragments.”**
- [ ] Abstract rewritten around the reference-conditioned evidence boundary and checked against the live Ecological Informatics limit.
- [ ] Highlights/keywords regenerated for Ecological Informatics.
- [ ] Cover letter rewritten around the positive conditional-ordering result plus adverse strong-reference tests, not a universal EOG improvement claim.
- [ ] Data/Code Availability updated to include authoritative island outcome fingerprint/provenance and final archive identifiers.
- [ ] Supplementary materials updated to archive pre-outcome contract, smoke gate, full prediction/fold/species outputs and explanatory tier QA.
- [ ] Author list, affiliations, corresponding author and contributions finalized and approved by all authors.
- [ ] Generative-AI disclosure reviewed by all authors and conformed to the live journal policy at submission time.

### Author confirmations still required

- [ ] Funding statement confirmed by all authors.
- [ ] Competing-interests statement confirmed by all authors.
- [ ] Ethics/permit relevance confirmed for any directly contributed field data.
- [ ] Originality and simultaneous-submission statement confirmed by all authors.

### Final live-policy verification

- [ ] Re-open the current *Ecological Informatics* author guide on the actual submission date.
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
- `the EOG graph reconstructs historical colonisation routes`;
- `R3 causally explains the original A-Islands conditional-concordance signal`;
- `R3 universally outperforms simpler island-isolation references`.

## Current stop/go rule

**GO to manuscript/result-package revision for Ecological Informatics. Do not rerun the authoritative island analysis, weaken R3, tune graph scales/taxa, or add a favourable dataset to rescue the island claim. HOLD DOI reservation and journal submission until the adverse island result is fully incorporated and the remaining author/policy/visual gates are complete.**
