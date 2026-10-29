# Experimental integration: BAM constraints × frozen EOG geometry (v0)

## Status and scope

**Additive exploratory adapter only.** Does not reopen the frozen EOG-WF
three-endpoint programme, the JBI inverse-BAM manuscript, any historical
synthetic fingerprints, or the root v0.1 compatibility API.

Scientific question:

> How do already-declared A/B/M constraint sets change the observable
> environmental point-cloud geometry of their realized intersection G,
> when all sets share the same feature coordinates and frozen reference?

This is a **forward known-mask diagnostic**. It does not claim that an
observed G uniquely reveals A, B or M, and it does not recover a historical
route, movement probability or causal effect from a geometric statistic.

## Existing components reused without rewriting them

- `eog.comparative.RobustReference` and `infer_comparative_geometry`:
  one shared median/MAD reference; original span, MST compactness,
  descriptive MST gap strength, threshold-sensitive component count.
- `eog.reference_policy.ReferenceDeclaration`: externally declared
  source of the reference, prospective/retrospective boundary, leakage gate.
- `eog.v2.known_truth_bam.BAMWorld`: original independent A, B, M
  bit masks and G=A&B&M, plus source world fingerprint.
- **New:** `eog.bam_geometry.profile_bam_geometry` and
  `profile_known_truth_bam_world` (standalone import, not root export).

The eight masks are `U, A, B, M, AB, AM, BM, ABM` where `U` is the
unchanged candidate node universe and `ABM=G`. The adapter checks mask
shape and type, reference dimensionality/policy, and BAMWorld G equality.

## Computational/interpretive contract

1. All eight groups use the exact same declared environmental feature
   columns and reference. **Do not fit a fresh scaler within each mask.**
2. Report full-size geometry with n and an explicit `not_estimable_lt2`
   status. Do not present a zero span for zero/one-point groups.
3. Cross-mask *descriptive* comparisons use matched-size subsampling
   (by default the true G count). Deterministic 5th/95th resampling
   quantiles are sensitivity ranges, **not confidence or posterior bounds**.
4. Report `ABM versus U/A/B/M/AB/AM/BM` matched-median log span ratios.
   These are not sequential, order-invariant **causal contributions**:
   nested masks overlap, and span/MST summaries are not additive.
5. Keep `mst_compactness`, `gap_strength`, and `mst_cut_components`
   separate and descriptive. MST components in environmental feature space
   are **not** geographic connected components or species populations.
6. SHA-256 records feature matrix, eight masks, shared reference,
   policy, n, random seed, resampling settings and result values.
   The input and world fingerprints remain independently available.
7. The reference mode for the bundled synthetic example is deliberately
   `pooled-descriptive / retrospective`: the complete finite candidate
   environment was examined. Do not relabel it a prospective ecological
   validation. Empirical holdout requires a genuine external/training-only
   reference and a predeclared feature/observation policy.
8. Identical G under two different BAM decompositions must yield identical
   G geometry and sampling statistics. This is a **unit/identifiability
   demonstration**, not independent evidence beyond the parent BAM theory.

## Reproduction

```bash
python -m pytest -q tests/test_bam_geometry_bridge.py
python benchmarks/run_bam_geometry_bridge_v0.py
```

The runner compares an unchanged 7×3 known-truth BAM landscape with
(i) no required partner, (ii) required partner and (iii) an impermeable
barrier. It prints a deterministic, descriptive JSON receipt. No new
field observations or heldout response rows are consumed.

## What the integration does **not** yet do

- Geographical support-topology overlay: the pre-existing
  `eog.support_topology` module takes a **frozen 2-D support field** and
  spatial occurrence anchors; BAM mask geometries on arbitrary feature
  matrices are not such fields. A future adapter must explicitly supply
  CRS, grid alignment, missing-mask semantics, anchors, thresholds, and
  neighbourhood definition before spatial components can be compared.
- Real ecological identification of which constraint dominates: independent
  abiotic, interaction, movement and observation-process evidence is needed.
- PERMDISP/hypervolume competitor benchmark or external macroecological
  validation: these must be separately designed and scored, without
  changing already-consumed endpoints or retrofitting the parent papers.

## Immediate scientific gate for the next phase

Use the existing **predeclared known-truth BAM** world roster and *new*
pre-score geometry endpoints to ask whether geometry distinguishes
different realized G under matched reference and sample size. Separately
audit worlds with identical G but different A/B/M, for which purely
G-derived statistics are necessarily non-identifying. Only then add a
georeferenced support-topology adapter and independent empirical tests.

A geometry metric cannot manufacture information absent from the
original occurrence + environmental observations.
