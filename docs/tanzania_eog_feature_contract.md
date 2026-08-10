# Tanzania benchmark: training-only EOG feature contract

This stage materializes the structural predictors required by the already-frozen Tanzania held-out benchmark. It does **not** fit occurrence probabilities, run current flow, compare methods, or inspect EOG performance.

## Inputs

Every run regenerates the complete chain from the official Dryad source:

1. verify all nine official files against the frozen sizes and MD5 digests;
2. re-run the CSV/TIFF structural audit;
3. re-run the explicit semantics and CRS alignment audit;
4. regenerate the non-degenerate 4→3→2→1 survey-component design and require fingerprint
   `f8b37bb30d230f92ad323870020d34e2225f898b85394124b965a2d0ecdeb324`;
5. construct features for the frozen 60-species cohort only.

Any upstream drift stops feature construction.

## Outer-fold anchors

For each species and outer fold, the only initial anchors are presence sites in the **outer training set**.

- A held-out fragment uses all outer-training presences.
- A training fragment receives an additional row-level cross-fit: the target fragment is removed from its own anchor set before any distance or graph feature is constructed.
- This row-level exclusion is applied whether the target response is presence or absence. For an absence it has no effect; for a presence it prevents zero-distance and automatic anchor-component membership.
- If row-level exclusion leaves no training presence anywhere, that row is marked invalid. No distance, reachability, or imputation is invented.

This is the structural analogue of out-of-fold prediction. A training presence is never allowed to teach the probability model that occupied sites have zero anchor distance or perfect reachability merely because it was used as its own anchor.

## Distance versus graph configuration

The feature set preserves two distinct quantities.

### Nearest training-occurrence distance

`nearest_anchor_distance_km` is the great-circle distance to the nearest remaining training-presence survey fragment across both regions. Its model-scale transform is:

`log10(1 + distance_km)`

This is a conventional source-to-target distance control.

### EOG structural reachability

EOG uses only anchors in the target's own regional 42-node graph. East and West cannot connect through an EOG edge.

For each of the four frozen survey-component scenarios, the producer records:

- whether the target node belongs to a component containing a same-region anchor;
- the normalized minimax geographic bottleneck along the best available path.

`eog_connected_frequency` is the fraction of the four scenarios in which the target is reachable. Because the radius ladder induces distinct 4, 3, 2, and 1 survey-node partitions, the feature can take `0`, `0.25`, `0.5`, `0.75`, or `1` rather than collapsing to a regional indicator.

If global anchors exist but none lies in the target region:

- nearest-anchor distance remains finite;
- same-region anchor count is zero;
- connected frequency is zero;
- normalized bottleneck is null.

This separation is deliberate: simple occurrence proximity is available to both the strict reference and EOG candidate, while EOG contributes only within-landscape patch-network configuration.

## Held-out outcome boundary

The feature artifacts do not export `occur` or `observed_presence`. A held-out label is neither used to construct its row nor copied into the structural feature file.

Labels are read only for:

- identifying outer-training presence anchors;
- deterministic training-set applicability counts.

The untouched held-out label will be joined only after current-flow quantities, probability-model roles, and predictions are frozen for scoring.

## Outputs

The workflow writes canonical JSON Lines:

- `primary_features.jsonl`: 60 species × 14 LOSO folds × 14 sites = 11,760 rows;
- `spatial_sensitivity_features.jsonl`: 60 species × 5 MST-block folds × 14 sites = 4,200 rows;
- `applicability.jsonl`: one row per species × fold = 1,140 rows;
- `feature_manifest.json`: exact fingerprints, validity counts, structural support distributions, and scientific-boundary flags;
- `nonestimable_groups.json`: explicit species/fold applicability failures.

Every feature row includes the fold/species/site key, training or held-out role, anchor counts and fingerprint, nearest distance, connected frequency, median normalized bottleneck, all four scenario results, and a row fingerprint.

## Frozen applicability

Primary LOSO:

- 11,760 feature rows;
- 11,746 valid rows;
- all 840 held-out rows valid;
- 14 invalid training rows caused by removal of the sole remaining training presence;
- 826 of 840 species-fold groups retain valid training presences and absences for the anchor-augmented probability tiers;
- 14 groups are explicitly non-estimable.

Spatial MST-block sensitivity:

- 4,200 feature rows;
- 4,113 valid rows;
- 822 of 840 held-out rows valid;
- 271 of 300 species-fold groups retain an estimable anchor-augmented training set;
- 29 groups are non-estimable and remain visible.

These are applicability and feature-support diagnostics, not predictive performance results.

## Reproducibility guard

The complete feature and applicability files are canonicalized and compared with committed fingerprints. Input ordering cannot alter the result. Tests additionally require:

- held-out-label invariance;
- hard failure on self-anchoring;
- equal nearest distance but different stepping-stone configuration to produce different EOG values;
- cross-region separation;
- explicit invalidity when no training anchor remains;
- invariant output under input-row permutation.

The next scientific step is to produce the source-faithful current-flow candidates, select resistance combinations using outer-training labels only, and then fit the already-declared probability tiers. No scoring occurs in this feature stage.
