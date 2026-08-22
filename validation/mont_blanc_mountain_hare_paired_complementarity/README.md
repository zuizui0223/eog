# Mont-Blanc mountain-hare fresh paired complementarity attempt

This directory freezes one fresh temporal test of EOG Layer B in the 46-camera
Alpine mountain-hare (*Lepus timidus varronis*) survey in the French Mont-Blanc
massif. It is candidate-specific validation infrastructure, not a new ecological
operator and not an API/CLI change.

Dryad version `277486` contains six independently stored objects. Preflight uses
the official version redirect and tokenized file manifest, keeps signed URLs only
in memory, and downloads only `README.md` and `camerainfo.csv`. The latter fixes
the 46-station registry, WGS84 geometry, setup dates, and camera-problem intervals.
It verifies the physical `taghare_1day.csv` header with 13 one-byte Range requests
and stops at the first CR. No response row or value is opened. The three ancillary
vegetation objects remain unopened.

The endpoint is observed monthly camera-detection reappearance. A risk row is a
station with at least 20 response-independent active camera days and zero released
contact dates in source month *t*, followed by at least 20 active days in target
month *t+1*. An event is at least one unique released contact date in the target
month. This is not latent occupancy, abundance, physical immigration, parentage,
or reconstructed seasonal migration.

January 2019 through December 2020 supplies 23 calibration transitions. January
2021 through June 2022 supplies 18 heldout transitions, scored in six calendar
quarters. Published materials do not provide split-specific zero-to-positive and
zero-to-zero counts, so preflight preserves `uncertain_pre_response` and authorizes
only an exact-count-first once-only run. Count failure means zero model fits and
zero heldout scores.

The primary contrast is a frozen strong random forest with calendar season,
response-independent terrain, habitat, camera, geometry, effort, conventional
source-distance exposure, and lagged contact-day predictors versus the identical
learner plus the unchanged ten-column
`symmetric_world_support_summary_v1` Layer-B block. Exact Station IDs and exact
world IDs are never supervised features. Favorable, null, and adverse results are
all terminally acceptable.

Outcome access requires a second commit adding only
`OUTCOME_AUTHORIZED_ONCE.json`. That marker binds the already-green parent commit,
contract, runner, preflight fingerprint, and 16-key authorization result. The
outcome workflow performs one full response download, never retries, and never
redesigns after opening.
