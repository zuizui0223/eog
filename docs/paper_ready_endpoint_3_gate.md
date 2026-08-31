# Paper-ready endpoint-3 binding gate

## Purpose

The reusable EOG validation gates already keep response access behind metadata,
geometry, estimability, structural, model, runtime, and once-only freezes. Endpoint 3
also carries paper-level obligations that must not drift independently:

- the already-frozen cross-ecosystem synthesis;
- the secondary ten-feature placebo;
- endpoint-specific favorable/null/adverse thresholds;
- the unchanged Layer-B representation;
- the hard stop on further candidate hunting after a valid predictive terminal result.

`src/eog/v2/paper_ready_endpoint.py` binds those objects into one response-blind receipt.
It adds no ecological operator and does not authorize opening a candidate by itself.

## Required sequence

1. A genuinely new candidate passes `CandidatePreflightDeclaration` and its
   response-blind metadata preflight.
2. Candidate-specific geometry, effort/surveyed-negative semantics, structural scales,
   holdout, source/process closure, Layer A, Layer B, comparator, preprocessing,
   decision thresholds, runtime, and STOP behavior are frozen through the existing
   sixteen-key `FrozenOutcomeAccessContract`.
3. The outcome-access contract's `metrics_decision` value must equal the actual
   `PredictiveComplementarityDeclaration.fingerprint`.
4. Its `layer_b_representation` value must equal the unchanged
   `PredictiveComplementarityDeclaration.eog_feature_fingerprint`.
5. The endpoint-3 boundary must bind the canonical fingerprints recorded in
   `validation/paper_ready_replication/frozen_endpoint_3_boundary_manifest.json`.
6. Only a `ready_for_endpoint_3_once_only_runner` receipt permits the already-frozen
   runner to begin. The exact count gate still runs first; failure means zero fits and
   zero heldout scores.

The attempt ID must be identical across candidate preflight, outcome access, and the
paper-ready boundary. A terminal candidate cannot be marked fresh and no response row
may already be open.

## Interpretation

This gate prevents detached or post-hoc contracts; it does not make a candidate
scientifically favorable. A source, transport, structural, schema, non-estimable, or
execution STOP retains its declared STOP meaning. It is not converted into a predictive
null or adverse result.

After endpoint 3 reaches a valid predictive favorable/null/adverse terminal decision,
candidate hunting stops. The only remaining work is the frozen synthesis, placebo
interpretation, figures, evidence table, manuscript, and submission package.
