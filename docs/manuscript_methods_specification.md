# Environmental Occupancy Geometry: methods specification

## Scope

Environmental Occupancy Geometry (EOG) describes the geometry of observed occurrence-associated states in a predeclared environmental feature space. The unit of analysis is an occurrence-by-feature matrix. EOG does not estimate habitat suitability, occurrence probability, occupancy, detection, abundance, environmental causation, or unobserved range boundaries.

Single-cloud analysis and comparative analysis are distinct. Single-cloud analysis describes geometry after within-cloud robust scaling. Comparative analysis describes differences after both groups are transformed by one frozen shared reference.

## Features and scaling

The primary feature set and feature order are fixed before EOG outcomes are calculated and require an ecological rationale. Each feature is transformed using its median and 1.4826 times its median absolute deviation. Zero-MAD features are neutralized.

Standardized span is the default 0.90 quantile of positive pairwise Euclidean distances in the transformed cloud. It is dispersion in within-cloud standardized units, not absolute environmental breadth across independently scaled groups.

## Tree summaries

A Euclidean minimum spanning tree is constructed over the transformed rows. `continuity` is environmental diameter divided by total MST length and is interpreted as MST compactness. It depends on sample size, support dimension, and cloud filling and is not generic path tortuosity.

`gap_strength` is the largest positive MST edge divided by the median positive MST edge. It is descriptive separation evidence. It has no universal cutoff and does not establish fragmentation or missing support. Component counts and labels are threshold-dependent diagnostics rather than ecological populations or habitat patches.

## Comparative extent

Comparative extent requires one robust reference fitted once and applied unchanged to both groups. The reference records feature medians, MAD scales, constant-feature flags, provenance, and a fingerprint.

The primary effect is `log(span_B / span_A)` from matched-size draws. A positive value means group B has greater observed dispersion than group A in the declared reference coordinates. Absolute span values from different references are not directly comparable.

External and training-only references may support held-out comparison in frozen reference units. Pooled-descriptive references are retrospective only. Outcome-informed construction, held-out leakage, and selection of the most favorable reference after inspecting results are invalid.

## Sampling diagnostics

Each draw takes the same number of rows from both groups: `floor(min(n_A, n_B) * fraction)`, with a minimum of four. The reported effect is the median across draws. The default sensitivity interval is the 0.05 and 0.95 quantiles.

This interval describes sensitivity to the observed occurrence rows. It is not a population confidence interval, sampling-bias correction, or posterior interval.

A two-sided label-permutation diagnostic is reported separately with a plus-one correction. Direction is supported only when at least 90% of draws preserve the estimated sign and the permutation value is below 0.10. This diagnostic requires exchangeability; spatial, temporal, repeated-measure, related-sample, or survey-effort structure may require restricted permutation or omission.

## Support classes

Comparisons of `continuity` or `gap_strength` require a shared predeclared support class. Tree-sensitive quantities must not be compared across arbitrary compact clouds, curves, rings, surfaces, or mixtures merely because they share a feature dimension.

## Manifest and runner

Each confirmatory comparison is frozen in an `AnalysisManifest` before outcomes are inspected. It records the scientific comparison, feature set, group direction, reference declaration and fingerprint, metrics, support class, resampling settings, random seed, claim scope, prohibited claims, software version, and group-specific input fingerprints.

The audited runner accepts only `row_id`, `group`, and the declared feature columns in exact order. It rejects duplicate IDs, unexpected groups, reordered or missing features, non-finite values, reference mismatch, input mismatch, and settings inconsistent with the manifest. Its deterministic result bundle carries the manifest, input, and reference identities together with the effect, diagnostics, ambiguity status, and claim-limited report text.

## Evidence boundaries

Validation showed that independent robust scaling removes absolute dilation, so within-cloud span cannot measure comparative breadth. MST compactness did not provide generic path directness across support classes. Raw gap strength was sample-size dependent and did not reliably diagnose missing bridges. Connected-null calibrations did not yield a generally valid confirmatory fragmentation procedure. These negative findings define the method's current boundaries.

## Minimum reporting

Report the feature rationale, scaling and reference modes, fingerprints, group direction, primary metric, support class where required, row counts, matched draw size, resampling and permutation settings, exchangeability rationale, effect, sensitivity interval, direction stability, permutation diagnostic, ambiguity status, software version, and prohibited interpretations.

Negative and ambiguous results remain reportable. EOG introduces no universal threshold and no composite headline score.
