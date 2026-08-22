# Springtail fresh paired complementarity attempt

This directory freezes one fresh, temporal, paired test of EOG Layer B in the
24-network *Folsomia candida* experiment of Rayfield et al. (2023). It is
candidate-specific validation infrastructure, not a new ecological operator and
not an API/CLI change.

The row-level experimental population table is physically separate from the
README and node/network spatial-property files at the pinned source commit. The
preflight may open only those nonresponse files, fixed Git tree metadata, and the
peer-reviewed aggregate figures named in `source_contract.json`. It must never
open the response table or the supporting spreadsheet.

The response endpoint is first **observed** colonization (`N > 0`) of each
non-source node. A released `N == 0` is a repeated photographic observed zero,
not a claim of latent biological absence. Calibration target observations end at
Day 7; later at-risk observations are held out. The physical landscape identity
(`Config` + `Rep`, called `landscapeID` by the authors) is used only for joins,
audits, and paired score aggregation. It is never a supervised feature.

The primary contrast is one frozen random forest with conventional predictors
versus the identical learner plus the unchanged, world-label-invariant Layer-B
summary. Favorable, null, and adverse outcomes are all terminally acceptable.

Outcome access requires a second commit that adds only
`OUTCOME_AUTHORIZED_ONCE.json`. That marker binds the already-green parent
commit, source contract, runner, and authorization-gate fingerprint. The outcome
workflow then makes exactly one response download, runs the exact count gate
before either model is fit, and never retries or redesigns after opening.

This README is intentionally frozen before outcome access. The terminal result
belongs in the immutable workflow artifact and an unchanged copied result JSON;
this file must not be edited to narrate a more favorable post-open story.
